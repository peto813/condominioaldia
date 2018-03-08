# -*- coding: utf-8 -*-
import string, random
from allauth.account.adapter import DefaultAccountAdapter
from django.utils.translation import gettext, gettext_lazy as _
from condominioaldia_app.models import Condominio, Affiliate
from condominioaldia_app.tasks import (
    send_confirmation_task,
    send_email,
    )
from rest_framework.response import Response
from condominioaldia_app.utils import get_user_type
from django.template import loader
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from condominioaldia_app.serializers import registroSerializer
from allauth.account.utils import (
	send_email_confirmation,
	user_username, 
	user_email, 
	user_field
	)

def get_comission(affiliate):
    related_condominios_count = affiliate.condominios.all().count()
    if related_condominios_count <= 10:
        comission = 0.1
    elif 11<related_condominios_count<=25:
        comission = 0.125
    elif related_condominios_count>25:
        comission = 0.15
    return comission


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

class condominioaldiaAccountAdapter(DefaultAccountAdapter):
	def send_confirmation_mail(self, request, emailconfirmation, signup):
		current_site = get_current_site(request)
		activate_url = self.get_email_confirmation_url(
			request,
			emailconfirmation)

		ctx = {
			"user": emailconfirmation.email_address.user,
			"activate_url": activate_url,
			"current_site": current_site,
			"key": emailconfirmation.key,
		}
		user_type = get_user_type(request)
		if user_type =='condominio':
			ctx['condominio'] = request.user.first_name.title() + ' ' +request.user.last_name.title()
		if signup:
			email_template = 'account/email/email_confirmation_signup'
		else:
			email_template = 'account/email/email_confirmation'
		self.send_mail(email_template,emailconfirmation.email_address.email,ctx, signup)

	def save_user(self, request, user, serializer, commit=True):
		"""
		Saves a new `User` instance using information provided in the
		signup form.
		"""
		secure = request.is_secure()
		protocol = 'https' if secure==True else 'http'
		serializer = registroSerializer(data  = request.data )

		url = '%s://%s' %( protocol, request.get_host())
		if serializer.is_valid():
			affiliate= serializer.validated_data.pop('affiliate', None)
			data = serializer.validated_data
			instance = data.get('instance')
			client_type = data.pop('client_type', None)
			first_name = data.get('first_name')
			last_name = data.get('last_name')
			email = data.get('email')
			username = data.get('email').replace('@', '')
			user_email(user, email)
			user_username(user, username)
			if first_name:
				user_field(user, 'first_name', first_name)
			if last_name:
				user_field(user, 'last_name', last_name)
			if 'password1' in data:
				user.set_password(data["password1"])
			else:
				user.set_unusable_password()
			self.populate_username(request, user)
			if commit:
				user.save()
				# Ability not to commit makes it easier to derive from
				# this adapter by adding
				if client_type:
					if client_type == 'condominio':
						condominio_data = {
							'rif' :data.get('rif'),
							'pais' :data.get('pais'),
							'terminos' :data.get('terminos'),
							'comprobante_rif' :data.get('comprobante_rif'),
							'user':user
						}
						instance = Condominio.objects.create(**condominio_data)
						if affiliate:
							instance.affiliate=affiliate
							comission = get_comission(affiliate)
							affiliate.comission = comission
							affiliate.save()
							#send email to affiliate
							protocol = 'https' if request.is_secure() else 'http'
							site_name=  get_current_site(request).name
							site_url = protocol+'://'+site_name

							message_context = {
								'affiliate': affiliate.user.get_full_name(),
								'condominio_name' : str(data.get('first_name')) + ' '+str(data.get('last_name') or ''),
								'site_url': site_url,
								'rif' : data.get('rif'),
								'pais' : data.get('pais')
							}
							subject_context= {
								'condominio_name' : str(data.get('first_name')) + ' '+str(data.get('last_name') or '')
							}
							subject = loader.render_to_string('account/email/affiliate_condo_subject.txt', subject_context)
							message= loader.render_to_string('account/email/affiliate_condo_message.txt', message_context)
							send_email.delay(subject, message, settings.DEFAULT_FROM_EMAIL, [affiliate.user.email])

					elif client_type =='afiliado':
						afiliado_dada = {
							'rif' :data.get('rif'),
							'terminos' :data.get('terminos'),
							'comprobante_rif' :data.get('comprobante_rif'),
							'comission' : 0.10,
							'user':user
							#'url' : url + '/#/registro?affiliate='+ str(user.id)
						}
						instance = Affiliate.objects.create(**afiliado_dada)
						instance.url = url + '/#/registro?affiliate='+ str(user.pk)

			instance.save()
			return user
		else:
			return Response(serializer.errors)

	def send_mail(self, template_prefix, email, context, signup):
		"""
		Renders an e-mail to `email`. `template_prefix` identifies the
		e-mail that is to be sent, e.g. "account/email/email_confirmation"
		"""
		
		user = context['user']
		user_type= user.get_user_type()
		# if user_type =='condominio':
		# 	condominio = user.condominio
		# elif user_type =='inquilino':
		# 	print dir(user.inquilino)
		# 	inmuebles = user.inquilino.inmueble_set.all()
		# 	if inmuebles.exists():
		# 		first_inmueble = inmuebles.earliest('created')
		# 		condominio = first_inmueble.condominio
		context['user'] = user.id
		#context['condominio'] = self.request.user.condominio.user.get_full_name()
		context.pop('current_site')
		if user_type =='inquilino' and self.request.user.is_authenticated():
			context['signup'] =signup
			template_prefix = 'account/email/inquilino_email_confirmation_signup'
			password = id_generator(8, string.ascii_uppercase + string.digits)
			context['password'] = password
			if self.request.user.is_staff:
				#print self.request.condominio.user.get_full_name()#passed in view request csv view
				condominio = self.request.condominio.user.get_full_name()
			else:
				condominio = self.request.user.condominio.user.get_full_name()

			context['condominio'] = condominio

			if signup == True:
				user.set_password(password)
				user.save()


		data = {
			'template_prefix': template_prefix,
			'email':email,
			'context': context
		}
		
		send_confirmation_task.delay(data)