# -*- coding: utf-8 -*-
from django.db import models
from django.db import connection
from django.db.models import Max, Min, Sum
from condominioaldia_app.utils import condominio_activator, last_day_of_month, month_range_dt

from dateutil.relativedelta import relativedelta
import datetime, pytz

class InmuebleManager(models.Manager):

    def get_all_properties(self, condominio):
        return self.filter(condominio = condominio)

    def get_debtors(self, condominio):
        return self.filter(condominio = condominio).filter(deuda_actual__lt = 0)

    def get_creditors(self, condominio):
        return self.filter(condominio = condominio).filter(deuda_actual__gte = 0)

    def get_board_members(self, condominio):
        return self.filter(condominio = condominio).filter(junta_de_condominio = True)

    def get_non_board_members(self, condominio):
        return self.filter(condominio = condominio).filter(junta_de_condominio = False)

    def get_particular_property(self, condominio, inmueble):
        return self.filter(condominio = condominio).filter(pk = inmueble)         




class EgresosCondominioManager(models.Manager):

    def get_month_query(self,month):
        minDate = month.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
        maxDate = month.replace(day= last_day_of_month(month), hour= 23, minute = 59, second=59, microsecond=999999)
        queryset = self.filter(mes__range=(minDate, maxDate))
        return queryset



    def get_data_range(self, condominio):
        '''
        This method checks condominium bills to
        establish a valid data range for income and expenses
        '''
        from condominioaldia_app.models import Factura_Condominio
        queryset = Factura_Condominio.objects.filter(condominio=condominio )


        #queryset = self.filter(condominio=condominio)
        if queryset.exists():
            earliest = queryset.earliest('mes').mes.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
            latest = queryset.latest('mes').mes
            latest =latest.replace(day= last_day_of_month(latest), hour= 23, minute = 59, second=59, microsecond=999999)
            
        else:
            earliest = condominio.user.date_joined.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
            latest =earliest.replace(day= last_day_of_month(earliest), hour= 23, minute = 59, second=59, microsecond=999999)
        return (earliest,latest,)


    def get_latest_editable_tuple(self, condominio):
        from condominioaldia_app.models import Factura_Condominio
        queryset = self.all()
        condo_bills = Factura_Condominio.objects.filter(condominio=condominio, tipo_de_factura = 'service_fee' )
        if condo_bills.exists():
            latest_bill = condo_bills.latest('created').mes
            month = condo_bills.latest('created').mes +relativedelta(months=1)
            month_range = month_range_dt(month)
        else:
            condominio_created = condominio.user.date_joined
            month_range = month_range_dt(condominio_created)

        return (month_range[0],month_range[1],)


    def get_latest_editable(self, condominio):
        from condominioaldia_app.models import Factura_Condominio
        queryset = self.all()
        condo_bills = Factura_Condominio.objects.filter(condominio=condominio, tipo_de_factura='service_fee' )
        if condo_bills.exists():
            latest_bill = condo_bills.latest('created').mes
            month = condo_bills.latest('created').mes +relativedelta(months=1)
            month_range = month_range_dt(month)
        else:
            condominio_created = condominio.user.date_joined
            month_range = month_range_dt(condominio_created)
        response = {
            'minDate': month_range[0],
            'maxDate' : month_range[1]
        }
        return response

class BancosManager(models.Manager):
    
    def get_account_balance(self, id, date_time ):
        from condominioaldia_app.models import Factura_Condominio_Extra_Colum
        balance= 0
        if self.exists():
            banco = self.filter(id = id).get(id=id)
            initial_balance = banco.balanceinicial
            begin_date= banco.condominio.user.date_joined
            end_date=date_time
            #aggregate(total_alicuota= Sum('alicuota'))['total_alicuota'] or 0
            egresos =banco.egreso_condominio_set.filter(fecha_facturacion__range=(begin_date, end_date)).aggregate(total_egreso= Sum('monto'))['total_egreso'] or 0
            ingresos =banco.ingreso_condominio_set.filter(fecha_facturacion__range=(begin_date, end_date)).aggregate(total_ingreso= Sum('monto'))['total_ingreso'] or 0
            extra_cols = banco.factura_condominio_extra_colum_set.filter(factura__mes__range=(begin_date, end_date)).aggregate(total_extra_col= Sum('monto'))['total_extra_col'] or 0
            balance= ingresos-egresos-extra_cols
        return balance

class IngresosCondominioManager(EgresosCondominioManager):
    pass

class TalonarioManager(models.Manager):
    pass


class Factura_CondominioManager(models.Manager):
    def get_control_number(self, talonarios):
        allowed_control_numbers = []
        for talonario in talonarios:
            control_num_range= range(talonario.nro_control_desde, talonario.nro_control_hasta+1)
            allowed_control_numbers +=control_num_range
        response= self.all().aggregate(Max('nro_control'))['nro_control__max']
        if not response:
            response= min(allowed_control_numbers)
        else:
            response +=1
        if response in allowed_control_numbers:
            return response

    def get_data_range(self, condominio):
        '''
        This method checks condominium bills to
        establish a valid data range for income and expenses
        '''
        queryset = self.filter(condominio=condominio )
        if queryset.exists():
            earliest = queryset.earliest('mes').mes.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
            latest = queryset.latest('mes').mes
            latest =latest.replace(day= last_day_of_month(latest), hour= 23, minute = 59, second=59, microsecond=999999)
            
        else:
            earliest = condominio.user.date_joined.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
            latest =earliest.replace(day= last_day_of_month(earliest), hour= 23, minute = 59, second=59, microsecond=999999)
        return (earliest,latest,)

    def get_latest_editable_tuple(self, condominio):
        condo_bills = self.filter(condominio=condominio, tipo_de_factura='service_fee' )
        if condo_bills.exists():
            latest_bill = condo_bills.latest('created').mes
            month = condo_bills.latest('created').mes +relativedelta(months=1)
            month_range = month_range_dt(month)
        else:
            condominio_created = condominio.user.date_joined
            month_range = month_range_dt(condominio_created)

        return (month_range[0],month_range[1],)


    # def get_all_properties(self, condominio):
    #     return self.filter(condominio = condominio)

class Cobranza_CondominioManager(models.Manager):
    def get_data_range(self, condominio):
        '''
        This method checks condominium bills to
        establish a valid data range for income and expenses
        '''
        queryset = self.filter(destinatario__condominio=condominio )
        if queryset.exists():
            earliest = queryset.earliest('mes').mes.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
            latest = queryset.latest('mes').mes
            latest =latest.replace(day= last_day_of_month(latest), hour= 23, minute = 59, second=59, microsecond=999999)
            
        else:
            earliest = condominio.user.date_joined.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
            latest =earliest.replace(day= last_day_of_month(earliest), hour= 23, minute = 59, second=59, microsecond=999999)
        return (earliest,latest,)


class Pago_CondominioManager(models.Manager):
    def get_data_range(self, condominio):
        '''
        This method checks condominium bills to
        establish a valid data range for income and expenses
        '''
        queryset = self.filter(condominio=condominio )
        if queryset.exists():
            earliest = queryset.earliest('created').created.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
            latest = queryset.latest('created').created
            latest =latest.replace(day= last_day_of_month(latest), hour= 23, minute = 59, second=59, microsecond=999999)
            
        else:
            earliest = condominio.user.date_joined.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
            latest =earliest.replace(day= last_day_of_month(earliest), hour= 23, minute = 59, second=59, microsecond=999999)
        return (earliest,latest,)