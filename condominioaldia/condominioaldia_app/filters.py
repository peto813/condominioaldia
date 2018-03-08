# -*- coding: utf-8 -*-

# encoding=utf8  
import django_filters
from models import *
from django.utils import timezone
from condominioaldia_app.utils import get_user_type, last_day_of_month
import datetime, pytz
from django.contrib.auth.models import User
from django.db.models import Q


class Paises_Filter(django_filters.FilterSet):
    class Meta:
        model = Paises
        fields = [ 'activo' ]

class UsuarioFilter(django_filters.FilterSet):
    tipo_usuario = django_filters.CharFilter( method = 'tipo_usuario_filter' )
    class Meta:
        model = User
        fields = [ 'email', 'tipo_usuario' ]
        #fields = {"search_param": ['iexact', 'icontains', 'in', 'startswith']}
    def tipo_usuario_filter( self, queryset, name, value ):
        if value == 'condominio':
            return queryset.filter(condominio__isnull = False)
        elif value=='inquilino':
            return queryset.filter(inquilino__isnull = False)


class InmuebleFilter(django_filters.FilterSet):
    class Meta:
        model = Inmueble
        fields =[ 'junta_de_condominio', 'condominio' ]

class IngresosFilter(django_filters.FilterSet):
    cerrado = django_filters.BooleanFilter( )
    month_created = django_filters.IsoDateTimeFilter( method = 'getMonth' )

    class Meta:
        model = Ingreso_Condominio
        fields =[  'month_created', 'cerrado' ]

    def getMonth( self, ingresos, name, value ):
        maxDate = datetime.datetime(value.year, value.month, last_day_of_month(value), tzinfo=pytz.utc).replace( hour= 23, minute = 59, second=59, microsecond=999999)
        minDate = datetime.datetime(value.year, value.month, 1, tzinfo=pytz.utc).replace(hour= 0, minute = 0, second=0,microsecond=0)
        return ingresos.filter(mes__range=(minDate, maxDate)).order_by('-fecha_facturacion')


class EgresoFilter(IngresosFilter):
    class Meta:
        model = Egreso_Condominio
        fields =[  'month_created', 'cerrado' ]


class PollsFilter(django_filters.FilterSet):
    month_created = django_filters.IsoDateTimeFilter( method = 'getMonth' )

    class Meta:
        model = Poll
        fields =[  'created', 'month_created' ]

    def getMonth( self, ingresos, name, value ):
        maxDate = datetime.datetime(value.year, value.month, last_day_of_month(value), tzinfo=pytz.utc).replace( hour= 23, minute = 59, second=59, microsecond=999999)
        minDate = datetime.datetime(value.year, value.month, 1, tzinfo=pytz.utc).replace(hour= 0, minute = 0, second=0,microsecond=0)
        return ingresos.filter(created__range=(minDate, maxDate))

class ingresos_afiliadoFilter(django_filters.FilterSet):
    month_created = django_filters.IsoDateTimeFilter( method = 'getMonth' )
    latest = django_filters.BooleanFilter( method = 'getLatest', name='latest' )

    class Meta:
        model = Affiliate_Income
        fields =[  'created', 'month_created', 'latest' ]

    def getLatest(self, ingresos, name, value):
        if ingresos.exists():
            latest = ingresos.latest('created').created
            minDate = latest.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
            maxDate = minDate.replace(day= last_day_of_month(minDate), hour= 23, minute = 59, second=59, microsecond=999999)
            return ingresos.filter(created__range=(minDate, maxDate))
        return []

    def getMonth( self, ingresos, name, value ):
        maxDate = datetime.datetime(value.year, value.month, last_day_of_month(value), tzinfo=pytz.utc)
        minDate = datetime.datetime(value.year, value.month, 1,  0,  0, 0,0,tzinfo=pytz.utc)
        return ingresos.filter(created__range=(minDate, maxDate))


class Factura_CondominioFilter(django_filters.FilterSet):
    year_created = django_filters.IsoDateTimeFilter( method = 'getYear' )
    mes = django_filters.IsoDateTimeFilter( method = 'get_month' )
    class Meta:
        model = Factura_Condominio
        fields =[ 'mes','year_created' ]

    def get_month( self, queryset, name, value ):
        minDate = value.replace(month= 1,day= 1, hour= 0, minute = 0, second=0,microsecond=0)
        maxDate = value.replace(day= last_day_of_month(value), hour= 23, minute = 59, second=59, microsecond=999999 )
        return queryset.filter(mes__range=(minDate, maxDate))

    def getYear( self, queryset, name, value ):
        minDate = value.replace(month= 1,day= 1, hour= 0, minute = 0, second=0,microsecond=0)
        maxDate = value.replace(month = 12,day= last_day_of_month(value), hour= 23, minute = 59, second=59, microsecond=999999 )
        return queryset.filter(mes__range=(minDate, maxDate))




class MessagesFilter(django_filters.FilterSet):
    month_created = django_filters.IsoDateTimeFilter( method = 'getMonth' )
    class Meta:
        model = Messages
        fields = [ 'month_created' ]


    def getMonth( self, messages, name, value ):
        maxDate = datetime.datetime(value.year, value.month, last_day_of_month(value), tzinfo=pytz.utc)
        minDate = datetime.datetime(value.year, value.month, 1, tzinfo=pytz.utc)
        return messages.filter(mes__range=(minDate, maxDate))