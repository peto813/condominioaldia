# -*- coding: utf-8 -*-
import re, csv
from django.contrib import messages
from rest_framework import serializers
from condominioaldia_app.models  import *
from condominioaldia_app.tasks import send_email,send_mass_email
from condominioaldia_app.utils import *
from condominioaldia_app.forms import customPasswordResetForm
from django.contrib.auth.models import User
from django.contrib.humanize.templatetags.humanize import intcomma
from django.conf import settings
from django.template import loader
from django.db.models import F, FloatField, Sum
from django.utils import timezone
from allauth.account.models import EmailAddress
from validators import *
from allauth.account import app_settings
from rest_framework.exceptions import ValidationError
from rest_auth.serializers import LoginSerializer, PasswordResetSerializer,PasswordChangeSerializer
from allauth.account.utils import send_email_confirmation
from django.utils.translation import gettext, gettext_lazy as _
from django.contrib.sites.shortcuts import get_current_site
from dateutil.relativedelta import relativedelta


class CustomModelSerializer(serializers.ModelSerializer):
	pass

class CustomSerializer(serializers.Serializer):
	pass

class customPasswordChangeSerializer(PasswordChangeSerializer):
	def validate_old_password(self, value):
		invalid_password_conditions = (
			self.old_password_field_enabled,
			self.user,
			not self.user.check_password(value)
		)

		if all(invalid_password_conditions):
			raise serializers.ValidationError(_('Invalid password'))
		return value


class customPasswordResetSerializer(PasswordResetSerializer):
	password_reset_form_class = customPasswordResetForm
	def validate_email(self, value):
		# Create PasswordResetForm with the serializer
		self.reset_form = self.password_reset_form_class(data=self.initial_data)
		try:
			email = User.objects.get(email = value)
		except:
			raise serializers.ValidationError(_("E-mail does not exist"))
		if not self.reset_form.is_valid():
			raise serializers.ValidationError(self.reset_form.errors)
		return value

class InmuebleCategorySerializer(serializers.ModelSerializer):
	#name= serializers.CharField(required = True)
	class Meta:
		model = InmuebleCategory
		fields = ['id','name','condominio']
		read_only_fields = ('id',)

class PaisesSerializer(serializers.ModelSerializer):
	class Meta:
		model = Paises
		#fields = ( 'title', 'created' )
		fields = '__all__'

class FaqSerializer(serializers.ModelSerializer):
	class Meta:
		model = Faq
		fields = '__all__'



class CondominioSerializer(serializers.ModelSerializer):
	pais =PaisesSerializer(read_only=True)
	logo = serializers.ImageField(required = False, allow_null= True)
	nombre = serializers.CharField(source ='user.first_name', read_only = True)
	class Meta:
		model = Condominio
		fields = '__all__'

	def validate_logo(self, logo):
		if logo:
			if logo.size > 2097152:
				#self.add_error('logo', "Archivo muy grande")
				raise ValidationError(_('Image too large.'))
		return logo

	def update(self, instance, validated_data):
		instance.logo = validated_data.get('logo',  instance.logo )
		instance.telefono1 = validated_data.get('telefono1',  instance.telefono1 )
		instance.telefono2 = validated_data.get('telefono2',  instance.telefono2 )
		instance.save()
		return instance

class CustomLoginSerializer(LoginSerializer):

	def validate(self, attrs):
		username = attrs.get('username')
		email = attrs.get('email')
		password = attrs.get('password')
		user = None
		if 'allauth' in settings.INSTALLED_APPS:
			# Authentication through email
			if app_settings.AUTHENTICATION_METHOD == app_settings.AuthenticationMethod.EMAIL:
				user = self._validate_email(email, password)

			# Authentication through username
			if app_settings.AUTHENTICATION_METHOD == app_settings.AuthenticationMethod.USERNAME:
				user = self._validate_username(username, password)

			# Authentication through either username or email
			else:
				user = self._validate_username_email(username, email, password)

		else:
			# Authentication without using allauth
			if email:
				try:
					username = UserModel.objects.get(email__iexact=email).get_username()
				except UserModel.DoesNotExist:
					pass

			if username:
				user = self._validate_username_email(username, '', password)

		# Did we get back an active user?
		if user:

			if not user.is_active:
				msg = _('User account is disabled.')
				raise ValidationError(msg)

		else:
			msg = _('Unable to log in with provided credentials.')
			raise ValidationError(msg)

		# If required, is the email verified?
		if 'rest_auth.registration' in settings.INSTALLED_APPS:
			if app_settings.EMAIL_VERIFICATION == app_settings.EmailVerificationMethod.MANDATORY:
				email_address = user.emailaddress_set.get(email=user.email)
				if not email_address.verified:
					request= self.context.get('request')
					send_email_confirmation(request, user, signup=False)
					raise serializers.ValidationError(_('You have not verified your E-mail, please check your inbox'))
			if hasattr(user, 'condominio'):
				if not user.condominio.aprobado:
					raise ValidationError(_('Your condominium is being evaluated by our analysts!'))
			elif hasattr(user, 'affiliate'):
				if not user.affiliate.aprobado:
					raise ValidationError(_('Your affiliation is being evaluated by our analysts!'))
			
			elif hasattr(user, 'inquilino'):
				if not user.inquilino.condominio_set.all().exists():
					raise ValidationError(_('This owner contains no properties affiliated to it.'))
		
		attrs['user'] = user
		return attrs


class VoteSerializer(serializers.Serializer):
	vote = serializers.BooleanField(required= True)
	poll = serializers.PrimaryKeyRelatedField(queryset = Poll.objects.all(), required= True)
	user = serializers.PrimaryKeyRelatedField(queryset = User.objects.all(), required= True)
	inmueble =serializers.PrimaryKeyRelatedField(queryset = Inmueble.objects.all(), required= True)

	def create(self, validated_data):
		inmueble = validated_data.get('inmueble')
		poll = validated_data.get('poll')
		vote= validated_data.get('vote')
		
		poll_result, created = Poll_Result.objects.get_or_create(poll= poll)

		if vote==True:
			poll_result.aye+=1
		else:
			poll_result.nay+=1

		poll_result.save()
		poll_vote = Poll_Vote.objects.create(inmueble = inmueble, result = poll_result, poll=poll)
		poll.votes +=1
		poll.save()
		return poll_result

	def validate_user(self, user):
		try:
			inquilino = user.inquilino
		except:
			pass
		if not inquilino:
			raise serializers.ValidationError(_("Wrong user type."))
		return user

	def validate(self, validated_data):
		inquilino = validated_data.get('user').inquilino
		inmueble =  validated_data.get('inmueble')
		poll= validated_data.get('poll')
		#check if poll has started
		now = timezone.now()

		if not poll.start<= now <poll.end:
			raise serializers.ValidationError(_("Poll is not active.")) 

		if not inmueble.inquilino == inquilino:
			raise serializers.ValidationError(_("User does not correspond to property.")) 
		try:
			vote = poll.poll_votes.filter(inmueble=inmueble)
			if vote.exists():
				raise serializers.ValidationError(_("You have already voted in this poll."))
		except:
			pass
		return validated_data




class InquilinoSerializer(serializers.ModelSerializer):
	user = serializers.SerializerMethodField(read_only = True)
	class Meta:
		model = Inquilino
		fields = '__all__'
		#depth = 1
	def get_user(self, inquilino):
		data = {
			'email':inquilino.user.email,
			'first_name':inquilino.user.first_name,
			'last_name':inquilino.user.last_name
		}
		return data

class PaginasAmarillasSerializer(serializers.ModelSerializer):
	email = serializers.EmailField(required= False, allow_blank = True, allow_null = True)
	mobil = serializers.CharField(required= False, allow_blank = True, allow_null = True)
	fijo = serializers.CharField(required= False, allow_blank = True, allow_null = True)
	
	class Meta:
		model = Paginas_Amarillas
		fields = '__all__'
		read_only_fields = ['condominio']

	def validate(self, validated_data):
		mobil = validated_data.get('mobil')
		fijo = validated_data.get('fijo')
		if (not mobil) and (not fijo):
			raise serializers.ValidationError(_("You should add at least one contact number"))
		return validated_data




class Assign_categorySerializer(serializers.Serializer):
	id=  serializers.PrimaryKeyRelatedField(required = True,queryset=InmuebleCategory.objects.all())
	selection = serializers.ListField(
	   child=serializers.PrimaryKeyRelatedField(queryset=Inmueble.objects.all()),
	   required = True
	)
	def create(self, validated_data):
		category = validated_data.get('id')
		inmuebles_list = validated_data.get('selection')
		for inmueble in inmuebles_list:
			category.inmuebles.add(inmueble)
		return validated_data.get('id')
	# class Meta:
	# 	model = InmuebleCategory
	# 	fields = ['id','name', 'selection']
	# 	read_only_fields = ('id',)

class Remove_categorySerializer(Assign_categorySerializer):
	id=  serializers.PrimaryKeyRelatedField(required = True,queryset=InmuebleCategory.objects.all())
	selection = serializers.ListField(
	   child=serializers.PrimaryKeyRelatedField(queryset=Inmueble.objects.all()),
	   required = True
	)
	def create(self, validated_data):
		category = validated_data.get('id')
		inmuebles_list = validated_data.get('selection')

		for inmueble in inmuebles_list:
			category.inmuebles.remove(inmueble)
		return validated_data.get('id')
	# class Meta:
	# 	model = InmuebleCategory
	# 	fields = ['id','name', 'selection']
	# 	read_only_fields = ('id',)


class InmuebleSerializer(serializers.Serializer):
	rif = serializers.CharField(required = False,write_only = True, allow_blank=True)#write_only = True
	email = serializers.EmailField(required = True,write_only = True)#write_only = True
	first_name = serializers.CharField(required = True,write_only = True)#write_only = True
	last_name = serializers.CharField(required = True,write_only = True)#write_only = True
	balanceinicial = serializers.DecimalField(required = True, max_digits=50, decimal_places=2)
	nombre_inmueble = serializers.CharField(required = True)
	alicuota = serializers.DecimalField(required = True, max_digits=7, decimal_places=4, max_value=100, min_value= 0)
	condominio = CondominioSerializer(read_only = True)
	inquilino = InquilinoSerializer(read_only = True)
	id= serializers.CharField(read_only = True)
	junta_de_condominio = serializers.BooleanField(required = False)
	cargo = serializers.CharField(required = False, allow_blank = True,allow_null= True)
	arrendado = serializers.BooleanField(required = False)
	arrendatario = serializers.CharField(required = False, allow_blank = True,allow_null= True)
	deuda_actual = serializers.DecimalField(required = False, max_digits=50, decimal_places=2, read_only= True)
	may_modify_inmueble = serializers.SerializerMethodField()
	categories = serializers.SerializerMethodField(required=False, read_only = True)
	no_miembro = serializers.SerializerMethodField(required = False, read_only=True)
	no_arrendado = serializers.SerializerMethodField(required = False, read_only=True)
	propietario =serializers.ReadOnlyField()

	def get_no_arrendado(self, inmueble):
		return inmueble.arrendado ==False

	def get_no_miembro(self, inmueble):
		return inmueble.junta_de_condominio ==False

	def get_categories(self, inmueble):
		serializer=  InmuebleCategorySerializer(inmueble.categories.all(), many=True)
		return serializer.data

	def get_may_modify_inmueble(self, inmueble):
		if inmueble.factura_propietario_set.all().exists():
			return False
		return True

	def validate_alicuota(self, alicuota):
		request = self.context['request']
		total_alicuota = total_alicuotas(Inmueble.objects.all(), request.user.condominio)
		if request.method == 'PATCH':
			total_alicuota = total_alicuota - alicuota

		if (total_alicuota + alicuota)>100:
			raise ValidationError(_("Percentages must not sum over 100"))
		elif alicuota>100:
			raise ValidationError(_("This value can not be greater than 100"))
		return alicuota

	def validate_email(self, email):
		if Condominio.objects.filter(user__email = email).exists():
			raise ValidationError(_("Condominium can not be an owner"))

		user = User.objects.filter(email = email)
		if user.exists():
			if user.get(email = email).is_staff:
				raise ValidationError(_("Invalid email."))
		return email

	def validate_nombre_inmueble(self, nombre_inmueble):
		#CAN NOT CHANGE INMUEBLE NAME IF THEERE ARE FACTURAS FOR THE CONDO
		request = self.context['request']
		#CHECK THAT INMUEBLE IS NOT ASSIGNED TO ANOTHER USER
		inmueble = request.user.condominio.inmueble_set.filter(nombre_inmueble = str(nombre_inmueble).strip().upper() )
		if inmueble.exists():
			inmueble = inmueble[0]
			if hasattr(inmueble, 'inquilino') == True:
				if request.method=='POST':
					#IF CREATING A NEW INMUEBLE IT CAN NOT BE ALREADY EXIST(NO DUP. FOR CONDO)
					raise ValidationError(_("This property already belongs to another owner."))

				elif request.method=='PATCH' and inmueble.nombre_inmueble != self.instance.nombre_inmueble:
					raise ValidationError(_("This property already belongs to another owner."))
		return nombre_inmueble

	def validate(self, validated_data):

		arrendado = validated_data.get('arrendado', None)
		arrendatario = validated_data.get('arrendatario', None)
		cargo = validated_data.get('cargo', None)
		junta_de_condominio = validated_data.get('junta_de_condominio', None)
		if arrendado and junta_de_condominio:
			raise ValidationError(_('Only owners can be part of the condominium board'))
		if arrendatario and (junta_de_condominio or cargo):
			raise ValidationError(_('Only owners can be part of the condominium board'))
		if cargo and (arrendatario==True or arrendado==True):
			raise ValidationError(_('Only owners can be part of the condominium board'))
		return validated_data

	def update(self, inmueble, validated_data):
		request = self.context['request']
		#NEED CODE THAT ALLOWS FOR CHANGES IN EMAIL ADDRESS
		#IF EMAIL ADDRESS IS SAME AS OLD CHANGE REST OF DATA NORMALLY
		#IF  EMAIL ADDRESS BEING CHANGED CHECK IF IT EXISTS(GET OR CREATE?)
		#IF IT EXISTS SWITCH TO IT
		#IF IT DOES NOT EXIST CREATE user/inquilino pair??
		#inmueble.inquilino.user.email = validated_data.get('email',  inmueble.cargo )
		user, created = User.objects.get_or_create( email = validated_data.get('email') )

		condominio = request.user.condominio
		user_data = {}
		user_data['email'] = validated_data.pop('email')
		#first_name = validated_data.pop('first_name')
		#last_name = validated_data.pop('last_name')
		if created:
			user.first_name = validated_data.pop('first_name', user.first_name)
			user.last_name = validated_data.pop('last_name', user.last_name)
			user.username = str(user_data['email'] ).split('@')[0]
			user.save()
			#create and attach an inquilino
			inquilino_data = {
				'rif':validated_data.pop('rif', None),
				'user': user
			}
			inquilino = Inquilino.objects.create(**inquilino_data)
			send_email_confirmation(request, user, signup=True)

		inmueble.inquilino = user.inquilino

		inmueble.cargo = validated_data.get('cargo',  inmueble.cargo )
		inmueble.junta_de_condominio = validated_data.get('junta_de_condominio',  inmueble.junta_de_condominio )
		inmueble.arrendatario = validated_data.get('arrendatario',  inmueble.arrendatario )
		inmueble.arrendado = validated_data.get('arrendado',  inmueble.arrendado )
		inmueble.alicuota = validated_data.get('alicuota',  inmueble.alicuota )
		inmueble.balanceinicial = validated_data.get('balanceinicial',  inmueble.balanceinicial )
		inmueble.nombre_inmueble = validated_data.get('nombre_inmueble',  inmueble.nombre_inmueble )
		inmueble.inquilino.rif = validated_data.get('rif',  inmueble.inquilino.rif )
		inmueble.inquilino.save()
		#OUY MAY NOT MODIFY THESE
		#inmueble.inquilino.user.first_name = validated_data.get('first_name',  inmueble.inquilino.user.first_name )
		#inmueble.inquilino.user.last_name = validated_data.get('last_name',  inmueble.inquilino.user.last_name )
		inmueble.save()
		#inmueble.inquilino.user.save()
		return inmueble

	def validate_balanceinicial(self, balanceinicial):
		request = self.context['request']
		if request.method =='PATCH':
			facturas_condominio = Factura_Condominio.objects.filter(condominio=request.user.condominio, tipo_de_factura ='service_fee')
			if facturas_condominio.exists():
				raise ValidationError(_("You may not modify initial balance once you have generated an expense report."))
		return balanceinicial

	def create(self, validated_data):
		request = self.context['request']
		#site name
		current_site = get_current_site(request)
		condominio = request.user.condominio
		user_data = {}
		user_data['email'] = validated_data.pop('email')

		#GET OR CREATE THE USER ACCORDING TO EMAIL
		user, created = User.objects.get_or_create( **user_data)
		if created:	
			user.first_name = validated_data.pop('first_name')
			user.last_name = validated_data.pop('last_name')
			user.username = str(user_data['email'] ).split('@')[0]
			user.save()

			inquilino_data = {
				'rif':validated_data.pop('rif', None),
				'user': user
			}
			inquilino = Inquilino.objects.create(**inquilino_data)
			send_email_confirmation(request, user, signup=True)

		elif not user.emailaddress_set.filter(verified= True).exists():#IF EMAIL ADDRESS HAS NOT BEEN CONFIRMED SEND CONFIRMATION EMAIL
			send_email_confirmation(request, user, signup=False)

		#GET OR CREATE INMUEBLE
		inmueble, inmueble_created = Inmueble.objects.get_or_create(condominio = condominio, nombre_inmueble = validated_data.pop('nombre_inmueble'))
		if inmueble_created:# IF INMUEBLE WAS CREATED ATTACH ALL OF THE NEW VALUES TO IT ESLE LEAVE IT AS IS
			for attr, value in validated_data.items():
				inmueble.deuda_actual = validated_data.pop('balanceinicial', 0)
				setattr(inmueble, attr, value)

		inmueble.inquilino = user.inquilino
		inmueble.save()
		return inmueble

class JuntaCondominioSerializer(InmuebleSerializer):
	def update(self, inmueble, validated_data):
			#email= inmueble.inquilino.user.email
			inmueble.cargo = validated_data.get('cargo',  inmueble.cargo )

			inmueble.junta_de_condominio = validated_data.get('junta_de_condominio',  inmueble.junta_de_condominio )

			inmueble.save()

			return inmueble

class UserSerializer(serializers.ModelSerializer):
	user_type = serializers.SerializerMethodField()

	def get_user_type(self, user):
		if hasattr(user, 'condominio'):
			user_type = 'condominio'
		elif hasattr(user, 'affiliate'):
			user_type = 'affiliate'
		elif hasattr(user, 'inquilino'):
			user_type = 'inquilino'
		else:
			user_type ='anonymous'
		return user_type

	detalles_usuario = serializers.SerializerMethodField()
	class Meta:
		model = User
		fields = ['id', 'username', 'last_login', 'first_name', 'last_name', 'email', 'is_active', 'date_joined', 'detalles_usuario','user_type']
		read_only_fields = ('id','username','last_login','first_name','last_name','email', 'is_active','date_joined',)
        extra_kwargs = {
            'password': {'write_only': True}
            }

	def get_detalles_usuario(self, user):
		if hasattr(user, 'condominio'):
			condominio = user.condominio
			user_type = 'condominio'
			serializer = CondominioSerializer(condominio)
			detalles = {
				'tipo_usuario': user_type,
				'cuenta_bancaria' : condominio.bancos_set.all().exists()
			}
			for key, value in serializer.data.iteritems():
				detalles[key] = value
			return detalles

		if hasattr(user, 'affiliate'):
			affiliate = user.affiliate
			user_type = 'affiliate'
			serializer = AffiliateSerializer(affiliate)
			return serializer.data


		if hasattr(user, 'inquilino'):
			inquilino = user.inquilino
			serializer = InquilinoSerializer(inquilino)
			return serializer.data


class BancosCondominioaldiaSerializer(serializers.ModelSerializer):
	class Meta:
		model = BancosCondominioaldia
		fields ='__all__'


class CarteleraSerializer(serializers.ModelSerializer):
	class Meta:
		model = Cartelera
		exclude = ['condominio']



class Banco_PaisSerializer(serializers.ModelSerializer):
	class Meta:
		model = Banco_Pais
		fields = '__all__'

class BancoChequeField(serializers.Field):

    def to_representation(self, obj):
    	serializer = Banco_PaisSerializer(obj)
        return serializer.data

    def to_internal_value(self, data):
    	if data:
        	return Banco_Pais.objects.get( id = data )
        return None


class ContactUsSerializer( serializers.Serializer ):
	CHOICES = (
		( 'product', 'product' ),
		( 'service', 'service' ),
		( 'suggestions', 'suggestions' ),
	)
	name = serializers.CharField(required = True, max_length=None, min_length=None, allow_blank=False, trim_whitespace=True)
	email = serializers.EmailField(required = True, max_length=None, min_length=None, allow_blank=False)
	subject = serializers.ChoiceField( CHOICES )
	message =  serializers.CharField(required = True, max_length=500, min_length=10, allow_blank=False, trim_whitespace=True)
    
	def save(self):
		send_email.delay(
			self.validated_data['subject'], 
			self.validated_data['message'], 
			settings.DEFAULT_FROM_EMAIL, 
			[str(settings.ADMINISTRATIVE_EMAIL)], 
			reply_to=[str(self.validated_data['email'])]
			)


class InstaPago_Serializer( serializers.Serializer ):
    name_on_card = serializers.CharField(required = True )
    card_number = serializers.CharField(max_length=16, min_length=15,  required = True )
    cvc = serializers.CharField( max_length =3, required = True )
    exp = serializers.DateField(required = True )
    rif = serializers.CharField(max_length=8, min_length=6, required = True )
    monto = serializers.DecimalField( decimal_places=2,max_digits=50, required= True)
    
    # def validate_exp(self, exp):
    #     now = timezone.now().date()
    #     now_month = datetime.date(now.year, now.month, 1)
    #     if exp <= now_month:
    #         raise serializers.ValidationError('Tarjeta de credito vencida')
    #     return exp

    def validate_rif(self, rif):
        try:
            rif_int = int(rif)
            if rif_int > 0:
                return rif
        except:
            raise serializers.ValidationError('Cedula/Rif invalido')


    def validate_cvc(self, cvc):
        try:
            cvc_int = int(cvc)
            if cvc_int > 0:
                return cvc
        except:
            raise serializers.ValidationError('CVC invalido')
        



class BancosSerializer(serializers.ModelSerializer):

	class Meta:
		model = Bancos
		exclude = ['condominio']
		read_only_fields = ['banco','condominio', 'balance']

	def validate(self, validated_data):
		if validated_data.get('editable') == False:
			raise serializers.ValidationError(_("This bank has a month bill associated with it, edition is not allowed."))
		return validated_data

	def create(self, validated_data):
		instance= Bancos.objects.create(banco=validated_data.get('banco_pais').name,balance=validated_data.get('balanceinicial'),**validated_data)
		return instance

	def update(self, instance, validated_data):
		instance.balanceinicial = validated_data.get('balanceinicial', instance.balanceinicial)
		instance.titular = validated_data.get('titular', instance.titular)
		instance.nro_cuenta = validated_data.get('nro_cuenta', instance.nro_cuenta)
		instance.banco_pais = validated_data.get('banco_pais', instance.banco_pais)
		ingresos=instance.ingreso_condominio_set.filter(aprobado=True).aggregate(total_mes= Sum('monto'))['total_mes'] or 0
		egresos =instance.egreso_condominio_set.all().aggregate(total_mes= Sum('monto'))['total_mes'] or 0
		instance.balance= instance.balanceinicial-egresos+ingresos
		instance.banco =instance.banco_pais.name
		instance.save()
		return instance


class BancoField(serializers.Field):
    def to_representation(self, obj):
    	serializer = BancosSerializer(obj)
        return serializer.data

    def to_internal_value(self, data):
    	if data:
        	return Bancos.objects.get( id = data )
        return None

class Ingreso_CondominioSerializer(serializers.ModelSerializer):
	monto = serializers.DecimalField(min_value = 0.01, decimal_places=2, max_digits = 50, required = True)
	nro_cheque = serializers.CharField(required = False, allow_blank= True, allow_null= True)
	banco_cheque = BancoChequeField(required=False)
	rif_pagador = serializers.CharField(required = False, allow_null = True, allow_blank = True)
	inmueble_data = serializers.SerializerMethodField(read_only = True)
	cobranza_condominio =serializers.PrimaryKeyRelatedField(queryset = Cobranza_Condominio.objects.all(),required = False, allow_null= True)
	propietario = serializers.ReadOnlyField()
	cobranza_description= serializers.SerializerMethodField(read_only= True)

	def get_cobranza_description(self, obj):
		try:
			return obj.cobranza_condominio.cobranza_condominio.asunto
		except:
			return _("Regular payment")

	#pagador =
	class Meta:
		model = Ingreso_Condominio
		fields = '__all__'
		read_only_fields = ['condIngreso_CondominioSeominio', 'cuenta_dep', 'condominio', 'propietario']

	def send_payment_acceptance(self, request, instance):
		subject_context = {}
		message_context={}
		protocol = 'https' if request.is_secure() else 'http'
		site  =get_current_site(request)
		site_name=  site.name.lower()
		site_url = protocol+'://'+site.domain
		condominio_name = instance.condominio.user.get_full_name().title()
		subject_context['condominio_name'], message_context['condominio_name'] =condominio_name, condominio_name
		message_context['moneda'] = instance.condominio.pais.moneda
		message_context['monto'] = abs(instance.monto.quantize(settings.TWOPLACES)) , 2
		message_context['inquilino'] = instance.inmueble.inquilino.user.get_full_name().title()
		message_context['site_url'] = site_url

		if instance.aprobado== True:
			subject_context['approval_status'] = _('accepted')
			message= loader.render_to_string('account/email/condo_accept_pay_message.txt', message_context)

		elif instance.aprobado ==False:
			subject_context['approval_status'] = _('rejected')
			message_context['razon_rechazo'] = instance.razon_rechazo.title()
			message= loader.render_to_string('account/email/condo_reject_pay_message.txt', message_context)
		
		#IF CONDOMINIO IS SAVING INSTANCE
		if get_user_type (request) =='condominio':
			subject = loader.render_to_string('account/email/condo_accept_pay_subject.txt', subject_context)
			send_email.delay(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.inmueble.inquilino.user.email] )

	def create(self, validated_data):
		request  = self.context['request']
		tipo_de_ingreso = validated_data.get('tipo_de_ingreso', None)
		cobranza = validated_data.pop('cobranza_condominio', None)
		instance = Ingreso_Condominio.objects.create(**validated_data)
		banco= validated_data.get('banco', None)
		if tipo_de_ingreso == 'pp':
			self.send_payment_acceptance(request,instance)
		elif tipo_de_ingreso =='cobranza':
			intermediary = cobranza.cobranza_condominio_destinatario_set.get(inmueble = request.session.get('inmueble'))
			intermediary.payment= instance
			intermediary.save()
			#cobranza.payment = instance
			#cobranza.save()
			#intance.mes = timezone.now
			#append payment to cobranza instance
		user_type = request.user.get_user_type()
		if user_type =='inquilino':
			instance.mes = timezone.now()
			instance.save()
		return instance

	def update(self, instance, validated_data):

		#ONLY SEND EMAIL IF APROBADO CHANGED FROM NONE TO RECHAZO OR APPROVAL
		if validated_data.get('aprobado',  instance.aprobado ) is not None:
			instance.razon_rechazo = validated_data.get('razon_rechazo',  instance.razon_rechazo )
			instance.aprobado = validated_data.get('aprobado',  instance.aprobado )
			self.send_payment_acceptance(self.context['request'],instance)
		instance.save()
		return instance

	def get_inmueble_data(self, ingreso):
		try:
			nombre_inmueble = ingreso.inmueble.nombre_inmueble
		except:
			nombre_inmueble = _('N/A')
		data = {
			'nombre_inmueble':nombre_inmueble
		}
		return data

	def validate_mes(self, mes):

		request= self.context['request']
		user_type= get_user_type(request)
		if user_type =='condominio':
			condominio = request.user.condominio
		elif user_type =='inquilino':
			return mes
		editable_period_dict =  Ingreso_Condominio.objects.get_latest_editable(condominio)
		if mes <= editable_period_dict['maxDate'] and mes >= editable_period_dict['minDate']:
			return mes
		else:
			raise ValidationError(_("You must specify a billing date pertaining to a valid period"))


	def validate(self, validated_data):
		request = self.context['request']
		
		if not request.method == 'PATCH':
			
			user_type = get_user_type(request)
			nro_cheque = validated_data.get('nro_cheque', None)
			banco_cheque = validated_data.get('banco_cheque', None)

			if user_type =='condominio':
				validated_data['aprobado'] = True
				condominio = request.user.condominio
				if condominio.retrasado == True:
					raise ValidationError(_("Your account is overdue, please pay the amount in full in order to restore complete service."))
			else:
				validated_data['condominio'] =self.context['condominio']
				validated_data['pagador'] =request.user.first_name +' '+request.user.last_name
				validated_data['posted_by'] =request.user

			if nro_cheque and not banco_cheque :
				raise ValidationError(_("You must specify the check bank's name."))

			if banco_cheque and not nro_cheque :
				raise ValidationError(_("You must specify the check number."))

			tipo_de_ingreso =validated_data.get('tipo_de_ingreso')

			if tipo_de_ingreso =='pp':
				#validated_data['propietario'] = str(validated_data['inmueble'].inquilino.user.first_name)
				validated_data['rif_pagador'] = str(validated_data['inmueble'].inquilino.rif) if validated_data['inmueble'].inquilino.rif else ''
				if validated_data['inmueble'].arrendado:
					validated_data['arrendatario'] = str(validated_data['inmueble'].arrendatario)
			
			elif tipo_de_ingreso =='po':
				validated_data['inmueble'] = None
				# if not validated_data.get('rif_pagador', None):
				# 	raise ValidationError(_("Payers fiscal number is required."))

			elif tipo_de_ingreso =='cobranza':
				#cobranzas_intermediary= obj.cobranza_condominio_destinatario_set.filter(inmueble =request.session.get('inmueble'), payment__isnull=True)
				cobranza =validated_data.get('cobranza_condominio')
				if cobranza.cobranza_condominio_destinatario_set.filter(inmueble =request.session.get('inmueble'), payment__isnull=False).exists():
					raise ValidationError(_("This payment request already has already has a payment."))

			banco= validated_data.get('banco')
			validated_data['banco_dep']  = banco.banco
			validated_data['cuenta_dep']  = banco.nro_cuenta

		#WILL ONLY LET YOU MODIFY IF IT HAS NOT BEEN APPROVED OR REJECTED
		if self.instance:
			if self.instance.aprobado is not None:
				raise serializers.ValidationError(_("This income has already been evaluated."))
		return validated_data


class registroSerializer(serializers.Serializer):
	CHOICES=(
		('condominio','condominio'),
		('afiliado','afiliado'),
	)
	email = serializers.EmailField(required = True)
	pais = serializers.CharField(required = False, allow_blank = True, allow_null=True)
	rif = serializers.CharField( required= True)
	first_name = serializers.CharField(required= True)
	last_name = serializers.CharField(required= False, allow_blank= True, allow_null= True)
	comprobante_rif = serializers.ImageField( required= False)
	password1 = serializers.CharField(required= True, allow_blank=False, min_length = 8)
	password2 = serializers.CharField(required= True, allow_blank=False, min_length = 8)
	terminos = serializers.BooleanField(required= True)
	client_type= serializers.ChoiceField(choices= CHOICES, required = False, allow_blank = True, allow_null=True)
	affiliate = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(),required = False, allow_null = True)

	def validate_affiliate(self, affiliate):
		#raise serializers.ValidationError(_("Not a valid affiliate."))

		if affiliate:
			try:
				affiliate= affiliate.affiliate
			except:
				raise serializers.ValidationError(_("Not a valid affiliate."))

		return affiliate

	def validate_terminos(self, terminos):
		if not terminos == True:
			raise serializers.ValidationError(_("You must accept terms and conditions"))
		return terminos

	def validate_pais(self, pais):
		try:
			pais = Paises.objects.get(nombre = str(pais).strip())
		except:
			raise serializers.ValidationError(_("Invalid country"))
		return pais

	def validate_email(self, email):
		user = User.objects.filter(email = email)
		if user.exists():
			raise ValidationError(_("This user already exists"))
		return email

	def validate_rif(self, rif):
		condominio = Condominio.objects.filter(rif = rif)
		inquilino = Inquilino.objects.filter(rif = rif)
		afiliado = Affiliate.objects.filter(rif = rif)
		if inquilino.exists() or condominio.exists() or afiliado.exists():
			raise ValidationError(_("This fiscal number belonds to another user."))
		return rif


	def validate(self, data):
		client_type = data.get('client_type', None)
		pais = data.get('pais', None)
		if client_type:
			if client_type =='condominio':
				if not pais:
					raise ValidationError(_("You must provide a country id."))
				reg = re.match(data['pais'].rif_regex ,data['rif'])
				if not reg:
					raise ValidationError("Numero %s invalido" %(data['pais'].nombre_registro_fiscal))
		password1 = data['password1']
		password2 = data['password2']
		if not password2 == password1:
			raise ValidationError(_("Passwords do not match"))
		return data



class contextSerializer(serializers.Serializer):
	maxDate = serializers.DateTimeField(required= False)
	minDate = serializers.DateTimeField(required= False)
	active_month =serializers.DateTimeField(required=False)

class CondominidoAfilliateSerialzier(serializers.ModelSerializer):
	user = UserSerializer()
	class Meta:
		model = Condominio
		fields = '__all__'


class Egreso_CondominioSerializer(serializers.ModelSerializer):
	banco = BancoField()
	tipo_egreso = serializers.CharField( allow_null= True, required= False)
	inmueble_data = serializers.SerializerMethodField(read_only = True)

	class Meta:
		model = Egreso_Condominio
		fields = '__all__'
		read_only_fields = ['condominio']

	def validate_tipo_egreso(self, tipo_egreso):
		request= self.context['request']
		tipo_egreso, created = Tipos_Egresos.objects.get_or_create(nombre= tipo_egreso.strip().lower(), pais=request.user.condominio.pais)
		return tipo_egreso

	def get_inmueble_data(self, ingreso):
		try:
			nombre_inmueble = ingreso.inmueble.nombre_inmueble
		except:
			nombre_inmueble = _('N/A')
		data = {
			'nombre_inmueble':nombre_inmueble
		}
		return data

	def update(self, instance, validated_data):
		instance.tipo_egreso = validated_data.get('tipo_egreso',  instance.tipo_egreso )
		instance.monto = validated_data.get('monto',  instance.monto )
		instance.banco = validated_data.get('banco',  instance.banco )
		instance.fecha_facturacion = validated_data.get('fecha_facturacion',  instance.fecha_facturacion )
		instance.nro_factura = validated_data.get('nro_factura',  instance.nro_factura )
		instance.detalles = validated_data.get('detalles',  instance.detalles )
		instance.save()
		return instance

	def validate(self, validated_data):
		request= self.context['request']
		user_type = get_user_type(request)
		if user_type =='condominio':
			#validated_data['aprobado'] = True
			condominio = request.user.condominio
			if condominio.retrasado == True:
				raise ValidationError(_("Your account is overdue, please pay the amount in full in order to restore complete service."))
		return validated_data

	def validate_fecha_facturacion(self, fecha_facturacion):
		request= self.context['request']
		editable_period_dict= Egreso_Condominio.objects.get_latest_editable(request.user.condominio)
		if not editable_period_dict['minDate']<=fecha_facturacion<=editable_period_dict['maxDate']:
			raise serializers.ValidationError(_('Bill date is out of valid billing period.'))
		return fecha_facturacion
	

class tiposEgresosSerializer(serializers.ModelSerializer):
	class Meta:
		model = Tipos_Egresos
		fields = '__all__'

class InmuebleField(serializers.Field):
    def to_representation(self, obj):
    	serializer = InmuebleSerializer(obj)
        return serializer.data

    def to_internal_value(self, data):
        return Inmueble.objects.get( id = data )

class DestinatarioField(serializers.Field):
	'''
	this field represents the dataset associated with this cobranza
	'''
	def to_representation(self, obj):
		#print obj.all()
		#inmuebles= [item.inmueble for item in obj.through.objects.all()]
		serializer = InmuebleSerializer(obj.all(), many=True)
		#print serializer.data
		return serializer.data

	def to_internal_value(self, destinatario):
		request = self.context.get('request')
		inmueble_pk = self.context.get('inmueble')
		#queryset = Inmueble.objects.all()
		if destinatario =='todos':
			destinatarios = request.user.condominio.inmueble_set.all()
		elif destinatario == 'especifico':
			destinatarios = request.user.condominio.inmueble_set.filter( pk= inmueble_pk)#need to pass inmueble
		elif destinatario == 'retrasados':
			destinatarios = request.user.condominio.inmueble_set.get_debtors(request.user.condominio)
		else:
			destinatarios = request.user.condominio.inmueble_set.filter(categories__id =destinatario)

		return destinatarios

class RecipienteField(serializers.Field):
	'''
	this field represents the text description of the destinatario field
	'''
	def to_representation(self, obj):
		if obj.category:
			return obj.category.name
		return obj.recipiente

	def get_attribute(self, obj):
		# We pass the object instance onto `to_representation`,
		# not just the field attribute.
		return obj


	def to_internal_value(self, recipiente):
		request = self.context.get('request')
		inmueble_pk = self.context.get('inmueble')
		if recipiente =='todos':
			destinatarios = 'todos'
		elif recipiente == 'especifico':
			inmueble = request.user.condominio.inmueble_set.get( pk= inmueble_pk)
			destinatarios = inmueble.inquilino.user.get_full_name()+ ' (%s)' %(inmueble.nombre_inmueble)#need to pass inmueble
			
		elif recipiente == 'retrasados':
			destinatarios = 'retrasados'
		else:
			destinatarios = _("Category: ") + str(InmuebleCategory.objects.get(pk=int(recipiente)).name)
		return destinatarios


class CategoryField(serializers.Field):
	'''
	this field represents the related category for the cobranza
	'''
	def to_representation(self, obj):
		if obj:
			return obj.name
			return obj

	def to_internal_value(self, data):
		#GETTING PRESUMED PK
		try:
			category = InmuebleCategory.objects.get(pk = data)
		except:
			category = None
		return category

class Cobranza_CondominioSerializer(serializers.ModelSerializer):
	category = CategoryField(write_only= True)
	recipiente = RecipienteField()
	destinatario =DestinatarioField(write_only= True)
	payment_required= serializers.SerializerMethodField(read_only= True)
	inmueble_payed = serializers.SerializerMethodField(read_only = True)
	class Meta:
		model = Cobranza_Condominio
		fields = '__all__'

	def get_inmueble_payed(self, obj):
		try:
			request = self.context['request']
			if obj.cobrar_cuando =='inmediato':
				cobranzas_intermediary= obj.cobranza_condominio_destinatario_set.get(inmueble =request.session.get('inmueble'))
				if cobranzas_intermediary.payment:
					return cobranzas_intermediary.payment.aprobado
				return None
		except:
			return None
		
	def get_payment_required(self, obj):
		try:
			request = self.context['request']
			if obj.cobrar_cuando =='inmediato':
				cobranzas_intermediary= obj.cobranza_condominio_destinatario_set.filter(inmueble =request.session.get('inmueble'), payment__isnull=True)
				return cobranzas_intermediary.exists()
			return False
		except:
			return False


	def validate_asunto(self, asunto):
		return asunto.strip().lower().title()

	def validate(self, validated_data):
		destinatario = validated_data.get('destinatario', None)
		inmueble = validated_data.get('inmueble', None)
		tipo_monto = validated_data.get('tipo_monto', None)
		monto = validated_data.get('monto', None)
		porcentaje = validated_data.get('porcentaje', None)
		cobrar_cuando = validated_data.get('cobrar_cuando', None)
		asunto = validated_data.get('asunto', None)
		mes = validated_data.get('mes', None)

		if destinatario =='especifico' and not inmueble:
			raise serializers.ValidationError(_("You must specify a property."))
		
		if tipo_monto =='monto':
			validated_data['porcentaje'] = None
			if not monto:
				raise serializers.ValidationError(_("You must specify an amount."))

		elif tipo_monto =='porcEgresos':
			validated_data['monto'] = None
			if not porcentaje:
				raise serializers.ValidationError(_("You must specify a percentage."))
			
			if cobrar_cuando =='inmediato':
				raise serializers.ValidationError(_("Can not charge immediately, must wait for period to end in order to get total expenses."))

		elif tipo_monto =='porAlicuota':
			validated_data['porcentaje'] = None
			if not monto:
				raise serializers.ValidationError(_("You must specify an amount."))
			


		#asunto, destinatario and mes can not be duplicated
		month_range = month_range_dt(mes)
		destinatario_id_list = [item.pk for item in destinatario]
		if Cobranza_Condominio.objects.filter(asunto =asunto, mes__range = (month_range[0], month_range[1]), cobranza_condominio_destinatario__inmueble__in =destinatario_id_list).exists():
			raise serializers.ValidationError(_("There are properties already being charged with %s. Please exclude them to prevent duplicates or delete existing charge.") %(asunto))
		return validated_data

	def create(self, validated_data):
		request = self.context.get('request')
		destinatarios = validated_data.pop('destinatario', None)
		tipo_monto = validated_data.get('tipo_monto', None)
		monto = validated_data.get('monto', None)

		instance = Cobranza_Condominio.objects.create(**validated_data)
		for destinatario in destinatarios:
			deuda_inmueble = 0
			if tipo_monto  =='porAlicuota':
				deuda_inmueble = destinatario.alicuota * monto /100
			intermediary_instance = Cobranza_Condominio_Destinatario.objects.create(cobranza_condominio = instance, inmueble = destinatario, deuda_inmueble = deuda_inmueble)
		return instance


	
class PollsApiViewSerializer(serializers.ModelSerializer):
	has_voted= serializers.SerializerMethodField(read_only = True)
	aye= serializers.IntegerField(read_only = True, source='poll_result.aye')
	nay= serializers.IntegerField(read_only = True, source='poll_result.nay')
	class Meta:
		model = Poll
		fields = '__all__'

	def get_has_voted(self, poll):
		has_voted = True
		try:
			request= self.context['request']
			user_type = get_user_type(request)
			if user_type =='inquilino' and request:
				has_voted = poll.poll_votes.filter(inmueble__inquilino= request.user.inquilino, poll= poll).exists()
		except:
			pass
		return has_voted

	def validate_start(self, start):
		now = timezone.now()
		if start.date() <now.date():
			raise serializers.ValidationError(_('Start date can not be before today.'))
		return start

	def validate(self, validated_data):
		start= validated_data.get('start')
		end= validated_data.get('end')
		diff = end.date() -start.date()
		if diff.days>7:
			raise serializers.ValidationError(_('Maximum poll period is 7 days.'))

		if diff.days<1:
			raise serializers.ValidationError(_('Minimum poll period is one day.'))

		if end <=start:
			raise serializers.ValidationError(_('Poll end time must be greater than start time.'))
		return validated_data



class MessagesSerializer(serializers.ModelSerializer):
	recipient_name=serializers.SerializerMethodField(read_only = True)

	class Meta:
		model = Messages
		fields = '__all__'
		read_only_fields = ['sender_type', 'sender', 'recipient']

	def get_recipient_name(self, message):
		if message.recipient.all().exists():
			if len(message.recipient.all()) ==1:
				return message.recipient.all()[0].get_full_name()
		else:
			return {}

	def save(self, kwargs):
		request = self.context[ 'request' ]
		inmueble = kwargs.get('inmueble', None)
		message =Messages.objects.create( sender = request.user, sender_type= get_user_type(request),**self.validated_data )

		recipients = self.validated_data.get('recipient_desc')
		if recipients =='TP':
			recipients = Inmueble.objects.get_all_properties(condominio = request.user.condominio)
		elif recipients =='PSD':
			recipients = Inmueble.objects.get_creditors(condominio = request.user.condominio)
		elif recipients =='PCD':
			recipients = Inmueble.objects.get_debtors(condominio = request.user.condominio)
		elif recipients =='PP':
			recipients = Inmueble.objects.get_particular_property(condominio = request.user.condominio, inmueble = inmueble)
		elif recipients =='JC':
			recipients = Inmueble.objects.get_board_members(condominio = request.user.condominio)
		elif recipients =='NBM':
			recipients = Inmueble.objects.get_non_board_members(condominio = request.user.condominio)

		recipient_users = [inmueble.inquilino.user for inmueble in recipients]
		message.recipient.set(recipient_users)
		recipient_email = [inmueble.inquilino.user.email for inmueble in recipients]
		#SEND EMAIL
		send_email.delay(self.validated_data.get('subject'), self.validated_data.get('message'), self.validated_data.get('sender'), recipient_email)
		#SEND SMS




class Extra_Column_Serializer(serializers.ModelSerializer):
	banco = BancoField(required= False)
	class Meta:
		model = Extra_Column
		#fields = '__all__'
		exclude=['factura']







class Cuotas_Serializer(serializers.Serializer):
	inmueble=serializers.PrimaryKeyRelatedField(source="id", queryset= Inmueble.objects.all())
	#inmueble = InmuebleSerializer(read_only=True)
	propietario=serializers.ReadOnlyField()
	nombre_inmueble=serializers.CharField(read_only= True)
	deuda_actual=serializers.SerializerMethodField(read_only = True)
	#extra_cols=serializers.SerializerMethodField(read_only = True)
	alicuota = serializers.DecimalField(required = True, max_digits=50, decimal_places=2)
	cuota= serializers.SerializerMethodField()
	pagos = serializers.SerializerMethodField( )
	junta_de_condominio = serializers.BooleanField(read_only = True)
	categories = serializers.SerializerMethodField(required=False, read_only = True)
	no_miembro = serializers.SerializerMethodField(required = False, read_only=True)
	no_arrendado = serializers.SerializerMethodField(required = False, read_only=True)
	arrendado = serializers.BooleanField(required= False, read_only = True)
	cobranzas = serializers.SerializerMethodField(required=False, read_only = True)
	def get_no_arrendado(self, inmueble):
		return inmueble.arrendado ==False

	def get_no_miembro(self, inmueble):
		return inmueble.junta_de_condominio ==False

	def get_categories(self, inmueble):
		serializer=  InmuebleCategorySerializer(inmueble.categories.all(), many=True)
		return serializer.data
	# def get_junta_de_condominio(self, inmueble):
	# 	serializer=  InmuebleCategorySerializer(inmueble.categories.all(), many=True)
	# 	return inmueble.junta_de_condominio

	def get_deuda_actual(self, inmueble):
		facturas = Factura_Propietario.objects.filter(inmueble=inmueble)
		if facturas.exists():
			deuda_actual = facturas.latest('created').monto
		else:
			deuda_actual = inmueble.balanceinicial
		return deuda_actual

	def get_cuota(self, inmueble):
		total = self.context['total']
		alicuota= inmueble.alicuota/100
		return total*alicuota

	def get_cobranzas(self, inmueble):
		cobranzas_inmueble= inmueble.cobranza_condominio_set.filter(editable= True)#.filter(Q(cobrar_cuando='relacion') | Q(cobranza_condominio_destinatario__payment__isnull=True, cobrar_cuando='inmediato'))
		serializer = Cobranza_CondominioSerializer(cobranzas_inmueble, many=True)
		return serializer.data

	def get_pagos(self, inmueble):
		ranges=self.context['range']
		facturas = Ingreso_Condominio.objects.filter(inmueble= inmueble).filter(cerrado=False).exclude(aprobado = False).exclude(aprobado = None)
		total =facturas.aggregate(total=Sum('monto'))['total'] if facturas.exists() else 0
		return total

	# def get_extra_cols(self, inmueble):
	# 	return []

# class EgresoDetalladoSerializer(Cuotas_Serializer):
# 	cuota= None
# 	pagos = None
class Factura_PropietarioSerializer(serializers.ModelSerializer):
	inmueble = InmuebleSerializer(read_only = True)
	cobranzas = serializers.SerializerMethodField()
	cobranzas_total = serializers.SerializerMethodField(read_only= True)
	#extra_cols = Extra_Column_Serializer(many= True)
	class Meta:
		model = Factura_Propietario
		fields = '__all__'

	def get_cobranzas_total(self, instance):
		return instance.cobranzas

	def get_cobranzas(self, factura_propietario):
		inmueble = factura_propietario.inmueble
		month_range = month_range_dt(factura_propietario.mes)
		cobranzas = inmueble.cobranza_condominio_set.filter(mes__range=(month_range[0], month_range[1]))
		serializer = Cobranza_CondominioSerializer(cobranzas, many=True)
		return serializer.data

class Special_Inmueble_Serializer(InmuebleSerializer):
	pagos = Factura_PropietarioSerializer(source="factura_propietario_set", many = True)
	# extra_cols =  serializers.SerializerMethodField(read_only = True)

	# def get_extra_cols(self, inmueble):
	# 	return []

class RelacionMes2Serializer(serializers.Serializer):
	inmuebles = Cuotas_Serializer(many= True)
	total= serializers.DecimalField(max_digits=50, decimal_places=4)
	comission = serializers.DecimalField(max_digits=50, decimal_places=2)
	month = serializers.DateTimeField()
	cuentas = BancosSerializer(many=True)
	columns = serializers.ListField(
	   child=serializers.CharField(required= False)
	)
class SocialLinksSerializer(serializers.ModelSerializer):
	class Meta:
		model = Social_Link
		fields = '__all__'	



class BuildRelacionMesSerializer(serializers.Serializer):
	inmueble = serializers.PrimaryKeyRelatedField(queryset=Inmueble.objects.all())
	#extra_cols = Extra_Column_Serializer(many= True)
	deuda_actual = serializers.DecimalField(required = True, max_digits=50, decimal_places=20)
	pagos = serializers.DecimalField(required = True, max_digits=50, decimal_places=20)
	cuota = serializers.DecimalField(required = True, max_digits=50, decimal_places=20)
	cobranzas = serializers.DecimalField(max_digits=50, decimal_places=20, read_only= True)

	def create(self, validated_data):
		validated_data['condominio'] = self.context['condominio']
		inmueble=validated_data['inmueble']
		validated_data['nombre_inmueble'] = inmueble.nombre_inmueble
		validated_data['deuda_previa'] = validated_data.pop('deuda_actual')
		mes = self.context['mes']
		cobranzas = inmueble.cobranza_condominio_set.filter(editable= True)
		egresos = inmueble.condominio.egreso_condominio_set.filter(cerrado = False)
		egresos_sum = egresos.aggregate(total_mes= Sum('monto'))['total_mes'] or 0
		validated_data['cobranzas' ]= get_total_cobranzas(cobranzas, inmueble, egresos_sum)
		# extra_cols = validated_data.pop('extra_cols')
		# monto_extra_cols = 0
		# for item in extra_cols:
		# 	monto_extra_cols +=item['monto']
		deuda_previa = validated_data.get('deuda_previa', None)
		cuota= validated_data.get('cuota', None)
		pagos= validated_data.get('pagos', None)
		
		monto = pagos+deuda_previa-(validated_data['cobranzas' ]+cuota)
		validated_data['cantidad'] = 1
		validated_data['rif'] = inmueble.inquilino.rif if inmueble.inquilino.rif else None
		validated_data['mes'] = mes
		validated_data['monto'] = monto
		validated_data['cantidad'] = 1
		#validated_data['deuda_nueva'] = monto
		#validated_data= merge_two_dicts(validated_data, data)
		factura_propietario = Factura_Propietario.objects.create(**validated_data)
		# if len(extra_cols) >0:
		# 	for column in extra_cols:
		# 		extras_col = Extra_Column.objects.create(**column).factura.add(factura_propietario)
		return factura_propietario

class Factura_Condominio_Extra_ColumSerializer(serializers.ModelSerializer):
	class Meta:
		model = Factura_Condominio_Extra_Colum
		fields = '__all__'

class PaymentMethodSerializer(serializers.ModelSerializer):
	class Meta:
		model = Payment_Method
		fields = '__all__'	

class PaymentMethodDetailSerializer(serializers.ModelSerializer):
	pais= PaisesSerializer()
	metodo_pago= PaymentMethodSerializer()
	class Meta:
		model = Payment_Method_Detail
		fields = '__all__'	

class Pagos_Deposito_CondominioSerializer(serializers.ModelSerializer):
	class Meta:
		model = Pagos_Condominio
		fields = '__all__'	
		read_only_fields = ['aprobado', 'condominio', 'fecha_aprobacion', 'monto', 'razon_rechazo']


	def validate_factura(self, factura):
		if factura.pagado==True:
			raise serializers.ValidationError(_('Bill has already been payed'))
		return factura


	def create(self, validated_data):
		pago_condominio = Pagos_Condominio.objects.create(**validated_data)
		return pago_condominio


class Pago_CondominioSerializer(serializers.ModelSerializer):
	tipo_de_pago = PaymentMethodDetailSerializer()
	class Meta:
		model = Pagos_Condominio
		fields = '__all__'

class Factura_CondominioSerializer(serializers.ModelSerializer):
	pago =Pago_CondominioSerializer(read_only = True)

	class Meta:
		model = Factura_Condominio
		fields = '__all__'
		read_only_fields = ['iva', 'sub_total']

	def create(self, validated_data):
		condominio = validated_data.get('condominio')
		validated_data['iva'] = (condominio.pais.iva*validated_data.get('monto')).quantize(settings.TWOPLACES)
		validated_data['sub_total'] = validated_data['monto']
		validated_data['monto'] = (validated_data['monto']+validated_data['iva']).quantize(settings.TWOPLACES)
		instance = Factura_Condominio.objects.create(**validated_data)
		return instance

class RelacionMesSerializer(serializers.Serializer):
	can_generate_relacion = serializers.BooleanField(read_only = True)
	month = serializers.DateTimeField()
	month_query= serializers.DateTimeField()
	minDate= serializers.DateTimeField()
	maxDate= serializers.DateTimeField()
	property_bills = Factura_PropietarioSerializer(many= True)
	latest_bill = Factura_CondominioSerializer()
	nonEvaluatedIngresos = serializers.BooleanField(read_only = True)
	columns = serializers.ListField(
	   child=serializers.CharField(required= False)
	)
	total_egresos = serializers.DecimalField( max_digits=50, decimal_places=2, read_only = True)

class ResumenCondominioSerializer(serializers.Serializer):
	nombre_inmueble=serializers.CharField(read_only = True)
	razon_social=serializers.CharField(read_only = True)
	deuda_actual=serializers.DecimalField( max_digits=50, decimal_places=2, read_only = True)
	pagos_sum=serializers.DecimalField( max_digits=50, decimal_places=2, read_only = True)
	cobranzas_sum=serializers.DecimalField( max_digits=50, decimal_places=2, read_only = True)
	categorias = serializers.SerializerMethodField()

	def get_categorias(self, ingreso):
		inmueble = self.context.get('inmueble')	
		categories = []
		if inmueble.junta_de_condominio ==True:
			categories.append('junta_de_condominio')

		elif inmueble.junta_de_condominio !=True:
			categories.append('no_miembro')

		if inmueble.arrendado ==True:
			categories.append('arrendatarios')

		else:
			categories.append('propietarios')	
		
		if inmueble.deuda_actual <0:
			categories.append('deudor')	

		for item in inmueble.categories.all():
			categories.append(item.name)

		return set(categories)

class UserField(serializers.Field):
    def to_representation(self, obj):
    	serializer = UserSerializer(obj)
        return serializer.data

    def to_internal_value(self, data):
        return User.objects.get( id = data )


class BlogSerializer(serializers.ModelSerializer):
	publisher = UserField()
	class Meta:
		model = Blog
		fields = '__all__'

class AffiliateSerializer(serializers.ModelSerializer):
	telefono1 = serializers.CharField(required = False, allow_null = True, allow_blank= True)
	telefono2 = serializers.CharField(required = False, allow_null = True, allow_blank= True)
	class Meta:
		model = Affiliate
		fields = '__all__'

	def update(self, instance, validated_data):
		instance.telefono1 = validated_data.get('telefono1',  instance.telefono1 )
		instance.telefono2 = validated_data.get('telefono2',  instance.telefono2 )
		instance.save()
		return instance

class Affiliate_IncomeSerializer(serializers.ModelSerializer):
	currency = serializers.SerializerMethodField()
	pais = serializers.CharField(source	= 'condominio.pais', read_only = True)
	class Meta:
		model = Affiliate_Income
		fields = '__all__'

	def get_currency(self, instance):
		return instance.condominio.pais.moneda


class Inmueble_UploadReqSerializer(serializers.ModelSerializer):
	monto = serializers.DecimalField(required = False, max_digits=50, decimal_places=2)
	class Meta:
		model = Inmueble_UploadReq
		exclude =['condominio']

	def validate_csv_file(self, csv_file):
		'''
		*Allowed content list containes allows mimetypes
		*max_size determines 
		'''
		max_size = 10485760
		allowed_content = [
			'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
			'text/csv'
		]
		if csv_file.size >max_size:
			raise serializers.ValidationError(_("file too large."))
		if not csv_file.content_type in allowed_content:
			raise serializers.ValidationError(_("invalid file type."))
		return csv_file

	def save(self, **kwargs):
		condominio= kwargs.pop('condominio')
		request = kwargs.pop('request')
		validated_data = self.validated_data
		instance = Inmueble_UploadReq.objects.create(condominio =condominio,**validated_data)
		messages.info(request, _("You have a new property upload request."))
		message = (_('A condominium needs its properties to be uploaded'), _('A condominium requires that its properties be uploaded, go to the user admin and provide a quote.' ), settings.DEFAULT_FROM_EMAIL, [email for (name, email) in settings.ADMINS])
		send_mass_email.delay((message, ),fail_silently = False)
		#send_email.delay(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.inmueble.inquilino.user.email] )

class Affiliate_Banc_AccountSerializer(serializers.ModelSerializer):
	affiliate= serializers.PrimaryKeyRelatedField(queryset = Affiliate.objects.all(), required= False)
	pais= serializers.PrimaryKeyRelatedField(queryset = Paises.objects.all(), required= False)


	def update(self, instance, validated_data):
		instance.pais = validated_data.get('pais', instance.pais)
		instance.titular = validated_data.get('titular', instance.titular)
		instance.banco = validated_data.get('banco', instance.banco)
		instance.nro_cuenta = validated_data.get('nro_cuenta', instance.nro_cuenta)
		instance.save()
		return instance

	def validate_pais(self, pais):
		request= self.context['request']
		#country_list= set([condominio.pais.pk for condominio in request.user.affiliate.condominios.all()])
		account_list = [acccount.pais.pk for acccount in request.user.affiliate.bank_accounts.all()]
		# if not pais.pk in country_list:
		# 	raise serializers.ValidationError(_('Country does not pertain to any of related condos.'))

		if pais.pk in account_list and not request.method=='PATCH':
			raise serializers.ValidationError(_('An account for this country is already registered.'))		
		return pais

	class Meta:
		model = Affiliate_Banc_Account
		fields = '__all__'

class InmuebleCSVSerializer(InmuebleSerializer):
	#junta_de_condominio = serializers.BooleanField()
	rif = serializers.CharField(required = False, allow_blank= True)#write_only = True
	email = serializers.EmailField(required = True)#write_only = True
	first_name = serializers.CharField(required = True)#write_only = True
	last_name = serializers.CharField(required = True)#write_only = True
	categories = None
	no_miembro = None
	no_arrendado = None
	#arrendado = serializers.BooleanField()
	may_modify_inmueble = None

	#balanceinicial = serializers.DecimalField()
	#alicuota = serializers.DecimalField()
	def validate_alicuota(self, alicuota):
		if alicuota <0:
			raise ValidationError(_("This value can not be negative"))
		return alicuota

	def validate_nombre_inmueble(self, nombre_inmueble):
		#CAN NOT CHANGE INMUEBLE NAME IF THEERE ARE FACTURAS FOR THE CONDO
		request = self.context['request']
		condominio= request.condominio
		#CHECK THAT INMUEBLE IS NOT ASSIGNED TO ANOTHER USER
		inmueble =condominio.inmueble_set.filter(nombre_inmueble = str(nombre_inmueble).strip().upper() )
		if inmueble.exists():
			inmueble = inmueble[0]
			if hasattr(inmueble, 'inquilino') == True:
				if request.method=='POST':
					#IF CREATING A NEW INMUEBLE IT CAN NOT BE ALREADY EXIST(NO DUP. FOR CONDO)
					raise ValidationError(_("This property already belongs to another owner."))

				elif request.method=='PATCH' and inmueble.nombre_inmueble != self.instance.nombre_inmueble:
					raise ValidationError(_("This property already belongs to another owner."))
		return nombre_inmueble

	def validate(self, validated_data):
		arrendado = validated_data.get('arrendado', None)
		arrendatario = validated_data.get('arrendatario', None)
		cargo = validated_data.get('cargo', None)
		junta_de_condominio = validated_data.get('junta_de_condominio', None)
		# if arrendado and junta_de_condominio:
		# 	raise ValidationError(_('Only owners can be part of the condominium board'))
		# if arrendatario and (junta_de_condominio or cargo):
		# 	raise ValidationError(_('Only owners can be part of the condominium board'))
		if cargo and (arrendatario==True or arrendado==True):
			raise ValidationError(_('Only owners can be part of the condominium board'))
		return validated_data


	def validate_balanceinicial(self, balanceinicial):
	# 	request = self.context['request']
	# 	if request.method =='PATCH':
	# 		facturas_condominio = Factura_Condominio.objects.filter(condominio=request.user.condominio)
	# 		if facturas_condominio.exists():
	# 			raise ValidationError(_("You may not modify initial balance once you have generated an expense report."))
		return balanceinicial


	def create(self, validated_data):
		request = self.context['request']
		#site name
		current_site = get_current_site(request)
		condominio = request.condominio
		user_data = {}
		user_data['email'] = validated_data.pop('email')

		#GET OR CREATE THE USER ACCORDING TO EMAIL
		user, created = User.objects.get_or_create( **user_data)
		if created:	
			user.first_name = validated_data.pop('first_name')
			user.last_name = validated_data.pop('last_name')
			user.username = str(user_data['email'] ).split('@')[0]
			user.save()

			inquilino_data = {
				'rif':validated_data.pop('rif', None),
				'user': user
			}
			inquilino = Inquilino.objects.create(**inquilino_data)
			send_email_confirmation(request, user, signup=True)

		elif not user.emailaddress_set.filter(verified= True).exists():#IF EMAIL ADDRESS HAS NOT BEEN CONFIRMED SEND CONFIRMATION EMAIL
			send_email_confirmation(request, user, signup=False)

		#GET OR CREATE INMUEBLE
		inmueble, inmueble_created = Inmueble.objects.get_or_create(condominio = condominio, nombre_inmueble = validated_data.pop('nombre_inmueble'))
		if inmueble_created:# IF INMUEBLE WAS CREATED ATTACH ALL OF THE NEW VALUES TO IT ESLE LEAVE IT AS IS

			for attr, value in validated_data.items():
				
				inmueble.deuda_actual = validated_data.pop('balanceinicial', 0)
				setattr(inmueble, attr, value)

		inmueble.inquilino = user.inquilino
		inmueble.save()
		return inmueble



# class Cargar_Codigos_CSVSerializer(serializers.Serializer):
#     csv_file = serializers.FileField(required = True)
#     condominio = serializers.PrimaryKeyRelatedField(required=True, queryset= Condominio.objects.all())

#     def validate_condominio(self, condominio):
#     	related_inmuebles= condominio.inmueble_set.all()
#     	if related_inmuebles.exists():
# 			raise serializers.ValidationError(_('The condominium can not have any affiliated properties nor have been billed in order to accept CSV file.'))
#     	return condominio

#     def validate_csv_file(self, file):
#         if not str(file.content_type) == 'text/csv':
#         	raise serializers.ValidationError(_("Wrong format type") )

#         fieldnames = ['first_name','last_name','rif','email','nombre_inmueble','balanceinicial','alicuota','junta_de_condominio','cargo','arrendado','arrendatario']
#         #VALIDATE THAT PROPOSED TOTAL IS NOT OVER 100
#         reader = csv.DictReader(file, fieldnames=fieldnames)
#         count=0
#         alicuota = 0
#         for row in reader:
#         	alicuota = row['alicuota']
#         	count+=1

#         if alicuota>100:
#         	raise serializers.ValidationError(_("Alicuotas in file can not be greater than 100%.") )
#         return file

	# def create(self, validated_data):
	# 	file= validated_data.get('csv_file')
	# 	fieldnames = ['first_name','last_name','rif','email','nombre_inmueble','balanceinicial','alicuota','junta_de_condominio','cargo','arrendado','arrendatario']
 #        reader = csv.DictReader(file, fieldnames=fieldnames)
 #        count=0
 #        for row in reader:
 #            if count>0:
 #                inmuebles_serializer = InmuebleSerializer(data = row, context={'request':request})
 #                if inmuebles_serializer.is_valid():
 #                    print inmuebles_serializer.validated_data
 #                else:
 #                    raise serializers.ValidationError(serializer.errors)
 #            count+=1

 #        return instance  




