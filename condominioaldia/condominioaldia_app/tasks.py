# -*- coding: utf-8 -*-
# Create your tasks here
from __future__ import absolute_import, unicode_literals
import decimal
from django.core.mail import send_mail, send_mass_mail, mail_admins, EmailMessage, EmailMultiAlternatives, get_connection
from allauth.account.adapter import DefaultAccountAdapter
from celery import shared_task
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.humanize.templatetags.humanize import intcomma
from django.utils.translation import gettext, gettext_lazy as _
from django.template import defaultfilters
#from condominioaldia_app.models import *
from condominioaldia_app.utils import update_condo_status, month_range_dt, get_total_cobranzas
from django.db.models import Sum
from django.template import loader
#from condominioaldia_app.bills import FacturaCondominioView
from easy_pdf.rendering import render_to_pdf
from dateutil.relativedelta import relativedelta
from allauth.account.models import EmailConfirmation
#import os

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'condominioaldia.settings')
# app = Celery('condominioaldia', broker='amqp://',broker_url = 'amqp://')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
#app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
#app.autodiscover_tasks()
def get_cols( inmuebles, mes):
	from condominioaldia_app.utils import month_range_dt
	month_range = month_range_dt(mes)
	cols = ['Inmueble', 'Residente', 'Balance Presente', 'Pagos', 'Cuota', 'Balance Nuevo' ]
	cobranza_names = []
	for inmueble in inmuebles:
		cobranzas_inmueble= inmueble.cobranza_condominio_set.filter(mes__range = (month_range[0],month_range[1]))
		for cobranza in cobranzas_inmueble:
			if not cobranza.asunto in cobranza_names:
				cobranza_names.append(cobranza.asunto)
	cobranza_names = sorted(cobranza_names)
	for item in cobranza_names:
		cols.insert(5, str(item))
	return {'cols':cols,'dynamic_cols': cobranza_names}

@shared_task
def test(arg):
    print(arg)


@shared_task 
def print_time():#CELERY BEAT PROCESS
	from django.utils import timezone

###SERVER MAINTENANCE TASKS##################

#DELETE EXPIRED CONFIRMATIONS

@shared_task 
def delete_expired_confirmations_beat():#CELERY BEAT PROCESS
	EmailConfirmation.objects.delete_expired_confirmations()

@shared_task 
def update_condo_status_beat():#CELERY BEAT PROCESS
	from condominioaldia_app.models import Condominio
	condominios = Condominio.objects.all()
	for condominio  in condominios:
		update_condo_status(condominio)

####################################


@shared_task 
def email_admins(subject, message, fail_silently=None):
 	mail_admins(subject, message, fail_silently)

@shared_task
def send_mass_email(datatuple,fail_silently=None):
    send_mass_mail(datatuple,fail_silently = fail_silently)

@shared_task
def send_email( subject, message, correoCondominioaldia, correosList, fail_silently = None, auth_user=None, auth_password=None, connection=None, html_message=None, reply_to= None, html_email_template_name= None, context= None ):
    email = EmailMultiAlternatives(subject, message, correoCondominioaldia, correosList,reply_to = reply_to)
    if html_message is not None:
        #html_email = loader.render_to_string(html_email_template_name, context)
        email.attach_alternative(html_message, 'text/html')
    email.send()

	# email = EmailMessage(
	#     subject,
	#     message,
	#     correoCondominioaldia,
	#     correosList,
	#     [],
	#     reply_to=reply_to
	# )
	# email.send()

@shared_task
def send_confirmation_task( data_obj ):
	data_obj['context']['current_site'] = Site.objects.get_current()
	user= User.objects.get(id=data_obj['context']['user'])
	data_obj['context']['user'] = user
	data_obj['context']['name'] = user.get_full_name().title()
	msg = DefaultAccountAdapter().render_mail(data_obj['template_prefix'], data_obj['email'], data_obj['context'])
	msg.send()

@shared_task
def send_pwd_recovery_task( subject, body, from_email, to_email, html_email_template_name ):
    email_message = EmailMultiAlternatives(subject, body, from_email, to_email)
    if html_email_template_name is not None:
        html_email = loader.render_to_string(html_email_template_name, context)
        email_message.attach_alternative(html_email, 'text/html')
    email_message.send()


@shared_task
def email_factura_condominio( subject, body, from_email, to_email, bcc, context):
	from condominioaldia_app.models import Egreso_Condominio, Factura_Condominio
	email = EmailMessage(
		subject,
		body,
		from_email,
		bcc,
		[]
	)
	template = 'pdf/condo_bill.html'
	factura = Factura_Condominio.objects.get(id=int(context['factura']))
	context['factura'] =factura
	context['due_date'] =factura.mes+relativedelta(months=1)
	egresos =list(Egreso_Condominio.objects.filter(pk__in =context['egresos']))

	# for extra_col in factura.extra_cols.all():
	# 	egresos.append({
	# 		'tipo_egreso' :extra_col.titulo,
	# 		'monto' :extra_col.monto,
	# 		'condominio': factura.condominio
	# 	})

	context['egresos'] = egresos
	filename = _('%s_bill.pdf' %(defaultfilters.date(factura.mes, "F Y")))
	pdf = render_to_pdf(template, context)
	content_type = 'application/pdf'
	email.attach(filename, pdf, content_type)
	email.send()


def render_propietario_report_pdf( inmueble_pk, mes, site_name):
	'''

	this method generates the resumen for propietarios pdf
	'''
	from condominioaldia_app.models import Inmueble

	month = mes
	inmueble = Inmueble.objects.get(pk=inmueble_pk)
	#GET THE EGRESOS
	month_range = month_range_dt(month)
	egresos =inmueble.condominio.egreso_condominio_set.filter(mes__range=(month_range[0], month_range[1]))
	sum_egresos = egresos.aggregate(total_deuda= Sum('monto'))['total_deuda'] or 0
	######################
	#cobranzas = inmueble.cobranza_condominio_set.filter(payment__aprobado =True)
	cobranzas = inmueble.cobranza_condominio_set.filter(mes__range=(month_range[0],month_range[1]))
	sum_cobranzas= get_total_cobranzas(cobranzas, inmueble, sum_egresos)

	pagos = inmueble.ingreso_condominio_set.filter(mes__range=(month_range[0], month_range[1]), aprobado=True)
	factura_propietario =inmueble.factura_propietario_set.filter(mes__range=(month_range[0], month_range[1]))[0]
	context = {}
	context['mes'] =month
	context['aviso'] ='''
	De acuerdo a los articulos 14 y 15 de la ley horizontal, 
	el presenteaviso de cobro tiene valor yfuerza ejecutiva
	'''
	#NEED TO GET TOTAL OWED
	debt_properties = inmueble.condominio.inmueble_set.filter(deuda_actual__lt=0)
	context['debt_properties'] = debt_properties
	context['pagos'] = pagos
	context['site_name']=site_name
	context['inmueble']=inmueble
	context['cobranzas']=cobranzas
	context['cuentas'] = inmueble.condominio.bancos_set.all()
	context['egresos'] = egresos
	context['sum_cobranzas'] =decimal.Decimal(sum_cobranzas).quantize(settings.TWOPLACES)
	context['factura_propietario'] =factura_propietario
	context['paper_type'] ='landscape'
	context['sum_egresos'] =sum_egresos
	context['pagesize'] ='letter'
	context['page_margin_top'] ='1cm'
	context['page_margin_bottom'] ='1cm'
	context['page_margin_left'] ='1cm'
	context['page_margin_right'] ='1cm'
	context['footer_height'] ='1cm'
	context['balance_title'] ='Deuda' if factura_propietario.monto <0 else 'Balance'
	template = 'pdf/reporte_mensual_propietario.html'
	pdf = render_to_pdf(template, context)
	return pdf


@shared_task
def email_egresos_cuotas( context):
	from condominioaldia_app.models import Egreso_Condominio, Condominio, Factura_Propietario, Bancos
	egresos_template = 'pdf/egresos_condominio_pdf.html'
	cuotas_template = 'pdf/relacion_cuotas_pdf.html'
	egresos = Egreso_Condominio.objects.filter(id__in =context.pop('egresos'))
	condominio = Condominio.objects.get(pk = context.pop('condominio'))
	facturas = Factura_Propietario.objects.filter(pk__in =context.pop('facturas'))
	site_name=context.pop('site_name')
	inmueble_pk = context.pop('inmueble_pk')
	site_url=context.pop('site_url')
	content_type = 'application/pdf'

	#good till here
	extra_cols = []
	extra_cols_list = []
	if len(facturas) >0:
		latest_bill = facturas.latest('created')
		mes = latest_bill.mes
		# for item in latest_bill.extra_cols.all():
		# 	extra_cols.append(item)
		# 	extra_cols_list.append(item.titulo)
	else:
		mes = condominio.user.date_joined

	totals = {}
	# for y in extra_cols_list:
	# 	totals[y] = 0

	# for item in extra_cols_list:
	# 	sum_x= 0
	# 	for factura in facturas:
	# 		for extra_col in factura.extra_cols.all():
	# 			if extra_col.titulo == item:
	# 				sum_x+=extra_col.monto
	# 	totals[item]=sum_x

	context ={
		'condominio': condominio,
		'paper_type':'landscape',
		'egresos':egresos,
		'mes': mes,
		'pagesize':'letter',
		'page_margin_top':'1cm',
		'page_margin_bottom':'1cm',
		'page_margin_left':'1cm',
		'page_margin_right':'1cm',
		'footer_height':'1cm'
	}

	#EGRESOS/RESUMEN PDF
	egresos_filename = _('%s_resumen.pdf' %(defaultfilters.date(mes, "F Y")))
	#egresos_pdf = render_to_pdf(egresos_template, context)
	egresos_pdf =render_propietario_report_pdf( inmueble_pk, mes, site_name)
	#email.attach(filename, pdf, content_type)

	#CUOTAS TEMPLATE
	del context['egresos']
	context['paper_type'] = 'portrait'
	context['totals'] = totals

	

	##################################
	month_range = month_range_dt(mes)
	queryset = facturas.filter(mes__range =(month_range[0], month_range[1]))

	balance_previo = queryset.aggregate(total_mes= Sum('monto'))['total_mes'] or 0
	sum_cuotas = -1*(queryset.aggregate(total_mes= Sum('cuota'))['total_mes'] or 0)
	sum_pagos = queryset.aggregate(total_mes= Sum('pagos'))['total_mes'] or 0
	sum_deuda_nueva = queryset.aggregate(total_mes= Sum('monto'))['total_mes'] or 0

	context['sum_cuotas'] =sum_cuotas
	context['sum_deuda_nueva'] =sum_deuda_nueva
	context['sum_pagos'] =sum_pagos
	columns = get_cols(condominio.inmueble_set.all(), mes)
	context['columns'] = columns['cols']
	context['balance_previo'] =balance_previo
	context['dynamic_cols'] = columns['dynamic_cols']
	context['dynamic_cols'] = columns['dynamic_cols']
	#######################################
	context['cuentas'] = Bancos.objects.filter(condominio =condominio)
	context['facturas'] = Factura_Propietario.objects.filter(pk__in=facturas)
	cuotas_filename = _('%s_summary.pdf' %(defaultfilters.date(mes, "F Y")))
	cuotas_pdf = render_to_pdf(cuotas_template, context)

	# messages=[]

	subject_context= {
		'condo_name':condominio.user.get_full_name(),
		'month':defaultfilters.date(mes, "F Y")
	}

	subject = loader.render_to_string('account/email/propietario_new_bill_subject.txt', subject_context)
	
	with get_connection() as connection:
		for bill in facturas:
			message_context = {
				'propietario_name': str(bill.inmueble.inquilino.user.first_name).title(),
				'condo_name': condominio.user.first_name.title(),
				'site_name': site_name.title(),
				'monto': intcomma( abs(bill.monto.quantize(settings.TWOPLACES)) , 2),
				'currency':condominio.pais.moneda,
				'site_url':site_url,
				'actual_debt':bill.monto.quantize(settings.TWOPLACES)
			}
			body= loader.render_to_string('account/email/propietario_new_bill.txt', message_context)
			email = EmailMessage(
				subject,
				body,
				settings.DEFAULT_FROM_EMAIL,
				[bill.inmueble.inquilino.user.email],
				connection=connection
			)
			email.attach(egresos_filename, egresos_pdf, content_type)
			email.attach(cuotas_filename, cuotas_pdf, content_type)	
			email.send(fail_silently=False)

