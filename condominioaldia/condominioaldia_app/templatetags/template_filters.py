import decimal
from django import template
from django.conf import settings
from django.db.models import Sum
from condominioaldia_app.utils import month_range_dt
register = template.Library()



def absolute_val(value): # Only one argument.
    """Converts a string into all lowercase"""
    return abs(value)
register.filter('abs', absolute_val)


def decimal_places(value1, value2):
    try:
    	param = decimal.Decimal(10) ** -int(value2)
    	return decimal.Decimal(value1).quantize(param)
    except:
        return 'value1 is %s' %(str(value1))
register.filter('decimal_places', decimal_places)

def get_sum(queryset,column):
    
    egreso_total = queryset.aggregate(total_mes= Sum('cuota'))['total_mes'] or 0
    total = 0
    for item in queryset:
        cobranzas_inmueble= item.inmueble.cobranza_condominio_set.filter(mes = item.mes)
        
        for cobranza in cobranzas_inmueble:
            
            if cobranza.asunto.lower().strip() == column.lower().strip():
                if cobranza.tipo_monto =='monto':
                    total+=cobranza.monto
                elif cobranza.tipo_monto =='porcEgresos':
                    cuenta = egreso_total*cobranza.porcentaje*item.inmueble.alicuota/100
                    total +=cuenta
    return total
register.filter('get_sum', get_sum)

def get_data(col, factura):
    month_range = month_range_dt(factura.mes)
    egresos = factura.condominio.egreso_condominio_set.filter(mes__range=(month_range[0], month_range[1]))
    sum_egresos= egresos.aggregate(total_deuda= Sum('monto'))['total_deuda'] or 0
    cobranzas = factura.get_cobranzas_for_current_period()
    for cobranza in cobranzas:
        if cobranza.asunto.lower().strip() == col.lower().strip():
            if cobranza.tipo_monto =='monto':
                return (cobranza.monto).quantize(settings.TWOPLACES)
            elif cobranza.tipo_monto =='porcEgresos':
                return (cobranza.porcentaje*factura.inmueble.alicuota/100*sum_egresos).quantize(settings.TWOPLACES)
    return 0
register.filter('get_data', get_data)

def multiply(value1, value2): 
    return (decimal.Decimal(value1)*decimal.Decimal(value2)).quantize(settings.TWOPLACES)
    #return 'result'
register.filter('multiply', multiply)

def divide(value1, value2): 
    try:
        return (decimal.Decimal(value1)/decimal.Decimal(value2)).quantize(settings.TWOPLACES)
    except:
        return 'DIV0ERROR'
register.filter('divide', divide)




def sum_key(dict_list, key):
    try:
        total=0
        if not len(dict_list)>0:
            return total
        for item in dict_list:
            try:
                #if type(item.__getattribute__(key))=='':
                total+= item.__getattribute__(key)
            except:
                item[key] =decimal.Decimal(item[key])
                total+=item[key]
        return total.quantize(settings.TWOPLACES)
    except:
        print 'error in sum_key template filter'
        return 0
register.filter('sum_key', sum_key)

def titulo(object_dict, key):
    if object_dict:
        return object_dict[key]
    return 0
register.filter('titulo', titulo)

def count_bool_queryset(queryset, param):
    try:
        counter = 0
        for item in queryset:
            if item[param] == True:
                counter+=1
        return counter
    except:
        print 'error in template filter'
        return 0
register.filter('count_bool_queryset', count_bool_queryset)

def accounting(value):
    if value:
    	if value[0] == str('-'):
    		return str(value).replace('-', '(') + (')')
    	return value
    return 'no value in accounting filter'
register.filter('accounting', accounting)

def get64(url):
    """
    Method returning base64 image data instead of URL
    """
    if url.startswith('http'):
        source = cStringIO.StringIO(urllib.urlopen(url).read()).read()
        if url.endswith('.svg'):
            binary = svg2png(source)
            return 'data:image/png;base64,' + base64.b64encode(binary)
        if url.endswith('.ttf'):
            return 'data:application/x-font-ttf;charset=utf-8;base64,' + base64.b64encode(source)
        return 'data:image/jpg;base64,' + base64.b64encode(source)
    return url
register.filter('get64', get64)