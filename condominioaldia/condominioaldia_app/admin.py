# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.http import HttpResponseRedirect 
from django.contrib import admin, messages
from django.conf import settings
from django.template.response import TemplateResponse
from django.utils import timezone
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.humanize.templatetags.humanize import intcomma
from django.template import loader
# from django.contrib import admin
# from django.conf import settings
from condominioaldia_app.serializers import Affiliate_IncomeSerializer
from .models import *
from condominioaldia_app.tasks import send_email
from allauth.account.utils import send_email_confirmation
# from django.utils.encoding import smart_unicode

# #USED TO GET URL
#from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.utils.translation import gettext, gettext_lazy as _
from condominioaldia_app.forms import TalonarioForm, AffiliateAdminForm, Affiliate_IncomeForm,PagosCondominioaldiaAdmin_Form
# #from django.contrib.auth.models import User
# from django.utils.html import format_html
from django.core.urlresolvers import reverse
# from django.core.mail import send_mail, EmailMessage
# from django.db.models import Q
# from django.contrib.auth.models import User
# from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe
admin.site.site_title = 'Administrador Condominioaldia'
admin.site.site_header = 'Administrador Condominioaldia'
admin.site.index_title = _("Control Panel")
admin.site.index_template = "custom_index.html"
#admin.site.site_url = '/'

# class ProfileInline(admin.StackedInline):
#     model = UserProfile
#     can_delete = False
#     verbose_name_plural = 'Profile'
#     fk_name = 'user'

class CustomUserAdmin(UserAdmin):
    #inlines = (ProfileInline, )
    list_display = ['username', 'first_name', 'last_name','email', 'is_superuser', 'is_active', 'tipo_usuario']
    #list_editable = ('is_active', )
    #search_fields = [ 'email', 'first_name', 'last_name' ]
    actions = [ 'resend_confirmation_email']
    list_filter = ('is_active', 'is_superuser', 'is_staff')  
    readonly_fields = ('tipo_usuario',)
    def tipo_usuario(self, obj):
        if hasattr(obj, 'condominio'):
            return _('condominium')
        elif hasattr(obj, 'inquilino'):
            return _('owner')
        elif hasattr(obj, 'affiliate'):
            return _('affiliate')
        else:
            return _('Staff')
        return obj.userprofile.mobile_number
    tipo_usuario.short_description = _("user type")

    
    def resend_confirmation_email(self, request, queryset):
        for user in queryset:
            if not user.is_staff and not user.is_superuser:
                send_email_confirmation(request, user)
    resend_confirmation_email.short_description = _("Resend confirmation E-mail")
    # def office_number(self, obj):
    #     return obj.userprofile.office_number 
    # def company_name(self, obj):
    #     return obj.userprofile.company_name
    # def profile_picture(self, obj):
    #     return mark_safe(obj.userprofile.image_tag())
        # html = u' <img src="%s" />' %(obj.userprofile.profile_picture)admin_thumbnail
        # return mark_safe(html)
    #profile_picture.allow_tags = True
    # def image_tag(self):
    #     return u'<img src="%s" />' % <URL to the image>          
    #mobile_number.allow_tags = True
    #mobile_number.short_description = "Mobile"
    #office_number.short_description = "Office #"
    # def get_inline_instances(self, request, obj=None):
    #     if not obj:
    #         return list()
    #     return super(CustomUserAdmin, self).get_inline_instances(request, obj)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

class Payment_MethodInline(admin.StackedInline):
    model = Payment_Method_Detail
    extra = 0
    fields = ("activo","metodo_pago","pais",)



class AffiliateAdmin( admin.ModelAdmin ):
    form = AffiliateAdminForm
    list_display = ['user', 'rif', 'aprobado','telefono1', 'created']
    readonly_fields = ['user', 'terminos','url', 'comprobante_rif' , 'rif']
    
    def save_model(self, request, obj, form, change):
        if form.has_changed() and form.is_valid():
            for data in form.changed_data:

                if data == 'aprobado' and obj.aprobado: # IF 'APROBADO' FIELD IS CHANGED TO APPROVED STATE
                    #subject = 'Su Condominio ha sido aprodado'
                    #message = 'Estimado(a) %s, Su Condominio ha sido aprobado por nuestros analistas! Bienvenido a CondominioAlDia; ahora puede disfrutar de todos nuestros servicios!' %(obj.user.first_name)
                    #subject = _("Your condominium has been approved")
                    subject = loader.render_to_string('account/email/affiliate_approved_subject.txt', {})
                    message = loader.render_to_string('account/email/affiliate_approved_message.txt', {'name' : obj.user.first_name, 'site_name': get_current_site(request).name})
                    #message = _("Dear %s, your condominium has been approved by our analysts!, welcome to %s; now you can enjoy our services." %(obj.user.first_name, get_current_site(request).name ) ) 
                    fromEmail = str(settings.DEFAULT_FROM_EMAIL)
                    emailList = [ obj.user.email ]
                    send_email.delay(subject, message, fromEmail, emailList, fail_silently = False )
                    obj.fecha_aprobacion = timezone.now()
                    obj.save()
                elif data =='aprobado' and not obj.aprobado:
                    razon_rechazo =  request.POST.get('razon_rechazo')
                    obj.razon_rechazo = str(razon_rechazo)
                    # subject = 'Ooops!, Su Condominio ha sido rechazado'
                    # message = 'Estimado(a) %s, Lamentamos informarle que su condominio ha sido rechazado. La razon de acuerdo a nuestros analistas es: %s. Puede intentar de registrarse nuevamente. Gracias por su paciencia!' %( obj.nombre, obj.razon_rechazo)
                    subject = _('Oops your affiliate account was not approved')
                    message = _('Dear '+obj.nombre+', we regret to inform you that your affiliate account was not approved. The reason is: '+ obj.razon_rechazo +'. You may try to register again!')
                    fromEmail = str(settings.DEFAULT_FROM_EMAIL)
                    emailList = [ obj.user.email ]     
                    send_email.delay(subject, message, fromEmail, emailList, fail_silently = False )
                    obj.user.delete()

        super(AffiliateAdmin, self).save_model(request, obj, form, change)   
admin.site.register(Affiliate, AffiliateAdmin)

class PaisesAdmin( admin.ModelAdmin ):
    inlines = (Payment_MethodInline,)
    # def user_instance(self, obj):
    #     return 'Id: '+ str(obj.user.pk)  + ' - ' + str(obj.user.first_name) + ' ' + str(obj.user.last_name)
    # def first_name(self, obj):
    #     return smart_unicode(obj.user.first_name)
    # def last_name(self, obj):
    #     return smart_unicode(obj.user.last_name)
    #user_instance.short_description = 'user_instance'
    # search_fields = ['=id', 'condominio__rif', ]
    # list_filter = ('timestamp', 'fechafacturacion',)  
    # save_on_top = True
    # form = Egresos_Condominio_Form
    #readonly_fields = ('user_instance', 'first_name', 'last_name', 'mobile_number', 'office_number', 'profile_picture', 'company_name',)
    #fields = [ 'user_instance', 'first_name', 'last_name','company_name',  'profile_picture', 'mobile_number', 'office_number' ]
    list_display = ['nombre', 'moneda', 'nombre_registro_fiscal','activo', 'rif_regex']
admin.site.register( Paises, PaisesAdmin )

class Affiliate_Banc_AccountAdmin( admin.ModelAdmin ):
    #inlines = (Payment_MethodInline,)
    # def user_instance(self, obj):
    #     return 'Id: '+ str(obj.user.pk)  + ' - ' + str(obj.user.first_name) + ' ' + str(obj.user.last_name)
    # def first_name(self, obj):
    #     return smart_unicode(obj.user.first_name)
    # def last_name(self, obj):
    #     return smart_unicode(obj.user.last_name)
    #user_instance.short_description = 'user_instance'
    # search_fields = ['=id', 'condominio__rif', ]
    list_filter = ('pais__nombre', 'banco',)  
    # save_on_top = True
    # form = Egresos_Condominio_Form
    #readonly_fields = ('user_instance', 'first_name', 'last_name', 'mobile_number', 'office_number', 'profile_picture', 'company_name',)
    #fields = [ 'user_instance', 'first_name', 'last_name','company_name',  'profile_picture', 'mobile_number', 'office_number' ]
    list_display = ['titular', 'created', 'pais','nro_cuenta', 'banco']
admin.site.register( Affiliate_Banc_Account, Affiliate_Banc_AccountAdmin )

class Affiliate_IncomeAdmin( admin.ModelAdmin ):
    def condo_payed(self, obj):
        return obj.factura_condominio.pagado == True
    condo_payed.boolean = True   
    condo_payed.short_description = _('Condo has payed')

    def save_model(self, request, obj, form, change):#ADDITIONAL VALIDATION IN MODEL'S SAVE METHOD IN models.py
        if form.has_changed() and form.is_valid():
            bank_account_queryset =Affiliate_Banc_Account.objects.filter(affiliate= obj.affiliate)
            if bank_account_queryset.exists():
                protocol = 'https' if request.is_secure() else 'http'
                site_name=  get_current_site(request).name
                site_url = protocol+'://'+site_name
                bank_account_instance = bank_account_queryset.first()
                subject = loader.render_to_string('account/email/affiliate_payment_sent_subject.txt', {})
                msg_context = {
                    'bank_name' : bank_account_instance.banco,
                    'currency': bank_account_instance.pais.moneda,
                    'monto': intcomma(obj.monto.quantize(settings.TWOPLACES),2),
                    'account_number':bank_account_instance.nro_cuenta,
                    'site_url': site_url.lower(),
                    'site_name': site_name,
                    'account_holder' :bank_account_instance.titular.title(),
                    'country' : bank_account_instance.pais.nombre.title(),
                    'affiliate' : obj.affiliate.user.get_full_name()
                }
                message = loader.render_to_string('account/email/affiliate_payment_sent_message.txt', msg_context)
                send_email.delay(subject, message, str(settings.DEFAULT_FROM_EMAIL), [obj.affiliate.user.email], fail_silently = False )
            super(Affiliate_IncomeAdmin, self).save_model(request, obj, form, change)

    form = Affiliate_IncomeForm
    readonly_fields = ('condo_payed','affiliate','monto','factura_condominio', 'condominio_name','condominio','comission','status',)
    fields = ('affiliate','status','monto','factura_condominio', 'condominio_name','condominio','comission', 'pagado', 'payment_proof',)
    list_display = ['id', 'affiliate','condominio_name','condo_payed','created', 'monto','pagado']
    list_filter=('pagado','factura_condominio__pagado',)
admin.site.register( Affiliate_Income, Affiliate_IncomeAdmin )

class PagosCondominioaldiaAdmin( admin.ModelAdmin ):
    #IF PAYMENT STATUS IS CHANGED FROM NOT APPROVED TO APPROVED OR IF APPROVED WHEN CREATING SEND EMAIL
    def save_model(self, request, obj, form, change):#ADDITIONAL VALIDATION IN MODEL'S SAVE METHOD IN models.py

        if form.has_changed() and form.is_valid():
            if obj: #OBJECT IS CREATED BY CONDO AND WILL ONLY BE PRESENT AS SUCH
                #PASS SOME PARAMETERS IN THE INSTANCE OBJECT.
                obj.request =request
                obj.affiliate = Affiliate
                obj.serializer = Affiliate_IncomeSerializer
                obj.send_email = send_email
                obj.fecha_aprobacion = timezone.now()
            super(PagosCondominioaldiaAdmin, self).save_model(request, obj, form, change)
        else:
            messages.error(request, _("Condo payment was not modified due to no modifications."))

    form = PagosCondominioaldiaAdmin_Form

    #inlines = (Payment_MethodInline,)
    # def user_instance(self, obj):
    #     return 'Id: '+ str(obj.user.pk)  + ' - ' + str(obj.user.first_name) + ' ' + str(obj.user.last_name)
    # def first_name(self, obj):
    #     return smart_unicode(obj.user.first_name)
    # def last_name(self, obj):
    #     return smart_unicode(obj.user.last_name)
    #user_instance.short_description = 'user_instance'
    # search_fields = ['=id', 'condominio__rif', ]
    list_filter = ('tipo_de_pago', 'banco__banco', 'factura__condominio__pais__nombre',) 
    def country(self, obj):
        return obj.factura.condominio.pais.nombre

    # save_on_top = True
    # form = Egresos_Condominio_Form
    readonly_fields = ('country','banco', 'factura', 'created', 'comprobante_pago', 'tipo_de_pago','nro_referencia','fecha_aprobacion','monto',)
    #fields = [ 'user_instance', 'first_name', 'last_name','company_name',  'profile_picture', 'mobile_number', 'office_number' ]
    list_display = ['id', 'banco', 'created', 'country','aprobado','tipo_de_pago','comprobante_pago']
admin.site.register( Pagos_Condominio, PagosCondominioaldiaAdmin )

class BancosCondominioaldiaAdmin( admin.ModelAdmin ):
    # def user_instance(self, obj):
    #     return 'Id: '+ str(obj.user.pk)  + ' - ' + str(obj.user.first_name) + ' ' + str(obj.user.last_name)
    # def first_name(self, obj):
    #     return smart_unicode(obj.user.first_name)
    # def last_name(self, obj):
    #     return smart_unicode(obj.user.last_name)
    #user_instance.short_description = 'user_instance'
    # search_fields = ['=id', 'condominio__rif', ]
    list_filter = ('pais__nombre', 'banco',)  
    # save_on_top = True
    # form = Egresos_Condominio_Form
    #readonly_fields = ('user_instance', 'first_name', 'last_name', 'mobile_number', 'office_number', 'profile_picture', 'company_name',)
    #fields = [ 'user_instance', 'first_name', 'last_name','company_name',  'profile_picture', 'mobile_number', 'office_number' ]
    list_display = ['id','pais', 'banco', 'nro_cuenta']
admin.site.register( BancosCondominioaldia, BancosCondominioaldiaAdmin )



class Payment_MethodAdmin( admin.ModelAdmin ):
    # def user_instance(self, obj):
    #     return 'Id: '+ str(obj.user.pk)  + ' - ' + str(obj.user.first_name) + ' ' + str(obj.user.last_name)
    # def first_name(self, obj):
    #     return smart_unicode(obj.user.first_name)
    # def last_name(self, obj):
    #     return smart_unicode(obj.user.last_name)
    #user_instance.short_description = 'user_instance'
    # search_fields = ['=id', 'condominio__rif', ]
    # list_filter = ('timestamp', 'fechafacturacion',)  
    # save_on_top = True
    # form = Egresos_Condominio_Form
    #readonly_fields = ('user_instance', 'first_name', 'last_name', 'mobile_number', 'office_number', 'profile_picture', 'company_name',)
    #fields = [ 'user_instance', 'first_name', 'last_name','company_name',  'profile_picture', 'mobile_number', 'office_number' ]
    list_display = ['id', 'nombre' ]
admin.site.register( Payment_Method, Payment_MethodAdmin )


class FaqAdmin( admin.ModelAdmin ):
    # def user_instance(self, obj):
    #     return 'Id: '+ str(obj.user.pk)  + ' - ' + str(obj.user.first_name) + ' ' + str(obj.user.last_name)
    # def first_name(self, obj):
    #     return smart_unicode(obj.user.first_name)
    # def last_name(self, obj):
    #     return smart_unicode(obj.user.last_name)
    #user_instance.short_description = 'user_instance'
    # search_fields = ['=id', 'condominio__rif', ]
    # list_filter = ('timestamp', 'fechafacturacion',)  
    # save_on_top = True
    # form = Egresos_Condominio_Form
    #readonly_fields = ('user_instance', 'first_name', 'last_name', 'mobile_number', 'office_number', 'profile_picture', 'company_name',)
    #fields = [ 'user_instance', 'first_name', 'last_name','company_name',  'profile_picture', 'mobile_number', 'office_number' ]
    list_display = ['id', 'pregunta', 'respuesta']
admin.site.register( Faq, FaqAdmin )


class UploadInmueblesAdmin( admin.ModelAdmin ):
    def button_add_inmuebles(self, obj):
        url = '/admin/inmuebles_csv/%s' %(str(obj.condominio.pk))
        html = u' <a style="color:#fff;background-color:#337ab7;border-color:#2e6da4;height:75px;padding:5px;border-radius:5px;" href="%s"><b>Cargar Inmuebles</b></a>' %(url)
        return mark_safe(html)
    button_add_inmuebles.short_description='Cargar'
    button_add_inmuebles.allow_tags = True

    readonly_fields = ('pago_condominio','ejecutado',)
    #fields = ['button_add_inmuebles']
    readonly_fields=['condominio','button_add_inmuebles', 'pago_condominio', 'pagado', 'csv_file']
    list_display = ['condominio', 'created', 'pagado','ejecutado', 'pago_condominio']
    list_display_links = ('condominio',)
admin.site.register( Inmueble_UploadReq, UploadInmueblesAdmin )


class PaginasAmarillasAdmin( admin.ModelAdmin ):
    pass
    # def user_instance(self, obj):
    #     return 'Id: '+ str(obj.user.pk)  + ' - ' + str(obj.user.first_name) + ' ' + str(obj.user.last_name)
    # def first_name(self, obj):
    #     return smart_unicode(obj.user.first_name)
    # def last_name(self, obj):
    #     return smart_unicode(obj.user.last_name)
    #user_instance.short_description = 'user_instance'
    # search_fields = ['=id', 'condominio__rif', ]
    # list_filter = ('timestamp', 'fechafacturacion',)  
    # save_on_top = True
    # form = Egresos_Condominio_Form
    #readonly_fields = ('user_instance', 'first_name', 'last_name', 'mobile_number', 'office_number', 'profile_picture', 'company_name',)
    #fields = [ 'user_instance', 'first_name', 'last_name','company_name',  'profile_picture', 'mobile_number', 'office_number' ]
    #list_display = ['nombre', 'moneda', 'nombre_registro_fiscal','activo']
admin.site.register( Paginas_Amarillas, PaginasAmarillasAdmin )

class InmuebleAdmin( admin.ModelAdmin ):
    pass
    # def user_instance(self, obj):
    #     return 'Id: '+ str(obj.user.pk)  + ' - ' + str(obj.user.first_name) + ' ' + str(obj.user.last_name)
    # def first_name(self, obj):
    #     return smart_unicode(obj.user.first_name)
    # def last_name(self, obj):
    #     return smart_unicode(obj.user.last_name)
    #user_instance.short_description = 'user_instance'
    # search_fields = ['=id', 'condominio__rif', ]
    # list_filter = ('timestamp', 'fechafacturacion',)  
    # save_on_top = True
    # form = Egresos_Condominio_Form
    readonly_fields = ('get_propietario',)
    #fields = [ 'user_instance', 'first_name', 'last_name','company_name',  'profile_picture', 'mobile_number', 'office_number' ]
    def get_propietario(self, obj):
        try:
            return obj.inquilino.user
        except:
            return 'Ninguno'
    get_propietario.short_description = _("Owner")

    list_display = ['id', 'nombre_inmueble', 'get_propietario']
admin.site.register( Inmueble, InmuebleAdmin )

class InquilinoAdmin( admin.ModelAdmin ):
    pass
    # def user_instance(self, obj):
    #     return 'Id: '+ str(obj.user.pk)  + ' - ' + str(obj.user.first_name) + ' ' + str(obj.user.last_name)
    # def first_name(self, obj):
    #     return smart_unicode(obj.user.first_name)
    # def last_name(self, obj):
    #     return smart_unicode(obj.user.last_name)
    #user_instance.short_description = 'user_instance'
    # search_fields = ['=id', 'condominio__rif', ]
    # list_filter = ('timestamp', 'fechafacturacion',)  
    # save_on_top = True
    # form = Egresos_Condominio_Form
    #readonly_fields = ('user_instance', 'first_name', 'last_name', 'mobile_number', 'office_number', 'profile_picture', 'company_name',)
    #fields = [ 'user_instance', 'first_name', 'last_name','company_name',  'profile_picture', 'mobile_number', 'office_number' ]
    #list_display = ['nombre', 'moneda', 'nombre_registro_fiscal','activo']
admin.site.register( Inquilino, InquilinoAdmin )

class InmuebleInline(admin.TabularInline):
    model = Inmueble
    extra = 1


class CondominioAdmin(admin.ModelAdmin):

    def has_delete_permission(self, request, obj=None):
        return False

    def borrar_ultimo_corte(modeladmin, request, queryset):
        request.session['del_corte_list'] = [item.pk for item in queryset]
        if request.POST.get('post'):
            print "Performing action"
            # action code here
            return None
        else:
            request.current_app = modeladmin.admin_site.name

            return TemplateResponse(request, "admin/borrar_ultimo_corte.html", {})
        borrar_ultimo_corte.short_description = _("Delete last cut.")
    
    def inmuebles_csv(self, request, queryset):
        if len(queryset) !=1:
            messages.error(request, _("Select a single condominium for CSV uploads."))
        condominio = queryset[0]
        #redirect to upload via CSV view
        return HttpResponseRedirect(reverse('inmuebles_csv', kwargs={'condominio':condominio.rif}))
    inmuebles_csv.short_description = _("Upload properties via CSV")

    #form = CondominioForm
    actions = ['inmuebles_csv', 'borrar_ultimo_corte']
    search_fields = ['rif', 'municipio', 'user__email','parroquia', 'telefono1', 'telefono2' ]
    list_filter = ('estado', 'aprobado','pais__nombre',) 
    fields = [ 'aprobado', 'userg', 'rif', 'logo','telefono1', 'telefono2', 'direccion', 'estado', 'municipio', 'parroquia', 'terminos', 'comprobante_rif', 'demo_mode']
    #save_on_top = True
    #form = Condominio_Admin_Form
    readonly_fields = ['email', 'userg', 'rif',  'user','terminos', 'comprobante_rif', 'pais' ]
    save_on_top = True
    # class Media:  
    #     css = {
    #          'all': ('css/admin/admin.css',)
    #     }

    #     js = ('jss/jquery.min.js','jss/adminjs/admincondominio.js',)

    list_display = ('email','userg', 'rif', 'pais', 'direccion','estado', 'municipio', 'telefono1', 'telefono2','aprobado', 'activo', 'demo_mode', )


    def email(self, obj):
        return obj.user.email
    email.short_description = 'correo'

    def userg(self, obj):
        return obj.user.get_full_name()
    userg.short_description = 'Usuario'
    def get_readonly_fields(self, request, obj=None):
        if obj:
            if obj.aprobado == True:
                return self.readonly_fields + ['aprobado']
        return self.readonly_fields
    # def qr_code(self, obj):
    #     codes = get_qr_code( settings.MEDIA_ROOT+'/'+str(obj.comprobante_rif) )
    #     return_string = ''
    #     i = 0
    #     for code in codes:
    #         val = URLValidator()
    #         try:
    #             val(str(code))
    #             return_string = '<label><strong>Codigo%s</strong></label><a  target="_blank" href="%s">%s</a><br>' % (str(i),str(code), str(code)) + return_string
    #         except ValidationError, e:
    #             return_string = '<label><strong>Codigo%s</strong></label><span>%s</span><br>' % (str(i),str(code)) + return_string
    #         i = i + 1
    #     return return_string

    # qr_code.allow_tags = True
    # qr_code.short_description = "Codigos en comprobante del Solicitante"


    #exclude=("nombre ",)

    inlines =(InmuebleInline,)

    def save_model(self, request, obj, form, change):
        if form.has_changed() and form.is_valid():
            for data in form.changed_data:

                if data == 'aprobado' and obj.aprobado: # IF 'APROBADO' FIELD IS CHANGED TO APPROVED STATE
                    #subject = 'Su Condominio ha sido aprodado'
                    #message = 'Estimado(a) %s, Su Condominio ha sido aprobado por nuestros analistas! Bienvenido a CondominioAlDia; ahora puede disfrutar de todos nuestros servicios!' %(obj.user.first_name)
                    #subject = _("Your condominium has been approved")
                    subject = loader.render_to_string('account/email/condo_approved_subject.txt', {})
                    message = loader.render_to_string('account/email/condo_approved_message.txt', {'name' : obj.user.first_name, 'site_name': get_current_site(request).name})
                    #message = _("Dear %s, your condominium has been approved by our analysts!, welcome to %s; now you can enjoy our services." %(obj.user.first_name, get_current_site(request).name ) ) 
                    fromEmail = str(settings.DEFAULT_FROM_EMAIL)
                    emailList = [ obj.user.email ]
                    send_email.delay(subject, message, fromEmail, emailList, fail_silently = False )
                    obj.fecha_aprobacion = timezone.now()
                    obj.save()
                elif data =='aprobado' and not obj.aprobado:
                    razon_rechazo =  request.POST.get('razon_rechazo')
                    obj.razon_rechazo = str(razon_rechazo)
                    # subject = 'Ooops!, Su Condominio ha sido rechazado'
                    # message = 'Estimado(a) %s, Lamentamos informarle que su condominio ha sido rechazado. La razon de acuerdo a nuestros analistas es: %s. Puede intentar de registrarse nuevamente. Gracias por su paciencia!' %( obj.nombre, obj.razon_rechazo)
                    subject = _('Oops your condominium was not approved')
                    message = _('Dear '+obj.nombre+', we regret to inform you that your condominium was not approved. The reason is: '+ obj.razon_rechazo +'. You may try to register again!')
                    fromEmail = str(settings.DEFAULT_FROM_EMAIL)
                    emailList = [ obj.user.email ]     
                    send_email.delay(subject, message, fromEmail, emailList, fail_silently = False )
                    obj.user.delete()

        super(CondominioAdmin, self).save_model(request, obj, form, change)   
admin.site.register(Condominio, CondominioAdmin)

class TalonarioAdmin( admin.ModelAdmin ):
    # def user_instance(self, obj):
    #     return 'Id: '+ str(obj.user.pk)  + ' - ' + str(obj.user.first_name) + ' ' + str(obj.user.last_name)
    # def first_name(self, obj):
    #     return smart_unicode(obj.user.first_name)
    # def last_name(self, obj):
    #     return smart_unicode(obj.user.last_name)
    #user_instance.short_description = 'user_instance'
    search_fields = ['id','nro_control_desde', 'nro_control_hasta' ]
    list_filter = ('pais',)  
    # save_on_top = True
    form = TalonarioForm
    #readonly_fields = ('user_instance', 'first_name', 'last_name', 'mobile_number', 'office_number', 'profile_picture', 'company_name',)
    #fields = [ 'user_instance', 'first_name', 'last_name','company_name',  'profile_picture', 'mobile_number', 'office_number' ]
    list_display = ['id','pais','nro_control_desde','nro_control_hasta', 'created']
admin.site.register( Talonario, TalonarioAdmin )

# class Social_LinkAdmin( admin.ModelAdmin ):
#     #inlines = (Payment_MethodInline,)
#     # def user_instance(self, obj):
#     #     return 'Id: '+ str(obj.user.pk)  + ' - ' + str(obj.user.first_name) + ' ' + str(obj.user.last_name)
#     # def first_name(self, obj):
#     #     return smart_unicode(obj.user.first_name)
#     # def last_name(self, obj):
#     #     return smart_unicode(obj.user.last_name)
#     #user_instance.short_description = 'user_instance'
#     # search_fields = ['=id', 'condominio__rif', ]
#     # list_filter = ('timestamp', 'fechafacturacion',)  
#     # save_on_top = True
#     # form = Egresos_Condominio_Form
#     #readonly_fields = ('user_instance', 'first_name', 'last_name', 'mobile_number', 'office_number', 'profile_picture', 'company_name',)
#     #fields = [ 'user_instance', 'first_name', 'last_name','company_name',  'profile_picture', 'mobile_number', 'office_number' ]
#     list_display = ['id', 'name', 'link','active']
# admin.site.register( Social_Link, Social_LinkAdmin )