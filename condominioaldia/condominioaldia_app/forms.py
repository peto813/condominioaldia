
# -*- coding: utf-8 -*-
import csv, decimal, os
from django import forms
from django.contrib.auth.forms import PasswordResetForm
#from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from django.contrib.auth import (
    authenticate, get_user_model, password_validation,
)
from django.core.exceptions import ValidationError
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.text import capfirst
from django.utils.translation import gettext, gettext_lazy as _
from condominioaldia_app.tasks import send_pwd_recovery_task
from condominioaldia_app.models import Talonario,Affiliate, Condominio, Affiliate_Income,Pagos_Condominio

UserModel = get_user_model()

class customPasswordResetForm(PasswordResetForm):
    # email = forms.EmailField(label=_("Email"), max_length=254)

    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        """
        Send a django.core.mail.EmailMultiAlternatives to `to_email`.
        """
        subject = loader.render_to_string(subject_template_name, context)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)
        send_pwd_recovery_task.delay(subject, body, from_email, [to_email], html_email_template_name)
        # email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
        # if html_email_template_name is not None:
        #     html_email = loader.render_to_string(html_email_template_name, context)
        #     email_message.attach_alternative(html_email, 'text/html')

        # email_message.send()

    # def get_users(self, email):
    #     """Given an email, return matching user(s) who should receive a reset.

    #     This allows subclasses to more easily customize the default policies
    #     that prevent inactive users and users with unusable passwords from
    #     resetting their password.
    #     """
    #     active_users = UserModel._default_manager.filter(**{
    #         '%s__iexact' % UserModel.get_email_field_name(): email,
    #         'is_active': True,
    #     })
    #     return (u for u in active_users if u.has_usable_password())

    def save(self, domain_override=None,
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None, html_email_template_name=None,
             extra_email_context=None):
        """
        Generate a one-use only link for resetting password and send it to the
        user.
        """
        email = self.cleaned_data["email"]
        protocol = 'https' if request.is_secure() else 'http'
        for user in self.get_users(email):
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            
            context = {
                'email': email,
                'domain': domain,
                'site_name': site_name,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': 'https' if use_https else 'http',
            }
            if extra_email_context is not None:
                context.update(extra_email_context)

            self.send_mail(
                subject_template_name, email_template_name, context, from_email,
                email, html_email_template_name=html_email_template_name,
            )



# class CondominioForm(forms.ModelForm):
#     logo = forms.FileField(required    = False)
#     def clean_logo(self):
#         logo = self.cleaned_data.get('logo', None)
#         print logo
#         from django.core.exceptions import ValidationError
#         if logo:
#             print logo.content_type
#             if not 'application/pdf' in str(logo.content_type):
#                 raise ValidationError("Please submit a valid PDF file.")
#         return logo
#     class Meta:
#         model = Condominio
#         fields = '__all__'

class Affiliate_IncomeForm(forms.ModelForm):
    #pagado = forms.BooleanField(required= True,help_text=_("This ONLY can be checked after the condominium has payed the pertaining bill."))
    class Meta:
        model = Affiliate_Income
        exclude= ['status']

    def clean_pagado(self):
        pagado = self.cleaned_data.get('pagado', None)
        if pagado ==False:
            raise ValidationError(_('This field is required.'))
        return pagado

    def clean(self):
        cleaned_data = super(Affiliate_IncomeForm, self).clean()
        payment_proof = cleaned_data.get('payment_proof', None)
        pagado = cleaned_data.get('pagado', None)
        if pagado==True and not payment_proof:
            self.add_error('payment_proof', _('Setting payed to true requires payment proof.'))


class PagosCondominioaldiaAdmin_Form(forms.ModelForm):
    #pago = forms.NullBooleanField(required = True)
    class Meta:
        model = Pagos_Condominio
        fields = '__all__'

    def clean(self):
        cleaned_data = super(PagosCondominioaldiaAdmin_Form, self).clean()
        razon_rechazo = cleaned_data.get('razon_rechazo', None)
        aprobado = cleaned_data.get('aprobado', None)

        if not aprobado:
            self.add_error('aprobado', _('You need to accept or reject this payment.')) 

        if aprobado == False and not razon_rechazo:
            self.add_error('razon_rechazo', _('You need to provide a reason for rejection.')) 

        pagado = cleaned_data.get('pagado', None)
        if pagado==True and not payment_proof:
            self.add_error('payment_proof', _('Setting payed to true requires payment proof.'))


class TalonarioForm(forms.ModelForm):

    class Meta:
        model = Talonario
        fields = '__all__'

    def clean(self):
        queryset= Talonario.objects.all()
        nro_control_desde= self.cleaned_data["nro_control_desde"]
        nro_control_hasta= self.cleaned_data["nro_control_hasta"]

        if nro_control_hasta <=nro_control_desde:
            self.add_error('nro_control_hasta', _('End control number must be greater than begin control number.'))

        if queryset.exists():
            if any(item.nro_control_desde<=nro_control_hasta<=item.nro_control_hasta for item in queryset):
                self.add_error('nro_control_hasta', _('Another bill book already contains bills in this range.'))
        
            if any(item.nro_control_desde<=nro_control_desde<=item.nro_control_hasta for item in queryset):
                self.add_error('nro_control_desde', _('Another bill book already contains bills in this range.'))


class AffiliateAdminForm(forms.ModelForm):
    razon_rechazo = forms.CharField(required= False)
    class Meta:
        model = Affiliate
        fields = '__all__'


    def clean(self):
        razon_rechazo = self.cleaned_data.get('razon_rechazo', None)
        aprobado= self.cleaned_data.get('aprobado', None)
        if aprobado ==False and not razon_rechazo:
            self.add_error('razon_rechazo', _('You must provide the cause of rejection.'))


class Mass_Email_Form(forms.Form):
    email = forms.EmailField(widget=forms.TextInput(attrs={ 'placeholder': _("E-mail") }), label=_("E-mail"),required = False)
    #email = forms.EmailField(required= True, label=_("Correo electronico"), attrs={'placeholder':'aa'})
    name= forms.CharField(widget=forms.TextInput(attrs={ 'placeholder': _("Name") }), required = False, label=_("Name"))
    csv_file = forms.FileField(required = False)
    def clean(self):
        cleaned_data =  self.cleaned_data
        csv_file = cleaned_data.get('csv_file' or None)
        if 'enviar' in self.data:
            if not cleaned_data.get('email', None):
                self.add_error('email', _('This field is required.'))
            if not cleaned_data.get('name', None):
                self.add_error('name', _('This field is required.'))
        elif 'send_csv' in self.data:
            if not csv_file:
                self.add_error('csv_file', _('Please select a file.'))


    # def __init__(self, *args, **kwargs):
    #     if 'send_csv' in str(args):
    #         self.fields['csv_file'] = forms.FileField(required = True)
    #     super(Mass_Email_Form, self).__init__(*args, **kwargs)


class Cargar_Codigos_CSVForm(forms.Form):
    csv_file = forms.FileField(required = True, label='Archivo')
    condominio = forms.CharField(required= False)

    def clean_condominio(self):
        
        try:
            condominio =Condominio.objects.get(pk=self.cleaned_data.get('condominio'))
        except:
            raise forms.ValidationError(_('Condominiun does not exist.'))

        related_inmuebles= condominio.inmueble_set.all()
        # if related_inmuebles.exists():
        #     raise forms.ValidationError(_('The condominium can not have any affiliated properties nor have been billed in order to accept CSV file.'))
        return condominio

    def clean_csv_file(self):
        file = self.cleaned_data.get('csv_file')
        if not str(file.content_type) == 'text/csv':
            raise forms.ValidationError(_("Wrong format type") )

        fieldnames = ['first_name','last_name','rif','email','nombre_inmueble','balanceinicial','alicuota','junta_de_condominio','cargo','arrendado','arrendatario']
        #VALIDATE THAT PROPOSED TOTAL IS NOT OVER 100
        reader = csv.DictReader(file, fieldnames=fieldnames)
        count=0
        alicuota = 0
        for row in reader:
            if count >0:
                alicuota += decimal.Decimal(row['alicuota'])
            count+=1
        if alicuota>100:
            raise forms.ValidationError(_("Property percentages in file can not add over 100%.") )
        return file