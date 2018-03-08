# -*- coding: utf-8 -*-
import decimal
import os
from django.db.models import Q, Sum
from condominioaldia_app.managers import (
    InmuebleManager, 
    EgresosCondominioManager,
    Factura_CondominioManager,
    TalonarioManager,
    IngresosCondominioManager,
    BancosManager,
    Cobranza_CondominioManager,
    Pago_CondominioManager,
)
from condominioaldia_app.utils import condominio_activator, month_range_dt
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import DEFERRED
from django.utils import timezone
from django.contrib.auth.models import User
from dateutil.relativedelta import relativedelta
from django.utils.translation import gettext, gettext_lazy as _
from django.core.files.storage import default_storage
from django.db.models.signals import post_delete, pre_delete, post_save, pre_save
from condominioaldia_app.signals_methods import (
    email_owner,
    user_deleted,
    condo_payment_saved,
    factura_condo_extra_col_update_account_balance,
    condo_account_initial_balance,
    post_recipiente_name,
)

from validators import *
from upload_paths import *
from django.utils.encoding import smart_unicode
from django.conf import settings


# Create your models here.
def clean_media(model ,attribute_name):
    '''
    This method cleans assigned files from the file system
    '''
    try:
        original_values= getattr(model, '_loaded_values')
        if getattr(model, attribute_name) == '' or getattr(model, attribute_name) == None:
            default_storage.delete(original_values[attribute_name])

        elif os.path.basename(getattr(model, attribute_name).path) != os.path.basename(original_values[attribute_name]):
            default_storage.delete(original_values[attribute_name])
        elif os.path.basename(getattr(model, attribute_name).path) == os.path.basename(original_values[attribute_name]):
            pass
    except:
        pass


def get_user_type(self):
    if self.is_staff:
        return 'staff'
    try:
        condominio_pk= self.condominio.pk
        return 'condominio'
    except:
        pass

    try:
        inquilino_pk= self.inquilino.pk
        return 'inquilino'
    except:
        pass

    try:
        affiliate_pk= self.affiliate.pk
        return 'affiliate'
    except:
        pass
    return None

def get_full_name(self):
    return (str(self.first_name) + ' ' + str(self.last_name))

def clean(self):
    user  =  User.objects.filter(email = self.email)
    if user.exists():
        self.errors ={}
        self.errors['email']=str(_('This email already exists.'))
        raise ValidationError(self.errors)


User.add_to_class("__str__", get_full_name)
User.add_to_class("clean", clean)
User.add_to_class("get_user_type", get_user_type)
pre_delete.connect(user_deleted, sender = User, dispatch_uid="condo_delete_files")



class Condominio(models.Model):
    user = models.OneToOneField(User, on_delete = models.CASCADE, null = True, verbose_name = _('user'))
    inquilinos = models.ManyToManyField('Inquilino', through = 'Inmueble')
    # REGULAR MODEL FIELDS
    rif = models.CharField( max_length = 16, primary_key = True, unique = True, blank = False, verbose_name = _('Fiscal number') )
    pais = models.ForeignKey('Paises', null = False, verbose_name = _('country'))
    estado = models.CharField( max_length = 40, null = False, default = '', blank = False,verbose_name = _('state' ))
    municipio = models.CharField( max_length = 40, null = True, default = '', blank = False, verbose_name = _('municipality') )
    parroquia = models.CharField( max_length = 40, null = True, default = '', blank = True,verbose_name = _('parish') )
    direccion = models.CharField( max_length = 200, null = False, verbose_name = _('address') )
    telefono1 = models.CharField( max_length = 15,  blank=True, null = True, verbose_name = _('phone 1') )
    telefono2 = models.CharField( max_length = 15,  blank=True, null=True, verbose_name = _('phone 2') )
    aprobado = models.NullBooleanField( default = None, verbose_name = _('Approved') )
    fecha_aprobacion = models.DateTimeField( auto_now_add = True, auto_now = False, null = True, verbose_name = _('Approval date') )
    comprobante_rif = models.ImageField( upload_to = upload_comprobante_rif, default='', null=False, blank= True, help_text=_('You must select a file'), verbose_name = _('fiscal number image'))
    logo = models.ImageField( upload_to = upload_logo_function, null = True, blank= True)
    terminos = models.BooleanField(null = False, default = False, verbose_name = _('Terms'))
    activo  = models.BooleanField(default = False, help_text =_("Condominiums will be deactivated when percentage falls below %s" %(settings.MINIMA_ALICUOTA)))
    razon_rechazo = models.CharField(max_length=1000, blank = True, null = True, default = "", verbose_name = _('Rejection cause'))
    comission = models.DecimalField(default = settings.COMISSION, verbose_name = _('service charge'), null = False, blank = False, decimal_places = 4, max_digits= 50)
    retrasado = models.BooleanField(default = False)
    affiliate =models.ForeignKey('Affiliate', null = True, blank = True, related_name='condominios')
    fast_help_popup =models.BooleanField(default=True)
    demo_mode = models.BooleanField(default = False)
    @classmethod
    def from_db(cls, db, field_names, values):
        # Default implementation of from_db() (subject to change and could
        # be replaced with super()).
        if len(values) != len(cls._meta.concrete_fields):
            values = list(values)
            values.reverse()
            values = [
                values.pop() if f.attname in field_names else DEFERRED
                for f in cls._meta.concrete_fields
            ]
        instance = cls(*values)
        instance._state.adding = False
        instance._state.db = db
        # customization to store the original field values on the instance
        instance._loaded_values = dict(zip(field_names, values))
        return instance

    class Meta:
        unique_together = ("rif", "pais")

    def image_tag(self):
        return u'<img src="/media/%s" />' % self.comprobante_rif
    image_tag.short_description = 'Image'
    image_tag.allow_tags = True

    def save(self, *args, **kwargs):
        clean_media(self ,'logo')
        clean_media(self ,'comprobante_rif')
        super(Condominio, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        try:
            default_storage.delete(self.comprobante_rif.path)
        except: 
            pass # when new photo then we do nothing, normal case

        #COMPROBANTE RIF
        try:
            default_storage.delete(self.__original_comprobante_rif.path)
        except: 
            pass # when new photo then we do nothing, normal case
        super(Condominio, self).delete(*args, **kwargs)

    #UNICODE RETURN OBJECT
    def __unicode__(self): #__str__ for python 3.3
        return smart_unicode(self.rif)

class Inquilino(models.Model):

    user = models.OneToOneField(User, on_delete = models.CASCADE, null = True, verbose_name = _('User'))
    rif = models.CharField( max_length = 16, unique = True, null = True, blank = True, verbose_name = _('Fiscal number'))
    telefono1 = models.CharField( max_length = 15, default = '', blank = True, null=True, verbose_name = _('Phone 1'))
    telefono2 = models.CharField( max_length = 15, default = '', blank = True, null=True, verbose_name = _('Phone 2'))
    fast_help_popup =models.BooleanField(default=True)

    def __unicode__(self): #__str__ for python 3.3
        return smart_unicode( self.user.first_name + self.user.last_name)

    def save(self, *args, **kwargs):
        self.rif = self.rif or None
        super(Inquilino, self).save(*args, **kwargs)


class Inmueble(models.Model):
    alicuota = models.DecimalField(max_digits=10, decimal_places=4, null = False, blank = True, default = 0, verbose_name = _('percentage representation'))
    arrendado = models.BooleanField(default = False, verbose_name = _('leased'))
    arrendatario = models.CharField( max_length=20, null= True, blank = True, default = '', verbose_name = _('Tenant') )
    balanceinicial = models.DecimalField(max_digits=50, decimal_places=4, null = True, blank = True, default = 0, verbose_name = _('initial balance'))
    cargo = models.CharField( max_length=20, null= True, blank = True, verbose_name = _('board position') )
    condominio = models.ForeignKey('Condominio', null = True, on_delete= models.CASCADE, verbose_name = _('Condominium'))
    deuda_actual = models.DecimalField(max_digits=25, decimal_places=4, null = False, blank = False, default = 0, verbose_name = _('current debt'))
    inquilino = models.ForeignKey('Inquilino', null = True, related_name = _('owner'))
    nombre_inmueble = models.CharField(max_length=20, verbose_name=_('Property name'), null= True, help_text = 'House number or name; apartment number, etc')   
    junta_de_condominio = models.BooleanField( default = False, verbose_name = _('board member') )
    objects = InmuebleManager()
    created = models.DateTimeField(auto_now_add=True, null=True, verbose_name = _('Created'))
    
    class Meta:
        ordering = ['alicuota']

    @property
    def is_orphan(self):#TELLS IF INMUEBLE HAS OWNDER ATTACHED TO IT OR NOT
        if self.inquilino:
            return True
        else:
            return False
    @property
    def propietario(self):#TELLS IF INMUEBLE HAS OWNDER ATTACHED TO IT OR NOT
        try:
            return self.inquilino.user.get_full_name()
        except:
            pass
        return _("No owner assigned")

    def save(self, *args, **kwargs):
        self.nombre_inmueble = self.nombre_inmueble.strip().upper()
        if not self.factura_propietario_set.all().exists():
            self.deuda_actual=self.balanceinicial
        super(Inmueble, self).save(*args, **kwargs)
        condominio_activator( self.condominio)
        

    def delete(self, *args, **kwargs):
        condominio_activator(self.condominio)
        super(Inmueble, self).delete(*args, **kwargs)

    def __unicode__(self):
        return smart_unicode(self.nombre_inmueble )

class Paises(models.Model):
    nombre =  models.CharField( max_length = 80, null=False, blank = False, primary_key = True, unique = True, verbose_name = _('country name') )
    moneda  = models.CharField( max_length = 80, null=False, blank = False, verbose_name = _('Currency') )
    activo = models.BooleanField( default = False, verbose_name = _('Active') )
    nombre_registro_fiscal = models.CharField( max_length = 80, null=False, blank = False, help_text= _('Fiscal number acronym') )
    rif_regex = models.CharField( max_length = 80, null=False, blank = False, verbose_name = _('fiscal number rexex'), help_text = "^[JEGVjegv][0-9.,$;]+$ for Venezuelan fiscal number input validation" )
    rif_placeholder= models.CharField(max_length = 80, null=False, blank = False, verbose_name = _('placeholder text'))
    rif_format = models.CharField(max_length = 80, null=False, blank = False, verbose_name = _('Fiscal number format'))
    iva = models.DecimalField(max_digits=50, decimal_places=4, verbose_name=_('sales tax'))
    razon_social =  models.CharField( max_length = 80, null=False, blank = False, verbose_name = _('company name') )
    rif_empresa = models.CharField( max_length = 80, null=False, blank = False, verbose_name = _('company fiscal number') )
    address= models.TextField( max_length = 1000, null=False, blank = False, verbose_name = _('company address') )
    state= models.CharField( max_length = 80, null=False, blank = False, verbose_name = _('company state') )
    city = models.CharField( max_length = 80, null=False, blank = False, verbose_name = _('company city') )
    zip_code = models.CharField( max_length = 80, null=True, blank = True, verbose_name = _('zip code') )
    email = models.EmailField(null = True, verbose_name = _('E-mail'))
    phone1 = models.CharField( max_length = 15,  blank=True, null = True, verbose_name = _('phone 1') )
    phone2 = models.CharField( max_length = 15,  blank=True, null = True, verbose_name = _('phone 2') )

    class Meta:
        verbose_name = _('Country')
        verbose_name_plural = _('Countries')

    #UNICODE RETURN OBJECT
    def __unicode__(self): #__str__ for python 3.3
        return smart_unicode(self.nombre)

class Paginas_Amarillas(models.Model):
    condominio = models.ForeignKey(Condominio, null = False, verbose_name = _('condominium'))
    oficio = models.CharField(max_length=40, null=False, blank = False, verbose_name = _('Job title'))
    nombre = models.CharField(max_length=40, null=False, verbose_name = _('Name'))
    mobil= models.CharField(max_length=15, default='', blank=True, null=True, verbose_name = _('Mobile'))
    fijo = models.CharField(max_length=15, default='', blank=True, null=True, verbose_name = _('Office number'))
    email = models.EmailField(null = True, verbose_name = _('E-mail'))
    class Meta:
        verbose_name = _('Yellow page')
        verbose_name_plural = _('Yellow pages')

    #UNICODE RETURN OBJECT
    def __unicode__(self): #__str__ for python 3.3
        return smart_unicode(self.oficio)


class Faq(models.Model):
    pregunta= models.TextField( max_length = 1000, null=False, blank = False, verbose_name = _('question') )
    respuesta= models.TextField( max_length = 1000, null=False, blank = False, verbose_name = _('answer') )
    class Meta:
        verbose_name = _('Faq')
        verbose_name_plural = _("Faq's")

    #UNICODE RETURN OBJECT
    def __unicode__(self): #__str__ for python 3.3
        return smart_unicode(self.id)

class Banco_Pais(models.Model):
    ##BANKS WHERE CONDOS CAN DEPOSIT
    pais = models.ForeignKey(Paises, null = False, verbose_name = _('country'))
    name = models.CharField(max_length=250, null= False,verbose_name = _('name'))
    bank_code = models.CharField(max_length=250, null= True,verbose_name = _('bank_code'))
    pre_fill_prefix =models.CharField(max_length=250, null= True,verbose_name = _('pre_fill_prefix'))
    swift = models.CharField(max_length=250, null= True,verbose_name = _('swift'))
    iban = models.CharField(max_length=250, null= True,verbose_name = _('iban'))
    def __unicode__(self): #__str__ for python 3.3
        return smart_unicode(self.name)
    class Meta:
        verbose_name = _('Bank')
        verbose_name_plural = _("Banks")
        ordering = ['name']

class Bancos(models.Model):
    ##CONDO BANK ACCOUNTS
    condominio = models.ForeignKey(Condominio, null = False, verbose_name = _('condominium'))
    titular =  models.CharField(max_length = 50, null = True, verbose_name = _('account owner'))
    nro_cuenta = models.CharField(max_length = 20, null = False, default = '', verbose_name = _('Acount number') )
    banco = models.CharField(max_length = 200, null = False, blank = True, verbose_name = _('bank'))
    banco_pais = models.ForeignKey(Banco_Pais, null = False, related_name="accounts")
    informacion_adicional = models.CharField(max_length = 150, null = True, verbose_name = _('aditional information'))
    balance = models.DecimalField(max_digits=50, decimal_places=4, null = False, blank = False, default = 0, verbose_name = _('balance'))
    balanceinicial = models.DecimalField(max_digits=50, decimal_places=4, null = False, blank = False, default = 0, verbose_name = _('balance'))
    fecha_balance_inicial = models.DateTimeField(null= False, verbose_name = _('initial balance date'))
    editable = models.BooleanField(default=True, verbose_name =_("editable"))
    objects = BancosManager()
    def __unicode__(self): #__str__ for python 3.3
        return smart_unicode(self.banco)
    class Meta:
        unique_together =('banco_pais', 'banco',)
        verbose_name = _('Condominium bank account')
        verbose_name_plural = _("Condominium bank accounts")

    # def save(self, *args, **kwargs):
    #     created =self.id ==None
    #     #if self.aprobado ==True:
    #     if created:
    #         self.banco=self.banco_pais.name
    #         self.balance=self.balanceinicial
    #     elif self.editable==True:
    #         #print self.egreso_condominio_set.all()
    #         #print self.ingreso_condominio_set.filter(aprobado=True)
    #         ingresos=self.ingreso_condominio_set.filter(aprobado=True).aggregate(total_mes= Sum('monto'))['total_mes'] or 0
    #         egresos =self.condominio.ingreso_condominio_set.all().aggregate(total_mes= Sum('monto'))['total_mes'] or 0
    #         self.balance = self.balanceinicial-egresos+ingresos
    #     super(Bancos, self).save(*args, **kwargs)
#post_save.connect(condo_account_initial_balance, sender = Bancos, dispatch_uid="condo_account_initial_balance")

class BancosCondominioaldia(models.Model):
    ##BANKS WHERE CONDOS CAN DEPOSIT
    pais = models.ForeignKey(Paises, null = False, verbose_name = _('country'))
    titular =  models.CharField(max_length = 50, null = True, verbose_name = _('account owner'))
    nro_cuenta = models.CharField(max_length = 20, null = False, default = '', verbose_name = _('Acount number') )
    banco = models.CharField(max_length = 200, null = False, blank = True, verbose_name = _('bank'))
    informacion_adicional = models.CharField(max_length = 150, null = True, verbose_name = _('aditional information'), blank= True)
    def __unicode__(self): #__str__ for python 3.3
        return smart_unicode(self.banco)
    class Meta:
        verbose_name = _('Condominioaldia account')
        verbose_name_plural = _("Condominioaldia accounts")


class Cartelera(models.Model):
    condominio = models.ForeignKey(Condominio, null = False,verbose_name = _('condominium'))
    titulo = models.CharField(max_length = 100, null = True, verbose_name = _('title'))
    descripcion = models.TextField(max_length = 5000, null = True, verbose_name = _('description'))
    created = models.DateTimeField(auto_now_add=True, null=True, verbose_name = _('Created'))
    class Meta:
        verbose_name = _('Announcement')
        verbose_name_plural = _('Announcements')
    def __unicode__(self): #__str__ for python 3.3
        return smart_unicode(self.titulo)


class Ingreso_Condominio(models.Model):
    ingreso_choices = (
        ('pp', _('Owner payment')),
        ('po', _('Normal income')),
        ('Reembolso', _('Refund')),
        ('cobranza', _('Charges/Penalties')),
        ('Intereses', _('Interest')),
    )
    listado_de_pagos = (
        ('Dep/Trans', 'Dep/Trans'),
        ('Instapago', 'Instapago'),
    )
    CHOICES = (
        (None, _("Not evaluated")),
        (True, _("Approved")),
        (False, _("Rejected")),
    )
    #__original_cierre_status = None

    banco_cheque = models.ForeignKey(Banco_Pais, null=True)
    banco =models.ForeignKey(Bancos, null = False)
    condominio = models.ForeignKey(Condominio)
    inmueble = models.ForeignKey( 'Inmueble', on_delete = models.SET_NULL, null = True, verbose_name = _('Property'))
    posted_by = models.ForeignKey(User, null = True, verbose_name = _('Posted by'))
    fecha_facturacion = models.DateTimeField(null= False, verbose_name = _('bill date'))
    aprobado = models.NullBooleanField( default = None, choices = CHOICES, verbose_name= _('Payment status') )
    arrendatario = models.CharField(max_length = 200, null = True, default= None, verbose_name = _('Tenant'))
    banco_dep = models.CharField(max_length = 100, null = True, default= None, verbose_name = _('Credited bank'))
    cerrado = models.BooleanField(default = False, help_text = _('This field states wheter the month is no longer editable'), verbose_name = _('Period closed'))
    comprobante_pago = models.FileField(upload_to = upload_pagos_inquilino, null=True, blank= True, verbose_name = _('Proof'))
    created = models.DateTimeField(auto_now_add= True, auto_now= False, null = True, verbose_name = _('Payment date'))
    cuenta_dep = models.CharField(max_length = 100, null = True, default= None, verbose_name = _('Credited account'))
    detalles = models.CharField( max_length=200, null = True, blank  = True, verbose_name = _('Details') )
    fecha_cierre = models.DateTimeField( null= True, verbose_name = _('Close date'))
    mes = models.DateTimeField( null= False, verbose_name = _('bill date'), help_text=_("This represents the monthly period")) 
    monto = models.DecimalField( max_digits=50, decimal_places=4, verbose_name = _("amount"), null=False )
    nro_cheque = models.CharField(max_length = 100, null = True, default= None, verbose_name = _('Check Number'))
    nro_referencia =  models.CharField(max_length=50, null = True, blank = True, verbose_name = _('Reference number'))
    pagador = models.CharField(max_length= 250, null = True, verbose_name = _('Payer name'))
    razon_rechazo = models.CharField(max_length=250, blank = True, null = True, default = "", verbose_name =_('Rejection reason'))
    rif_pagador = models.CharField( max_length = 16, blank = False, verbose_name = _('Payer fiscal number') )
    tipo_de_ingreso = models.CharField(null = False, blank = False, choices = ingreso_choices, max_length= 50, verbose_name = _('Income type'))
    tipo_de_pago = models.CharField( max_length = 60, choices = listado_de_pagos, null = False, blank = False, default='Dep/Trans')
    objects = IngresosCondominioManager()

    class Meta:
        verbose_name = _('Condominium Income')
        verbose_name_plural = _('Condominium Incomes')
        ordering = ['-fecha_facturacion']

    @property
    def propietario(self):#TELLS IF INMUEBLE HAS OWNDER ATTACHED TO IT OR NOT
        try:
            return self.inmueble.inquilino.user.get_full_name()
        except:
            pass
        return self.pagador

    @classmethod
    def from_db(cls, db, field_names, values):
        # Default implementation of from_db() (subject to change and could
        # be replaced with super()).
        if len(values) != len(cls._meta.concrete_fields):
            values = list(values)
            values.reverse()
            values = [
                values.pop() if f.attname in field_names else DEFERRED
                for f in cls._meta.concrete_fields
            ]
        instance = cls(*values)
        instance._state.adding = False
        instance._state.db = db
        instance._loaded_values = dict(zip(field_names, values))
        return instance

    def save(self, *args, **kwargs):
        created =self.id ==None
        if self.aprobado ==True:
            if created:
                self.banco.balance +=self.monto
                self.banco.save()
            else:
                previously_approved = self._loaded_values['aprobado']
                if not previously_approved:
                    self.banco.balance +=self.monto
                    self.banco.save()
                    #mark any cobranza as closed or non editable
                    month_range = month_range_dt(self.mes)
                    self.inmueble.cobranza_condominio_set.filter(cobranza_condominio_destinatario__payment= self).update(editable= False)
        
        clean_media(self ,'comprobante_pago')
        super(Ingreso_Condominio, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.banco.balance -=self.monto
        self.banco.save()

        try:
            default_storage.delete(self.comprobante_pago.path)
        except: 
            pass # when new photo then we do nothing, normal case


        super(Ingreso_Condominio, self).delete(*args, **kwargs)

    def image_tag(self):
        return u'<img src="/media/%s" />' % self.comprobante_pago
    image_tag.short_description = _('Image')
    image_tag.allow_tags = True

    def __unicode__(self): #__str__ for python 3.3
        return smart_unicode(self.id)

#pre_delete.connect(ingreso_deleted, sender = User, dispatch_uid="ingreso_deleted")


class Cobranza_Condominio_Destinatario(models.Model):
    cobranza_condominio = models.ForeignKey('Cobranza_Condominio')
    inmueble = models.ForeignKey('Inmueble')
    payment = models.OneToOneField('Ingreso_Condominio', null=True, verbose_name=_("payment"), related_name ="cobranza_condominio")
    deuda_inmueble  = models.DecimalField( max_digits=50, decimal_places=2, verbose_name = _("amount"), null=True )


class Cobranza_Condominio(models.Model):
    tipo_pago_choices = (
        ('porcEgresos', _("Percentage of expenses")),
        ('monto', _("amount")),
        ('porAlicuota', _("by alicuote")),
    )
    tipo_recurrencia_choices = (
        ('una', _("one-time")),
        ('mensual', _("monthly")),
    )   
    tipo_cobrar_cuando_choices = (
        ('inmediato', _("charge-now")),
        ('relacion', _("show in next bill")),
    ) 
    editable = models.BooleanField(default=True)
    destinatario = models.ManyToManyField(Inmueble, through = Cobranza_Condominio_Destinatario)
    recipiente = models.CharField(max_length=250, null = True, blank= True,verbose_name = _("recipient"))
    tipo_monto = models.CharField(max_length=25,choices = tipo_pago_choices, null= False)
    monto = models.DecimalField( max_digits=50, decimal_places=2, verbose_name = _("amount"), null=True )
    porcentaje = models.DecimalField( max_digits=50, decimal_places=4, verbose_name = _("amount"), null=True )
    recurrencia = models.CharField(max_length=25,choices = tipo_recurrencia_choices, null= False)
    cobrar_cuando = models.CharField(max_length=25,choices = tipo_cobrar_cuando_choices, null= False)
    #inmueble = models.ForeignKey(Inmueble, null=False, verbose_name=_("property"))
    condominio = models.ForeignKey(Condominio,null = False)
    created = models.DateTimeField(auto_now_add= True, auto_now= False, null = True, verbose_name = _('Payment date'))
    #payment = models.OneToOneField(Ingreso_Condominio, null=True, verbose_name=_("payment"), related_name ="cobranza_condominio")
    asunto = models.CharField(max_length=250, null= False, verbose_name=_("subject"))
    objects = Cobranza_CondominioManager()
    category = models.ForeignKey('InmuebleCategory', null =True, default = None)
    mes = models.DateTimeField(null = False, blank = True, verbose_name = _('cobranza date'), help_text=_("This represents the monthly period"))
    class Meta:
        verbose_name = _('Condominium payment order')
        verbose_name_plural = _('Condominium payment orders')
        ordering = ['-created']
        #unique_together=(("asunto", "restaurant"),)

    def __unicode__(self): #__str__ for python 3.3
        return smart_unicode(self.id)  

    def save(self, *args, **kwargs):
        self.asunto = self.asunto.strip().lower().title()
        super(Cobranza_Condominio, self).save(*args, **kwargs)

#post_save.connect(email_owner, sender = Cobranza_Condominio, dispatch_uid="email_owner_signal")


class Tipos_Egresos(models.Model):
    nombre = models.CharField(max_length=250, null= False,verbose_name = _('Name'), primary_key = True)
    created = models.DateTimeField(auto_now_add= True, auto_now= False, verbose_name = _('Created'))
    pais = models.ForeignKey(Paises, null= False)
    def __unicode__(self): #__str__ for python 3.3
        return smart_unicode(self.nombre) 

class Messages(models.Model):
    choices = (
        ('TP',_('Every property')),
        ('PSD',_('Debt free propierties')),
        ('PCD',_('Properties with debt')),
        ('PP',_('Particular property')),
        ('JC',_('Board members')),
        ('NBM',_('Exclude board members')),
    )
    created = models.DateTimeField(auto_now_add= True, auto_now= False, verbose_name = _('Created'))
    email = models.BooleanField(default= False)
    message = models.CharField(max_length=145, null= False,verbose_name = _('message'))
    recipient = models.ManyToManyField(User, verbose_name= _('recipient'), related_name =_('recipient'))
    recipient_desc = models.CharField(choices= choices,max_length=145, null= True, blank=True, verbose_name = _('recipient description'), help_text=_('Whom the message was intented for?'))
    sender = models.ForeignKey(User, null = False, verbose_name= _('sender'), related_name =_('sender'))
    sender_type = models.CharField( null = False, blank = False, max_length = 50)
    sms = models.BooleanField(default= False)
    subject = models.CharField(max_length=50, null= False,verbose_name = _('subject'))
    class Meta:
        verbose_name = _('message')
        verbose_name_plural = _('messages')
    def __unicode__(self): #__str__ for python 3.3
        return smart_unicode(self.subject) 

class Egreso_Condominio(models.Model):
    #__original_cierre_status = None
    EGRESO_TYPE_CHOICES = (
        ('todos', _('All owners')),
        ('particular', _('Particular owners')),
    )
    deudores = models.CharField(choices= EGRESO_TYPE_CHOICES, max_length = 50, blank = True, null = True, default = 'todos', verbose_name =_("debtors"))
    id = models.AutoField( verbose_name = _("Reference number"), primary_key = True )
    created = models.DateTimeField(auto_now_add= True, auto_now= False, verbose_name = _('Created'))
    condominio = models.ForeignKey(Condominio, null = True, on_delete = models.CASCADE)
    monto = models.DecimalField(max_digits= 65, decimal_places=4, null = False )
    #FECHA FACTURACION ES MES
    mes = models.DateTimeField(null = True, blank = True, verbose_name = _('Bill date'), help_text=_("This represents the monthly period"))
    detalles = models.CharField(max_length=250, null= False, default = 'details')
    cerrado = models.BooleanField( default = False, verbose_name = _('closed') )
    fecha_cierre = models.DateTimeField( null = True, default = None,verbose_name = _('Cutoff date') )
    fecha_facturacion = models.DateTimeField(null= False, verbose_name = _('bill date'))
    nro_factura = models.CharField(max_length=250, null= True, blank = True, default = '', verbose_name = _('Invoice number'))
    tipo_egreso = models.ForeignKey(Tipos_Egresos, null = False, verbose_name = _('expense type'))
    banco = models.ForeignKey(Bancos, null = False)
    objects = EgresosCondominioManager()
    class Meta:
        verbose_name = _('Condominium expense')
        verbose_name_plural = _('Condominium expenses')

    @classmethod
    def from_db(cls, db, field_names, values):
        # Default implementation of from_db() (subject to change and could
        # be replaced with super()).
        if len(values) != len(cls._meta.concrete_fields):
            values = list(values)
            values.reverse()
            values = [
                values.pop() if f.attname in field_names else DEFERRED
                for f in cls._meta.concrete_fields
            ]
        instance = cls(*values)
        instance._state.adding = False
        instance._state.db = db
        instance._loaded_values = dict(zip(field_names, values))
        return instance

    def save(self, *args, **kwargs):
        created =self.id ==None
        if created:
            self.banco.balance -=self.monto
            self.banco.save()
        else:
            if self._loaded_values['banco_id'] ==self.banco.id:
                self.banco.balance -=self.monto-self._loaded_values['monto']
            else:
                #add balance from old bank
                prev_banco = Bancos.objects.get(pk=self._loaded_values['banco_id'])
                prev_banco.balance +=self._loaded_values['monto']
                prev_banco.save()
                #subtract balance from new bank
                self.banco.balance -=self.monto
            self.banco.save()
        super(Egreso_Condominio, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.banco.balance +=self.monto
        self.banco.save()
        super(Egreso_Condominio, self).delete(*args, **kwargs)

    def __unicode__(self): #__str__ for python 3.3
        return smart_unicode(self.id)


class Poll(models.Model):
    question = models.CharField(max_length=200)
    condominio = models.ForeignKey( Condominio, null = True, on_delete= models.CASCADE )
    created = models.DateTimeField( auto_now_add=True, auto_now= False, null = True )
    ballot_close_timestamp = models.DateTimeField( null = True )
    start = models.DateTimeField( null = True, default = None )
    end = models.DateTimeField( null = True, default = None )
    details = models.CharField( max_length = 200, null = False, blank = True )
    active = models.BooleanField( default = True)
    votes = models.IntegerField(default=0, null= False, blank = True)
    def __unicode__(self):  # Python 3: def __str__(self):
        return self.question

class Poll_Result( models.Model ):
    aye = models.IntegerField( null = True, default = 0 )
    nay = models.IntegerField( null = True, default = 0 )
    poll = models.OneToOneField( Poll, on_delete = models.CASCADE, null = False )
    created = models.DateTimeField(auto_now_add=False, auto_now= True, null = True)

class Poll_Vote( models.Model ):#this is created when the resident has voted
    inmueble = models.ForeignKey( Inmueble )
    result = models.ForeignKey( Poll_Result )
    poll = models.ForeignKey( Poll, related_name ='poll_votes' )
    created = models.DateTimeField( auto_now_add = True )


class Factura(models.Model):
    cantidad = models.IntegerField(default=0, null= False, blank = True, verbose_name =_("quantity"))
    created = models.DateTimeField( auto_now_add=True, auto_now= False, null = True, verbose_name =_("created") )
    nro_control = models.IntegerField(default=0, null= True, blank = True, verbose_name =_("control number"))
    nro_control_desde = models.IntegerField(default=0, null= True, blank = True,verbose_name =_("control number begin"))
    nro_control_hasta = models.IntegerField(default=0, null= True, blank = True, verbose_name =_("control number end"))
    rif = models.CharField(max_length= 15, null = True, verbose_name =_("fiscal number"))
    razon_social = models.CharField(max_length= 50, null = True, verbose_name =_("payer name"))
    sub_total = models.DecimalField( max_digits= 50, decimal_places=4, verbose_name =_("sub-total"), default =0, null= True )#
    iva =  models.DecimalField( max_digits= 50, decimal_places=4, verbose_name =_("sales tax"), default =0, null= True )#
    monto = models.DecimalField( max_digits= 50, decimal_places=4, verbose_name =_("amount"), default =0, null= False )

    class Meta:
        verbose_name = _('bill')
        verbose_name_plural = _('Bills')
        abstract = True



class Talonario(models.Model):
    pais= models.ForeignKey(Paises, null= True, on_delete = models.SET_NULL, blank = False)
    nro_control_desde = models.IntegerField(default=0, null= True, blank = True,verbose_name =_("control number begin"))
    nro_control_hasta = models.IntegerField(default=0, null= True, blank = True, verbose_name =_("control number end"))
    created = models.DateTimeField(auto_now_add=True, null=True, verbose_name = _('Created'))
    #objects =TalonarioManager()
    class Meta:
        verbose_name = _('Receipt book')
        verbose_name_plural = _('Receipt books')
        ordering = ['nro_control_desde']

    def __unicode__( self ): #__str__ for python 3.3
        return smart_unicode( self.id )



class Factura_Condominio(Factura):
    choices = (
        ('service_fee', _('condominium service fee')),
        #('Credit Card', _('Credit Card')),
        # ('Reembolso', _('Refund')),
        # ('Cobranza de multa', _('Penalty charge')),
        # ('Intereses', _('Interest')),
    )
    tipo_de_factura = models.CharField( default= 'service_fee',choices=choices,null = False, max_length = 250, verbose_name= _('name')  )
    talonario = models.ForeignKey(Talonario, null = True, verbose_name =_('checkbook bills'), on_delete = models.SET_NULL)
    condominio = models.ForeignKey( Condominio, null = True, on_delete = models.SET_NULL, verbose_name =_("condominium") )
    descripcion= models.CharField(max_length= 250, null = True, verbose_name =_("description"))
    mes = models.DateTimeField(null = True, blank = True, verbose_name =_("month") )
    pagado = models.BooleanField( default = False, null = False, verbose_name =_("Payed by condominium") )
    objects = Factura_CondominioManager()
    demo_mode = models.BooleanField( default = False, help_text=_("Determines if Condominium will be charged.") )
    class Meta:
        verbose_name = _('condominium invoice')
        verbose_name_plural = _('condominium invoices')

    def __unicode__( self ): #__str__ for python 3.3
        return smart_unicode( self.id )

class Factura_Propietario(Factura):
    deuda_previa = models.DecimalField(max_digits = 50, decimal_places=4, null = False, default= 0, verbose_name =  _('previous balance'))
    pagos = models.DecimalField(max_digits = 50, decimal_places = 4, null = False, default = 0,  verbose_name = _('payments'))
    inmueble = models.ForeignKey('Inmueble', null = True, on_delete = models.SET_NULL )
    condominio = models.ForeignKey(Condominio, null = False, on_delete = models.CASCADE )
    nombre_inmueble=models.CharField( null = False, max_length = 250, verbose_name= _('property')  )
    mes = models.DateTimeField(null = True, blank = True,  verbose_name =_("month") )
    cuota =  models.DecimalField(max_digits = 50, decimal_places=4, null = False)
    deuda_nueva = models.DecimalField(max_digits = 50, decimal_places=4, null = False, default= 0, verbose_name =  _('new balance'))
    cobranzas =models.DecimalField(max_digits = 50, decimal_places=4, null = False, default= 0, verbose_name =  _('payment requests'))
    class Meta:
        verbose_name = _('owner invoice')
        verbose_name_plural = _('owner invoices')

    def __unicode__( self ): #__str__ for python 3.3
        return smart_unicode( self.id )

    def get_cobranzas_for_current_period(self, *args, **kwargs):
        month_range= month_range_dt(self.mes)
        cobranzas = self.inmueble.cobranza_condominio_set.filter(mes__range=(month_range[0],month_range[1]))
        return cobranzas

    def save(self, *args, **kwargs):
        created =self.id ==None
        if created:
            inmueble= self.inmueble
            inmueble.deuda_actual = self.monto
            inmueble.save()
        super(Factura_Propietario, self).save(*args, **kwargs)

class Extra_Column( models.Model ):
    factura = models.ManyToManyField(Factura_Propietario, verbose_name= _('receipt'), related_name='extra_cols' )
    titulo = models.CharField( null = False, max_length = 250, verbose_name= _('title')  )
    monto = models.DecimalField(max_digits=50, decimal_places=4, null = False, default = 0, verbose_name= _('amount') )
    def __unicode__( self ): #__str__ for python 3.3
        return smart_unicode( self.titulo )
    class Meta:
        verbose_name = _('Extra Column')
        verbose_name_plural = _('Extra Columns')

class Factura_Condominio_Extra_Colum( models.Model):
    factura=models.ForeignKey(Factura_Condominio, verbose_name= _('receipt'), related_name='extra_cols' )
    titulo = models.CharField( null = False, max_length = 250, verbose_name= _('title')  )
    monto = models.DecimalField(max_digits=50, decimal_places=4, null = False, default = 0, verbose_name= _('amount') )
    banco = models.ForeignKey(Bancos ,null = False, max_length=200, verbose_name=_('bank') )

    def __unicode__( self ): #__str__ for python 3.3
        return smart_unicode( self.titulo )
    class Meta:
        verbose_name = _('Condo extra quote')
        verbose_name_plural = _('Condo extra quotes')

pre_save.connect(factura_condo_extra_col_update_account_balance, sender = Factura_Condominio_Extra_Colum, dispatch_uid='factura_condo_extra_col_update_account_balance_signal')

class Payment_Method_Detail(models.Model):
    activo = models.BooleanField( default = False,  verbose_name= _('active')  )
    created = models.DateTimeField(auto_now_add=True, null=True, verbose_name = _('Created'))
    metodo_pago = models.ForeignKey('Payment_Method')
    pais= models.ForeignKey(Paises)
    def __unicode__( self ): #__str__ for python 3.3
        return smart_unicode( self.metodo_pago.nombre )
    class Meta:
        verbose_name = _('Payment method for country')
        verbose_name_plural = _("Payment methods for country")
        unique_together = (("metodo_pago", "pais"),)

class Payment_Method(models.Model):
    choices = (
        ('Deposito/Transferencia', _('Deposit-Transfer')),
        ('Credit Card', _('Credit Card')),
        # ('Reembolso', _('Refund')),
        # ('Cobranza de multa', _('Penalty charge')),
        # ('Intereses', _('Interest')),
    )
    nombre = models.CharField( choices=choices,null = False, max_length = 250, verbose_name= _('name')  )
    paises = models.ManyToManyField(Paises, through='Payment_Method_Detail')
    class Meta:
        verbose_name = _('Payment Method')
        verbose_name_plural = _("Payment Methods")
    def __unicode__( self ): #__str__ for python 3.3
        return smart_unicode( self.nombre )

class EntryQuerySet(models.QuerySet):
    def published(self):
        return self.filter(publish= True)

class Blog(models.Model):
    condominio = models.ForeignKey(Condominio, on_delete = models.CASCADE, null = False)
    publisher = models.ForeignKey(User)
    body = models.TextField(max_length = 250)
    #slug = models.SlugField(max_length = 200, unique = True)
    publish  = models.BooleanField(default = True)
    created = models.DateTimeField(auto_now_add= True)
    modified = models.DateTimeField(auto_now= True)
    objects = EntryQuerySet.as_manager()

    def __unicode__( self ): #__str__ for python 3.3
        return smart_unicode( self.publisher )

    class Meta:
        verbose_name = _('Blog Entry')
        verbose_name_plural = _('Blog Entries')
        ordering = ['-created']

class Affiliate(models.Model):
    fast_help_popup =models.BooleanField(default=True)
    comission = models.DecimalField(default=0.1, max_digits=4, decimal_places=2)
    rif = models.CharField( max_length = 16, primary_key = True, unique = True, blank = False, verbose_name = _('Fiscal number') )
    created = models.DateTimeField(auto_now_add= True)
    aprobado = models.NullBooleanField( default = None, verbose_name = _('Approved') )
    user = models.OneToOneField(User, null = True, verbose_name = _('user'), on_delete=models.CASCADE)
    terminos = models.BooleanField(null = False, default = False, verbose_name = _('Terms'))
    url = models.URLField(max_length = 200, unique = True, null = True)
    comprobante_rif = models.ImageField( upload_to = upload_comprobante_rif, default='', null=False, blank= True, help_text=_('You must select a file'), verbose_name = _('fiscal number image'))
    telefono1 = models.CharField( max_length = 15,  blank=True, null = True, verbose_name = _('phone 1') )
    telefono2 = models.CharField( max_length = 15,  blank=True, null = True, verbose_name = _('phone 2') )
    fecha_aprobacion = models.DateTimeField( auto_now_add = True, auto_now = False, null = True, verbose_name = _('Approval date') )
    razon_rechazo = models.CharField(max_length=1000, blank = True, null = True, default = "", verbose_name = _('Rejection cause'))

    def __unicode__( self ): #__str__ for python 3.3
        return smart_unicode( self.user.first_name + ' '+self.user.last_name)

    class Meta:
        verbose_name = _('Affiliate')
        verbose_name_plural = _('Affiliates')
        ordering = ['-created']

class Pagos_Condominio( models.Model ):
    choices = (
        ( None, "Por revisar" ),
        ( True, "Aprobar" ),
        ( False, "Rechazar" )
    )
    aprobado = models.NullBooleanField(default = None, choices = choices,verbose_name=_('approved') )
    banco = models.ForeignKey(Bancos ,null = False, max_length=200, verbose_name=_('bank') )
    comprobante_pago  = models.ImageField( upload_to = upload_pagos_condominio, null = True, blank = True, verbose_name=_('proof')  )
    created = models.DateTimeField(auto_now_add=True, null=True, verbose_name = _('created'))
    factura = models.OneToOneField( Factura_Condominio, null = True, verbose_name=_('bill'), related_name = "pago" )
    fecha_aprobacion = models.DateTimeField( blank = True, null = True, verbose_name=_('approval date')  )
    monto = models.DecimalField( max_digits= 50, decimal_places = 2,verbose_name=_('amount')  )
    nro_referencia = models.CharField( max_length=200, null = True)
    razon_rechazo = models.CharField( max_length=200, blank = True, null = True, default = "",verbose_name=_('rejection reason') )
    tipo_de_pago = models.ForeignKey(Payment_Method_Detail,max_length = 60, null = True, blank = True,verbose_name=_('payment method')  )
    ultima_modificacion = models.DateTimeField( auto_now_add = False, auto_now= True, null = True, blank = True,verbose_name=_('last modified')  )
    egreso = models.OneToOneField(Egreso_Condominio, null= True, verbose_name=_("expense"))
    objects = Pago_CondominioManager()
    class Meta:
        verbose_name = _('condominium payment')
        verbose_name_plural = _('condominium payments')

    def __unicode__( self ): #__str__ for python 3.3
        return smart_unicode( self.id )

    @classmethod
    def from_db(cls, db, field_names, values):
        # Default implementation of from_db() (subject to change and could
        # be replaced with super()).
        if len(values) != len(cls._meta.concrete_fields):
            values = list(values)
            values.reverse()
            values = [
                values.pop() if f.attname in field_names else DEFERRED
                for f in cls._meta.concrete_fields
            ]
        instance = cls(*values)
        instance._state.adding = False
        instance._state.db = db
        # customization to store the original field values on the instance
        instance._loaded_values = dict(zip(field_names, values))
        return instance

    def save(self, *args, **kwargs):
        clean_media(self ,'comprobante_pago')
        #should create a pertaining egreso if the payment has been accepted
        try:
            if self._loaded_values['aprobado'] !=True and self.aprobado ==True:
                tipo_egreso, created =Tipos_Egresos.objects.get_or_create(nombre=_("condominium payment"), pais =self.factura.condominio.pais)
                mes = Factura_Condominio.objects.get_latest_editable_tuple(self.factura.condominio)[0]
                data ={
                    'banco': self.banco,
                    'nro_factura': self.factura.nro_control,
                    'condominio':self.factura.condominio,
                    'monto': self.monto,
                    'mes':mes,
                    'detalles':_("condominium payment of service fee"),
                    'deudores':'todos',
                    'fecha_facturacion': mes,
                    'tipo_egreso': tipo_egreso

                }
                self.egreso = Egreso_Condominio.objects.create(**data)
        except:
            pass
        super(Pagos_Condominio, self).save(*args, **kwargs)

pre_save.connect(condo_payment_saved, sender = Pagos_Condominio, dispatch_uid='condo_payment_signal')

class Affiliate_Banc_Account(models.Model):
    pais= models.ForeignKey(Paises)
    created = models.DateTimeField(auto_now_add= True)
    titular =  models.CharField(max_length = 50, null = True, verbose_name = _('account owner'))
    nro_cuenta = models.CharField(max_length = 20, null = False, default = '', verbose_name = _('Acount number') )
    banco = models.CharField(max_length = 200, null = False, blank = True, verbose_name = _('bank'))
    informacion_adicional = models.CharField(max_length = 150, null = True, verbose_name = _('aditional information'))
    affiliate = models.ForeignKey(Affiliate, verbose_name = _('affiliate'), related_name='bank_accounts')
    class Meta:
        verbose_name = _('Affiliate bank account')
        verbose_name_plural = _('Affiliate bank accounts')

class Affiliate_Income(models.Model):
    CHOICES = (
        ('AP', _('Awaiting payment from condominium')),
        ('PP', _('Preparing payment')),
        ('PA', _('Payed')),
        #('Cobranza de multa', _('Penalty charge')),
        #('Intereses', _('Interest')),
    )
    comission = models.DecimalField(default=0.1, max_digits=4, decimal_places=2)
    monto = models.DecimalField( max_digits=50, decimal_places=2)
    condominio= models.ForeignKey(Condominio, null= True, on_delete= models.SET_NULL)
    condominio_name = models.CharField(max_length=50, null =False)
    affiliate = models.ForeignKey(Affiliate, verbose_name = _('affiliate name'))
    created = models.DateTimeField(auto_now_add= True)
    status = models.CharField(choices = CHOICES, max_length = 100, verbose_name = _('status'), null = False, default = 'AP')
    factura_condominio = models.OneToOneField(Factura_Condominio, null = False, unique= True)
    pagado = models.BooleanField( default = False, verbose_name = _('Affiliate payment issued'),blank = False, help_text=_("This can be checked ONLY after the condominium has payeed the pertaining bill."))
    payment_proof = models.ImageField( upload_to = upload_affiliate_payment, default='', null=True, blank= True, help_text=_('You must select a file'), verbose_name = _('payment proof'))

    def __unicode__( self ): #__str__ for python 3.3
        return smart_unicode( self.id )

    def clean(self):
        self.errors ={}
        if self.pagado == True and self.factura_condominio.pagado == False:
            self.errors['pagado']=str(_('You may only pay comission if the related condominium bill has been payed.'))
            raise ValidationError(self.errors)

    @classmethod
    def from_db(cls, db, field_names, values):
        # Default implementation of from_db() (subject to change and could
        # be replaced with super()).
        if len(values) != len(cls._meta.concrete_fields):
            values = list(values)
            values.reverse()
            values = [
                values.pop() if f.attname in field_names else DEFERRED
                for f in cls._meta.concrete_fields
            ]
        instance = cls(*values)
        instance._state.adding = False
        instance._state.db = db
        # customization to store the original field values on the instance
        instance._loaded_values = dict(zip(field_names, values))
        return instance

    def save(self, *args, **kwargs):
        clean_media(self ,'payment_proof')
        super(Affiliate_Income, self).save(*args, **kwargs)


    class Meta:
        verbose_name = _('Affiliate Income')
        verbose_name_plural = _('Affiliates Income')
        ordering = ['-created']


class Social_Link(models.Model):
    CHOICES = (
        (None, _('--------')),
        ('FB', _('Facebook')),
        ('TW', _('Twitter')),
        ('GOO', _('Google')),
        #('Cobranza de multa', _('Penalty charge')),
        #('Intereses', _('Interest')),
    )
    created = models.DateTimeField(auto_now_add= True, verbose_name=_("created"))
    name = models.CharField(unique= True,choices = CHOICES, max_length = 100, verbose_name = _('name'), null = False, default = 'AP', blank = True)
    link = models.URLField(max_length = 200, unique = True, null = False, verbose_name = _('link'))
    active = models.BooleanField(default=False, verbose_name = _('active'))

    class Meta:
        verbose_name = _('Social Link')
        verbose_name_plural = _('Social Links')

    def __unicode__( self ): #__str__ for python 3.3
        return smart_unicode( self.name )

class InmuebleCategory(models.Model):
    """docstring for ClassName"""
    name = models.CharField( validators = [validate_category_name],max_length=50, null= False, blank = False, verbose_name = _('name') )
    condominio =models.ForeignKey(Condominio, null = False, on_delete=models.CASCADE)
    inmuebles = models.ManyToManyField(Inmueble, related_name="categories")
    class Meta:
        verbose_name = _('Property Category')
        verbose_name_plural = _('Property Categories')
        unique_together =('name','condominio',)

    #UNICODE RETURN OBJECT
    def __unicode__(self): #__str__ for python 3.3
        return smart_unicode(self.name)

#post_save.connect(post_recipiente_name, sender = InmuebleCategory, dispatch_uid='pre_condition_name_signal')


class Inmueble_UploadReq(models.Model):       
    condominio= models.ForeignKey(Condominio, null = False)
    created = models.DateTimeField(auto_now_add=True, null=True, verbose_name = _('created'))
    csv_file =  models.FileField(upload_to = upload_req_carg_inmueble, null=False, blank= False, verbose_name = _('file'))
    monto = models.DecimalField( max_digits=50, decimal_places=4, verbose_name = _("amount"), null=True, blank=True )
    pagado = models.BooleanField( default = False, null = False, verbose_name =_("Payed by condominium") )
    ejecutado = models.BooleanField( default = False, null = False, verbose_name =_("case closed") )
    pago_condominio = models.OneToOneField(Pagos_Condominio, null = True, verbose_name=_("condominium payment"))
    class Meta:
        verbose_name = _('Property upload request')
        verbose_name_plural = _('Property upload requests')
    def __unicode__(self): #__str__ for python 3.3
        return smart_unicode( self.id)