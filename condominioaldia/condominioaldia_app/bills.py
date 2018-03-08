# -*- coding: utf-8 -*-
import dateutil.parser
from django.contrib.sites.shortcuts import get_current_site
from condominioaldia_app.models import *
from easy_pdf.views import PDFTemplateView, PDFTemplateResponseMixin
from django.utils.translation import gettext, gettext_lazy as _
from django.template import defaultfilters
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden
from condominioaldia_app.utils import last_day_of_month, month_range_dt,get_user_type, get_total_cobranzas
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.http import Http404
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from django.core.urlresolvers import reverse





class ReporteMensualPropietario(PDFTemplateView):
	template_name = 'pdf/reporte_mensual_propietario.html'
	def get(self, request,*args, **kwargs):
		if not request.user.is_authenticated:
			return HttpResponseRedirect(reverse('index'))
		#AUTHENTICATION
		# if not request.user.is_authenticated==True:
		# 	return redirect(reverse('index'))


		param = request.GET.get('month_created', None)
		if not param:
			raise Http404(_("Must provide a month"))
		month = dateutil.parser.parse(param)
		inmueble = Inmueble.objects.get(pk= self.request.session.get('inmueble'))
		#GET THE EGRESOS
		month_range = month_range_dt(month)
		egresos =inmueble.condominio.egreso_condominio_set.filter(mes__range=(month_range[0], month_range[1]))
		sum_egresos = egresos.aggregate(total_deuda= Sum('monto'))['total_deuda'] or 0
		######################
		#cobranzas = inmueble.cobranza_condominio_set.filter(payment__aprobado =True)
		cobranzas = inmueble.cobranza_condominio_set.filter(mes__range=(month_range[0],month_range[1]))
		sum_cobranzas= get_total_cobranzas(cobranzas, inmueble, sum_egresos)

		pagos = inmueble.ingreso_condominio_set.filter(mes__range=(month_range[0], month_range[1]), aprobado=True)
		factura_propietario =inmueble.factura_propietario_set.filter(mes__range=(month_range[0], month_range[1]))[0]
		kwargs['mes'] =month
		kwargs['aviso'] ='''
		De acuerdo a los articulos 14 y 15 de la ley horizontal, 
		el presenteaviso de cobro tiene valor yfuerza ejecutiva
		'''
		#NEED TO GET TOTAL OWED
		debt_properties = inmueble.condominio.inmueble_set.filter(deuda_actual__lt=0)
		kwargs['debt_properties'] = debt_properties
		kwargs['pagos'] = pagos
		kwargs['site_name']=get_current_site(request).name
		kwargs['inmueble']=inmueble
		kwargs['cobranzas']=cobranzas
		kwargs['cuentas'] = inmueble.condominio.bancos_set.all()
		kwargs['egresos'] = egresos
		kwargs['sum_cobranzas'] =decimal.Decimal(sum_cobranzas).quantize(settings.TWOPLACES)
		kwargs['factura_propietario'] =factura_propietario
		kwargs['paper_type'] ='landscape'
		kwargs['sum_egresos'] =sum_egresos
		kwargs['pagesize'] ='letter'
		kwargs['page_margin_top'] ='1cm'
		kwargs['page_margin_bottom'] ='1cm'
		kwargs['page_margin_left'] ='1cm'
		kwargs['page_margin_right'] ='1cm'
		kwargs['footer_height'] ='1cm'
		kwargs['balance_title'] ='Deuda' if factura_propietario.monto <0 else 'Balance'
		context = self.get_context_data(**kwargs)
		return self.render_to_response(context)

	def get_context_data(self,**kwargs):
		return super(ReporteMensualPropietario, self).get_context_data(
		pagesize=kwargs.pop('pagesize'),
		paper_type=kwargs.pop('paper_type'),
		#border = factura.condominio,
		page_margin_top=kwargs.pop('page_margin_top'),
		page_margin_bottom=kwargs.pop('page_margin_bottom'),
		page_margin_left=kwargs.pop('page_margin_left'),
		page_margin_right=kwargs.pop('page_margin_right'),
		footer_height=kwargs.pop('footer_height'),
		#egresos=kwargs.pop('egresos'),
		#mes= kwargs.pop('mes'),
		#cuentas=kwargs.pop('cuentas'),
		#mes=kwargs.pop('mes'),
		#title=_('%s bill' %( defaultfilters.date(self.get_object().mes, "F Y") ) ),
		**kwargs
		)

class RelacionCuotas(PDFTemplateView):
	template_name = 'pdf/relacion_cuotas_pdf.html'
	#download_filename = _('%s_bill.pdf')
	queryset = Factura_Propietario.objects.all()

	def get_cols(self, inmuebles):
		cols = ['Inmueble', 'Residente', 'Balance Presente', 'Pagos', 'Cuota', 'Balance Nuevo' ]
		cobranza_names = []
		for inmueble in inmuebles:
			cobranzas_inmueble= inmueble.cobranza_condominio_set.filter(mes__range = (self.month_range[0],self.month_range[1]))
			for cobranza in cobranzas_inmueble:
				if not cobranza.asunto in cobranza_names:
					cobranza_names.append(cobranza.asunto)
		cobranza_names = sorted(cobranza_names)
		for item in cobranza_names:
			cols.insert(5, str(item))
		return {'cols':cols,'dynamic_cols': cobranza_names}

	def get_queryset(self, request):

		user_type = get_user_type(request)
		if user_type =='condominio':
			self.condominio=self.request.user.condominio
			return self.queryset.filter(condominio = self.request.user.condominio)
		elif user_type =='inquilino':
			inmueble_id= self.request.session.get('inmueble')
			self.condominio = Inmueble.objects.get(pk =inmueble_id).condominio
			return self.queryset.filter(condominio= self.condominio)

	def get(self, request,*args, **kwargs):
		if not request.user.is_authenticated:
			return HttpResponseRedirect(reverse('index'))

		param = request.GET.get('month_created', None)   
		if not param:
			raise Http404(_("Must provide a month"))

		month = dateutil.parser.parse(param)
		self.month_range = month_range_dt(month)
		queryset = self.get_queryset(request)
		queryset = queryset.filter(mes__range =(self.month_range[0], self.month_range[1]))
		factura_condominio = Factura_Condominio.objects.filter(condominio=self.condominio, mes__range =(self.month_range[0], self.month_range[1]))
		if factura_condominio.exists():
			factura_condominio =factura_condominio[0]
		else:
			raise Http404(_("Could not find corresponding condominium bill."))
	
		columns = self.get_cols(factura_condominio.condominio.inmueble_set.all())

		balance_previo = queryset.aggregate(total_mes= Sum('monto'))['total_mes'] or 0
		sum_cuotas = -1*(queryset.aggregate(total_mes= Sum('cuota'))['total_mes'] or 0)
		sum_pagos = queryset.aggregate(total_mes= Sum('pagos'))['total_mes'] or 0
		sum_deuda_nueva = queryset.aggregate(total_mes= Sum('monto'))['total_mes'] or 0
		
		kwargs['cuentas'] = Bancos.objects.filter(condominio =factura_condominio.condominio) 
		kwargs['factura'] = factura_condominio
		kwargs['dynamic_cols'] = columns['dynamic_cols']
		kwargs['columns'] = columns['cols']
		kwargs['facturas_propietarios'] =queryset
		kwargs['sum_cuotas'] =sum_cuotas
		kwargs['sum_pagos'] =sum_pagos
		kwargs['sum_deuda_nueva'] =sum_deuda_nueva
		kwargs['mes'] =month
		kwargs['balance_previo'] =balance_previo
		kwargs['paper_type'] ='landscape'
		kwargs['pagesize'] ='letter'
		kwargs['page_margin_top'] ='1cm'
		kwargs['page_margin_bottom'] ='1cm'
		kwargs['page_margin_left'] ='1cm'
		kwargs['page_margin_right'] ='1cm'
		kwargs['footer_height'] ='1cm'

		context = self.get_context_data(**kwargs)
		return self.render_to_response(context)

	def get_object(self ):
		if not self.request.user.is_authenticated():
			raise PermissionDenied(_('Permission denied'))
		try:
			return self.queryset
			#return self.queryset.filter(condominio=self.request.user.condominio).get(pk=self.kwargs['pk'])
		except self.queryset.model.DoesNotExist:
			raise Http404(_("Bill does not exist"))

	def get_context_data(self,**kwargs):
		factura = kwargs.pop('factura')
		return super(RelacionCuotas, self).get_context_data(
		pagesize=kwargs.pop('pagesize'),
		paper_type=kwargs.pop('paper_type'),
		condominio = factura.condominio,
		page_margin_top=kwargs.pop('page_margin_top'),
		page_margin_bottom=kwargs.pop('page_margin_bottom'),
		page_margin_left=kwargs.pop('page_margin_left'),
		page_margin_right=kwargs.pop('page_margin_right'),
		footer_height=kwargs.pop('footer_height'),
		cuentas=kwargs.pop('cuentas'),
		facturas=kwargs.pop('facturas_propietarios'),
		mes=kwargs.pop('mes'),
		#title=_('%s bill' %( defaultfilters.date(self.get_object().mes, "F Y") ) ),
		**kwargs
		)


class EgresosCondominioPDF(PDFTemplateView):
	template_name = 'pdf/egresos_condominio_pdf.html'
	#download_filename = _('%s_bill.pdf')
	queryset = Egreso_Condominio.objects.all()

	def get_queryset(self):
		user_type =self.request.user.get_user_type()
		if user_type =='condominio':
			self.condominio=self.request.user.condominio
			return self.queryset.filter(condominio = self.condominio)
		elif user_type =='inquilino':
			inmueble_id= self.request.session.get('inmueble')
			self.condominio = Inmueble.objects.get(pk =inmueble_id).condominio
			return self.queryset.filter(condominio= self.condominio)



	def get(self, request,*args, **kwargs):
		if not request.user.is_authenticated:
			return HttpResponseRedirect(reverse('index'))
		param = request.GET.get('month_created', None)   
		if not param:
			raise Http404(_("Must provide a month"))

		month = dateutil.parser.parse(param)
		month_range = month_range_dt(month)
		queryset = list(self.get_queryset().filter(mes__range =(month_range[0], month_range[1])) if self.get_queryset() else [])
		factura_condominio = Factura_Condominio.objects.filter(condominio=self.condominio, mes__range =(month_range[0], month_range[1]))
		if factura_condominio.exists():
			factura_condominio =factura_condominio[0]
		else:
			raise Http404(_("Could not find corresponding condominium bill."))
	
		# for extra_col in factura_condominio.extra_cols.all():
		# 	queryset.append({
		# 		'tipo_egreso' :extra_col.titulo,
		# 		'monto' :extra_col.monto,
		# 		'condominio': factura_condominio.condominio
		# 	})
		kwargs['egresos'] = queryset
		kwargs['factura'] =factura_condominio
		kwargs['due_date'] =factura_condominio.mes+relativedelta(months=1)
		kwargs['mes'] =month
		kwargs['paper_type'] ='landscape'
		kwargs['pagesize'] ='letter'
		kwargs['page_margin_top'] ='1cm'
		kwargs['page_margin_bottom'] ='1cm'
		kwargs['page_margin_left'] ='1cm'
		kwargs['page_margin_right'] ='1cm'
		kwargs['footer_height'] ='1cm'

		context = self.get_context_data(**kwargs)
		return self.render_to_response(context)






	def get_context_data(self,**kwargs):
		#factura=self.get_object()
		factura = kwargs.pop('factura')
		return super(EgresosCondominioPDF, self).get_context_data(
		pagesize=kwargs.pop('pagesize'),
		paper_type=kwargs.pop('paper_type'),
		condominio = factura.condominio,
		page_margin_top=kwargs.pop('page_margin_top'),
		page_margin_bottom=kwargs.pop('page_margin_bottom'),
		page_margin_left=kwargs.pop('page_margin_left'),
		page_margin_right=kwargs.pop('page_margin_right'),
		footer_height=kwargs.pop('footer_height'),
		egresos=kwargs.pop('egresos'),
		factura= factura,
		due_date=kwargs.pop('due_date'),
		mes=kwargs.pop('mes'),
		#title=_('%s bill' %( defaultfilters.date(self.get_object().mes, "F Y") ) ),
		**kwargs
		)



class FacturaCondominioView(PDFTemplateView):
	template_name = 'pdf/condo_bill.html'
	#download_filename = _('%s_bill.pdf')
	queryset = Factura_Condominio.objects.all()

	def get_object(self ):
		try:

			if not self.request.user.is_authenticated():
				raise PermissionDenied(_('Permission denied'))
			return self.queryset.filter(condominio=self.request.user.condominio).get(pk=self.kwargs['pk'])
		except:
			raise Http404(_("Bill does not exist"))


	def get(self, request,*args, **kwargs):
		if not request.user.is_authenticated:
			return HttpResponseRedirect(reverse('index'))
		"""
		Handles GET request and returns HTTP response.
		"""
		context = self.get_context_data(**kwargs)
		return self.render_to_response(context)
		# except:
		# 	return HttpResponseRedirect('www.cnn.com')

	def get_queryset(self):
		queryset = self.queryset.filter(condominio = self.request.user.condominio)
		return queryset

	def get_egresos(self, month):
		minDate= month.replace(day= 1, hour= 0, minute = 0, second=0,microsecond=0)
		maxDate= month.replace(day= last_day_of_month(minDate), hour= 23, minute = 59, second=59, microsecond=999999 )
		egresos= Egreso_Condominio.objects.filter(condominio=self.request.user.condominio).filter(mes__range=(minDate, maxDate))
		return egresos

	def get_context_data(self,**kwargs):
		factura=self.get_object()
		return super(FacturaCondominioView, self).get_context_data(
		pagesize='LETTER',
		#today=timezone.now(),
		factura = factura,
		page_margin_top='0.5cm',
		page_margin_bottom='5cm',
		page_margin_left='1cm',
		page_margin_right='1cm',
		footer_height='4cm',
		egresos=self.get_egresos(factura.mes),
		due_date=self.get_object().mes+relativedelta(months=1),
		title=_('%s bill' %( defaultfilters.date(self.get_object().mes, "F Y") ) ),
		**kwargs
		)

    # def get_context_data(self, **kwargs):
    # 	first_name= self.request.user.first_name
    #     return super(HelloPDFView, self).get_context_data(
    #         pagesize='letter',
    #         title=_('%s bill' %(first_name)),
    #         download_filename = _('bill.pdf')
    #         **kwargs
    #     )