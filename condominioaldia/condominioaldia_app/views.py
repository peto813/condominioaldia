# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from allauth.account.models import EmailConfirmationHMAC, EmailConfirmation
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
import requests, datetime, pytz, dateutil.parser, csv, json, calendar
from rest_framework.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.humanize.templatetags.humanize import intcomma
from django.template import defaultfilters
from django.conf import settings
from django.db.models import Q, Sum
from django.http import Http404
from django.shortcuts import render
from django.template import loader
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext, gettext_lazy as _
from django.views.generic import TemplateView
from dateutil.relativedelta import relativedelta
from condominioaldia_app.tasks import (
    send_email,
    send_mass_email,
    email_factura_condominio,
    email_egresos_cuotas,
    email_admins,
    )
from condominioaldia_app.models import *
from condominioaldia_app.utils import register_cc_payment,unescape,Instapago, condominio_activator, get_user_type, last_day_of_month, last_instant_of_month,month_range_dt, blog_paginator_summary, update_condo_status, send_condo_status_message,data_range, get_total_cobranzas
from condominioaldia_app.forms import Cargar_Codigos_CSVForm, Mass_Email_Form
from condominioaldia_app.formsets import Mass_MarkettingFormset
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework import serializers
from rest_framework.filters import SearchFilter
from rest_framework.generics import GenericAPIView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator

# Create your views here.

#REST FRAMEWORK IMPORTS 
from rest_framework import generics
from rest_framework import viewsets
from rest_framework.mixins import CreateModelMixin
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_auth.views import LoginView, PasswordResetView, PasswordChangeView
from rest_auth.registration import views as rest_auth_views
from allauth.account.adapter import DefaultAccountAdapter, get_adapter
#from allauth.account.views import ConfirmEmailView as AllauthConfirmEmailView

#SERIALIZERS
from serializers import (
    JuntaCondominioSerializer,
    InstaPago_Serializer,
    ContactUsSerializer,
    ResumenCondominioSerializer,
    Cobranza_CondominioSerializer,
    Banco_PaisSerializer,
    Remove_categorySerializer,
	PaisesSerializer,
    BancosCondominioaldiaSerializer,
    UserSerializer,
    InmuebleSerializer,
    InquilinoSerializer,
    CustomLoginSerializer,
    PaginasAmarillasSerializer,
    BancosSerializer,
    CarteleraSerializer,
    customPasswordResetSerializer,
    Ingreso_CondominioSerializer,
    contextSerializer,
    Egreso_CondominioSerializer,
    tiposEgresosSerializer,
    CondominioSerializer,
    customPasswordChangeSerializer,
    FaqSerializer,
    MessagesSerializer,
    PollsApiViewSerializer,
    Factura_CondominioSerializer,
    RelacionMesSerializer,
    RelacionMes2Serializer,
    Factura_PropietarioSerializer,
    BuildRelacionMesSerializer,
    Factura_Condominio_Extra_ColumSerializer,
    PaymentMethodDetailSerializer,
    Pagos_Deposito_CondominioSerializer,
    BlogSerializer,
    AffiliateSerializer,
    Affiliate_IncomeSerializer,
    Affiliate_Banc_AccountSerializer,
    CondominidoAfilliateSerialzier,
    VoteSerializer,
    InmuebleCategorySerializer,
    Assign_categorySerializer,
    SocialLinksSerializer,
    InmuebleCSVSerializer,
    Inmueble_UploadReqSerializer,
	)

#FILTERS
from django_filters.rest_framework import DjangoFilterBackend
from filters import (
	Paises_Filter,
    UsuarioFilter,
    InmuebleFilter,
    IngresosFilter,
    EgresoFilter,
    MessagesFilter,
    PollsFilter,
    Factura_CondominioFilter,
    ingresos_afiliadoFilter,
	)


#PAGINATIONS
from pagination import (
    StandardResultsSetPagination,
    BlogPagination,    
    )

#PERMISSIONS
from condominioaldia_app.permissions import *


@method_decorator(staff_member_required, name='dispatch')
class confirm_deletionView(TemplateView):

    def reverse_latest_cierre(self, condominios):
        message= _("No bills exist.")
        for condominio in condominios:
            factura_condominio = condominio.factura_condominio_set.all()
            
            if factura_condominio.exists():
                #delete latest factura_condominio
                latest_factura = factura_condominio.latest('mes')
                date_range = month_range_dt(latest_factura.mes)
                egresos, ingresos = condominio.egreso_condominio_set.all(),condominio.ingreso_condominio_set.all()
                cobranzas = condominio.cobranza_condominio_set.all()
                facturas_propietarios = condominio.factura_propietario_set.all()
                bancos= condominio.bancos_set.all()

                #delete any open egresos/ingresos/cobranzas/ (current period) and factura_propietario(latest)
                #egresos.filter(cerrado=False).delete()
                for egreso in egresos.filter(cerrado=False):
                    egreso.delete()

                #ingresos.filter(cerrado=False).delete()
                for ingreso in ingresos.filter(cerrado=False):
                    ingreso.delete()
                
                cobranzas.filter(editable= True).delete()#cobranzas for period to delete
                
                facturas_propietarios.filter(mes__range=(date_range[0], date_range[1])).delete()
                latest_factura.delete()

                #reverse cierre estatus for the ingresos/bancos editability/egresos/cobranzas for past month
                egresos.filter(mes__range=(date_range[0], date_range[1])).update(cerrado = False)
                ingresos.filter(mes__range=(date_range[0], date_range[1])).update(cerrado = False)
                bancos.filter(fecha_balance_inicial__range=(date_range[0], date_range[1])).update(editable= True)
                cobranzas.filter(mes__range=(date_range[0], date_range[1])).exclude(cobrar_cuando ='inmediato', cobranza_condominio_destinatario__payment__aprobado = True).update(editable= True)


                ### further test by creating a in inmediato with a payment
             
                # for cobranza in cobranzas:
                #     if cobranza.cobrar_cuando =='inmediato' and cobranza.cobranza_condominio_destinatario.payment:
                #         if cobranza.cobranza_condominio_destinatario.payment.aprobado == True:
                #             pass
                #     else:
                #         cobranza.editable=True


                '''
                note: verify bank balance is restored to past months balance prior 
                to relacion de cuotas
                '''
            message= _("Last cut succesfully reversed.")
        return message

    def post(self, request, **kwargs):
        condominios= Condominio.objects.filter(pk__in =request.session.get('del_corte_list')) 
        message = self.reverse_latest_cierre(condominios)
        messages.info(request, message)
        del request.session['del_corte_list']
        return HttpResponseRedirect('/admin/condominioaldia_app/condominio/')

@method_decorator(staff_member_required, name='dispatch')
class Marketting_Email(TemplateView):
    template_name = "marketting_email.html"

    def post(self, request, **kwargs):
        context = self.get_context_data()
        if 'enviar' in str(request.POST):
            form = Mass_Email_Form(request.POST or None, request.FILES or None)
            if form.is_valid():
                context['recipient_name'] = form.validated_data.get('name')
                subject = "Condominioaldia - ¡Vivir en comunidad se acaba de hacer mas facil!"
                html_message= loader.render_to_string('account/email/promotional_email.html', context)
                message = loader.render_to_string('account/email/promotional_email.txt', context)
                send_email.delay(subject, message,settings.DEFAULT_FROM_EMAIL, [form.validated_data.get('email')],html_message = html_message)
                context['post_success'] = True
            else:
                context['post_success'] = False
                context['form'] = form

        elif 'send_csv' in str(request.POST):
            form = Mass_Email_Form(request.POST or None,request.FILES or None, 'send_csv')
            if form.is_valid():
                fieldnames =['name', 'email']
                csv_file = form.validated_data.get('csv_file')
                reader = csv.DictReader(csv_file, fieldnames=fieldnames)#READ CSV FILE ROWS
                count=0
                for row in reader:
                    if count!=0:
                        form =  Mass_Email_Form(row)
                        if form.is_valid():
                            #send the message
                            context['recipient_name'] = form.validated_data.get('name')
                            subject = "Condominioaldia - ¡Vivir en comunidad se acaba de hacer mas facil!"
                            html_message= loader.render_to_string('account/email/promotional_email.html', context)
                            message = loader.render_to_string('account/email/promotional_email.txt', context)
                            send_email.delay(subject, message, settings.DEFAULT_FROM_EMAIL, [row['email']], html_message = html_message )
                        else:
                            print form.errors, 'row invalid'
                    count+=1
                # formset= Mass_MarkettingFormset(request.POST or None)
                # if formset.is_valid():
                #     print formset.validated_data
                # else:
                #     print formset.errors
                context['post_success'] = True
            else:
                context['post_success'] = False
                context['form'] = form

        elif 'download_sample' in str(request.POST):

            #file_type= request.GET.get('file_type')

            # if file_type =='csv':
            #     url = os.path.join(settings.STATIC_ROOT, 'samples/inmuebles.csv')
            #     extension='csv'
            #     content_type='text/csv'
            # elif file_type =='excel':
            #     url = os.path.join(settings.STATIC_ROOT, 'samples/inmuebles.xlsx')
            #     content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            #     extension='xlsx'
            url = os.path.join(settings.STATIC_ROOT, 'samples/bulk_marketting_email.csv')
            file = open(url, 'rb')
            filename = 'emailsamplecsv.%s' %('csv')
            response = HttpResponse(file, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="%s"' % filename
            return response


        # recipient= ['universal_video@hotmail.com']
        #print context
        ##############
        # context['recipient_name'] ='Alberto'
        # ##########
        # subject = "Condominioaldia - ¡Vivir en comunidad se acaba de hacer mas facil!"
        # html_message= loader.render_to_string('account/email/promotional_email.html', context)
        # message = loader.render_to_string('account/email/promotional_email.txt', context)
        # send_email.delay(subject, message,settings.DEFAULT_FROM_EMAIL, recipient,html_message = html_message)
        return self.render_to_response(context)

    def get(self, request):
        context = self.get_context_data()
        return self.render_to_response(context) 

    def get_context_data(self, **kwargs):
        request_method =self.request.method
        context = super(Marketting_Email, self).get_context_data(**kwargs)
        context['title'] =_("Marketting E-mail")
        site = get_current_site(self.request)
        context['site_title'] = str(site.name).title()
        form = Mass_Email_Form()
        context['form'] = form
        if request_method =='GET':
            pass
        elif request_method== 'POST':
            context['url'] = reverse('index')
            protocol = 'https' if self.request.is_secure() else 'http'
            context['logo'] = protocol+'://'+os.path.join(str(site.domain), 'static/img/logos/logo2.png')
            context['url'] = protocol+'://'+str(site.domain)
            context['tw_icon'] = protocol+'://'+os.path.join(str(site.domain), 'static/img/logos/twitterlogo.png')
            context['fb_icon'] = protocol+'://'+os.path.join(str(site.domain), 'static/img/logos/fblogo.ico')
            context['email'] = self.request.POST.get('email', None)
            context['recipient_name'] = self.request.POST.get('name', '')
            context['site_name'] = str(site.name).title()
        return context

class CustomLoginView(LoginView):
    serializer_class = CustomLoginSerializer


# class testView(TemplateView):
#     template_name = "a.html"
#     def get(self, request):
#         ctx = {}
#         from django.conf import settings
#         ctx['STATIC_ROOT'] = settings.STATIC_ROOT
#         ctx['STATICFILES_DIRS'] = settings.STATICFILES_DIRS
#         ctx['MEDIA_ROOT'] = settings.MEDIA_ROOT
#         ctx['STATIC_URL'] = settings.STATIC_URL
#         return self.render_to_response(ctx)


@method_decorator(staff_member_required, name='dispatch')
class InmuebleCSVView(TemplateView):
    template_name = "upload_inmuebles_csv.html"


    def get_object(self, condominio_id):
        return Condominio.objects.get(pk =condominio_id)

    def get(self, request, condominio= None, *args, **kwargs):
        try:
            self.object = self.get_object(condominio)
        except Http404:
            self.object = None

        ctx = self.get_context_data()
        ctx['condominio'] = self.object
        return self.render_to_response(ctx) 

    def post(self, request, *args, **kwargs):
        post_type =request.POST.get('post_type', None)
        kwargs['post_type'] = post_type
        '''CHECK WHETHER USER IS POSTING A VERIFICATION OR CREATING'''
        if post_type =='guardar':

            context = self.get_context_data(**kwargs)
            context['guardar'] = True
            form =context["form"]
            table_list= self.request.session.get('table_list')# CALL SESSION
            
            #print table_list[0], type(table_list)
            for data in table_list:
                self.request.condominio = Condominio.objects.get(pk=self.request.session.get('condominio'))
                serializer = InmuebleCSVSerializer(data= data, context={'request':self.request})
                if serializer.is_valid():
                    serializer.save()
                    context['guardar']=None
                    context["form"]=None
                else:
                    print serializer.errors

            self.request.session.pop('table_list')
            self.request.session.pop('condominio')
            self.request.session.pop('file_name') 
            context['success'] = True
            return super(InmuebleCSVView, self).render_to_response(context)


        elif post_type =='verify':
            context = self.get_context_data(**kwargs)
            form =context["form"]

            table_list = []
            json_list = []
            error_counter =0
            if form.is_valid():
                '''
                IF FORM DATA IS VALID CREATE A JSON LIST OF ELEMENTS AND RETURN TO
                USER FOR VISUAL VERIFICATION. THEN SET THE SESSION VARIABLE AND RETURN FORMS
                INITIAL VALUES
                '''
                file= form.validated_data.get('csv_file')
                fieldnames = ['first_name','last_name','rif','email','nombre_inmueble','balanceinicial','alicuota','junta_de_condominio','cargo','arrendado','arrendatario']
                reader = csv.DictReader(file, fieldnames=fieldnames)#READ CSV FILE ROWS
                count=0
                for row in reader:
                    if count>0:
                        request.condominio=form.validated_data.get('condominio')
                        inmuebles_serializer = InmuebleCSVSerializer(data = row, context={'request':request})
                        if inmuebles_serializer.is_valid():
                            context['guardar'] = True
                            table_list.append(inmuebles_serializer.data)
                            json_list.append(inmuebles_serializer.data)
                        else:
                            error_counter+=1
                            error_dict = {}
                            for key, value in inmuebles_serializer.errors.iteritems():
                                error_dict['error_message'] = value[0]
                            error_dict['email'] = row['email']
                            error_dict['error_in_row'] = True
                            table_list.append(error_dict)
                            json_list.append(error_dict)
                    context['error_counter']=error_counter
                            #print inmuebles_serializer.errors
                    count+=1
                form = Cargar_Codigos_CSVForm(initial={'csv_file': file})

                request.session['condominio'] = request.condominio.pk#SET SESSION FOR USE LATER
                request.session['table_list'] = json_list#SET SESSION FOR USE LATER
                request.session['file_name'] = file.name#SET SESSION FOR USE LATER
                ########
            else:
                print form.errors

        context["form"] =form
        context['table_list']=table_list
        
        return super(InmuebleCSVView, self).render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super(InmuebleCSVView, self).get_context_data(**kwargs)
        context['success'] = False
        context['title'] = _("Bulk upload properties")
        site = get_current_site(self.request)
        context['site_title'] = str(site.name).title()
        post_type = kwargs.get('post_type', None)
        data = self.request.POST.copy()
        data['condominio'] = kwargs.get('condominio', None)
        if data['condominio']:
            context['moneda'] =Condominio.objects.get(pk = data['condominio']).pais.moneda
        if self.request.method=='GET':
            form = Cargar_Codigos_CSVForm()
        elif self.request.method=='POST' and post_type=='verify':
            form = Cargar_Codigos_CSVForm(data or None, self.request.FILES or None)  # instance= None
        elif self.request.method=='POST' and post_type=='guardar':
            form = Cargar_Codigos_CSVForm(initial={'csv_file': self.request.session.get('file_name')})  # instance= None
       
        context["form"] = form
        #protocol = 'https' if self.request.is_secure() else 'http'

        context['ejemploCSV'] = os.path.join(settings.STATIC_URL, 'samples')+ '/inmuebles.xlsx'
        return context

class confirmEmailView(TemplateView, rest_auth_views.VerifyEmailView):
    template_name = "email_confirm.html"

    def get(self, *args, **kwargs):
        try:
            self.object = self.get_object()
            if settings.ACCOUNT_CONFIRM_EMAIL_ON_GET:
                return self.post(*args, **kwargs)
        except Http404:
            self.object = None
        ctx = self.get_context_data()
        return self.render_to_response(ctx)

    def get_usertype(self, user):
        if hasattr(user, 'affiliate'):
            user_type='affiliate'
        elif hasattr(user, 'inquilino'):
            user_type='inquilino'
        elif hasattr(user, 'condominio'):
            user_type='condominio'
        return user_type

    def get_object(self, queryset=None):
        key = self.kwargs['key']
        emailconfirmation = EmailConfirmationHMAC.from_key(key)
        if not emailconfirmation:
            if queryset is None:
                queryset = self.get_queryset()
            try:
                emailconfirmation = queryset.get(key=key.lower())

                if emailconfirmation.key_expired()==True:
                    setattr(emailconfirmation, 'message', _("This confirmation link is expired. If you try to login you will be sent a new confirmation link.")) 
                    setattr(emailconfirmation, 'account_verified', False)

                elif emailconfirmation.key_expired()==False:
                    
                    setattr(emailconfirmation, 'account_verified', True)
                    setattr(emailconfirmation, 'message', _("E-mail verified"))

                    if emailconfirmation.email_address.verified == False:
                        #message = (_('New affiliate or condo needs approval'), _('Please enter the admin panel; condominiums(or affiliate) section and verify a new condominiums or affiliate information; approve or reject at discretion' ), settings.DEFAULT_FROM_EMAIL, [email for (name, email) in settings.ADMINS])
                        user_type =self.get_usertype(emailconfirmation.email_address.user)
                        if user_type == 'condominio':
                            message = (_('New condominium needs approval'), _('Please enter the admin panel; condominiums section and verify a new condominiums information; approve or reject at discretion' ), settings.DEFAULT_FROM_EMAIL, [email for (name, email) in settings.ADMINS])
                        elif user_type =='affiliate':
                            message= (_('New affiliate needs approval'), _('Please enter the admin panel; affiliates section and verify a new affiliate information; approve or reject at discretion' ), settings.DEFAULT_FROM_EMAIL, [email for (name, email) in settings.ADMINS])
                        if user_type != 'inquilino':
                            send_mass_email.delay((message, ),fail_silently = False)
                        messages.info(self.request, _("New affiliate or condo needs approval"))

            except EmailConfirmation.DoesNotExist:
                class emailconfirmation: pass
                emailconfirmation.account_verified = False
                emailconfirmation.message = _('This E-mail confirmation link is invalid.')
        return emailconfirmation

    def post(self, *args, **kwargs):
        self.object = confirmation = self.get_object()
        if confirmation.account_verified == True:
            confirmation.confirm(self.request)
        ctx = self.get_context_data()
        ctx['account_verified'] = confirmation.account_verified
        ctx['message'] = confirmation.message
        return self.render_to_response(ctx)
        #return redirect(redirect_url)
    # def get_context_data(self, **kwargs):
    #     print kwargs
    #     if kwargs['key']:
    #         secure = self.request.is_secure()
    #         protocol = 'https' if secure==True else 'http'
    #         url = '%s://%s%s' %( protocol, self.request.get_host(), reverse('rest_verify_email'))
    #         r = requests.post(url, data = kwargs )
    #         #print r
    #         #print dir(r)
    #         print dir(r.request)
    #         if r.status_code == 200 :
    #             account_verified  = True

    #             message = (_('New affiliate or condo needs approval'), _('Please enter the admin panel; condominiums(or affiliate) section and verify a new condominiums or affiliate information; approve or reject at discretion' ), settings.DEFAULT_FROM_EMAIL, [email for (name, email) in settings.ADMINS])
    #             # if user_type == 'condominio':
    #             #     message = (_('New condominium needs approval'), _('Please enter the admin panel; condominiums section and verify a new condominiums information; approve or reject at discretion' ), settings.DEFAULT_FROM_EMAIL, [email for (name, email) in settings.ADMINS])
    #             # elif user_type =='affiliate':
    #             #     message= (_('New affiliate needs approval'), _('Please enter the admin panel; affiliates section and verify a new affiliate information; approve or reject at discretion' ), settings.DEFAULT_FROM_EMAIL, [email for (name, email) in settings.ADMINS])
    #             user_type = get_user_type(self.request)
    #             print user_type
    #             if user_type != 'inquilino' and self.request.user.emailaddress_set.filter(verified=False).exists():
    #                 send_mass_email.delay((message, ),fail_silently = False)
    #             messages.info(self.request, _("New affiliate or condo needs approval"))
    #         else:
    #             account_verified = False
    #     context = super( confirmEmailView, self ).get_context_data(**kwargs)
    #     context['account_verified'] = account_verified
    #     context['return_url'] = self.request.get_host()
    #     return context
class help_itemsView(generics.ListAPIView):
    queryset =Social_Link.objects.all()
    serializer_class =SocialLinksSerializer
    #queryset =HelpItems.objects.all()

class SocialLinksView(generics.ListAPIView):
    queryset =Social_Link.objects.all()
    serializer_class =SocialLinksSerializer


class IndexView(TemplateView ):
    template_name = "index.html"
    # def get_context_data(self, **kwargs):
    #     context = super(IndexView, self).get_context_data(**kwargs)
    #     social_links = Social_Link.objects.all()
    #     for link in social_links:
    #         context[link.name] = link.link
    #     return context

class Bank_Accounts_Condominioaldia_View(APIView):
    permission_classes = (IsAuthenticated,  )
    queryset = BancosCondominioaldia.objects.all()
    serializer_class = BancosCondominioaldiaSerializer
    facturas = Factura_Condominio.objects.filter(pagado=False)
    payment_method = Payment_Method_Detail.objects.all()

    def get_queryset(self):
        queryset=self.queryset.filter(pais=self.request.user.condominio.pais)
        return queryset

    def get_factura(self, pk):
        try:
            return self.facturas.filter(condominio=self.request.user.condominio).get(pk = pk)
        except Factura_Condominio.DoesNotExist:
            raise Http404

    def get_payment_method(self, pk):
        try:
            return self.payment_method.filter(pais=self.request.user.condominio.pais).get(pk = pk)
        except self.facturas.model.DoesNotExist:    
            raise Http404

    def get(self, request,factura= None, payment_method=None):
        accounts_queryset=self.get_queryset()
        factura= self.get_factura(factura)
        payment_method= self.get_payment_method(payment_method)
        accounts_serializer= self.serializer_class(accounts_queryset, many= True)
        factura_serializer= Factura_CondominioSerializer(factura)
        payment_method_serializer= PaymentMethodDetailSerializer(payment_method)
        context= {
            'accounts' :accounts_serializer.data,
            'factura' : factura_serializer.data,
            'payment_method':payment_method_serializer.data
        }
        return Response(context, status = status.HTTP_200_OK )

    def send_admins_email(self):
        subject = _("You have a new payment awaiting approval.")
        message= _("Go to the condominioaldia admin panel and check a verify a deposit/transfer that you may have.")
        email_admins.delay(subject, message, fail_silently=True)

    def post(self, request, factura=None, tipo_de_pago= None):
        serializer = Pagos_Deposito_CondominioSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save( monto = serializer.validated_data.get('factura').monto)
            self.send_admins_email()
            return Response(serializer.data, status = status.HTTP_200_OK )

class GetUserView(APIView):
    permission_classes = (IsAuthenticated,  )
    lookup_field = 'email'
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get(self, request, email,format=None):
        user = User.objects.filter(email = email)
        if user.exists():
            instance= User.objects.get(email = email)
            serializer= self.serializer_class(instance)
            return Response(serializer.data, status = status.HTTP_200_OK )
        #return Response('NOT FOUND', status = status.HTTP_200_OK )
        return Response('NOT FOUND', status=status.HTTP_400_BAD_REQUEST) 


class InquilinosViewSet(viewsets.ModelViewSet):
    queryset = Inquilino.objects.all()
    serializer_class = InquilinoSerializer
    permission_classes = (IsAuthenticated, IsRelatedToCondominio, UsuarioAprobado, IsCondominioOrReadonly,)
    filter_backends = ( DjangoFilterBackend, )


class InmuebleViewSet(viewsets.ModelViewSet):
    queryset = Inmueble.objects.all()
    serializer_class = InmuebleSerializer
    permission_classes = (IsAuthenticated, IsRelatedToCondominio, UsuarioAprobado, IsCondominioOrReadonly,)
    filter_backends = ( DjangoFilterBackend, )
    filter_class = InmuebleFilter

    def get_object(self, pk):
        try:
            return Inmueble.objects.get(pk=pk)
        except Inmueble.DoesNotExist:
            raise Http404

    def get_queryset(self):
        user_type = get_user_type(self.request)
        if user_type =='condominio':
            return self.queryset.filter(condominio = self.request.user.condominio)
        elif user_type =='inquilino':
            inmueble_id= self.request.session.get('inmueble')
            condominio = Inmueble.objects.get(pk =inmueble_id).condominio
            return self.queryset.filter(condominio= condominio)

    def create(self, request):
        data = request.data.copy()
        serializer = InmuebleSerializer( data = data, context = {'request': request})
        if serializer.is_valid():
            serializer.save()
            serializer = InmuebleSerializer(Inmueble.objects.filter(condominio = request.user.condominio), many= True)
            request.user.condominio.refresh_from_db()
            context = {
                'condominio_activo': request.user.condominio.activo,
                'data':serializer.data
            }
            return Response(context, status=status.HTTP_200_OK)
        else:
            print serializer.errors
        return Response('serializer.data', status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    def partial_update(self, request, pk = None):
        instance = self.get_object(pk)
        data= request.data.copy()
        facturas_propietario = instance.factura_propietario_set.all()
        if facturas_propietario.exists():
            data.pop('nombre_inmueble', None)
            data.pop('balanceinicial', None)

        serializer = self.get_serializer(instance, data = data, partial = True, context ={'request':request})
        if serializer.is_valid():
            serializer.save()
            serializer = self.get_serializer( Inmueble.objects.filter(condominio = request.user.condominio), many = True )
            request.user.condominio.refresh_from_db()
            context = {
                'condominio_activo': request.user.condominio.activo,
                'data':serializer.data
            }
            return Response(context, status=status.HTTP_200_OK)
        else:
            print serializer.errors
        return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST) 

class JuntaCondominioViewSet(InmuebleViewSet):
    serializer_class = JuntaCondominioSerializer
    permission_classes = (IsAuthenticated, IsRelatedToCondominio, UsuarioAprobado, IsCondominioOrReadonly,)

    def partial_update(self, request, pk = None):

        instance = self.get_object(pk)
        data= request.data.copy()
        facturas_propietario = instance.factura_propietario_set.all()
        if facturas_propietario.exists():
            data.pop('nombre_inmueble', None)
            data.pop('balanceinicial', None)

        serializer = self.get_serializer(instance, data = data, partial = True, context ={'request':request})
        if serializer.is_valid():
            serializer.save()
            request.user.condominio.refresh_from_db()
            serializer = InmuebleSerializer(request.user.condominio.inmueble_set.filter(junta_de_condominio=True) , many = True )
            context = {
                'condominio_activo': request.user.condominio.activo,
                'data':serializer.data
            }
            return Response(context, status=status.HTTP_200_OK)
        else:
            print serializer.errors
        return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST) 


class PaymentMethodView(generics.ListAPIView):
    queryset = Payment_Method_Detail.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = PaymentMethodDetailSerializer
    def get_queryset(self):
        pais= self.request.user.condominio.pais
        queryset= self.queryset.filter(pais=pais)
        return queryset

class PaisesListView(generics.ListAPIView):
    queryset = Paises.objects.all()
    serializer_class = PaisesSerializer
    permission_classes = (AllowAny,)
    filter_backends = ( DjangoFilterBackend, )
    filter_class = Paises_Filter

class CarteleraViewSet(viewsets.ModelViewSet):
    queryset = Cartelera.objects.all()
    serializer_class = CarteleraSerializer

    def get_object(self, pk):
        try:
            return Cartelera.objects.get(pk=pk)
        except Cartelera.DoesNotExist:
            raise Http404

    def create(self, request):
        data = request.data.copy()
        serializer = self.get_serializer(data = data)
        if serializer.is_valid():
            serializer.save(condominio= request.user.condominio)
            serializer = self.get_serializer(Cartelera.objects.filter(condominio = request.user.condominio), many= True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            print serializer.errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def destroy(self, request, pk= None):
        self.get_object(pk).delete()
        serializer = self.get_serializer(Cartelera.objects.filter(condominio = request.user.condominio), many= True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class bancoAfiliadoViewSet(viewsets.ModelViewSet):
    queryset = Affiliate_Banc_Account.objects.all()
    serializer_class = Affiliate_Banc_AccountSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field= 'pk'

    def get_queryset(self):
        return self.queryset.filter(affiliate=self.request.user.affiliate)

    def get_object(self, pk= None):
        try:
            obj = Affiliate_Banc_Account.objects.get(pk=pk)
            self.check_object_permissions(self.request, obj)
            return obj
        except Affiliate_Banc_Account.DoesNotExist:
            raise Http404

    def partial_update(self, request, pk = None):
        instance = self.get_object(pk)
        serializer = self.get_serializer(instance ,data = request.data, partial = True)
        if serializer.is_valid():
            serializer.save()
            serializer = self.get_serializer(Affiliate_Banc_Account.objects.filter(affiliate = request.user.affiliate), many= True)
            return Response(serializer.data, status=status.HTTP_200_OK) 
        else:
            print serializer.errors
        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)


    def destroy(self, request, pk= None):
        self.get_object(pk).delete()
        serializer = self.get_serializer(Affiliate_Banc_Account.objects.filter(affiliate = request.user.affiliate), many= True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def list(self, request):
        queryset = self.get_queryset()
        accounts_serializer = Affiliate_Banc_AccountSerializer(queryset, many=True)
        country_list= set([pais.pk for pais in Paises.objects.all()])
        context= {
            'accounts' : accounts_serializer.data,
            'countries': country_list
        }
        return Response(context)

    def create(self, request):
        data = request.data.copy()
        data['pais']= 'Venezuela'
        serializer = self.get_serializer(data=data, context={'request':request})
        if serializer.is_valid():
            serializer.save(affiliate= request.user.affiliate)
            serializer = self.get_serializer(Affiliate_Banc_Account.objects.filter(affiliate = request.user.affiliate), many= True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            print serializer.errors
        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)



class userViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,IsOwner,)
    filter_backends = ( DjangoFilterBackend, )
    filter_class = UsuarioFilter

    def get_object(self, email= None):
        try:
            obj = User.objects.get(email=email)
            self.check_object_permissions(self.request, obj)
            return obj
        except User.DoesNotExist:
            raise Http404

    def get_queryset(self):
        return self.queryset.filter(id=self.request.user.id)

class FaqView(generics.ListAPIView):
    queryset = Faq.objects.all()
    serializer_class = FaqSerializer

class customChangePwdView(PasswordChangeView):
    serializer_class = customPasswordChangeSerializer


class resumen_condominioApiView(APIView):
    permission_classes = (IsAuthenticated,)
    categories_queryset = InmuebleCategory.objects.all()
    
    def get_categories(self):
        user_type = get_user_type(self.request)
        if user_type =='condominio':
            quer_set= self.categories_queryset.filter(condominio = self.request.user.condominio)
        elif user_type =='inquilino':
            inmueble_id= self.request.session.get('inmueble')
            condominio = Inmueble.objects.get(pk =inmueble_id).condominio
            quer_set= self.categories_queryset.filter(condominio= condominio)
        serializer= InmuebleCategorySerializer(quer_set, many= True)
        return serializer.data


    def get_context(self, month):
        self.condominio=self.request.user.condominio
        #what is total to be collected
        facturas_condominio = Factura_Condominio.objects.filter(condominio = self.condominio)
        facturas_propietarios = Factura_Propietario.objects.filter(condominio = self.condominio)
        active_month = Factura_Condominio.objects.get_latest_editable_tuple(self.condominio)
        ingresos_condominio =Ingreso_Condominio.objects.filter(mes__range=(active_month[0], active_month[1]),  condominio = self.condominio, aprobado=True)
        pagos_sum = ingresos_condominio.aggregate(total_payed= Sum('monto'))['total_payed'] or 0
        cobranzas_condo_sum=0
        egresos_totales_periodo = self.condominio.egreso_condominio_set.filter(mes__range=(active_month[0], active_month[1])).aggregate(total_monto= Sum('monto'))['total_monto'] or 0
        
        if facturas_condominio.exists():
            latest_factura = facturas_condominio.filter(tipo_de_factura='service_fee').latest('created')
            month_range = month_range_dt(latest_factura.mes)
            facturas_propietarios = facturas_propietarios.filter(mes__range=(month_range[0],month_range[1]))
            total_owed =facturas_propietarios.aggregate(total_owed= Sum('monto'))['total_owed']
            inmuebles = self.condominio.inmueble_set.all()
            inmueble_summary = []
            for inmueble in inmuebles:
                cobranzas = inmueble.cobranza_condominio_set.filter(editable= True)

                cobranzas_sum = get_total_cobranzas(cobranzas, inmueble,egresos_totales_periodo)

                #deuda_actual = inmueble.factura_propietario_set.all().latest('created').deuda_nueva
                pagos_sum_inmueble = ingresos_condominio.filter(inmueble = inmueble).aggregate(total_monto= Sum('monto'))['total_monto'] or 0
                inmueble_data = {
                    'nombre_inmueble':inmueble.nombre_inmueble,
                    'deuda_actual':inmueble.deuda_actual,
                    'pagos_sum':pagos_sum_inmueble,
                    'cobranzas_sum':cobranzas_sum,
                    'razon_social':inmueble.inquilino.user.get_full_name()
                }
                cobranzas_condo_sum+=cobranzas_sum
                serializer = ResumenCondominioSerializer(inmueble_data, context= {'inmueble':inmueble})
                inmueble_summary.append(serializer.data)
        else:
            inmuebles = self.condominio.inmueble_set.all()
            total_owed=inmuebles.aggregate(total_owed= Sum('balanceinicial'))['total_owed']
            inmueble_summary = []
            for inmueble in inmuebles:

                cobranzas = inmueble.cobranza_condominio_set.filter(editable= True)
                
                cobranzas_sum = get_total_cobranzas(cobranzas, inmueble,egresos_totales_periodo)

                pagos_sum_inmueble = ingresos_condominio.filter(inmueble = inmueble).aggregate(total_monto= Sum('monto'))['total_monto'] or 0
                inmueble_data = {
                    'nombre_inmueble':inmueble.nombre_inmueble,
                    'pagos_sum':pagos_sum_inmueble,
                    'deuda_actual':inmueble.balanceinicial,
                    'cobranzas_sum':cobranzas_sum,
                    'razon_social':inmueble.inquilino.user.get_full_name()
                }
                cobranzas_condo_sum+=cobranzas_sum
                serializer = ResumenCondominioSerializer(inmueble_data, context= {'inmueble':inmueble})
                inmueble_summary.append(serializer.data)

        categories = InmuebleCategory.objects.filter(condominio =self.condominio)
        categories_serializer = InmuebleCategorySerializer(categories,many= True)
        cuentas = BancosSerializer(self.condominio.bancos_set.all(), many= True).data

        context={
            'total_owed':total_owed,
            'inmueble_summary':inmueble_summary,
            'pagos_recibidos':pagos_sum,
            'active_month':active_month[0],
            'categories':categories_serializer.data,
            'cobranzas_condo_sum':cobranzas_condo_sum,
            'egresos_totales_periodo':egresos_totales_periodo,
            'cuentas':cuentas

        }
        return context
        
    def get(self, request):
        month = request.GET.get('month_created', None)
        context= self.get_context(month)
        return Response(context, status=status.HTTP_200_OK)

    def post(self, request):
        request.session['inmueble'] = request.data['inmueble']
        return Response('OK', status=status.HTTP_200_OK)

class SetSesionView(APIView):
    def post(self, request):
        request.session['inmueble'] = request.data['inmueble']
        return Response('OK', status=status.HTTP_200_OK)

class UserProfileView(APIView):
    queryset = User.objects.all()

    def patch(self, request):
        data = request.data.copy()
        try:
            data['logo'] = None if data['logo'] == 'null' else data['logo']
        except:
            pass
        user_type = get_user_type(request)
        if user_type =='condominio':
            serializer = CondominioSerializer(request.user.condominio, data = data, partial= True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                print serializer.errors
            
        elif user_type =='affiliate':
            serializer = AffiliateSerializer(request.user.affiliate, data = data, partial= True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                print serializer.errors

        elif user_type =='inquilino':
            data['rif'] = request.user.inquilino.rif if request.user.inquilino.rif else None
            serializer = InquilinoSerializer(request.user.inquilino, data = data, partial= True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                print serializer.errors
        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)

class MessagesApiView(APIView):
    queryset = Messages.objects.all()
    permission_classes = (IsAuthenticated,)
    second_serializer = contextSerializer
    serializer_class = MessagesSerializer
    def get_range_info(self, data):
        response= {}
        if self.queryset.exists():
            earliest= self.queryset.earliest('created').created
            latest= self.queryset.latest('created').created
            minDate= earliest.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
            maxDate= latest.replace(day= last_day_of_month(latest), hour= 23, minute = 59, second=59, microsecond=999999 )
            response['minDate'] = minDate
            response['maxDate'] = maxDate
            response['data'] = data.filter(created__range=(minDate, maxDate))
        else:
            response['minDate'] = self.request.user.date_joined.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
            response['maxDate'] = self.request.user.date_joined.replace(day= last_day_of_month(self.request.user.date_joined), hour= 23, minute = 59, second=59, microsecond=999999)
            response['data'] = []
        return response

    def get_inmuebles(self):
        inmuebles = Inmueble.objects.filter(condominio = self.request.user.condominio)
        serializer = InmuebleSerializer(inmuebles, many= True)
        return serializer.data

    def get(self, request, format=None):
        data = {}
        message_info= self.get_range_info(self.queryset)
        serialized_messages = self.serializer_class(message_info['data'], many= True, context={'request': request})
        inmuebles = self.get_inmuebles()
        context = {
            'maxDate':message_info['maxDate'],
            'minDate':message_info['minDate'],
            'active_month' :message_info['active_month']
        }
        serialized_ingreso_context = self.second_serializer(context)
        data = {
            'data': serialized_messages.data,
            'context' : serialized_ingreso_context.data,
            'inmuebles': inmuebles
        }
        return Response(data, status = status.HTTP_200_OK )



class ResumenPropietarioView(APIView):
    #permissions for inquilino must be set
    permission_classes = (IsAuthenticated, InquilinoHasChosenInmueble,)

    def get_context_data(self):
        inmueble = Inmueble.objects.get(pk= self.request.session.get('inmueble'))
        minDate = inmueble.created
        facturas_propietarios = inmueble.factura_propietario_set.all()
        if facturas_propietarios.exists():
            maxDate= facturas_propietarios.latest('mes').mes
        else:
            maxDate = minDate.replace(day= last_day_of_month(minDate), hour= 23, minute = 59, second=59, microsecond=999999 )
        
        param = self.request.GET.get('month_created', None)   
        if param:
            month = dateutil.parser.parse(param)
        else:
            month = maxDate
        date_range =month_range_dt(month)
        facturas_propietarios = facturas_propietarios.filter(mes__range=(date_range[0], date_range[1]))
        serializer = Factura_PropietarioSerializer(facturas_propietarios, many= True)
        context = {
            'maxDate' : maxDate,
            'minDate':minDate,
            'results': serializer.data
        }
        return context

    def get(self, request):
        context=self.get_context_data()
        return Response(context, status = status.HTTP_200_OK ) 

class CondoHomeView(GenericAPIView,APIView):
    permission_classes = (IsAuthenticated,IsCondominio)
    queryset = Blog.objects.all().order_by('-created')
    pagination_class = BlogPagination


    def get_circulante(self):
        condominio =self.request.user.condominio
        facturas_condo = Factura_Condominio.objects.filter(condominio= condominio)
        period = Factura_Condominio.objects.get_latest_editable_tuple(condominio)

        egresos_totales_periodo = self.condominio.egreso_condominio_set.filter(mes__range=(period[0], period[1])).aggregate(total_monto= Sum('monto'))['total_monto'] or 0
        inmuebles = condominio.inmueble_set.all()
        cobranzas_sum = 0
        for inmueble in inmuebles:
            cobranzas = inmueble.cobranza_condominio_set.filter(editable= True)
            cobranzas_sum += get_total_cobranzas(cobranzas, inmueble,egresos_totales_periodo)

        #inmueble = Inmueble.objects.get(pk =self.request.session.get('inmueble'))
        
        if facturas_condo.exists():
            latest_factura = condominio.factura_condominio_set.filter(tipo_de_factura='service_fee').latest('created')
            month_range=month_range_dt(latest_factura.mes)
            facturas_propietarios = Factura_Propietario.objects.filter(condominio = condominio, mes__range=(month_range[0], month_range[1]))
            sum_balance = facturas_propietarios.aggregate(total_deuda= Sum('monto'))['total_deuda']
        else:
            sum_balance = inmuebles.aggregate(total_deuda= Sum('balanceinicial'))['total_deuda'] or 0

        payments = Ingreso_Condominio.objects.filter(condominio = condominio, aprobado =True,mes__range=(period[0],period[1],))
        
        if payments.exists():
            sum_payments = payments.aggregate(total_pagos= Sum('monto'))['total_pagos']
        else:
            sum_payments =0

        circulante = sum_payments+sum_balance-cobranzas_sum-egresos_totales_periodo
        return circulante

    def get_propietarios_morosos(self):
        try:
            propietarios_morosos = Inmueble.objects.filter(condominio=self.condominio).filter(deuda_actual__lt=0).count()
            return propietarios_morosos
        except:
            return 0

    def get_pagos_por_evaluar(self):
        try:
            pagos_por_evaluar = Ingreso_Condominio.objects.filter(aprobado=None).count()
            return pagos_por_evaluar
        except:
            return 0

    def get_facturas_pendientes(self):
        try:
            facturas_pendientes = Factura_Condominio.objects.filter(pagado=False, demo_mode=False).count()
            return facturas_pendientes
        except:
            return 0

    def get_encuestas_vigentes(self):
        try:
            now = timezone.now()
            encuestas_vigentes = Poll.objects.filter(end__gt=now, start__lte =now).count()
            return encuestas_vigentes
        except:
            return 0

    def get_blog_data(self):
        month_unicode = self.request.GET.get('month_created' , None)
        blog = self.queryset.filter(condominio =self.condominio)

        if blog.exists():
            min_date_instance = blog.earliest('created')
            minDate = min_date_instance.created.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
        else:
            minDate = timezone.now().replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)

        if month_unicode:
            month= dateutil.parser.parse(month_unicode)
            begin, end = month_range_dt(month)[0], month_range_dt(month)[1]
            blog = blog.filter(created__range=(begin, end))
        else:
            month = timezone.now()
            begin, end = month_range_dt(month)[0], month_range_dt(month)[1]
            blog = blog.filter(created__range=(begin, end))

        dict_obj = {}
        dict_obj['minDate'] = minDate
        dict_obj['blog'] = blog
        return dict_obj

    def get_context(self):
        blog_data = self.get_blog_data()
        context = {
            'propietarios_morosos': self.get_propietarios_morosos(),
            'pagos_por_evaluar':self.get_pagos_por_evaluar(),
            'facturas_pendientes':self.get_facturas_pendientes(),
            'encuestas_vigentes':self.get_encuestas_vigentes(),
            'blog': blog_data['blog'],
            'minDate':blog_data['minDate'],
            'deuda' :self.get_circulante()
        }
        return context


    def get(self, request):
        #########
        self.condominio= self.get_condominio()
        #########
        context = self.get_context()
        page = self.paginate_queryset(context.pop('blog'))
        context['blog'] =page
        user_type = request.user.get_user_type()
        if user_type=='condominio':
            condominio_activator(request.user.condominio)
        return self.get_paginated_response(context)

    def get_condominio(self):
        user_type = get_user_type(self.request)
        self.user_type = user_type
        if user_type =='condominio':
            self.condominio = self.request.user.condominio
            return self.condominio
        elif user_type =='inquilino':
            inmueble_id= self.request.session.get('inmueble')
            self.condominio =  Inmueble.objects.get(pk =inmueble_id).condominio
            return self.condominio

    def post(self, request):
        data= request.data.copy()
        data['condominio'] = self.get_condominio()
        data['publisher'] = request.user.id
        serializer= BlogSerializer(data= data)
        if serializer.is_valid():
            serializer.save()
            blog_queryset = Blog.objects.filter(condominio = self.condominio).order_by('-created')
            context = self.get_context()
            page = self.paginate_queryset(context.pop('blog'))
            context['blog'] =page
            return self.get_paginated_response(context)
            #serializer = BlogSerializer(blog_queryset, many= True)
            #return Response(serializer.data, status = status.HTTP_200_OK )
        else:
            print serializer.errors
            return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST )




class IngresoCondoModalView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        bancos = Banco_PaisSerializer(Banco_Pais.objects.filter(pais =request.user.condominio.pais), many= True).data
        cuentas = BancosSerializer(Bancos.objects.filter(condominio =request.user.condominio), many= True).data
        inmuebles = InmuebleSerializer(Inmueble.objects.filter(condominio =request.user.condominio), many= True).data
        context={
            'bancos':bancos,
            'inmuebles':inmuebles,
            'cuentas':cuentas
        }
        return Response(context, status = status.HTTP_200_OK )

class EgresosContextModal(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        tipos_egresos = tiposEgresosSerializer(Tipos_Egresos.objects.filter(pais =request.user.condominio.pais), many= True).data
        cuentas = BancosSerializer(Bancos.objects.filter(condominio =request.user.condominio), many= True).data
        #inmuebles = InmuebleSerializer(Inmueble.objects.filter(condominio =request.user.condominio), many= True).data
        
        context={
            'tipos_egresos':tipos_egresos,
            'cuentas':cuentas
        }
        return Response(context, status = status.HTTP_200_OK )

class IngresoCondominioApiView(APIView):
    queryset = Ingreso_Condominio.objects.all().order_by('-mes')
    permission_classes = (IsAuthenticated,)
    filter_backends = ( DjangoFilterBackend,)
    facturas_condo = Factura_Condominio.objects.all()
    second_serializer = contextSerializer
    serializer_class = Ingreso_CondominioSerializer
    filter_class = IngresosFilter
    
    def get_latest(self, active_month):
        start= active_month.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
        end =active_month
        queryset= self.get_queryset().filter(mes__range=(start, end))
        return queryset

    def get_queryset(self):
        user_type = self.request.user.get_user_type()
        self.user_type = user_type
        if user_type =='condominio':
            self.condominio = self.request.user.condominio
            return self.queryset.filter(condominio = self.condominio)
        elif user_type =='inquilino':
            inmueble_id= self.request.session.get('inmueble')
            self.condominio =  Inmueble.objects.get(pk =inmueble_id).condominio
            return self.queryset.filter(condominio= self.condominio )



    def get(self, request, format=None):
        '''
        gets context, data range, and editable period
        '''
        try:
            condominio = request.user.condominio
        except:
            condominio = Inmueble.objects.get(pk=request.session.get('inmueble')).condominio
        may_get_pdf = Factura_Condominio.objects.filter(condominio = condominio).exists()
        data_range = Factura_Condominio.objects.get_data_range(condominio)
        latest_editable = Factura_Condominio.objects.get_latest_editable_tuple(condominio)
        minDate = data_range[0]
        maxDate = latest_editable[1]
        latest = self.queryset.filter(mes__range=(latest_editable[0], latest_editable[1],))
        context = {
            'maxDate':maxDate,
            'minDate':minDate,
            'active_month': maxDate
        }
        serialized_ingreso_context = self.second_serializer(context)
        serialized_ingresos = self.serializer_class(latest, many= True)
        data = {
            'data': serialized_ingresos.data,
            'context' : serialized_ingreso_context.data,
            'may_get_pdf':may_get_pdf
        }
        return Response(data, status = status.HTTP_200_OK )

class Egresos_CondominioApiView(IngresoCondominioApiView):
    queryset = Egreso_Condominio.objects.all().order_by('-fecha_facturacion')
    permission_classes = (IsAuthenticated,)
    filter_backends = ( DjangoFilterBackend,)
    filter_class = EgresoFilter
    serializer_class = Egreso_CondominioSerializer

class AffiliateHomeView(APIView):
    permission_classes = (IsOwnerOrReadOnly,)
    def get_object(self):
        try:
            obj =Affiliate.objects.get(user = self.request.user)
            self.check_object_permissions(self.request, obj)
            return AffiliateSerializer(obj).data
        except Affiliate.DoesNotExist:
            raise Http404

    def get(self, request, format = None):
        condominio_serializer = CondominidoAfilliateSerialzier(request.user.affiliate.condominios.all(), many= True)
        context = {
            'affiliate_data': self.get_object(),
            'condominios' : condominio_serializer.data
            #'register_bank' : self.get_should_register_bank()
        }
        return Response(context, status=status.HTTP_200_OK)


class AffiliateViewSet(viewsets.ModelViewSet):
    queryset = Affiliate.objects.all()
    permission_classes = (
        IsOwnerOrReadOnly,
    )
    serializer_class = AffiliateSerializer


class EgresosViewSet(viewsets.ModelViewSet):
    queryset = Egreso_Condominio.objects.all()
    permission_classes = (IsAuthenticated, IsCondominioOrReadonly,AbiertoOrReadOnly,IsOwnerOrReadOnly,)
    filter_backends = ( SearchFilter,DjangoFilterBackend,)
    search_fields = ['tipo_egreso__nombre', 'nro_factura']
    filter_class = EgresoFilter
    serializer_class = Egreso_CondominioSerializer

    def partial_update(self, request, pk= None):
        data = request.data.copy()
        instance = self.get_object(pk)
        serializer = self.get_serializer( instance,data = data, partial= True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            queryset = Egreso_Condominio.objects.get_month_query(instance.mes)
            serializer = self.get_serializer( queryset , many= True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            print serializer.errors
        return Response(serializer.errors, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    def get_queryset(self):
        user_type = get_user_type(self.request)
        self.user_type = user_type
        if user_type =='condominio':
            self.condominio = self.request.user.condominio
            return self.queryset.filter(condominio = self.condominio)
        elif user_type =='inquilino':
            inmueble_id= self.request.session.get('inmueble')
            self.condominio =  Inmueble.objects.get(pk =inmueble_id).condominio
            return self.queryset.filter(condominio= self.condominio )

    def get_month(self):
        queryset = self.get_queryset().filter( cerrado =True )
        if queryset.exists():
            month= queryset.latest('mes').mes+relativedelta(months=1)
        else:
            month = self.request.user.date_joined.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
        return month


    def create(self, request):
        data= request.data.copy()
        data['mes'] = self.get_month()
        serializer = self.get_serializer(data= data, context={'request':request})
        if serializer.is_valid():
            serializer.save(condominio = request.user.condominio)
            queryset = Egreso_Condominio.objects.get_month_query(serializer.validated_data.get('mes')).filter(condominio = request.user.condominio)
            serializer = self.get_serializer(queryset, many = True)
            return Response(serializer.data, status = status.HTTP_200_OK)
        else:
            print serializer.errors
        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)

    def get_object(self, pk):
        try:
            obj =Egreso_Condominio.objects.get(pk = pk)
            self.check_object_permissions(self.request, obj)
            return obj
        except Egreso_Condominio.DoesNotExist:
            raise Http404

    def destroy(self, request, pk= None):
        instance = self.get_object(pk)
        instance.delete()
        serializer = self.get_serializer(Egreso_Condominio.objects.filter(condominio = request.user.condominio), many= True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class tiposEgresosViewSet(viewsets.ModelViewSet):
    queryset = Tipos_Egresos.objects.all()
    serializer_class = tiposEgresosSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = ( SearchFilter,DjangoFilterBackend,)

class Pago_InquilinoView(APIView):
    queryset = Ingreso_Condominio.objects.all()
    serializer_class= Ingreso_CondominioSerializer
    permission_classes = (IsAuthenticated,)

    def get_inmueble(self):
        try:
            obj =Inmueble.objects.get(pk = self.request.session.get('inmueble'))
            #self.check_object_permissions(self.request, obj)
            return obj
        except Inmueble.DoesNotExist:
            raise Http404

    def get_queryset(self):
        return self.queryset.filter(inmueble = self.request.session.get('inmueble'))
    
    def get_range(self, mes= None):
        queryset= self.get_queryset()
        if queryset.exists():
            minDate=queryset.earliest('mes').mes.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
            maxDate=queryset.latest('mes').mes
            maxDate=maxDate.replace(day= last_day_of_month(maxDate), hour= 23, minute = 59, second=59, microsecond=999999 )
        else:
            minDate= self.request.user.date_joined.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
            maxDate=minDate.replace(day= last_day_of_month(minDate), hour= 23, minute = 59, second=59, microsecond=999999 )
        date_range={
            'maxDate':maxDate,
            'minDate':minDate
        }
        return date_range

    def get(self, request):
        queryset = self.get_queryset()
        month = self.request.GET.get('month_created', None)
        if month:
            date_range = month_range_dt(dateutil.parser.parse(month))
            queryset= queryset.filter(created__range = (date_range[0], date_range[1]))
            serializer = self.serializer_class(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)


        inmueble = self.get_inmueble()
        data_range = self.get_range()#total range of the dataset
        mes = Factura_Condominio.objects.get_latest_editable_tuple(inmueble.condominio)[0]
        date_range = month_range_dt(mes)#range for the current month
        queryset=queryset.filter(created__range = (date_range[0], date_range[1]))
        serializer = self.serializer_class(queryset, many=True)
        data_range['active_month'] = mes
        context_serializer = contextSerializer(data_range)
        context = {
            'pagos' :serializer.data,
            'payment_param':context_serializer.data
        }
        return Response(context, status=status.HTTP_200_OK)

    def get_month(self):
        inmueble_id = self.request.session.get('inmueble')
        condominio =Inmueble.objects.get(pk =inmueble_id).condominio
        factura_condominio = Factura_Condominio.objects.filter( condominio =condominio )
        if factura_condominio.exists():
            month= factura_condominio.latest('mes').mes+relativedelta(months=1)
        else:
            month = condominio.user.date_joined.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
        return month

    def post(self, request):
        data = request.data.copy()
        #payment_type = data['payment_type']
        data['fecha_facturacion'] = timezone.now()
        ##################
        #data['tipo_de_ingreso'] ='pp'
        #################
        data['mes'] = self.get_month()
        inmueble = Inmueble.objects.get(pk = request.session.get('inmueble'))
        condominio = inmueble.condominio
        data['inmueble'] = inmueble.pk
        serializer = Ingreso_CondominioSerializer(data= data, context={'request':request, 'condominio':condominio})
        if serializer.is_valid():
            serializer.save()
            message_context = {
                'condominio': condominio.user.first_name.title() + ' '+condominio.user.last_name.title(),
                'inquilino': inmueble.inquilino.user.first_name.title() +' '+inmueble.inquilino.user.last_name.title(),
                'monto' : intcomma( serializer.validated_data.get('monto') , 2),
                'currency': condominio.pais.moneda,
                'site_name':get_current_site(request).name
            }
            subject_context= {
                'inquilino':inmueble.inquilino.user.first_name +' '+inmueble.inquilino.user.last_name
            }
            subject = loader.render_to_string('account/email/condominio_new_payment_subject.txt', subject_context)
            message= loader.render_to_string('account/email/condominio_new_payment_message.txt', message_context)
            send_email.delay(subject, message, settings.DEFAULT_FROM_EMAIL, [condominio.user.email])
            return Response(serializer.data, status=status.HTTP_200_OK) 
        else:
            print serializer.errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 

class IngresosViewSet(viewsets.ModelViewSet):
    queryset = Ingreso_Condominio.objects.all().order_by('-fecha_facturacion')
    serializer_class = Ingreso_CondominioSerializer
    permission_classes = (IsAuthenticated, IsCondominioOrReadonly,AbiertoOrReadOnly,IsOwnerOrReadOnly,)
    filter_backends = ( SearchFilter,DjangoFilterBackend,)
    search_fields = ['propietario', 'pagador', 'inmueble__nombre_inmueble', 'arrendatario', 'banco_dep', 'monto', 'created']
    filter_class = IngresosFilter

    def get_queryset(self):
        user_type = get_user_type(self.request)
        self.user_type = user_type
        if user_type =='condominio':
            self.condominio = self.request.user.condominio
            return self.queryset.filter(condominio = self.condominio)
        elif user_type =='inquilino':
            inmueble_id= self.request.session.get('inmueble')
            self.condominio =  Inmueble.objects.get(pk =inmueble_id).condominio
            return self.queryset.filter(condominio= self.condominio )

    def get_object(self, pk):
        try:
            obj =Ingreso_Condominio.objects.get(pk = pk)
            self.check_object_permissions(self.request, obj)
            return obj
        except Ingreso_Condominio.DoesNotExist:
            raise Http404


##############################
    def get_month(self):
        queryset = self.get_queryset().filter( cerrado =True )
        if queryset.exists():
            month= queryset.latest('mes').mes+relativedelta(months=1)
        else:
            month = self.request.user.date_joined.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
        return month
#################################

    def partial_update(self, request, pk= None):
        data = request.data.copy()
        instance = self.get_object(pk)
        serializer = self.get_serializer( instance,data = data, partial= True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            queryset = Ingreso_Condominio.objects.get_month_query(instance.mes)
            serializer = self.get_serializer( queryset , many= True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            print serializer.errors
        return Response(serializer.errors, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    def create(self, request):
        data = request.data.copy()
        data['mes'] = Factura_Condominio.objects.get_latest_editable_tuple(request.user.condominio)[0]
        serializer = self.get_serializer( data = data, context= {'request':request})
        if serializer.is_valid():
            condominio = request.user.condominio
            serializer.save(condominio = condominio, posted_by=request.user)
            queryset = Ingreso_Condominio.objects.get_month_query(serializer.validated_data.get('mes')).filter(condominio = request.user.condominio)
            serializer = self.get_serializer(queryset, many= True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            print serializer.errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk= None):
        instance = self.get_object(pk)
        if instance.posted_by == request.user:
            instance.delete()

        data_range = month_range_dt(Factura_Condominio.objects.get_latest_editable_tuple(request.user.condominio)[0])
        serializer = self.get_serializer(Ingreso_Condominio.objects.filter(condominio = request.user.condominio, mes__range=(data_range[0], data_range[1])), many= True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class bancosView(APIView):
    queryset = Bancos.objects.all()
    serializer_class = BancosSerializer
    permission_classes = (IsAuthenticated,IsBancoOwnerOrReadonly,)

    def get_queryset(self):
        user_type = get_user_type(self.request)
        if user_type =='condominio':
            self.condominio=self.request.user.condominio
            return self.queryset.filter(condominio = self.condominio)
        elif user_type =='inquilino':
            inmueble_id= self.request.session.get('inmueble')
            self.condominio = Inmueble.objects.get(pk =inmueble_id).condominio
            return self.queryset.filter(condominio= self.condominio)

    def get_bancos_pais(self):
        return Banco_Pais.objects.filter(pais = self.request.user.condominio.pais)

    def get(self, request):
        bancos_serializer= BancosSerializer(self.get_queryset(),many= True)
        latest_ediable_period=Factura_Condominio.objects.get_latest_editable_tuple(self.condominio)
        bancos_pais_serializer =Banco_PaisSerializer(self.get_bancos_pais(), many= True)
        context = {
            'bancos':bancos_serializer.data,
            'fecha_cuenta': latest_ediable_period[0],
            'bancos_pais': bancos_pais_serializer.data
        }
        return Response(context, status=status.HTTP_200_OK)

class bancosViewSet(viewsets.ModelViewSet):
    queryset = Bancos.objects.all()
    serializer_class = BancosSerializer
    permission_classes = (IsAuthenticated,IsBancoOwnerOrReadonly,)

    def get_queryset(self):
        user_type = get_user_type(self.request)
        if user_type =='condominio':
            return self.queryset.filter(condominio = self.request.user.condominio)
        elif user_type =='inquilino':
            inmueble_id= self.request.session.get('inmueble')
            condominio = Inmueble.objects.get(pk =inmueble_id).condominio
            return self.queryset.filter(condominio= condominio)

    def get_object(self, pk):
        try:
            return Bancos.objects.get(pk=pk)
        except Bancos.DoesNotExist:
            raise Http404

    def destroy(self, request, pk= None):
        self.get_object(pk).delete()
        serializer = self.get_serializer(Bancos.objects.filter(condominio = request.user.condominio), many= True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        data = request.data.copy()
        latest_ediable_period=Factura_Condominio.objects.get_latest_editable_tuple(request.user.condominio)
        data['fecha_balance_inicial'] = latest_ediable_period[0]
        serializer = self.get_serializer(data = data)
        if serializer.is_valid():
            serializer.save(condominio= request.user.condominio)
            serializer = self.get_serializer(Bancos.objects.filter(condominio = request.user.condominio), many= True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    def partial_update(self, request, pk= None):
        data = request.data.copy()
        serializer = self.get_serializer( self.get_object(pk),data = data, partial= True)
        if serializer.is_valid():
            serializer.save(condominio= request.user.condominio)
            serializer = self.get_serializer(Bancos.objects.filter(condominio = request.user.condominio), many= True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            print serializer.errors
        return Response(serializer.errors, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

class paginasAmarillasViewSet(viewsets.ModelViewSet):
    queryset = Paginas_Amarillas.objects.all()
    serializer_class = PaginasAmarillasSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user_type = get_user_type(self.request)
        if user_type =='condominio':
            return self.queryset.filter(condominio = self.request.user.condominio)
        elif user_type =='inquilino':
            inmueble_id= self.request.session.get('inmueble')
            condominio = Inmueble.objects.get(pk =inmueble_id).condominio
            return self.queryset.filter(condominio= condominio)

    def get_object(self, pk):
        try:
            return Paginas_Amarillas.objects.get(pk=pk)
        except Paginas_Amarillas.DoesNotExist:
            raise Http404

    def destroy(self, request, pk= None):
        self.get_object(pk).delete()
        serializer = self.get_serializer(Paginas_Amarillas.objects.filter(condominio = request.user.condominio), many= True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, pk= None):
        data = request.data.copy()
        serializer = self.get_serializer( self.get_object(pk),data = data, partial= True)
        if serializer.is_valid():
            serializer.save(condominio= request.user.condominio)
            serializer = self.get_serializer(Paginas_Amarillas.objects.filter(condominio = request.user.condominio), many= True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
    
    def create(self, request):
        serializer = self.get_serializer( data = request.data)
        if serializer.is_valid():
            serializer.save(condominio = request.user.condominio)
            serializer = self.get_serializer(Paginas_Amarillas.objects.filter(condominio = request.user.condominio), many= True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            print serializer.errors
        return Response('error', status=status.HTTP_400_BAD_REQUEST)

# class egresos_detalladosApiView(APIView):

#     def get_context(self):
#         self.condominio = self.request.user.condominio
#         cuentas = BancosSerializer(self.condominio.bancos_set.all(), many= True).data
#         active_month = Factura_Condominio.objects.get_latest_editable_tuple(self.condominio)
#         inmuebles = EgresoDetalladoSerializer(self.condominio.inmueble_set.all(), many= True).data
#         context= {
#             'cuentas':cuentas,
#             'active_month':active_month[0],
#             'inmuebles':inmuebles
#         }
#         return context

#     def get(self, request):
#         context= self.get_context()
#         return Response(context, status=status.HTTP_200_OK)

#     def post(self, request):
#         #context= self.get_context()
#         print request.data
#         serializers = EgresoDetalladoSerializer(data = request.data, many = True)
#         if serializer.is_valid():
#             print serializer.validated_data
#         else:
#             print serializer.errors
#         return Response('ok', status=status.HTTP_200_OK)

class verificarRif(APIView):
    def get(self, request, rif=None, format = None):
        if rif:
            condominio = Condominio.objects.filter(rif = rif)
            inquilino = Inquilino.objects.filter(rif = rif)
            afiliado = Affiliate.objects.filter(rif = rif)
            if inquilino.exists() or condominio.exists() or afiliado.exists():
                return Response(_('fiscal number already in use'), status = status.HTTP_400_BAD_REQUEST )
            else:
                return Response(_('fiscal number available'), status=status.HTTP_200_OK)


class verificarCorreo(APIView):
    def get(self, request, email,format = None):
        try:
            user = User.objects.get(email = email)
            return Response(_('email already in use'), status = status.HTTP_400_BAD_REQUEST )
        except:
            return Response(_('email available'), status=status.HTTP_200_OK)
        
class BorrarInmuebles(APIView):
    queryset = Inmueble.objects.all()
    permission_classes = (IsAuthenticated,UsuarioAprobado,)
    def get_queryset(self):
        return self.queryset.filter(condominio = self.request.user.condominio)

    def post(self, request,format = None):
        inmuebles = self.get_queryset()#condos inmuebles
        data= [int(item) for item in set(list(request.data))]
        if inmuebles.exists():
            inmuebles_ids = [inmueble.pk for inmueble in inmuebles]#condo inmuble ids
            erase_ids = data#ids of inmuebles to be deleted
            if not set(erase_ids).issubset(inmuebles_ids):#return request error if proposed inmuebles dont belong to condo
                return Response(_('inmuebles not part of your condominium.'), status = status.HTTP_400_BAD_REQUEST)
        
            condo_bills = Factura_Condominio.objects.filter(condominio = request.user.condominio)
            if condo_bills.exists():
                inmuebles.filter(id__in = request.data, inquilino__isnull=False).update(inquilino = None)
            else:
                inmuebles.filter(id__in = request.data).delete()

            condominio_activator(request.user.condominio)

            queryset =self.get_queryset()
            serializer = InmuebleSerializer(queryset, many = True)
            request.user.condominio.refresh_from_db()
            context = {
                'condominio_activo': request.user.condominio.activo,
                'data':serializer.data
            }
            return Response(context, status=status.HTTP_200_OK)
        return Response(_('You have no inmuebles registered for this condominium.'), status = status.HTTP_400_BAD_REQUEST)
        

class customPasswordResetView(PasswordResetView):
    serializer_class = customPasswordResetSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"detail": _("Password reset e-mail has been sent.")},
                status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)


class InmuebleCategoryViewSet(viewsets.ModelViewSet):
    queryset = InmuebleCategory.objects.all()
    serializer_class = InmuebleCategorySerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user_type = get_user_type(self.request)
        if user_type =='condominio':
            return self.queryset.filter(condominio = self.request.user.condominio)
        elif user_type =='inquilino':
            inmueble_id= self.request.session.get('inmueble')
            condominio = Inmueble.objects.get(pk =inmueble_id).condominio
            return self.queryset.filter(condominio= condominio)


    def destroy(self, request, pk= None):
        try:
            self.get_queryset().filter(pk=pk).delete()
            now = timezone.now()
            serializer = self.get_serializer(self.get_queryset(),many = True)
            inmueble_queryset = Inmueble.objects.filter(condominio = request.user.condominio)
            context ={
                'categories': serializer.data,
                'inmuebles': InmuebleSerializer(inmueble_queryset,many= True).data
            }
            return Response(context, status=status.HTTP_200_OK)
        except:
            return Response('could not delete', status = status.HTTP_400_BAD_REQUEST)

    def get_object(self, pk):
        try:
            return InmuebleCategory.objects.get(pk=pk)
        except InmuebleCategory.DoesNotExist:
            raise Http404

    def partial_update(self, request, pk = None):
        instance = self.get_object(pk)

        serializer = self.get_serializer(instance, data = request.data, partial = True, context ={'request':request})
        if serializer.is_valid():
            serializer.save()
            serializer = self.get_serializer( self.get_queryset(), many = True )
            inmueble_queryset = Inmueble.objects.filter(condominio = request.user.condominio)
            context ={
                'categories': serializer.data,
                'inmuebles': InmuebleSerializer(inmueble_queryset,many= True).data
            }
            return Response(context, status=status.HTTP_200_OK)

    def create(self, request):
        data = request.data.copy()
        data['condominio'] = request.user.condominio
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save()
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many= True)
            return Response(serializer.data,status=status.HTTP_200_OK)
        else:
            print serializer.errors
            return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)

class Remove_categoryView(APIView):
    queryset = Inmueble.objects.all()

    def get_queryset(self):
        return self.queryset.filter(condominio = self.request.user.condominio)

    def post(self, request):
        serializer = Remove_categorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            queryset = self.get_queryset()
            serializer = InmuebleSerializer(queryset, many= True)
            return Response(serializer.data,status=status.HTTP_200_OK)
        else:
            print serializer.errors
            return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)


class Assign_categoryView(APIView):
    queryset = Inmueble.objects.all()

    def get_queryset(self):
        return self.queryset.filter(condominio = self.request.user.condominio)

    def post(self, request):
        serializer = Assign_categorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            queryset = self.get_queryset()
            serializer = InmuebleSerializer(queryset, many= True)
            return Response(serializer.data,status=status.HTTP_200_OK)
        else:
            print serializer.errors
            return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)

class smsEmailViewSet(viewsets.ModelViewSet):
    queryset = Messages.objects.all()
    serializer_class = MessagesSerializer
    permission_classes = (IsAuthenticated,)
    second_serializer = contextSerializer
    filter_backends = ( DjangoFilterBackend, )
    filter_class = MessagesFilter

    def get_inmuebles(self):
        inmuebles = Inmueble.objects.filter(condominio = self.request.user.condominio)
        serializer = InmuebleSerializer(inmuebles, many= True)
        return serializer.data

    def get_message_info(self, messages):
        response= {}
        if self.queryset.exists():
            earliest= self.queryset.earliest('created').created
            minDate= earliest.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
            response['minDate'] = minDate
        else:
            response['minDate'] = self.request.user.date_joined.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
        
        response['maxDate'] = timezone.now().replace(day= last_day_of_month(timezone.now()), hour= 23, minute = 59, second=59, microsecond=999999 )
        return response

    def list(self, request, *args, **kwargs):

        param = request.GET.get('month_created', None)   
        if param:
            month = dateutil.parser.parse(param)
        else:
            month = timezone.now()

        date_range = month_range_dt(timezone.now())
        serialized_messages = self.get_serializer( self.get_queryset(), many=True, context={'request': request})
        data = {}
        message_info= self.get_message_info(self.queryset)
        inmuebles = self.get_inmuebles()
        context = {
            'maxDate':message_info['maxDate'],
            'minDate':message_info['minDate']
        }
        serialized_ingreso_context = self.second_serializer(context)
        data = {
            'data': serialized_messages.data,
            'context' : serialized_ingreso_context.data,
            'inmuebles': inmuebles
        }
        return Response(data)

    def get_queryset(self):
        month = self.request.GET.get('month_created', None)
        if month:
            date_range = month_range_dt(dateutil.parser.parse(month))
            return self.queryset.filter(sender__condominio = self.request.user.condominio).filter(created__range = (date_range[0], date_range[1]))
        date_range = month_range_dt(timezone.now())
        return self.queryset.filter(sender__condominio = self.request.user.condominio).filter(created__range = (date_range[0], date_range[1]))

    def create(self, request):
        serializer = self.get_serializer(data = request.data)
        if serializer.is_valid():
            serializer.save({'inmueble' : request.data.get('inmueble', None)})
            now = timezone.now()
            serializer = self.get_serializer(self.get_queryset(),many = True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)

class PollsApiView(APIView):
    queryset = Poll.objects.all()
    serializer_class = PollsApiViewSerializer
    permission_classes = (IsAuthenticated,)
    second_serializer = contextSerializer

    def get_queryset(self):
        user_type = get_user_type(self.request)
        if user_type =='condominio':
            return self.queryset.filter(condominio = self.request.user.condominio)
        elif user_type =='inquilino':
            inmueble_id= self.request.session.get('inmueble')
            condominio = Inmueble.objects.get(pk =inmueble_id).condominio
            return self.queryset.filter(condominio= condominio)

    def get_poll_info(self, messages):
        response= {}
        now = timezone.now()
        if self.queryset.exists():
            earliest= self.queryset.earliest('created').created
            latest = now
            minDate= earliest.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
            maxDate= latest.replace(day= last_day_of_month(latest), hour= 23, minute = 59, second=59, microsecond=999999 )
            response['minDate'] = minDate
            alter_mindDate = minDate.replace(year= maxDate.year, month=maxDate.month)
            response['data'] = messages.filter(created__range=(alter_mindDate, maxDate))
        else:
            response['minDate'] = self.request.user.date_joined.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
            response['data'] = []

        response['maxDate'] = now
        response['active_month'] = now
        return response

    def get(self, request, format=None):
        data = {}
        queryset = self.get_queryset()
        now = timezone.now()
        try:
            close_polls = queryset.filter(end__lt=now).update(active=False, ballot_close_timestamp=now)
        except:
            pass
        poll_info= self.get_poll_info(queryset)
        serialized_polls = self.serializer_class(poll_info['data'], many= True, context={'request': request})
        now = timezone.now()
        context = {
            'maxDate':now,
            'minDate':poll_info['minDate'],
            'active_month': now
        }

        serialized_condtext = self.second_serializer(context)
        data = {
            'data': serialized_polls.data,
            'context' : serialized_condtext.data
        }
        return Response(data, status = status.HTTP_200_OK )

class PollsViewSet(viewsets.ModelViewSet):
    queryset = Poll.objects.all().order_by('-created')
    permission_classes = (IsAuthenticated,)
    serializer_class = PollsApiViewSerializer
    filter_backends = ( SearchFilter,DjangoFilterBackend,)
    search_fields = ['question']
    filter_class = PollsFilter

    def get_queryset(self):
        user_type = get_user_type(self.request)
        if user_type =='condominio':
            return self.queryset.filter(condominio = self.request.user.condominio)
        elif user_type =='inquilino':
            inmueble_id= self.request.session.get('inmueble')
            condominio = Inmueble.objects.get(pk =inmueble_id).condominio
            return self.queryset.filter(condominio= condominio)

    def create(self, request):
        serializer = self.get_serializer(data = request.data)
        if serializer.is_valid():
            serializer.save(condominio = request.user.condominio)
            now = timezone.now()
            date_range = month_range_dt(now)
            serializer = self.get_serializer(self.get_queryset().filter(created__range=(date_range[0],date_range[1] )),many = True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            print serializer.errors
        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk= None):
        try:
            self.get_queryset().filter(pk=pk).delete()
            now = timezone.now()
            date_range = month_range_dt(now)
            serializer = self.get_serializer(self.get_queryset().filter(created__range=(date_range[0],date_range[1] )),many = True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except:
            return Response('could not delete', status = status.HTTP_400_BAD_REQUEST)

class Factura_CondominioViewSet(viewsets.ModelViewSet):
    queryset = Factura_Condominio.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = Factura_CondominioSerializer
    filter_backends = ( DjangoFilterBackend,)
    filter_class = Factura_CondominioFilter

    def get_queryset(self):
        return self.queryset.filter(condominio = self.request.user.condominio)

class Factura_CondominioApiView(MessagesApiView):
    queryset = Factura_Condominio.objects.all()
    second_serializer = contextSerializer
    serializer_class = Factura_CondominioSerializer

    def get_range_info(self, data):
        response= {}
        if self.queryset.exists():
            earliest= self.queryset.earliest('mes').mes
            latest= self.queryset.latest('mes').mes
            minDate= earliest.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
            maxDate= latest.replace(day= last_day_of_month(latest), hour= 23, minute = 59, second=59, microsecond=999999 )
            response['minDate'] = minDate
            response['maxDate'] = maxDate
            alter_mindDate = minDate.replace(year= maxDate.year)
            response['data'] = data.filter(mes__range=(alter_mindDate, maxDate))
        else:
            response['minDate'] = self.request.user.date_joined.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
            response['maxDate'] = self.request.user.date_joined.replace(day= last_day_of_month(self.request.user.date_joined), hour= 23, minute = 59, second=59, microsecond=999999)
            response['data'] = []
        response['active_month'] = response['maxDate']
        return response

class VoteView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        data= request.data.copy()
        data['user']=request.user.id
        data['inmueble'] = Inmueble.objects.get(pk = request.session.get('inmueble')).pk
        serializer = VoteSerializer(data= data)
        if serializer.is_valid():
            serializer.save()
            inmueble = serializer.validated_data.get('inmueble')
            queryset = Poll.objects.filter(condominio = inmueble.condominio)
            polls = PollsApiViewSerializer(queryset, many = True)
            return Response(polls.data, status=status.HTTP_200_OK) 
        else:
            print serializer.errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 


class ContactUsApiView( APIView ):
    def post(self, request, format = None):
        serializer = ContactUsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(_("Thank you for your inquiry, we will get back to you as soon as possible!"), status=status.HTTP_200_OK)
        else:
            print serializer.errors
        return Response( serializer.errors, status = status.HTTP_400_BAD_REQUEST )


class RelacionMes2View(APIView):

    permission_classes = (IsAuthenticated,)
    egreso_queryset = Egreso_Condominio.objects.all()
    ingreso_queryset =Ingreso_Condominio.objects.all()
    facturas_condominios = Factura_Condominio.objects.all()
    
    def get_range(self):
        queryset= self.facturas_condominios.filter(condominio =self.request.user.condominio)
        if queryset.exists():
            minDate=queryset.earliest('mes').mes.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
            maxDate=queryset.latest('mes').mes
            maxDate=maxDate.replace(day= last_day_of_month(maxDate), hour= 23, minute = 59, second=59, microsecond=999999 )
            active_month = maxDate+relativedelta(months=1)
        else:
            minDate= self.request.user.date_joined.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
            maxDate=minDate.replace(day= last_day_of_month(minDate), hour= 23, minute = 59, second=59, microsecond=999999 )
            active_month=minDate
        date_range={
            'maxDate':maxDate,
            'minDate':minDate,
            'active_month': active_month
        }
        return date_range

    def get_cols(self, inmuebles, month):
        cols = ['Inmueble', 'Residente', 'Balance Presente', 'Pagos', 'Cuota', 'Balance Nuevo' ]
        cobranza_names = []
        for inmueble in inmuebles:
            cobranzas_inmueble= inmueble.cobranza_condominio_set.filter(editable=True)
            for cobranza in cobranzas_inmueble:
                if not cobranza.asunto in cobranza_names:
                    cobranza_names.append(cobranza.asunto)
        cobranza_names = sorted(cobranza_names)
        for item in cobranza_names:
            cols.insert(5, str(item))
        return cols


    def get(self, request, format=None):
        month = self.get_month()
        total = self.get_total()
        inmuebles = self.get_inmuebles()
        columns = self.get_cols(inmuebles, month)
        context= {
            'inmuebles': inmuebles,
            'total' : total,
            'columns':columns,
            'comission': self.request.user.condominio.comission,
            'month': month,
            'cuentas' :self.request.user.condominio.bancos_set.all()
        }
        serializer = RelacionMes2Serializer(context, context={'range': self.get_range(), 'total': total})
        return Response(serializer.data, status = status.HTTP_200_OK )

    def get_egreso_queryset(self):
        try:
            user_type = get_user_type(self.request)
            if user_type =='condominio':
                return self.egreso_queryset.filter(condominio = self.request.user.condominio).filter(cerrado = False)
            elif user_type =='inquilino':
                inmueble_id= self.request.session.get('inmueble')
                self.condominio = Inmueble.objects.get(pk =inmueble_id).condominio
                return self.egreso_queryset.filter(condominio= self.condominio)
        except:
            return []

    def get_ingreso_queryset(self):
        try:
            user_type = get_user_type(self.request)
            if user_type =='condominio':
                return self.ingreso_queryset.filter(condominio = self.request.user.condominio).filter(cerrado = False)
            elif user_type =='inquilino':
                inmueble_id= self.request.session.get('inmueble')
                self.condominio = Inmueble.objects.get(pk =inmueble_id).condominio
                return self.ingreso_queryset.filter(condominio= self.condominio)
        except:
            return []

    def get_inmuebles(self):
        inmuebles = Inmueble.objects.filter(condominio= self.request.user.condominio)
        return inmuebles

    def get_month(self):
        condominio = self.request.user.condominio
        factura_condominio = self.facturas_condominios.filter( condominio =condominio,tipo_de_factura='service_fee' )
        if factura_condominio.exists():
            month= factura_condominio.latest('mes').mes+relativedelta(months=1)
        else:
            month = self.request.user.date_joined.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
        return month

    def get_total(self, extra_add= None):
        if not extra_add:
            extra_add = 0
        total = self.get_egreso_queryset().aggregate(total_mes= Sum('monto'))['total_mes'] or 0
        return total+decimal.Decimal(extra_add)


    def prorate_if_first_month(self, condominio, monto):
        '''
        Checks if its first month so that prorate discount can be applied
        '''
        facturas = Factura_Condominio.objects.filter(condominio =condominio)
        if not facturas.exists():
            date_joined = condominio.user.date_joined
            total_days_month = int(calendar.monthrange( date_joined.year,  date_joined.month )[1])
            days = total_days_month-int(date_joined.day)
            month_fraction = decimal.Decimal(days)/decimal.Decimal(total_days_month) 

        else:
            month_fraction = 1
        return monto*month_fraction


    def create_factura_condominio(self, facturas_propietarios):
        talonarios = Talonario.objects.all()
        descripcion = str(_('Condominioaldia administrative fee'))
        nro_control = Factura_Condominio.objects.get_control_number(talonarios)
        talonario = talonarios.filter(nro_control_desde__lte=nro_control).filter(nro_control_hasta__gte=nro_control).first()
        nro_control_desde= talonario.nro_control_desde
        nro_control_hasta= talonario.nro_control_hasta
        condominio = self.request.user.condominio
        #extra_expenses =0
        pagos = 0
        deuda_previa = 0
        total = 0

        for item in facturas_propietarios:#condo bill is calculated as percentage of expenses
            total+=item.cuota
            # for obj in item.extra_cols.all():
            #     total+=obj.monto

        total = self.prorate_if_first_month(condominio, total)
        monto = (total*condominio.comission).quantize(settings.TWOPLACES) if condominio.demo_mode == False else 0
        data = {
            'condominio' :condominio,
            'mes' :facturas_propietarios[0].mes,
            'descripcion': descripcion,
            'cantidad' :1,
            'nro_control':nro_control,
            'nro_control_desde':nro_control_desde,
            'nro_control_hasta':nro_control_hasta,
            'rif':condominio.rif,
            'razon_social': self.request.user.first_name,
            'monto' : monto,
            'talonario' :talonario.id,
            'demo_mode': condominio.demo_mode
        }
        serializer = Factura_CondominioSerializer(data= data)
        if serializer.is_valid():
            factura_condominio =serializer.save()
            # condo_extra_cols = self.get_condo_extra_cols(facturas_propietarios, factura_condominio, extra_col_map)
            # extra_col_serializer= Factura_Condominio_Extra_ColumSerializer(data=condo_extra_cols, many=True)
            # if extra_col_serializer.is_valid():
            #     extra_col_serializer.save()
            # else:
            #     print extra_col_serializer.errors
            return factura_condominio
        else:
            print serializer.errors
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 

    def close_egresos_for_month(self):
        try:
            egresos = self.get_egreso_queryset().update(cerrado = True,fecha_cierre=timezone.now())
        except:
            pass

    def close_ingresos_for_month(self):
        try:
            ingresos = self.get_ingreso_queryset().update(cerrado = True,fecha_cierre=timezone.now())
        except:
            pass

    def send_condo_billing_email(self, bill):
        protocol = 'https' if self.request.is_secure() else 'http'
        site=  get_current_site(self.request)
        site_name=  site.name
        month = bill.mes
        monto=bill.monto.quantize(settings.TWOPLACES)
        condo_name= self.request.user.first_name.title()
        site_url = protocol+'://'+str(site.domain)
        currency= self.request.user.condominio.pais.moneda
        message_context = {
            'condo_name': condo_name.title(),
            'monto': intcomma( abs(monto) , 2),
            'site_name': site_name,
            'site_url': site_url,
            'currency':currency,
            'month' :defaultfilters.date(month, "F Y")
        }
        subject_context= {
            'site_name':site_name,
            'month':defaultfilters.date(month, "F Y")
        }
        subject = loader.render_to_string('account/email/condominio_new_bill_subject.txt', subject_context)
        message= loader.render_to_string('account/email/condominio_new_bill.txt', message_context)
        from_email= settings.DEFAULT_FROM_EMAIL
        to_email= []
        bcc= [self.request.user.email]
        egresos = self.request.user.condominio.egreso_condominio_set.filter(cerrado= False)
        pdf_context ={
            'pagesize':'LETTER',
            'factura' : bill.id,
            'page_margin_top':'1cm',
            'page_margin_bottom':'5cm',
            'page_margin_left':'1cm',
            'page_margin_right':'1cm',
            'footer_height':'4cm',
            'header_margin_top':'0cm',
            'header_margin_bottom':'0cm',
            #################ERROR#############
            'egresos':[egreso.id for egreso in egresos]
        }

        email_factura_condominio.delay(subject, message, from_email, to_email, bcc, pdf_context)

    def send_owner_billing_email(self, bills):
        protocol = 'https' if self.request.is_secure() else 'http'
        site=  get_current_site(self.request)
        month = self.get_month()
        condo_name= self.request.user.first_name
        site_name=  site.name

        site_url = protocol+'://'+str(site.domain)
        currency= self.request.user.condominio.pais.moneda

        subject_context= {
            'condo_name':condo_name,
            'month':defaultfilters.date(month, "F Y")
        }

        subject = loader.render_to_string('account/email/propietario_new_bill_subject.txt', subject_context)
        message_list= []
        for bill in bills:
            message_context = {
                'propietario_name': str(bill.inmueble.inquilino.user.first_name).title(),
                'condo_name': condo_name.title(),
                'site_name': site_name.title(),
                'monto': intcomma( abs(bill.monto.quantize(settings.TWOPLACES)) , 2),
                'currency':currency,
                'site_url':site_url,
                'actual_debt':bill.monto.quantize(settings.TWOPLACES)
            }
            body= loader.render_to_string('account/email/propietario_new_bill.txt', message_context)
            context =  {
                'egresos' : [egreso.id for egreso in self.get_egreso_queryset()],
                'condominio': self.request.user.condominio.pk,
                'facturas' : [factura.id for factura in bills],
                'site_name':site_name,
                'site_url':site_url,
                'inmueble_pk': bill.inmueble.pk  
            }
            message = (subject, body, settings.DEFAULT_FROM_EMAIL, [],[bill.inmueble.inquilino.user.email])
            message_list.append(message)
        datatuple= tuple(message_list)
        email_egresos_cuotas.delay(context)

    def check_relacion_perm(self):
        condominio=self.request.user.condominio
        status = True
        facturas = self.facturas_condominios
        if facturas.exists():
            latest_factura = facturas.filter(tipo_de_factura='service_fee').latest('created')
            mes = latest_factura.mes+relativedelta(months=1)
        else:
            mes = condominio.user.date_joined.replace(day=1, hour= 0, minute = 0, second=0,microsecond=0 )
        end_date = last_instant_of_month(mes) 

        now = timezone.now()

        if not now>end_date:
            status = False
        return status

    def create_propietario_bills(self):
        mes = self.get_month()
        monto= self.get_total()
        condominio=self.request.user.condominio
        data= [item.copy() for item in self.request.data.pop('rows')]

        ##################
        if settings.DEBUG==True:
            can_generate_relacion = True
        else:
            can_generate_relacion = self.check_relacion_perm()
        ##################
        if can_generate_relacion:
            serializer =BuildRelacionMesSerializer(data= data, many= True, context={'mes': mes, 'monto':monto, 'condominio':condominio})
            if serializer.is_valid():

                facturas_propietarios=serializer.save()
            else:
                print serializer.errors
                return Response(serializer.errors[0], status=status.HTTP_400_BAD_REQUEST) 
            return facturas_propietarios
        else:
            raise serializers.ValidationError(_('Month expenses analysis can only be generated when the next month has begun.'))

    def verify_income(self):
        try:
            unverified_income = self.get_ingreso_queryset().filter(aprobado = None)
            if unverified_income.exists():
                return False
            return True
        except:
            return True

    def close_cobranzas(self, cobranzas):
        recurring_cobranzas = cobranzas.filter(editable= True).exclude(cobrar_cuando='relacion', recurrencia='una' ).exclude(cobrar_cuando='inmediato')
        id_open__list=[]
        for item in recurring_cobranzas:
            '''
            as per django documentation, an object can be copied like this
            '''
            old_destinatarios = item.destinatario.all()
            item.pk = None
            item.save()#create new instance clone of old instance
            id_open__list.append(item.pk)

            if old_destinatarios:
                for destinatario in old_destinatarios:
                    intermediary_instance = Cobranza_Condominio_Destinatario.objects.create(cobranza_condominio = item, inmueble = destinatario)
        

        cobranzas.update(editable=False)
        try:
            Cobranza_Condominio.objects.filter(pk__in =id_open__list).update(editable= True,mes= item.mes+relativedelta(months=1))
        except:
            pass

    def post(self, request):
        #extra_col_map = self.request.data.pop('extra_col_map' , None)
        if not self.verify_income():
            return Response(_('You have unverified payments pending.'), status=status.HTTP_400_BAD_REQUEST)
        
        if request.user.condominio.retrasado == True:
            return Response(_("Your account is overdue, please pay the amount in full in order to restore complete service."), status=status.HTTP_400_BAD_REQUEST)

        orphan_properties = Inmueble.objects.filter(condominio= request.user.condominio, inquilino__isnull=True)
       
        if orphan_properties.exists():
            return Response(_("You have properties that don't have owners assigned. Go to inmuebles section and assing owners"), status=status.HTTP_400_BAD_REQUEST)
        facturas_propietarios=self.create_propietario_bills()
        self.send_owner_billing_email(facturas_propietarios)
        factura_condominio = self.create_factura_condominio(facturas_propietarios)
        condominio = factura_condominio.condominio
        condominio.bancos_set.all().update(editable = False)
        if not condominio.demo_mode ==True:
            self.send_condo_billing_email(factura_condominio)
        self.close_egresos_for_month()
        self.close_ingresos_for_month()


        #MAKE RECURRING COBRANZAS CLOSE THEM FOR PAST PERIODS
        all_cobranzas = condominio.cobranza_condominio_set.all()

        ################close cobranzas###
        self.close_cobranzas(all_cobranzas)
        ###################


        return Response('ok', status = status.HTTP_200_OK )

class RelacionSummaryView(APIView):
    permission_classes = (IsAuthenticated, IsCondominioOrReadonly,AbiertoOrReadOnly,IsOwnerOrReadOnly,)

    def get_context(self):
        cuentas_queryset = Bancos.objects.filter(condominio = self.request.user.condominio)
        ############################
        relacion_date = timezone.now()
        ###############################
        context = {
            'cuentas':BancosSerializer(cuentas_queryset, many= True).data,
            'relacion_date':relacion_date
        }
        return context

    def get(self, request):
        context = self.get_context()
        return Response(context, status = status.HTTP_200_OK )

class CobranzasCondominio_ApiView(APIView):
    permission_classes = (IsAuthenticated, IsCondominio)
    queryset= Cobranza_Condominio.objects.all()

    def get_queryset(self):
        self.condominio = self.request.user.condominio
        return self.queryset.filter(condominio = self.request.user.condominio)
    
    def get(self, request):
        month_unicode = self.request.GET.get('month_created' , None)
        data = self.get_queryset()
        if month_unicode:
            month= dateutil.parser.parse(month_unicode)
        else:
            month = Factura_Condominio.objects.get_latest_editable_tuple(self.condominio)[0]
            #month= timezone.now()

        data = self.get_queryset()
        data_range = Cobranza_Condominio.objects.get_data_range(self.condominio)
        queryset_range = month_range_dt(month)
        data = Cobranza_CondominioSerializer(data.filter( mes__range=(queryset_range[0], queryset_range[1]) ), many= True).data
        inmuebles = self.condominio.inmueble_set.filter(inquilino__isnull=False)
        context =  {
            'minDate' :data_range[0],
            'maxDate' :data_range[1],
            'active_month' :month.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0),
            'data':data,
            'inmuebles':InmuebleSerializer(inmuebles, many=True).data
        }
        return Response(context, status = status.HTTP_200_OK )

    def post(self, request):
        post_type = request.data.pop('post_type' , None)
        if not post_type:
            data = request.data.copy()
            recipiente = data.get('destinatario', None)
            condominio = request.user.condominio
            data['condominio'] = condominio
            data['recipiente'] = recipiente
            data['category'] = recipiente
            data['mes']=Factura_Condominio.objects.get_latest_editable_tuple(condominio)[0]
            serializer = Cobranza_CondominioSerializer(data =data, context = {'request':request, 'inmueble':data.pop('inmueble', None), 'recipiente':recipiente})
            if serializer.is_valid():
                instance = serializer.save()
                queryset_range = month_range_dt(instance.mes)
                queryset = self.get_queryset().filter(mes__range=(queryset_range[0], queryset_range[1]))
                serializer = Cobranza_CondominioSerializer(queryset, many = True)
                #return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 
                return Response(serializer.data, status = status.HTTP_200_OK )
            else:
                print serializer.errors
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 
        
        elif post_type =='delete':
            queryset = self.get_queryset().filter(id__in=request.data['data_list'])
            if queryset.exists():
                for instance in queryset:
                    if instance.editable == True:
                        for item in instance.cobranza_condominio_destinatario_set.all():
                            item.delete()
                        instance.delete()

            queryset_range = month_range_dt(instance.mes)
            serializer = Cobranza_CondominioSerializer(self.get_queryset().filter(mes__range=(queryset_range[0],queryset_range[1])), many =True)
            return Response(serializer.data, status = status.HTTP_200_OK )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 

class CobranzasPropietario_ApiView(CobranzasCondominio_ApiView):
    permission_classes = (IsAuthenticated, InquilinoHasChosenInmueble)
    def get_queryset(self):
        inmueble_id= self.request.session.get('inmueble')
        inmueble =Inmueble.objects.get(pk =inmueble_id)
        #print dir(inmueble)
        self.condominio = inmueble.condominio
        return self.queryset.filter(condominio = self.condominio)
        #return self.queryset.filter(cobranza_condominio_destinatario__inmueble = inmueble_id)

    def get(self, request):
        month_unicode = self.request.GET.get('month_created' , None)
        data = self.get_queryset()
        if month_unicode:
            month= dateutil.parser.parse(month_unicode)
        else:
            month= timezone.now()
            month =Factura_Condominio.objects.get_latest_editable_tuple(self.condominio)[0]

        data_range = Cobranza_Condominio.objects.get_data_range(self.condominio)
        queryset_range = month_range_dt(month)
        data = Cobranza_CondominioSerializer(data.filter( mes__range=(queryset_range[0], queryset_range[1]) ), context={'request':request},many= True).data
        #inmuebles = self.condominio.inmueble_set.filter(inquilino__isnull=False)
        context =  {
            'minDate' :data_range[0],
            'maxDate' :data_range[1],
            'active_month' :month.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0),
            'data':data
            #'inmuebles':InmuebleSerializer(inmuebles, many=True).data
        }
        return Response(context, status = status.HTTP_200_OK )



class RelacionMesView(RelacionMes2View):
    queryset = Factura_Condominio.objects.all()
    permission_classes = (IsAuthenticated,InquilinoHasChosenInmueble,)
    
    def get_queryset(self):
        try:
            user_type = get_user_type(self.request)

            if user_type =='condominio':
                self.condominio = self.request.user.condominio
                return self.queryset.filter(condominio = self.condominio)
            elif user_type =='inquilino':
                inmueble_id= self.request.session.get('inmueble')
                self.condominio = Inmueble.objects.get(pk =inmueble_id).condominio
                return self.queryset.filter(condominio= self.condominio)
        except:
            return []

    def get_latest_bill(self):
        factura_condominio = self.get_queryset()
        if factura_condominio.exists():
            latest_bill = factura_condominio.latest('created')
        else:
            latest_bill= None
        return latest_bill

    def get_property_bills(self, mes):
        month_range = month_range_dt(mes)
        property_bills = Factura_Propietario.objects.filter(condominio = self.condominio, mes__range=(month_range[0], month_range[1]))
        return property_bills

    def get_month(self):
        condominio = self.condominio
        if self.get_queryset().exists():
            month= self.get_queryset().latest('mes').mes+relativedelta(months=1)
        else:
            month = self.condominio.user.date_joined.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
        return month

    def get_context(self, month):
        bills = self.get_queryset()
        nonEvaluatedIngresos = self.verify_income()
        latest_bill = self.get_latest_bill()

        if latest_bill:
            range_of_data = data_range(self.get_queryset(), 'mes')
            minDate = range_of_data['minDate']
            maxDate = range_of_data['maxDate']
            relation_month  = range_of_data['maxDate']+relativedelta(months = 1)
        else:
            range_of_data = month_range_dt(self.condominio.user.date_joined)
            minDate = range_of_data[0]
            maxDate = range_of_data[1]
            relation_month  = maxDate

        if month:
            month = dateutil.parser.parse(month)
        else:
            if latest_bill:
                month = latest_bill.mes
            else:
                month = self.condominio.user.date_joined

        property_bills = self.get_property_bills(month)
        month_range=month_range_dt(month)
        total_egresos = self.condominio.egreso_condominio_set.filter(mes__range= (month_range[0],month_range[1])).aggregate(total_deuda= Sum('monto'))['total_deuda']
        context = {}
        context['month'] = relation_month
        context['property_bills'] = property_bills
        context['nonEvaluatedIngresos'] = nonEvaluatedIngresos
        context['minDate'] = minDate
        context['maxDate'] = maxDate
        context['month_query'] = latest_bill.mes if latest_bill else self.condominio.user.date_joined
        context['latest_bill'] = latest_bill
        context['columns'] =self.get_cols(self.condominio.inmueble_set.all(), month)
        context['total_egresos'] = total_egresos

        now = timezone.now()
        
        if settings.DEBUG ==True:
            context['can_generate_relacion'] = True
        else:
            context['can_generate_relacion'] = True if (now >=last_instant_of_month(month)) else False
        print context
        return context

    def get_cols(self, inmuebles, month):
        month_range= month_range_dt(month)
        cols = ['Inmueble', 'Residente', 'Balance Presente', 'Pagos', 'Cuota', 'Balance Nuevo' ]
        cobranza_names = []
        for inmueble in inmuebles:
            cobranzas_inmueble= inmueble.cobranza_condominio_set.filter(mes__range=(month_range[0], month_range[1]))
            for cobranza in cobranzas_inmueble:
                if not cobranza.asunto in cobranza_names:
                    cobranza_names.append(cobranza.asunto)
        cobranza_names = sorted(cobranza_names)
        for item in cobranza_names:
            cols.insert(5, str(item))
        return cols

    def get(self, request, month=None,format=None):
        context= self.get_context(month)
        serializer = RelacionMesSerializer(context)
        return Response(serializer.data, status = status.HTTP_200_OK )


class inmueblesSampleFilesView(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        file_type= request.GET.get('file_type')

        if file_type =='csv':
            url = os.path.join(settings.STATIC_ROOT, 'samples/inmuebles.csv')
            extension='csv'
            content_type='text/csv'
        elif file_type =='excel':
            url = os.path.join(settings.STATIC_ROOT, 'samples/inmuebles.xlsx')
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            extension='xlsx'
        file = open(url, 'rb')
        filename = 'inmuebles_ejemplo.%s' %(extension)
        response = HttpResponse(file, content_type=content_type)
        response['Content-Disposition'] = 'attachment; filename="%s"' % filename
        return response

    def post(self, request):
        data = request.data.copy()
        serializer = Inmueble_UploadReqSerializer(data=data)
        if serializer.is_valid():
            serializer.save(condominio=request.user.condominio, request=request)
            return Response(_("Thank you for your request, we will contact you via E-mail with further instructions."), status = status.HTTP_200_OK )
        else:
            print serializer.errors
        return Response('NOT FOUND', status=status.HTTP_400_BAD_REQUEST) 
        

class inquilino_homeView(CondoHomeView):
    permission_classes = (IsAuthenticated,)

    def get_cartelera(self):
        queryset = Cartelera.objects.filter(condominio = self.condominio)
        serializer = CarteleraSerializer(queryset, many= True)
        return serializer

    def get_circulante(self, inmueble):
        condominio =inmueble.condominio
        period = Factura_Condominio.objects.get_latest_editable_tuple(condominio)
        egresos_totales_periodo = condominio.egreso_condominio_set.filter(mes__range=(period[0], period[1])).aggregate(total_monto= Sum('monto'))['total_monto'] or 0
        inmuebles = condominio.inmueble_set.all()
        cobranzas_sum = 0
        for inmueble in inmuebles:
            cobranzas = inmueble.cobranza_condominio_set.filter(editable= True)
            cobranzas_sum = get_total_cobranzas(cobranzas, inmueble,egresos_totales_periodo)

        
        facturas_propietarios = Factura_Propietario.objects.filter(condominio = condominio)
        if facturas_propietarios.exists():
            latest_factura = condominio.factura_condominio_set.filter(tipo_de_factura='service_fee').latest('created')
            sum_balance = facturas_propietarios.aggregate(total_deuda= Sum('monto'))['total_deuda']
        else:
            sum_balance = inmuebles.aggregate(total_deuda= Sum('balanceinicial'))['total_deuda']

        
        payments = Ingreso_Condominio.objects.filter(condominio = condominio, aprobado =True,mes__range=(period[0],period[1],))
        
        if payments.exists():
            sum_payments = payments.aggregate(total_pagos= Sum('monto'))['total_pagos']
        else:
            sum_payments =0

        circulante = sum_payments+sum_balance-cobranzas_sum-egresos_totales_periodo
        return circulante

    def get_balance_actual(self, inmueble):
        facturas = inmueble.factura_propietario_set.all()
        deuda_actual = facturas.latest('created').monto if facturas.exists() else inmueble.balanceinicial
        cobranzas_inmediatas = inmueble.cobranza_condominio_set.filter(editable = True,cobrar_cuando= 'inmediato' )
        sum_cobranzas_pendientes = cobranzas_inmediatas.aggregate(total_payed= Sum('monto'))['total_payed'] or 0
        self.cobranzas_pendientes_count = cobranzas_inmediatas.count() if cobranzas_inmediatas else 0
        return deuda_actual-sum_cobranzas_pendientes

    def get_encuestas_vigentes(self, inmueble):
        polls_count = Poll.objects.filter(condominio = inmueble.condominio, active= True).count()
        return polls_count

    def get_context(self):
        blog_data = self.get_blog_data()
        inmueble = Inmueble.objects.get(pk =self.request.session.get('inmueble'))
        context = {
            'cartelera': self.get_cartelera().data,
            'circulante': self.get_circulante(inmueble),
            'balance_actual': self.get_balance_actual(inmueble),
            'encuestas_vigentes': self.get_encuestas_vigentes(inmueble),
            'cobranzas_pendientes':self.cobranzas_pendientes_count,
            'blog': blog_data['blog'],
            'minDate':blog_data['minDate']
        }
        return context


class inquilino_inmueblesView(APIView):
    queryset = Inmueble.objects.all()
    serializer_class = InmuebleSerializer
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        queryset= self.queryset.filter(inquilino = self.request.user.inquilino)
        return queryset

    def get(self, request):
        queryset = self.get_queryset()
        serializer = InmuebleSerializer(queryset, many= True)
        return Response(serializer.data, status = status.HTTP_200_OK )

class ingresos_afiliadoView(generics.ListAPIView):
    queryset = Affiliate_Income.objects.all()
    serializer_class = Affiliate_IncomeSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = ( DjangoFilterBackend,)
    second_serializer = contextSerializer
    filter_class = ingresos_afiliadoFilter

    def get(self, request, *args, **kwargs):
        queryset = self.list(request, *args, **kwargs)
        serializer= Affiliate_IncomeSerializer(queryset, many = True)
        ingresos = self.list(request, *args, **kwargs).data
        date_range= self.get_range()
        maxDate = date_range['maxDate']
        context = {
            'maxDate':maxDate,
            'minDate':date_range['minDate']
        }
        serialized_ingreso_context = self.second_serializer(context)
        data = {
            'data': ingresos,
            'income_context' : serialized_ingreso_context.data
        }
        return Response(data, status = status.HTTP_200_OK )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(queryset, many=True)
        return serializer


    def get_range(self, active_month = None):
        queryset= self.queryset.filter(affiliate =self.request.user.affiliate)
        if queryset.exists():
            minDate=queryset.earliest('created').created.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
            maxDate=queryset.latest('created').created
            maxDate=maxDate.replace(day= last_day_of_month(maxDate), hour= 23, minute = 59, second=59, microsecond=999999 )
        else:
            minDate= self.request.user.date_joined.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
            maxDate=minDate.replace(day= last_day_of_month(minDate), hour= 23, minute = 59, second=59, microsecond=999999 )
        date_range={
            'maxDate':maxDate,
            'minDate':minDate
        }
        return date_range

    def get_queryset(self):
        return self.queryset.filter(affiliate=self.request.user.affiliate)

class tipsApiView(APIView):
    permission_classes = (IsAuthenticated,)
    def post(self, request):
        if request.data['dontShow'] == True:
            user_type=get_user_type(request)
            role_instance = getattr(request.user, user_type)#returns condominio/affiliate/inquilino instance
            role_instance.fast_help_popup =False
            role_instance.save()
        return Response('ok', status = status.HTTP_200_OK)

class InstaPagoView(APIView, Instapago):
    permission_classes = (IsAuthenticated,)
    def post(self, request):
        user_type = request.user.get_user_type()
        if user_type =='condominio':
            condominio = request.user.condominio
        elif user_type =='inquilino':
            inmueble = Inmueble.objects.get(pk = request.session.get('inmueble'))
            condominio =inmueble.condominio
        currency = condominio.pais.moneda
        data = request.data.copy()
        data['exp'] = dateutil.parser.parse(data['exp']).date()

        json_data = {}
        json_data['KeyId'] ='2D5B4B8F-6720-4F90-89E9-249EF03A8CF3'
        json_data['PublicKeyId'] ='5cf5cdb0dcbc1657d7f89fca215a8546'
        json_data['Amount'] =data.get('monto')
        json_data['Description'] = data.get('description')
        json_data['CardHolder'] = data.get('name_on_card')
        json_data['CardHolderID'] = data.get('rif')
        json_data['CardNumber'] = data.get('card_number')
        json_data['CVC'] = data.get('cvc')
        json_data['ExpirationDate'] = data.get('exp').strftime('%m/%Y')
        json_data['StatusId'] = 2
        json_data['IP'] = request.META['REMOTE_ADDR']

        instapago = self.submit_payment(**json_data)
        if int(instapago['code']) == 201:
            register_cc_payment(request, instapago, 'Instapago')
            email_voucher = instapago['voucher']
            instapago['voucher'] =  unescape(instapago['voucher'])
            subject = 'Pago recibido exitosamente a la tarjeta terminando en %s' %(data.get('card_number')[:4])
            monto = decimal.Decimal(data['monto']).quantize(settings.TWOPLACES)
            message = 'Estimado %s, se ha cobrado la cantidad de %s a su tarjeta de credito exitosamente, gracias por utilizar Condominioaldia.net' %(request.user.get_full_name(), monto)
            site=  get_current_site(self.request)
            site_name=  site.name

            context = {
                'name':request.user.get_full_name(),
                'currency': currency,
                'email_voucher':instapago['voucher'],
                'monto':monto,
                'site_name':site_name,
                'end_cc': data.get('card_number')[:4],
                'description':json_data['Description']
            }
            msg_html = loader.render_to_string('account/email/credit_card_email.txt', context)
            send_email.delay(subject, message, settings.DEFAULT_FROM_EMAIL, [request.user.email], fail_silently = False, html_message= msg_html, html_email_template_name='account/email/credit_card_email.txt')
           
        return Response(instapago, status = status.HTTP_200_OK)
        #     D = decimal.Decimal
        #     response_dict['paymentResponse']['voucher'] = unescape(response_dict['paymentResponse']['voucher'])
        #     subject = 'Pago exitoso'
        #     #message = 'Estimado %s, se ha cobrado la cantidad de %s a su tarjeta de credito exitosamente, gracias por utilizar Condominioaldia.net' %(request.user.condominio.nombre, Amount)
        #     correoCondominioaldia = str(settings.EMAIL_HOST_USER)
        #     correosList = [ str(request.user.email) ]
        #     #REGISTER PAYMENT
        #     pago = Pagos_Condominio.objects.create(condominio = condominio, fecha_de_pago = timezone.now().date(), monto = paymentAmount, fecha_aprobacion_pago = timezone.now().date(), tipo_de_pago = 'Instapago', pago_aprobado = True, factura = factura)
        #     #SET FACTURA STATUS TO PAID
        #     factura = Factura_Condominio.objects.get(pk = facturaID)
        #     factura.pagado = True
        #     factura.save()
        #     request.session['bill_status'] = str(condominio_bill_status(condominio)['status'])
        #     #ADD TO EGRESOS FOR CURRENT MONTH
        #     Egresos_Condominio.objects.create(monto = paymentAmount, fechafacturacion = timezone.now().date(), titulo = 'PAGO CONDOMINIOALDIA', publicado = False, condominio = condominio )


        #     email_title = 'Pago de Condominio exitoso'
        #     message = 'Estimado %s, el cobro por un monto de %s %s ha sido cargada exitosamente a su tarjeta de credito.' %(str(condominio.nombre), request.session['currency'], str(Amount))
        #     label_msg_2  ='Voucher'
        #     msg2 = ''
        #     some_button = ''
        #     label_msg3 = ''
        #     msg3 = ''
        #     context = {
        #         'email_title': email_title,
        #         'message': message,
        #         'label_msg_2': label_msg_2,
        #         'msg2': response_dict['paymentResponse']['voucher'],
        #         'some_button': some_button,
        #         'label_msg3': label_msg3,
        #         'msg3': msg3
        #     }
        #     #msg_html = response_dict['paymentResponse']['voucher']
        #     msg_html = render_to_string('base_email.html', context)
        #     send_email.delay(subject, message, correoCondominioaldia, correosList, fail_silently = False, html_message= msg_html)
        # print serializer.validated_data
        #else:
            #print serializer.errors
        #return Response(serializer.errors, status = status.HTTP_200_OK)

    def get(self, request):
        #from django.core.mail import send_mail, send_mass_mail, mail_admins, EmailMessage, EmailMultiAlternatives, get_connection
        #send_mail('test subject', 'test message', settings.DEFAULT_FROM_EMAIL, ['peto813@hotmail.com'])
        return Response('ok', status = status.HTTP_200_OK)
        # #return self.get_paginated_response(page)


class testApiView(APIView):

    def post(self, request):
        return Response('ok', status = status.HTTP_200_OK)

    def get(self, request):
        print request.user.condominio.egreso_condominio_set.all()
        return Response('ok', status = status.HTTP_200_OK)
        # #return self.get_paginated_response(page)
