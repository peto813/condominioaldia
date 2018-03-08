# -*- coding: utf-8 -*-
"""condominioaldia URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic import TemplateView
#from django.conf.urls import *
from rest_framework import routers
#from django.contrib import admin
from django.conf import settings
from condominioaldia_app import bills
#from allauth.account.views import confirm_email as allauthemailconfirmation
from condominioaldia_app.views import (
    IndexView,
    PaisesListView,
    userViewSet,
    verificarCorreo,
    confirmEmailView,
    InmuebleViewSet,
    CustomLoginView,
    InquilinosViewSet,
    GetUserView,
    BorrarInmuebles,
    paginasAmarillasViewSet,
    bancosViewSet,
    CarteleraViewSet,
    IngresosViewSet,
    customPasswordResetView,
    IngresoCondominioApiView,
    Egresos_CondominioApiView,
    verificarRif,
    tiposEgresosViewSet,
    EgresosViewSet,
    UserProfileView,
    customChangePwdView as PasswordChangeView,
    FaqView,
    smsEmailViewSet,
    MessagesApiView,
    PollsApiView,
    PollsViewSet,
    Factura_CondominioViewSet,
    Factura_CondominioApiView,
    RelacionMesView,
    RelacionMes2View,
    PaymentMethodView,
    Bank_Accounts_Condominioaldia_View,
    CondoHomeView,
    AffiliateViewSet,
    AffiliateHomeView,
    ingresos_afiliadoView,
    bancoAfiliadoViewSet,
    inquilino_inmueblesView,
    inquilino_homeView,
    SetSesionView,
    Pago_InquilinoView,
    VoteView,
    InmuebleCategoryViewSet,
    Assign_categoryView,
    Remove_categoryView,
    SocialLinksView,
    inmueblesSampleFilesView,
    InmuebleCSVView,
    testApiView,
    Marketting_Email,
    bancosView,
    CobranzasCondominio_ApiView,
    CobranzasPropietario_ApiView,
    IngresoCondoModalView,
    EgresosContextModal,
    ResumenPropietarioView,
    help_itemsView,
    RelacionSummaryView,
    tipsApiView,
    resumen_condominioApiView,
    confirm_deletionView,
    testView,
    ContactUsApiView,
    InstaPagoView,
    JuntaCondominioViewSet,
    #egresos_detalladosApiView,
    )

#from allauth.account.views import confirm_email

router = routers.DefaultRouter()
router.register( r'users', userViewSet, 'users' )
router.register( r'inmuebles', InmuebleViewSet, 'inmuebles' )
router.register( r'inquilinos', InquilinosViewSet, 'inquilinos' )
router.register( r'paginas_amarillas', paginasAmarillasViewSet, 'paginas_amarillas' )
router.register( r'bancos', bancosViewSet, 'bancos' )
router.register( r'cartelera', CarteleraViewSet, 'cartelera' )
router.register( r'ingresos', IngresosViewSet, 'ingresos' )
router.register( r'egresos', EgresosViewSet, 'egresos' )
router.register( r'tipos_egresos', tiposEgresosViewSet, 'tipos_egresos' )
router.register( r'sms_email', smsEmailViewSet, 'sms_email' )
router.register( r'polls', PollsViewSet, 'polls' )
router.register( r'factura_condominio', Factura_CondominioViewSet, 'factura_condominio' )
#router.register( r'affiliate', AffiliateViewSet, 'affiliate' )
router.register( r'banco_afiliado', bancoAfiliadoViewSet, 'banco_afiliado' )
router.register( r'inmueble_category', InmuebleCategoryViewSet, 'inmueble_category' )
router.register( r'junta_condominio', JuntaCondominioViewSet, 'junta_condominio' )

#template.add_to_builtins('django.templatetags.i18n')



urlpatterns = [
    url('^', include('django.contrib.auth.urls')),
    url(r'^api/', include(router.urls)),
    url(r'^admin/marketting_email/$', Marketting_Email.as_view(), name='marketting_email'),
    url(r'^admin/confirmarborrarCorte/$', confirm_deletionView.as_view(), name='confirm_deletion'),
    
    url(r'^admin/inmuebles_csv/(?P<condominio>.*?)/$', InmuebleCSVView.as_view(), name='inmuebles_csv'),
    url(r'^admin/', admin.site.urls, name = 'admin'),
    url(r'^$', IndexView.as_view(), name= 'index'),
    #url(r'^$', include('condominioaldia_app.urls'))
    url(r'^accounts/', include('allauth.urls')),
    url(r'^rest-auth/password/change/$', PasswordChangeView.as_view(), name='rest_password_change'),
    url(r'^rest-auth/password/reset/$', customPasswordResetView.as_view(), name='rest_password_reset'),
    url(r'^rest-auth/login/$', CustomLoginView.as_view(), name='rest_login'),
    url(r'^rest-auth/registration/account-confirm-email/(?P<key>[-:\w]+)/$', confirmEmailView.as_view(), name="account_confirm_email"),
    url(r'^rest-auth/', include('rest_auth.urls')),
    url(r'^rest-auth/registration/', include('rest_auth.registration.urls')),
    url(r'^api/paises/', PaisesListView.as_view(), name='paises-list'),
    #url(r'^api/registro_condominio/', registroCondominioView.as_view(), name='registro_condominio'),
    url(r'^api/verificar_correo/(.*?)/$', verificarCorreo.as_view(), name='verificar_correo'),
    url(r'^api/verificar_rif/(.*?)/$', verificarRif.as_view(), name='verificar_rif'),
    url(r'^api/user_email/(?P<email>.*?)/$', GetUserView.as_view(), name='user_email'),
    url(r'^api/borrarinmuebles/$', BorrarInmuebles.as_view(), name='borrarinmuebles'),
    url(r'^api/condominio_ingreso/$', IngresoCondominioApiView.as_view(), name='condominio_ingreso'),
    url(r'^api/condominio_egreso/$', Egresos_CondominioApiView.as_view(), name='condominio_egreso'),
    url(r'^api/user_profile/$', UserProfileView.as_view(), name='user_profile'),
    url(r'^api/faq/$', FaqView.as_view(), name='faq'),
    url(r'^api/messages/$', MessagesApiView.as_view(), name='messages'),
    url(r'^api/get_polls/$', PollsApiView.as_view(), name='get_polls'),
    url(r'^api/get_factura_condominio/$', Factura_CondominioApiView.as_view(), name='get_factura_condominio'),
    url(r'^api/relacion_mes/(?P<month>.*?)/$', RelacionMesView.as_view(), name='relacion_mes'),
    url(r'^api/relacion_mes/$', RelacionMesView.as_view(), name='relacion_mes'),
    url(r'^api/relacion_mes2/$', RelacionMes2View.as_view(), name='relacion_mes2'),
    url(r'^api/facturas/(?P<pk>.*?)/$', bills.FacturaCondominioView.as_view(), name='condo_bill'),
    url(r'^api/egresos_pdf/$', bills.EgresosCondominioPDF.as_view(), name='egresos_pdf'),
    url(r'^api/payment_methods/$', PaymentMethodView.as_view(), name='payment_methods'),
    url(r'^api/pago_dep_trans/(?P<factura>.*?)/(?P<payment_method>.*?)/$', Bank_Accounts_Condominioaldia_View.as_view(), name='pago_dep_trans'),
    url(r'^api/pago_dep_trans/$', Bank_Accounts_Condominioaldia_View.as_view(), name='pago_dep_trans'),
    url(r'^api/condo_home/$', CondoHomeView.as_view(), name='condo_home'),
    #url(r'^api/affiliate_home/$', AffiliateHomeView.as_view(), name='affiliate_home'),
    url(r'^api/ingresos_afiliado/$', ingresos_afiliadoView.as_view(), name='ingresos_afiliado'),
    url(r'^api/cobranzas_condominio/$', CobranzasCondominio_ApiView.as_view(), name='cobranzas_condominio'),    
    url(r'^api/cobranzas_propietario/$', CobranzasPropietario_ApiView.as_view(), name='cobranzas_propietario'),    
    url(r'^api/inquilino_home/$', inquilino_homeView.as_view(), name='inquilino_home'), 
    url(r'^api/inmuebles_csv_sample/$', inmueblesSampleFilesView.as_view(), name='inmuebles_csv_sample'),   
    url(r'^api/vote/$', VoteView.as_view(), name='vote'),
    url(r'^api/set_session/$', SetSesionView.as_view(), name='set_session'),
    url(r'^api/banco_view/$', bancosView.as_view(), name='banco_view'),
    url(r'^api/pago_inquilino/$', Pago_InquilinoView.as_view(), name='pago_inquilino'),
    url(r'^api/inquilino_inmuebles/$', inquilino_inmueblesView.as_view(), name='inquilino_inmuebles'), 
    url(r'^api/assign_category/$', Assign_categoryView.as_view(), name='assign_category'),   
    url(r'^api/remove_category/$', Remove_categoryView.as_view(), name='remove_category'),   
    url(r'^api/social_links/$', SocialLinksView.as_view(), name='social_links'), 
    url(r'^api/ingreso_condo_modal_context/$', IngresoCondoModalView.as_view(), name='ingreso_condo_modal_context'),   
    url(r'^api/relacion_pdf/$', bills.RelacionCuotas.as_view(), name='relacion_pdf'),
    url(r'^api/egresos_context_modal/$', EgresosContextModal.as_view(), name='egresos_context_modal'),
    url(r'^api/resumen_propietario/$', ResumenPropietarioView.as_view(), name='resumen_propietario'),
    url(r'^api/help_items/$', help_itemsView.as_view(), name='help_items'),
    url(r'^api/relacion_mes_summary/$', RelacionSummaryView.as_view(), name='relacion_mes_summary'),
    url(r'^api/tips/$', tipsApiView.as_view(), name='tips'),
    url(r'^api/resumen_condominio/$', resumen_condominioApiView.as_view(), name='resumen_condominio'),
    url(r'^api/contactus/$', ContactUsApiView.as_view(), name='contactus'),
    url(r'^api/instapago/$', InstaPagoView.as_view(), name='instapago'),
    #url(r'^api/junta_condominio/$', JuntaCondominioView.as_view(), name='junta_condominio'),
  
    #url(r'^api/egresos_detallados/$', egresos_detalladosApiView.as_view(), name='egresos_detallados'),
 
    ################
    #url(r'^promotional_email/$', TestTemplate.as_view(), name='promotional_email'),
    url(r'^api/reporte_prop_pdf/$', bills.ReporteMensualPropietario.as_view(), name='reporte_prop_pdf'),
    url(r'^api/test/$', testApiView.as_view(), name='test'),
    url(r'^test/$', testView.as_view(), name='testview'),
        #ALLAUTH URLS
    #url(r'^accounts/', include('allauth.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)