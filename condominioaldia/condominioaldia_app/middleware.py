import condominioaldia_app.utils as utils
from django.contrib import messages
from condominioaldia_app.models import Talonario, Condominio
from django.utils.translation import gettext, gettext_lazy as _

class CondoStatusResponseMiddleware(object):

	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		response = self.get_response(request)
		#request.user.condominio.refresh_from_db(), #refresh_from_db

		if request.user.is_authenticated():
			user_type = utils.get_user_type(request)
			if user_type == 'condominio':
				retrasado = request.user.condominio.retrasado
				request.session['retrasado'] = retrasado
				retrasado = 'true' if retrasado ==True else 'false'
				condominio = Condominio.objects.get(pk = request.user.condominio.pk)
				activo = 'true' if request.user.condominio.activo ==True else 'false'
				response['retrasado'] = retrasado
				response['activo'] = activo
				has_bank_account = request.user.condominio.bancos_set.all().exists()
				response['has_bank_account'] = 'true' if has_bank_account ==True else 'false'

			elif user_type == 'affiliate':
				banks_country_list = [acccount.pais.pk for acccount in request.user.affiliate.bank_accounts.all()]
				aff_country_list =set([condominio.pais.pk for condominio in request.user.affiliate.condominios.all()])
				if len(aff_country_list) > len(banks_country_list):
					response['affiliate_need_account'] = 'true'
				else:
					response['affiliate_need_account'] = 'false'
					
			elif request.user.is_staff:
				talonarios_exist = Talonario.objects.all().exists()
				if talonarios_exist== False:
					messages.error(request, _("Please register receipt book(s)."))
		return response
