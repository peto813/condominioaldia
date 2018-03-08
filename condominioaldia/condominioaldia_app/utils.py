import decimal, calendar, pytz, datetime, requests
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.humanize.templatetags.humanize import intcomma
from django.db.models import F, FloatField, Sum
from django.utils.translation import gettext, gettext_lazy as _
from django.utils import timezone
import models

#from allauth.account.utils import send_email_confirmation
#emailaddress.send_confirmation()

def get_user_type(request):
	if hasattr(request.user, 'condominio') :
		return 'condominio'
	elif hasattr(request.user, 'inquilino'):
		return 'inquilino'
	elif hasattr(request.user, 'affiliate'):
		return 'affiliate'
	#user_type = 'condominio' if hasattr(request.user, 'condominio') else 'inquilino'
	#return user_type

#RETURNS WHETHER CONDOMINIO IS ACTIVE AND SETS AUTOMATICALLY
def condominio_activator(condominio):
	D = decimal.Decimal
	inmuebles = condominio.inmueble_set.all()
	if inmuebles.exists():
		total = D(inmuebles.filter(condominio = condominio).values('alicuota').aggregate(Sum('alicuota'))['alicuota__sum'] or 0)
		if total>=D(settings.MINIMA_ALICUOTA):
			condominio.activo = True
			condominio.save()
		else:
			condominio.activo = False
			condominio.save()
	else:
		condominio.activo = False
		condominio.save()
	return condominio.activo

def total_alicuotas(inmuebles, condominio):
	D = decimal.Decimal
	total = D(inmuebles.filter(condominio = condominio).values('alicuota').aggregate(Sum('alicuota'))['alicuota__sum'] or 0)
	return total

def last_day_of_month(date):
	lastdayofmonth = calendar.monthrange( date.year,  date.month )[1]
	return lastdayofmonth

def last_instant_of_month(datetime):
	lastdayofmonth = calendar.monthrange( datetime.year,  datetime.month )[1]
	return datetime.replace(day= lastdayofmonth, hour= 23, minute = 59, second=59, microsecond=999999)

def localize_tz(date):
	return pytz.timezone(settings.TIME_ZONE).localize(date)


def blog_paginator_summary(paginator, serializer):
	pagination_dict = {
		'next_link' :paginator.get_next_link(),
		'previous_link' :paginator.get_previous_link(),
		'page' :paginator.page.number,
		'page_count' :paginator.page.paginator.num_pages,
		'results' : serializer.data
    }
	return pagination_dict

def data_range(queryset, parameter):
	'''
	parameter is the key(string) value to sort by, ex. "created", "timestamp"
	'''
	range_obj= {}
	try:
		if queryset.exists():
			latest = getattr(queryset.latest(parameter), parameter)
			latest = latest.replace(day= last_day_of_month(latest), hour= 23, minute = 59, second=59, microsecond=999999 )
			earliest = getattr(queryset.earliest(parameter), parameter).replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
		 	range_obj['minDate'] =earliest
		 	range_obj['maxDate'] =latest
		 	return range_obj
		else:
			return None
	except:
		pass
	return None

def unescape(text):												
	new_string = text.replace('&lt;', '<').replace('&gt;', '>').replace('&#39;', "'").replace('&quot;', '"').replace('&amp;', '&')
	return new_string

class Instapago:
	def submit_payment(self, KeyId, PublicKeyId, Amount, Description, CardHolder, 
		CardHolderID, CardNumber, CVC, ExpirationDate, StatusId, IP, opt_OrderNumber = None, 
		opt_Address = None, opt_City = None, opt_ZipCode = None, opt_State = None ):
		url = 'https://api.instapago.com/payment'
		payload = {
			'KeyId': KeyId,
			'PublicKeyId' : PublicKeyId,
			'Amount' : Amount,
			'Description' : Description,
			'CardHolder' : CardHolder,
			'CardHolderID' : CardHolderID,
			'CardNumber' : CardNumber,
			'CVC': CVC,
			'ExpirationDate' : ExpirationDate,
			'StatusId' : StatusId,
			'IP' : IP,
			'opt_OrderNumber' : opt_OrderNumber,
			'opt_Address' : opt_Address,
			'opt_City' : opt_City,
			'opt_ZipCode' : opt_ZipCode,
			'opt_State' : opt_State
		}

		r = requests.post( url, data = payload, headers = {'content-type': 'application/x-www-form-urlencoded'})
		return r.json()

def month_range_dt(date):
	day_range = calendar.monthrange(date.year, date.month)
	begin = date.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
	end = date.replace(day= day_range[1], hour= 23, minute = 59, second=59, microsecond=999999) 
	return (begin, end,)

def getLatestEditablePeriod(request, ingresosQuerySet):
	if get_user_type(request) == 'condominio':
		ingresos_cerrados = ingresosQuerySet.filter(condominio = request.user.condominio).filter(cerrado = True)
		if ingresos_cerrados.exists():
			ultimo_ingreso_cerrado = ingresos_cerrados.latest('mes')
			last_day = last_day_of_month(ultimo_ingreso_cerrado.mes)
			cierre_ultimo_periodo =  datetime.datetime( ultimo_ingreso_cerrado.mes.year, ultimo_ingreso_cerrado.mes.month, last_day, tzinfo=pytz.utc )
			editable_period =  cierre_ultimo_periodo + datetime.timedelta(days=1)
			#for calendar
			minDate = datetime.datetime(request.user.date_joined.year, request.user.date_joined.month, 1, tzinfo=pytz.utc)
			maxDate =datetime.datetime(editable_period.year, editable_period.month, last_day, tzinfo=pytz.utc)
			maxDate = pytz.utc.localize(datetime.datetime.combine(maxDate, datetime.time.max))
			response = {
				'minDate': minDate,
				'maxDate' : maxDate,
				#'period' : editable_period,
				#'data' : ingresosQuerySet.filter(created__range=(minDate, maxDate))
			}
		else:
			condominio_created = request.user.date_joined
			last_day = last_day_of_month(condominio_created)
			maxDate = datetime.datetime(condominio_created.year, condominio_created.month, last_day, tzinfo=pytz.utc)
			maxDate = pytz.utc.localize(datetime.datetime.combine(maxDate, datetime.time.max))
			minDate = datetime.datetime(condominio_created.year, condominio_created.month, 1, tzinfo=pytz.utc)
			response = {
				'minDate': minDate,
				'maxDate' : maxDate,
				#'period' : condominio_created,#date when first loaded 
				#'data' : ingresosQuerySet.filter(created__range=(minDate, maxDate))
			}
			return response
	return ingresosQuerySet


def merge_two_dicts(x, y):
    """Given two dicts, merge them into a new dict as a shallow copy."""
    z = x.copy()
    z.update(y)
    return z



def send_condo_status_message(request,condominio,account_active):
    condo_status = _('activated') if account_active else _('temporarily limited')
    
    monto = models.Factura_Condominio.objects.filter(condominio = condominio, pagado = False).aggregate(total_mes= Sum('monto'))['total_mes'] or 0
    subject_context = {
        'status':condo_status 
    }
    message_context = {
        'name':condominio.user.get_full_name(),
        'currency':condominio.pais.moneda,
        'monto':intcomma(monto.quantize(settings.TWOPLACES),2),
        'site_name':get_current_site(request).name
    } 
    subject = loader.render_to_string('account/email/account_restored_subject.txt', subject_context)
    
    if account_active == True:
        message= loader.render_to_string('account/email/account_restored_message.txt', message_context)
    else:
        message= loader.render_to_string('account/email/account_suspended_message.txt', message_context)
    send_email.delay(subject, message, settings.DEFAULT_FROM_EMAIL, [condominio.user.email])


def update_condo_status(condominio):
	'''Use this function to update a condominium 
	status based on bills (late or not late with payments)'''
	updated = False
	condo_unpayed_bills = models.Factura_Condominio.objects.filter(condominio = condominio, pagado = False, demo_mode = False)
	#a week after second unpayed bill was emitted disable condo account
	if condo_unpayed_bills.exists():
		if condo_unpayed_bills.count() >=2:
			latest = condo_unpayed_bills.latest('created')
			now = timezone.now()
			cut_off_date = (latest.created+datetime.timedelta(days = 7)).replace(hour= 23, minute = 59, second=59, microsecond=999999)
			if now>cut_off_date and condominio.retrasado == False:#right
				condominio.retrasado = True
				#condominio.save()
				updated=True

			elif now<=cut_off_date and condominio.retrasado ==True:#right
				condominio.retrasado = False
				#condominio.save()
				updated=True

		elif condo_unpayed_bills.count() <2 and condominio.retrasado ==True:#right
			condominio.retrasado = False
			#condominio.save()
			updated=True

	elif not condo_unpayed_bills.exists() and condominio.retrasado ==True:#right
		condominio.retrasado = False
		#condominio.save()
		updated=True

	if updated==True:
		condominio.save()
	return updated


def get_total_cobranzas(cobranzas_queryset, inmueble, egresos_totales_periodo):
    if cobranzas_queryset.exists():
        cobranzas_sum = 0

        for cobranza in cobranzas_queryset:

            if cobranza.tipo_monto=='monto':
                cobranzas_sum+=cobranza.monto

            elif cobranza.tipo_monto=='porcEgresos':
                porcion = inmueble.alicuota/100*egresos_totales_periodo*cobranza.porcentaje
                cobranzas_sum+=porcion
    else:
    	cobranzas_sum = 0
    return cobranzas_sum


def register_cc_payment(request, payment_info, tipo_de_pago):

	success =  False
	user_type = request.user.get_user_type()
	if user_type =='condominio':
		pago_condominio = models.Pagos_Condominio.objects.create(**payment_data)
	elif user_type =='inquilino':
		inmueble = models.Inmueble.objects.get(pk=request.session.get('inmueble'))
		banco_instance =inmueble.condominio.bancos_set.all().first()
		payment_data={
			'condominio':inmueble.condominio,
			'fecha_facturacion':timezone.now(),
			'monto':decimal.Decimal(str(payment_info['amount']).replace(',', '')),
			'inmueble':inmueble,
			'aprobado':True,
			'posted_by':request.user,
			'tipo_de_ingreso':'pp',
			'arrendatario':inmueble.arrendatario,
			'tipo_de_pago':tipo_de_pago,
			'banco':banco_instance,
			'banco_dep':banco_instance.banco,
			'mes':timezone.now().replace(day=1),
			'cuenta_dep':banco.nro_cuenta,
			'detalles': 'credit card payment'
		}
		ingreso_condominio= models.Ingreso_Condominio.objects.create(**payment_data)

	return success

class Country:
	venezuela_list = (
	    ('', 'Seleccione un Banco'),
	    ('0003', 'Banco Industrial de Venezuela'),
	    ('0102', 'Banco de Venezuela'),
	    ('0104', 'Venezolano de Credito'),
	    ('0105', 'Banco Mercantil'),
	    ('0108', 'Banco Provincial'),
	    ('0114', 'Bancaribe'),
	    ('0115', 'Banco Exterior'),
	    ('0116', 'Banco Occidental de Descuento'),
	    ('0128', 'Banco Caroni'),
	    ('0134', 'Banesco'),
	    ('0137', 'Banco Sofitasa'),
	    ('0138', 'Banco Plaza'),
	    ('0146', 'Banco de la Gente Emprendedora'),
	    ('0149', 'Banco del Pueblo Soberano'),
	    ('0151', 'Banco Fondo Comun'),
	    ('0156', '100 % Banco'),
	    ('0157', 'DelSur Banco'),
	    ('0163', 'Banco del Tesoro'),
	    ('0166', 'Banco Agricola de Venezuela'),
	    ('0168', 'Bancrecer'),
	    ('0169', 'Mi Banco Microfinanciero'),
	    ('0171', 'Banco Activo'),
	    ('0172', 'Bancamiga Banco Microfinanciero'),
	    ('0173', 'Banco Internacional de Desarrollo'),
	    ('0174', 'Banplus'),
	    ('0175', 'Banco Bicentenario'),
	    ('0176', 'Banco Espirito Santo'),
	    ('0177', 'Banco de la Fuerza Armada Nacional Bolivariana'),
	    ('0190', 'Citibank'),
	    ('0191', 'Banco Nacional de Credito'),
	    ('0601', 'Instituto Municipal de Credito Popular'),
	)
