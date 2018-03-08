# -*- coding: utf-8 -*-
import os, shutil
import decimal
from django.core.files.storage import default_storage
from django.core.exceptions import ValidationError
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.sites.models import Site
from django.conf import settings
from django.db.models import Sum
from condominioaldia_app.tasks import send_email
from condominioaldia_app.utils import update_condo_status
from django.contrib.humanize.templatetags.humanize import intcomma
from django.template import loader
from django.utils.translation import gettext, gettext_lazy as _

def post_recipiente_name(sender, instance, **kwargs):
	instance.name= str(instance.name).lower().strip()
	instance.save()

def user_deleted(sender, instance, **kwargs):
	try:
		#DELETE COMPROBANTE RIF
		current_dir = os.path.dirname(instance.condominio.comprobante_rif.path)
		parent= os.path.dirname(current_dir)
		shutil.rmtree(parent)
		#DELETE LOGO
		current_dir = os.path.dirname(instance.condominio.logo.path)
		parent= os.path.dirname(current_dir)
		shutil.rmtree(parent)	
	except: 
		pass

# def check_aliquot(sender, instance, **kwargs):
# 	''' 
# 	this method checks all of the aliquot totals,
# 	if its within acceptable range it activates the condo
# 	'''
# 	inmuebles = instance.condominio.inmueble_set.all()
# 	if inmuebles.exists():
# 		total= inmuebles.aggregate(total_alicuota= Sum('alicuota'))['total_alicuota'] or 0
# 		if total >=decimal.Decimal(settings.MINIMA_ALICUOTA):
# 			instance.condominio.activo = True
# 			instance.condominio.save()
# 		else:
# 			instance.condominio.activo = False
# 			instance.condominio.save()


def factura_condo_extra_col_update_account_balance(sender, instance, **kwargs):
	''' 
	runs when an extra_col is saved and updates the 
	condominium account balance
	'''
	instance.banco.balance -=instance.monto
	instance.banco.save()

# def factura_condominio_close_month(sender, instance, created,**kwargs):
# 	''' 
# 	sets the initial balance to the balance when instance is created
# 	'''
# 	if created == True:
# 		bancos = instance.condominio.bancos_set.all()
# 		bancos.update(editable = False)
# 		for item in bancos:
# 			item.ingreso_condominio_set.all().update(cerrado=True)
# 			item.egreso_condominio_set.all().update(cerrado=True)
# 		instance.save()

def email_owner(sender, instance, created,**kwargs):
	if created == True:
		current_site = Site.objects.get_current()
		message_context = {
			'recipient_name': instance.inmueble.inquilino.user.get_full_name().title(),
			'condominio_name':instance.inmueble.condominio.user.get_full_name().title(),
			'cobranza_subject': instance.asunto,
			'currency': instance.inmueble.condominio.pais.moneda,
			'monto':intcomma( instance.monto.quantize(settings.TWOPLACES), 2),
			'site_name': current_site.name,
			'site_url': current_site.domain

		}
		subject_context= {
			'condominio_name':instance.inmueble.condominio.user.get_full_name().title()
		}
		subject = loader.render_to_string('account/email/cobranza_subject.txt', subject_context)
		message= loader.render_to_string('account/email/cobranza_message.txt', message_context)
		send_email.delay(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.inmueble.inquilino.user.email])





def condo_account_initial_balance(sender, instance, created,**kwargs):
	''' 
	sets the initial balance to the balance when instance is created
	'''
	from condominioaldia_app.models import Bancos
	if created == True:
		instance.banco=instance.banco_pais.name
		instance.balance=instance.balanceinicial
		instance.save()
	else:

		ingresos=instance.ingreso_condominio_set.filter(aprobado=True).aggregate(total_mes= Sum('monto'))['total_mes'] or 0
		egresos =instance.egreso_condominio_set.all().aggregate(total_mes= Sum('monto'))['total_mes'] or 0
		Bancos.objects.filter(pk = instance.pk).update(balance = instance.balanceinicial-egresos+ingresos)
		instance.balance = instance.balanceinicial-egresos+ingresos
		#print instance.balance
		#instance.save()
		#print instance.balanceinicial, 'balance'
		#print instance.balance, 'balance'

def condo_payment_saved(sender, instance, **kwargs):
	'''
	runs before a condo payment is saved. 
	1) updates condo status based on late payments
	2) assigns affiliate payments and emails affiliate
	'''
	#LEAVE THIS HERE TO AVOID CIRCULAR IMPORT ERROR
	from condominioaldia_app.tasks import send_email
	from condominioaldia_app.serializers import Affiliate_IncomeSerializer

	pago_condominio = instance
	condominio = instance.factura.condominio
	factura_condominio = instance.factura
	affiliate = factura_condominio.condominio.affiliate
	update_condo_status(condominio)#update condo status

	#1) SET AFFILIATE CONDO BILL PAYED TO TRUE
	pago_condominio.factura.pagado = True
	pago_condominio.factura.save()
	#2)run when there is an affiliate and the payment has been approved
	if affiliate and instance.aprobado == True:
		request= instance.request
		protocol = 'https' if request.is_secure() else 'http'
		site_name=  get_current_site(request).name
		site_url = protocol+'://'+site_name

		monto =affiliate.comission * factura_condominio.monto
		data = {
			'comission' : affiliate.comission,
			'monto' : monto.quantize(settings.TWOPLACES),
			'condominio' : condominio.rif,
			'condominio_name' : condominio.user.get_full_name(),
			'pagado' : False,
			'affiliate' :affiliate.pk,
			'factura_condominio': factura_condominio.pk
		}
		serializer = Affiliate_IncomeSerializer(data=data)
		if serializer.is_valid():
			affiliate_income =serializer.save()
			message_context = {
				'affiliate': affiliate.user.get_full_name().title(),
				'condominio' : condominio.user.get_full_name().title(),
				'monto' :intcomma( monto.quantize(settings.TWOPLACES), 2),
				'currency': condominio.pais.moneda,
				'site_url':site_url.lower(),
				'site_name':site_name
			}
			subject_context= {
				'condominio':factura_condominio.condominio.user.get_full_name().title()
			}
			subject = loader.render_to_string('account/email/affiliate_new_income_subject.txt', subject_context)
			message= loader.render_to_string('account/email/affiliate_new_income_message.txt', message_context)
			send_email.delay(subject, message, settings.DEFAULT_FROM_EMAIL, [affiliate.user.email])


