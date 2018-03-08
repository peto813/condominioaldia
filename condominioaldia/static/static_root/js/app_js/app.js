
var condominioAlDiaApp = angular.module("condominioAlDiaApp",
 [ 
    'ui.router', 
    'ui.bootstrap', 
    'ngMessages', 
    'condominioAlDiaAppControllers',
    'condominioAlDiaAppDirectives', 
    'condominioAlDiaAppServices', 
    'condominioAlDiaAppFilters',
    'ngSanitize',
    'textAngular', 
    'ngAnimate', 
    'ngFileUpload',
    'ui.utils.masks'
]);
  
 condominioAlDiaApp.config([
    '$httpProvider', function( $httpProvider ){
        $httpProvider.interceptors.push('tokenAuthInterceptor');
        $httpProvider.interceptors.push('throttleInterceptor');
        $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    }
])

condominioAlDiaApp.config(function($stateProvider, $urlRouterProvider){
    $stateProvider

        .state('test', {
            url:'/test',
            templateUrl : 'static/ng_templates/test.html',
            isLogin: true,
            controller : 'testController',
            data : { pageTitle: 'CondominioAlDia | test' }
            // resolve: {
            //     listaPaises: function($http) {
            //         var url = 'api/paises/?activo=True';
            //         return $http({ 
            //             method: 'GET', 
            //             url: url
            //         }).then(function(response){
            //             return response.data;
            //         })
            //     }
            // }
        })

        .state('registro_gracias', {
            url:'/registro_gracias',
            templateUrl : 'static/ng_templates/registrogracias.html',
            isLogin: false,
            data : { pageTitle: 'Condominioaldia | Gracias' }
        })

        .state('resumen_condominio', {
            url:'/resumen_condominio',
            templateUrl : 'static/ng_templates/condominio/resumen_condominio.html',
            isLogin: true,
            viewRole : 'condominio',
            showSidebar :true,
            data : { pageTitle: 'Condominioaldia | Resumen' },
            controller : 'resumen_condominioController',
            resolve: {
                context: function($http) {
                    var url = 'api/resumen_condominio/';
                    return $http({ 
                        method: 'GET', 
                        url: url
                    }).then(function(response){
                        return response.data;
                    })
                }
            } 
            
        })

        .state('inicio', {
            url:'/inicio',
            templateUrl : 'static/ng_templates/condominio/inicio.html',
            isLogin: true,
            controller : 'inicioController',
            viewRole : 'condominio',
            showSidebar :true,
            data : { pageTitle: 'Condominioaldia | Inicio' },
            resolve: {
                condo_home_screen_data: function($http) {
                    var url = 'api/condo_home/';
                    return $http({ 
                        method: 'GET', 
                        url: url
                    }).then(function(response){
                        return response.data;
                    })
                }
            } 
        })


        //AFFILIATE VIEWS
        .state('ingresos_afiliado', {
            url:'/ingresos_afiliado',
            templateUrl : 'static/ng_templates/affiliate/ingresos_afiliado.html',
            isLogin: true,
            viewRole : 'affiliate',
            controller : 'ingresos_afiliadoController',
            data : { pageTitle: 'Condominioaldia | Ingresos' },
            resolve: {
                context: function($http) {
                    var url = 'api/ingresos_afiliado/?latest=True';
                    return $http({ 
                        method: 'GET', 
                        url: url
                    }).then(function(response){
                        return response.data;
                    })
                }
            } 
        })
        .state('banco_afiliado', {
            url:'/banco_afiliado',
            templateUrl : 'static/ng_templates/affiliate/banco_afiliado.html',
            isLogin: true,
            viewRole : 'affiliate',
            controller : 'banco_afiliadoController',
            data : { pageTitle: 'Condominioaldia | Banco' },
            resolve: {
                context: function($http) {
                    var url = 'api/banco_afiliado/';
                    return $http({ 
                        method: 'GET', 
                        url: url
                    }).then(function(response){
                        return response.data;
                    })
                }
            } 
        })


        //                 PROPIETARIO VIEWS

        .state('inquilino_inicio', {
            url:'/inquilino_inicio',
            templateUrl : 'static/ng_templates/inquilino/inquilino_inicio.html',
            isLogin: true,
            viewRole : 'inquilino',
            controller : 'inquilino_inicioController',
            showSidebar:true,
            data : { pageTitle: 'Condominioaldia | Inicio' },
            resolve: {
                context: function($http, $location) {
                    var url = 'api/inquilino_home/';
                    return $http({ 
                        method: 'GET', 
                        url: url
                    }).then(function(response){
                        return response.data;
                    })
                }
            } 
        })
        .state('select_inmueble', {
            url:'/select_inmueble',
            templateUrl : 'static/ng_templates/inquilino/select_inmueble.html',
            isLogin: true,
            viewRole : 'inquilino',
            controller : 'select_inmuebleController',
            showSidebar:false,
            data : { pageTitle: 'Condominioaldia | Seleccione inmueble' },
            resolve: {
                context: function($http) {
                    var url = 'api/inquilino_inmuebles/';
                    return $http({ 
                        method: 'GET', 
                        url: url
                    }).then(function(response){
                        return response.data;
                    })
                }
            } 
        })
        .state('pagos_inquilino', {
            url:'/pagos_inquilino',
            templateUrl : 'static/ng_templates/inquilino/pagos_inquilino.html',
            isLogin: true,
            showSidebar:true,
            viewRole : 'inquilino',
            controller : 'pagos_inquilinoController',
            data : { pageTitle: 'Condominioaldia | Inicio' },
            resolve: {
                context: function($http) {
                    var url = 'api/pago_inquilino/';
                    return $http({ 
                        method: 'GET', 
                        url: url
                    }).then(function(response){
                        console.log(response)
                        return response.data;
                    })
                }
            } 
        })
        .state('pago_propietario_dep', {
            url:'/pago_propietario_dep',
            templateUrl : 'static/ng_templates/inquilino/pago_propietario_dep.html',
            isLogin: true,
            viewRole : 'inquilino',
            controller : 'pago_propietario_depController',
            data : { pageTitle: 'Condominioaldia | Deposito' },
            resolve: {
                bancos: function($http) {
                    var url = 'api/bancos/';
                    return $http({ 
                        method: 'GET', 
                        url: url
                    }).then(function(response){
                        return response.data;
                    })
                }
            } 
        })

        //          AFFILIATE VIEWS

        .state('affiliate_inicio', {
            url:'/affiliate_inicio',
            templateUrl : 'static/ng_templates/affiliate/affiliate_inicio.html',
            isLogin: true,
            viewRole : 'affiliate',
            controller : 'affiliateInicioController',
            data : { pageTitle: 'Condominioaldia | Inicio' },
            resolve: {
                affiliate_home: function($http) {
                    var url = 'api/affiliate_home/';
                    return $http({ 
                        method: 'GET', 
                        url: url
                    }).then(function(response){
                        return response.data;
                    })
                }
            } 
        })


        .state('register_affiliate', {
            url:'/register_affiliate',
            templateUrl : 'static/ng_templates/affiliate/register_affiliate.html',
            controller : 'negociosController',
            data : { pageTitle: 'Condominioaldia | Afiliarse' },
            isLogin: false
        })

        //CONDOMINIO
        .state('junta_condominio', {
            url:'/junta_condominio',
            templateUrl : 'static/ng_templates/junta_condominio.html',
            isLogin: true,
            controller : 'juntaCondominioController',
            showSidebar :true,
            data : { pageTitle: 'Condominioaldia | Junta de Condominio' },
            resolve: {
                juntaCondominio: function($http) {
                    var url = 'api/inmuebles/?junta_de_condominio=True';
                    return $http({ 
                        method: 'GET', 
                        url: url
                    }).then(function(response){
                        return response.data;
                    })
                }
            }     
        })

        .state('inmuebles', {
            url:'/inmuebles',
            templateUrl : 'static/ng_templates/condominio/registro_inmuebles.html',
            data : { pageTitle: 'Condominioaldia | Inmuebles' },
            isLogin: true,
            viewRole: 'condominio',
            showSidebar :true,
            controller : 'inmueblesController',
            resolve: {
                listaInmuebles: function($http) {
                    var url = 'api/inmuebles/';
                    return $http({ 
                        method: 'GET', 
                        url: url
                    }).then(function(response){
                        return response.data;
                    }, function(errors){
                        console.log(errors)
                    })
                },
                categories: function($http) {
                    var url = 'api/inmueble_category/';
                    return $http({ 
                        method: 'GET', 
                        url: url
                    }).then(function(response){
                        return response.data;
                    }, function(errors){
                        alert(errors);
                    })
                }
            }       
        })


        .state('resumen_propietario', {
            url:'/resumen_propietario',
            templateUrl : 'static/ng_templates/inquilino/resumen_propietario.html',
            controller : 'resumen_propietarioController',
            data : { pageTitle: 'CondominioAlDia | Resumen' },
            isLogin: true,
            showSidebar:true,
            viewRole : 'inquilino',
            resolve: {
                context: function($http) {
                    var url = 'api/resumen_propietario/';
                    return $http({ 
                        method: 'GET', 
                        url: url
                    }).then(function(response){
                        return response.data;
                    })
                }
            }
        })

        .state('cobranzas_propietario', {
            url:'/cobranzas_propietario',
            templateUrl : 'static/ng_templates/inquilino/cobranzas_propietario.html',
            controller : 'cobranzas_propietarioController',
            data : { pageTitle: 'CondominioAlDia | Cobranzas' },
            isLogin: true,
            viewRole : 'inquilino',
            showSidebar:true,
            resolve: {
                context: function($http) {
                    var url = 'api/cobranzas_propietario/';
                    return $http({ 
                        method: 'GET', 
                        url: url
                    }).then(function(response){
                        return response.data;
                    })
                }
            }
        })

        .state('registro', {
            url:'/registro',
            templateUrl : 'static/ng_templates/registro.html',
            isLogin: false,
            controller : 'registroController',
            data : { pageTitle: 'CondominioAlDia | Registro' },
            resolve: {
                listaPaises: function($http) {
                    var url = 'api/paises/?activo=True';
                    return $http({ 
                        method: 'GET', 
                        url: url
                    }).then(function(response){
                        return response.data;
                    })
                }
            }
        })
        .state('terminos', {
            url:'/terminos',
            templateUrl : 'static/ng_templates/terminos.html',
            data : { pageTitle: 'Terms & Conditions' }
        })
        .state('paginas_amarillas', {
            url:'/paginas_amarillas',
            templateUrl : 'static/ng_templates/paginas_amarillas.html',
            isLogin: true,
            showSidebar :true,
            controller : 'paginasAmarillasController',
            data : { pageTitle: 'CondominioAlDia | Paginas amarillas' },
            resolve: {
                pagAmarillas: function($http) {
                    var url = 'api/paginas_amarillas/'
                    return $http({ 
                        method: 'GET', 
                        url: url,
                    }).then(function(response){
                        return response.data;
                    })
                }
            }
        })

        .state('bancos', {
            url:'/bancos',
            templateUrl : 'static/ng_templates/condominio/bancos.html',
            isLogin: true,
            showSidebar :true,
            controller : 'bancosController',
            data : { pageTitle: 'CondominioAlDia | Bancos' },
            viewRole : 'condominio',
            resolve: {
                bancos: function($http) {
                    var url = 'api/banco_view/'
                    return $http({ 
                        method: 'GET', 
                        url: url,
                    }).then(function(response){
                        return response.data;
                    })
                },
                accordionOpen :function(){
                    return true;
                }
            }
        })
        .state('cobranzas', {
            url:'/cobranzas',
            templateUrl : 'static/ng_templates/condominio/cobranzas_condominio.html',
            isLogin: true,
            showSidebar :true,
            controller : 'CobranzasController',
            data : { pageTitle: 'CondominioAlDia | Cobranzas' },
            viewRole : 'condominio',
            resolve: {
                context: function($http, $location) {

                    var url = 'api/cobranzas_condominio/';
                    return $http({ 
                        method: 'GET', 
                        url: url,
                    }).then(function(response){
                          try {
                                return response.data;
                          } catch (err) {
                                $location.path('/');
                          }
                    })
                },
                accordionOpen :function(){
                    return true;
                }
            }
        })

        .state('quienes_somos', {
            url:'/quienes_somos',
            templateUrl : 'static/ng_templates/quienes_somos.html',
            isLogin: false,
            controller: 'quienesSomosController',
            data : { pageTitle: 'Condominioaldia | Quienes Somos' }
        })
        .state('cartelera', {
            url:'/cartelera',
            templateUrl : 'static/ng_templates/cartelera.html',
            isLogin: true,
            showSidebar :true,
            controller : 'carteleraController',
            data : { pageTitle: 'Condominioaldia | Cartelera' },
            resolve: {
                cartelera: function($http) {
                    var url = 'api/cartelera/';
                    return $http({ 
                        method: 'GET', 
                        url: url
                    }).then(function(accounts){
                        return accounts.data;
                    })
                }
            }
        })
        .state('egresos', {
            url:'/egresos',
            templateUrl : 'static/ng_templates/egresos.html',
            data : { pageTitle: 'Condominioaldia | Egresos' },
            controller : 'egresosController',
            isLogin: true,
            showSidebar :true,
            resolve: {
                egresos: function($http) {
                    var url = 'api/condominio_egreso/';
                    return $http({ 
                        method: 'GET', 
                        url: url
                    }).then(function(egresos){
                        return egresos.data;
                    })
                }
            }

        })  

        .state('reset_password', {
            url:'/reset_password',
            templateUrl : 'static/ng_templates/reset_password.html',
            data : { pageTitle: 'Choose Payment Method' },
            controller : 'reset_passwordController',
            isLogin: false

        })  


        .state('ingresos', {
            url:'/ingresos',
            templateUrl : 'static/ng_templates/ingresos.html',
            data : { pageTitle: 'Condominioaldia | Ingresos' },
            controller : 'ingresosController',
            isLogin: true,
            showSidebar :true,
            resolve: {
                ingresos: function($http) {
                    var url = 'api/condominio_ingreso/';
                    return $http({ 
                        method: 'GET', 
                        url: url
                    }).then(function(ingresos){
                        return ingresos.data;
                    })
                }
            }

        })  

        .state('faq', {
            url:'/faq',
            templateUrl : 'static/ng_templates/faq.html',
            isLogin: false,
            data : { pageTitle: 'Condominioaldia | Preguntas Frecuentes' },
            controller : 'FaqController',
            resolve: {
                faq: function($http) {
                    var url = 'api/faq/';
                    return $http({ 
                        method: 'GET', 
                        url: url
                    }).then(function(faq){
                        return faq.data;
                    })
                }
            }
        })

        .state('sms_email', {
            url:'/sms_email',
            templateUrl : 'static/ng_templates/sms_email.html',
            data : { pageTitle: 'Condominioaldia | Sms-Email' },
            controller : 'sms_emailController',
            isLogin: true,
            showSidebar :true,
            resolve: {
                messages: function($http) {
                    var now = new Date();
                    //var url = 'api/sms_email/?current_month=' +now.toISOString();
                    //var url = 'api/messages/';
                    var url = 'api/sms_email/';
                    return $http({ 
                        method: 'GET', 
                        url: url,
                    }).then(function(messages){
                        return messages.data;
                    })
                }
            }

        })  

        .state('/', {
            url:'/',
            templateUrl : 'static/ng_templates/landing_page.html',
            controller : 'landingPageController',
            data : { pageTitle: 'Condominioaldia | Bienvenido' },
            isLogin: false
            // resolve: {
            //     social_links: function($http) {
            //         var url = 'api/social_links/';
            //         return $http({ 
            //             method: 'GET', 
            //             url: url,
            //         }).then(function(response){
            //             return response.data;
            //         })

            //     }
            // }
        })
        .state('perfil', {
            url:'/perfil',
            templateUrl : 'static/ng_templates/perfil.html',
            controller : 'perfilController',
            isLogin: true,
            data : { pageTitle: 'Condominioaldia | Perfil' },
            resolve: {
                perfilData: function($window) {
                    return JSON.parse($window.sessionStorage.getItem('userDataString'));

                }
            }
        })
        .state('facturacion_condominio', {
            url:'/facturacion_condominio',
            templateUrl : 'static/ng_templates/condominio/facturacion.html',
            controller : 'facturacionCondoController',
            data : { pageTitle: 'Condominioaldia | facturacion' },
            isLogin: true,
            showSidebar :true,
            resolve: {
                facturacion_data: function($http) {
                    var url = 'api/get_factura_condominio/';

                    return $http({ 
                        method: 'GET', 
                        url: url,
                    }).then(function(response){
                        return response.data;
                    })
                }
            }
            
        })
        .state('encuestas', {
            url:'/encuestas',
            templateUrl : 'static/ng_templates/polls.html',
            controller : 'pollsController',
            data : { pageTitle: 'Condominioaldia | Encuestas' },
            isLogin: true,
            showSidebar :true,
            resolve: {
                polls_data: function($http) {
                    var url = 'api/get_polls/';
                    //var url = 'api/polls/';
                    return $http({ 
                        method: 'GET', 
                        url: url,
                    }).then(function(response){
                        return response.data;
                    })
                }
            }
            
        })

        .state('relacion_mes2', {
            url:'/relacion_mes2',
            templateUrl : 'static/ng_templates/relacion_mes2.html',
            controller : 'relacionMes2Controller',
            data : { pageTitle: 'Condominioaldia | Relacion' },
            isLogin: true,
            isPayed:true,
            viewRole : 'condominio',
            resolve: {
                context: function($http) {
                    var url = 'api/relacion_mes2/';
                    return $http({ 
                        method: 'GET', 
                        url: url,
                    }).then(function(response){
                        return response.data;
                    })
                },
                categories: function($http) {
                    var url = 'api/inmueble_category/';
                    return $http({ 
                        method: 'GET', 
                        url: url
                    }).then(function(response){
                        return response.data;
                    }, function(errors){
                        alert(errors);
                    })
                }
            }

        })


        .state('relacion_mes', {
            url:'/relacion_mes',
            templateUrl : 'static/ng_templates/relacion_mes.html',
            controller : 'relacionMesController',
            data : { pageTitle: 'Condominioaldia | Relacion' },
            isLogin: true,
            showSidebar :true,
            resolve: {
                context: function($http) {
                    var url = 'api/relacion_mes/';
                    return $http({ 
                        method: 'GET', 
                        url: url,
                    }).then(function(response){
                        return response.data;
                    })
                },
                categories: function($http) {
                    var url = 'api/inmueble_category/';
                    return $http({ 
                        method: 'GET', 
                        url: url
                    }).then(function(response){
                        return response.data;
                    }, function(errors){
                        alert(errors);
                    })
                }
            }

        })

        .state('pago_dep_trans', {
            url:'/pago_dep_trans',
            templateUrl : 'static/ng_templates/pago_dep_trans.html',
            controller : 'pagosDepTransController',
            data : { pageTitle: 'Condominioaldia | Pagos' },
            isLogin: true,
            resolve: {
                context: function($http, $location) {
                    var params= $location.search();
                    //var url = 'api/facturas/?pk=' + params.factura + '/';
                    var url = 'api/pago_dep_trans/' + params.factura + '/'+ params.payment_method + '/';
                    return $http({ 
                        method: 'GET', 
                        url: url,
                    }).then(function(response){
                        return response.data;
                    })
                }
            }

        })

        .state('negocios', {
            url:'/negocios',
            templateUrl : 'static/ng_templates/negocios.html',
            data : { pageTitle: 'Condominioaldia | Negocios' },
            isLogin: false
        })

        .state('contact', {
            url:'/contact',
            templateUrl : 'static/ng_templates/contact.html',
            data : { pageTitle: 'Condominioaldia | Contacto' },
            controller:'contactUsController',
            isLogin: false
        })

        .state('instapago', {
            url:'/instapago',
            templateUrl : 'static/ng_templates/instapago.html',
            data : { pageTitle: 'Condominioaldia | Pago TDC' },
            controller:'instapagoController',
            isLogin: true,
            resolve: { 
                payment_params: function($stateParams, $location){
                    //Check if url parameter is missing.
                    if ($location.search().balance === undefined || $location.search().payment_type =='undefined' ) {
                      //Do something such as navigating to a different page.
                      $location.path('/');
                    }
                    var data = {};
                    data.balance = parseFloat($location.search().balance)
                    data.payment_type = $location.search().payment_type;
                    return data;
                }
            }

        })

        .state('not_found', {
            url:'/not_found',
            templateUrl : 'static/ng_templates/badUrl.html',
            data : { pageTitle: 'Condominioaldia | Error' }
        })
        
        //$urlRouterProvider.otherwise('/');
        // Example of using function rule as param
        $urlRouterProvider.otherwise(function($injector, $location){
            $location.path('/');
        });
});




condominioAlDiaApp.config([
    '$interpolateProvider', function( $interpolateProvider ){
        $interpolateProvider.startSymbol('[[').endSymbol(']]'); 
    }
])



condominioAlDiaApp.run(['$rootScope', '$state', '$stateParams', '$location', '$window', 'userSessionServices','helpService','$uibModal',
    function($rootScope, $state, $stateParams, $location, $window, userSessionServices,helpService, $uibModal )
{   //$rootScope.showAlerts = true;
    $rootScope.alerts=[];

    $rootScope.helpModal = function(event){
        if (event.key=='F1'){
            //call help modal for current screen
            helpService.check()
        }
    }
    //$rootScope.sessionData= JSON.parse(sessionStorage.getItem('userDataString'));

//     //RUN CODE WHEN ROUTE CHANGES
    $rootScope.$on('$stateChangeStart', function(event, next,toStateParams, fromState, fromParams){
        //$rootScope.alerts=[];                     
        var can_access_url=userSessionServices.canAccessUrl(next, event);
        // if(can_access_url==false){
        //     event.preventDefault();
        //     $location.url('/perfil');
        // }
        $rootScope.userAuthenticated = userSessionServices.isAuthenticated();
        //$rootScope.sessionData= JSON.parse(sessionStorage.getItem('userDataString'));
        $rootScope.currentView = $location.path();
        //CHECKS GRANTS OR BLOCKS ACCESS BASED ON AUTHENTICATION STATUS AND USER ROLE RETURNS TRUE FOR ACCESS GRANTED FALSE FOR DENIED
        userSessionServices.setRootScope(next);
        
        switch($location.path()) {

            case '/bancos':
                $rootScope.accordionOpen= true;
                break;

            case '/facturacion_condominio':
                $rootScope.accordionOpen= true;
                break;
            case '/egresos':
                $rootScope.accordionOpen= true;
                break;
            case '/ingresos':
                $rootScope.accordionOpen= true;
                break;
            case '/relacion_mes':
                $rootScope.accordionOpen= true;
                break;
            case '/cobranzas':
                $rootScope.accordionOpen= true;
                break;
            case '/resumen_condominio':
                $rootScope.accordionOpen= true;
                break;
/*            case '/egresos_detallados':
                $rootScope.accordionOpen= true;
                break;*/               
            default:
                $rootScope.accordionOpen= false;
                break;
        } 
    });

}]);




// // //JAVSCRIPT PROTOTYPE FUNCTIONS
Date.prototype.addDays = function(days) {
    this.setDate(this.getDate() + parseInt(days));
    return this;

};



Date.prototype.addMonths = function( months) {
  var d = this.getDate();
  this.setMonth(this.getMonth() + +months);
  if (this.getDate() != d) {
    this.setDate(0);
  }
  return this;

};

Date.prototype.toISODate= function(){
    return String(this.getFullYear() + "-" + (this.getMonth() + 1) + "-" + 1);
}

Date.prototype.toUTC= function(){
var now_utc = new Date(this.getUTCFullYear(), this.getUTCMonth(), this.getUTCDate(),  this.getUTCHours(), this.getUTCMinutes(), this.getUTCSeconds());
    return now_utc;
}

String.prototype.toBoolean= function(){
    var isTrueSet = (this == 'true');
    return isTrueSet;
}


// Date.prototype.monthDays= function(){
//     var d= new Date(this.getUTCFullYear(), this.getMonth()+1, 0);
//     return d.getDate();
// }

