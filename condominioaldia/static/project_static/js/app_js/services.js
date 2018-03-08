var condominioAlDiaAppServices = angular.module('condominioAlDiaAppServices',[]);

condominioAlDiaAppServices.factory('tableServices', [ function( ){

        return {

            getCheckedRows: function( data_list, checked_row_name, return_key) {
                var checked_rows = []
                for(var i in data_list){
                  if (data_list[i][checked_row_name] == true){
                    checked_rows.push(data_list[i][return_key])
                  }
                }
                return checked_rows
            }
        };             
}]);

condominioAlDiaAppServices.factory('genericServices', [ '$uibModal','$q',function( $uibModal, $q ){

        return {

            confirmModal: function( question) {
              var deferred = $q.defer();
              var modalInstance = $uibModal.open({
                  ariaLabelledBy: 'modal-title',
                  ariaDescribedBy: 'modal-body',
                  //animation: $scope.animationsEnabled,
                  templateUrl: 'static/ng_templates/modals/confirmModal.html',
                  controller: 'confirmModalController',
                  size: 'sm',
                  resolve: {
                    question: function(){
                      return question;
                    }  
                  }
              });
              modalInstance.result.then(function (response) {
                deferred.resolve(response);
              })
                return deferred.promise;
            },
            alertModal: function( message, heading, size ) {
              var deferred = $q.defer();
              var modalInstance = $uibModal.open({
                  ariaLabelledBy: 'modal-title',
                  ariaDescribedBy: 'modal-body',
                  animation: true,
                  templateUrl: 'static/ng_templates/modals/alertModal.html',
                  controller: 'alertModalController',
                  size: size||'sm',
                  resolve: {
                    message: function(){
                      return message;
                    },
                    heading: function(){
                      return heading;
                    }
                  }
              });
              modalInstance.result.then(function (response) {
                deferred.resolve(response);
              })
                return deferred.promise;
            }
        };             
}]);


//THIS SERVICE REQUIRED GOOGLE MAPS INITIALIZATION
condominioAlDiaAppServices.factory('googleMapsApiService', [ '$http', '$q',function( $http, $q ){

        return {

            getAutionList: function( ) {
                //var deferred = $q.defer();
                var url = 'api/auctions/';
                return $http({ 
                    method: 'GET', 
                    url: url
                })
                //return deferred.promise;
            }
        };             
}]);



condominioAlDiaAppServices.factory('socialAppService', function($q, $http, $window) {

  //THIS SERVICE REQUIRES THAT THERE BE A FB OBJECT GENERATED AS PER Facebook SDK INSTRUCTIONS

    return {

        getFbToken : function(){
          var deferred = $q.defer();
          FB.login(function(FbResponse){

            if(FbResponse.status == 'connected'){
              var FbData = {
                  'access_token': FbResponse.authResponse.accessToken
              }

              $http.post( 'rest-auth/facebook/', FbData )
                .success(function(DRFResponse){
                  //APP TOKEN AQUIRED
                  $window.sessionStorage.setItem( 'token', DRFResponse.key );
                  deferred.resolve('Success');
                })
                .error(function(DRFError){//deferred.reject(errors);})
                  deferred.reject(DRFError);
                })
            }

          }, {
    scope: 'email', 
    return_scopes: true
});
          return deferred.promise;
        },

        getGoogleToken: function() {
            var deferred = $q.defer();
            GoogleAuth  = gapi.auth2.getAuthInstance();
            GoogleAuth.signIn()
            .then(function( googleResponse){

                //$window.sessionStorage.setItem('profilePicture', googleResponse.Zi)
                var googleData = {
                    'access_token': googleResponse.Zi.access_token
                }

                $http.post( 'rest-auth/google/', googleData )
                .success(function(DRFResponse){

                  //APP TOKEN AQUIRED
                  $window.sessionStorage.setItem( 'token', DRFResponse.key );

                  deferred.resolve('Success');
                })
                .error(function(DRFError){//deferred.reject(errors);})
                  deferred.reject(DRFError);
                })
              
            })
            // .then(function(googleErrorResponse){
            //   deferred.reject(googleErrorResponse);
            // })
    
            return deferred.promise;
        }
    }
}); 


condominioAlDiaAppServices.factory('yearListService', function ($window, $q) {

      return {

        request: function() {
          var user_string = $window.sessionStorage.getItem('userDataString');
          var yearList =[];
          if (user_string){
            var year_joined = new Date(JSON.parse(user_string).date_joined).getFullYear();
            var this_year = new Date().getFullYear();

            do {
                yearList.push(year_joined)
                year_joined++;
            }
            while ( year_joined<= this_year);
              return yearList;
          }
          return yearList ;

        }
      }
});

condominioAlDiaAppServices.factory('throttleInterceptor', function ($window, $q, $location, $rootScope, $injector) {

    return {
        request: function(config) {
            var $http = $injector.get('$http'),
            copiedConfig = angular.copy(config);

            delete copiedConfig.headers;
            function configsAreEqual(pendingRequestConfig) {
            var copiedPendingRequestConfig = angular.copy(pendingRequestConfig);

            delete copiedPendingRequestConfig.headers;

            return angular.equals(copiedConfig, copiedPendingRequestConfig);
            }

            if ($http.pendingRequests.some(configsAreEqual)) {
              //return null;
              return $q.reject('duplicate request');
            }
            return config || $q.when(config);
        }
    }
});

condominioAlDiaAppServices.factory('helpService', function ($window, $q, $location, $rootScope, $injector, $uibModal) {
      return {
        check: function() {

          switch($location.path()) {
              case '/perfil':
                  var items = {
                      'Numeros telefonicos':'Puede modificar/agregar sus numeros telefonicos y asi los propietarios podran contactarlo(a).',
                      'Seguridad' : 'Le recomendamos cambiar su contraseña con regularidad para garantizar la seguridad de su cuenta.',
                      'Logo' : 'En caso de los condominios podran agregar/modificar/eliminar el logo de su condominio.'
                  };  
                  break;
              case '/junta_condominio':
                  if ($rootScope.userData.user_type == 'condominio'){
                    var items = {
                        'Agregar Miembro':'En caso de ser condominio puede agregar miembro de la junta de condominio.',
                        'Borrar Miembro' : 'Le permite borrar miembros de la junta de condominio.'                  
                      };                    
                  }else if ($rootScope.userData.user_type == 'inquilino'){
                    var items = {
                        'Informacion':'Aca podra ver la informacion de contacto y de la junta de condominio.',
                      };    
                  }
  
                  break;
              case '/paginas_amarillas':
                  var items = {
                      'Agregar contacto':'Cualquier informacion de contacto de interes para los propietarios puede ser visualizada o registrada (solo condominios) aca. Ej: Casilla de vigilancia, servicios de plomeria, piscina, fumigacion etc.'                    };  
                  break;
              case '/sms_email':
                  var items = {
                      'Informacion':'Envie correos electronicos o SMS ( muy pronto), a los propietarios segun su deuda, miembros de la junta, etc.'
                  };  
                  break;
              case '/encuestas':
                  var items = {
                      'Registrar encuesta':'Proponga encuestas a preguntas cuya respuesta puede ser contestada con un "SI" o "NO", los propietarios podran responder desde su cuenta condominioaldia.',
                      'Buscar por mes' : 'Podra consultar el historico de las encuestas realizadas.'                  
                    };  
                  break;
              case '/cartelera':
                  var items = {
                      'Agregar a cartelera':'Le permite colocar anuncios en la cartelera virtual, la cual podra ser leida por los propietarios al ingresar a sus cuentas.',
                    };  
                  break;
              case '/bancos':
                  var items = {
                      'Agregar cuenta':'Registre sus cuentas bancarias con sus balances iniciales para la fecha solicitada. Esto le permitira a condominioaldia calcular el balance segun los ingresos/egresos al momento de cada corte mensual (relacion de cuota) para su verificacion.',
                      'Informacion adicional' :'Una vez haya generado un corte mensual (relacion de cuotas) no podra modificar los datos iniciales de las cuentas relacionadas. Podra registrar nuevas cuentas.'
                    };  
                  break;
              case '/cobranzas':
                  var items = {
                      'Agregar cuenta':'Registre sus cuentas bancarias con sus balances iniciales para la fecha solicitada. Esto le permitira a condominioaldia calcular el balance segun los ingresos/egresos al momento de cada corte mensual (relacion de cuota) para su verificacion.',
                      'Informacion adicional' :'Una vez haya generado un corte mensual (relacion de cuotas) no podra modificar los datos iniciales de las cuentas relacionadas. Podra registrar nuevas cuentas.'
                    };  
                  break;
              case '/select_inmueble':

                  var items = {
                      'Seleccione un Inmueble ( Ver )':'Seleccione el inmueble que desea gestionar.',
                      'Detalles del condominio' : 'Haciendo click en el nombre del condominio podra ver detalles.',
                  };
                  break;
              case '/inicio':
                  var items = {
                      'inmuebles':'Cargue o elimine inmuebles, registre propietarios, organize inmuebles por categorias.',
                      'junta de condominio' : 'Cargue/Elimine miembros de la junta de condominio.',
                      'encuestas' : 'Encueste a sus propietarios.',
                      'finanzas' : 'Bancos, cobranzas, ingresos, egresos, facturas y relaciones de cuotas.',
                      'bancos' : 'Cargue la informacion de sus cuentas bancarias, esto nos permite llevar el balance y corroborar al final de cada mes.',
                      'cobranzas' : 'Cargue directamente al propietario, ya sea multas, alquileres, etc.',
                      'ingresos': 'Registre pagos de propietarios o particulares, apruebe o rechace pagos reibidos y consulte su historico de ingresos.',
                      'egresos': 'Registre gastos que seran distribuidos segun la ley horizontal (segun porcentaje alicuota). Consulte su historico de gastos.',
                      'facturacion': 'Pague y revise sus facturas, consulte su historico de facturacion.',
                      'relaciones de cuotas' : 'Aca podra generar corte de cada mes, cargar egresos detallados (que no se distribuyen por ley horizontal) y consultar su historico de cortes.',
                      'cartelera' : 'La cartelera virtual le permite publicar cualquier notificacion que pretenda que vean los propietarios. Horarios de cortes, notificacion de fumigacion, etc.',
                      'paginas amarillas' : 'Cargar informacion de contacto relevante para sus propietarios. Ej: contacto de vigilancia, policia, plomero, etc.',
                      'Sms/Email' : 'Envie notificaciones cortas de correo electronico (sms muy pronto), discrimine segun quienes deben, junta de condominio, etc.'

                  };  
                  break;
              case '/inquilino_inicio':
                  var items = {
                      'Blog':'Podras escribir informacion/mensajes que el resto de los integrantes del condominio podran ver.',
                      'Cartelera':'Informacion de para los propietarios ( Horarios de cortes, normas de convivencia, etc)',
                      'Resumen':'Muestra el resumen del propietario de cada mes',
                      'Ver Inmuebles' : 'Aca podra seleccionar tus inmuebles',
                      'Pagos' : 'Registra/gestiona tus pagos.',               
                      'Cobranzas' : 'Revisa/paga tus cobranzas',
                      'Junta de condominio' : 'Ver informacion de la junta de condominio',
                      'Encuestas' : 'Participa en encuestas creadas por su condominio',
                      'Relacione de cuotas' : 'Revisa los cortes mensuales generados por tu condomio',
                      'Ingresos del condominio' : 'Consulta los pagos/ingresos recibidos por el condominio.',
                      'Egresos del condominio' : 'Consulta los gastos/egresos del condominio.',
                      'Paginas Amarillas' : 'Listado de informacion de contacto de interes de tu condominio. Ej: Policia, Bomberos, etc.',


                  };  
                  break;

              case '/inmuebles':
                  var items = {
                      'Agregar Inmueble':'Registre inmuebles que forman parte de su condominio, deben totalizar 100% para poder habilitar otras opciones. El balance inicial representa el saldo del inmueble al inicio del mes en que usted se registro con Condominioaldia. ',
                      'Borrar inmuebles' : 'Puede eliminar inmuebles solo si no ha generado cortes (relacion de cuotas).',
                      'Registrar Categorias' : 'Le permite clasificar los inmuebles segun categorias de su preferencia para hacer el manejo de los mismos mas facil. Ej: Piso 1, terreno, casa, townhouse, etc.',
                      'Solicitar carga de inmuebles' : 'Si necesita ayuda registrando los inmuebles podemos ayudarle. Cargue un archivo de excel o CSV segun el ejemplo proporcionado.',
                  };
                  //code block
                  break;
              default:
                  var items ={};
                  //code block
          } 

                if ($rootScope.helpModalOpened ==false || !$rootScope.helpModalOpened){
                  var modalInstance = $uibModal.open({
                      ariaLabelledBy: 'modal-title',
                      ariaDescribedBy: 'modal-body',
                      animation: true,
                      templateUrl: 'static/ng_templates/modals/help_menu.html',
                      controller: 'help_menuModalController',
                      size: 'lg',
                      resolve:{
                        help_items:function(){
                          return items;
                        }
                      }
                  });
                  
                  modalInstance.result.then(function (status) {
                    $rootScope.helpModalOpened =false;
                  });
                }

        } 
  }
});

condominioAlDiaAppServices.factory('tokenAuthInterceptor', function ($window, $q, $location, $rootScope, $injector) {
    return {
        request: function(config) {
            config.headers = config.headers || {};
            if ($window.sessionStorage.getItem('token')) {
              // may also use localStorage
                config.headers.Authorization = 'Token ' + $window.sessionStorage.getItem('token');
            }
            return config || $q.when(config);
        },
        // optional method
       'responseError': function(rejection) {
        console.log(rejection)
            if (rejection.status === 401) {
              //sessionStorage.removeItem('token');
              sessionStorage.clear();
              //window.location = "/account/login?redirectUrl=" + Base64.encode(document.URL);
              window.location ='/';
              var rejection= rejection.statusText;

            }
            else if (rejection.status === 403){
                var rejection= rejection.statusText;
                window.location ='/';
            }else if (rejection.status === 404){
                var rejection= rejection.statusText;
                window.location ='/';
            }
          return $q.reject(rejection);
        },
        response: function(data) {
          if (!$rootScope.alerts){
            $rootScope.alerts=[];
          }
          if (data.status === 200) {
            //var alerts_present=true;
            if(data.headers().activo){
              if(data.headers().activo.toBoolean()== true){
                $rootScope.alerts=[];
              }else if(data.headers().activo.toBoolean()== false){
                  $rootScope.alerts.push( { type: 'danger', msg: 'Sus inmuebles deben totalizar 100%' });
                  $rootScope.marginTop = '90px;'
                  //alerts_present=true;
              }
              if($rootScope.userData){
                $rootScope.userData.detalles_usuario.activo = data.headers().activo.toBoolean();
              }
            } 

            if(data.headers().has_bank_account&&$rootScope.alerts.length==0){

              if(data.headers().has_bank_account.toBoolean()== false){
                  $rootScope.alerts.push( { type: 'danger', msg: 'Agregue una cuenta bancaria' });
                  alerts_present=true;
              }
              if($rootScope.userData){
                $rootScope.has_bank_account = data.headers().has_bank_account.toBoolean();
                if($rootScope.has_bank_account==false){
                  $rootScope.marginTop ='90px;'
                }
              }
              
            }  

            if(data.headers().retrasado&&$rootScope.alerts.length==0){
              //when a condominio is behind
                
              $rootScope.retrasado = (data.headers().retrasado).toBoolean();
              if($rootScope.retrasado == true){
                    $rootScope.alerts.push( { type: 'danger', msg: 'Su perfil presenta retrasos.' });
              }
            }

            if(data.headers().affiliate_need_account&&$rootScope.alerts.length==0){
              //when a affiliate needs to add an account
              $rootScope.need_account = (data.headers().affiliate_need_account).toBoolean();
              if($rootScope.need_account == true){
                $rootScope.account_message= 'Registre cuenta bancaria para cada pais donde tiene condominio.';
              }
              // if(need_account == true){
              //   $rootScope.need_account= need_account;
              // }
            }

// ////////////////////
          }else if (data.status === 401) {

              sessionStorage.removeItem('token');
              $location.path('/'); 
          }
          // if(alerts_present==false){
          //   $rootScope.alerts =[];
          //   $rootScope.showAlerts = false;
          // }else{
          //   $rootScope.showAlerts = true;
          // }
          
          return data || $q.when(data);
        }
    };
});



condominioAlDiaAppServices.factory('userSessionServices', ['$http', '$window', '$location', '$q', '$rootScope', 'genericServices','$uibModal',
  function( $http, $window, $location, $q,$rootScope, genericServices, $uibModal ){
    var errors =  {};
    var _identity = undefined, _authenticated = false;

    return{
      setRootScope : function( next ){
        $rootScope.marginTop ='70px;'
        var user_authenticated = sessionStorage.getItem('token') ? true:false;
        // $rootScope.redirect= function(url){
        //   $location.path(url);
        // }
        $rootScope.url = $location.path();
        if (user_authenticated== true){
            $rootScope.userData = JSON.parse(sessionStorage.getItem('userDataString'));
            if ($rootScope.need_account==true||$rootScope.userData.detalles_usuario.activo==false){
              $rootScope.marginTop ='90px;'
              console.log
            }
            //var alerts_present=false;
            if($rootScope.userData.user_type == 'condominio'){
              if($rootScope.retrasado==true){
                $rootScope.marginTop ='90px;'
              }


            }else if($rootScope.userData.user_type == 'inquilino'){//IF PROPIETARIO...
              $rootScope.userData.detalles_usuario.pais = {};
              $rootScope.marginTop ='90px;'
              $rootScope.condominio_nombre = sessionStorage.getItem('condominio_nombre');
              $rootScope.nombre_inmueble = sessionStorage.getItem('nombre_inmueble');
              $rootScope.userData.detalles_usuario.pais.moneda =sessionStorage.getItem('moneda');
              $rootScope.userData.detalles_usuario.logo =sessionStorage.getItem('logo');
              $rootScope.show_property_tag =true;
            }

            $rootScope.nombre_completo = $rootScope.userData.first_name + ' ' + $rootScope.userData.last_name;
            $rootScope.userAuthenticated = true;
            //$rootScope.brandUrl = '#/' +this.getBaseUrl();
            $rootScope.title = next.data.pageTitle;
        }else{
            $rootScope.userAuthenticated = false;
            //$rootScope.brandUrl = '#/landing_page';
        }
        

      },
      canAccessUrl : function( next, event ){
          if (next.showSidebar==true){
            $rootScope.showSidebar=true;
          }else{
            $rootScope.showSidebar=false;
          }
          var user_authenticated = sessionStorage.getItem('token') ? true:false;
          // if (user_authenticated== true) {
          //   var user_data = JSON.parse(sessionStorage.getItem('userDataString'));
          //   var user_role= user_data.user_type;
          //   var user_active = user_data.detalles_usuario.activo;
          // } 

          var canAccessUrl= false;

          //DETERMINE IF USER IS AUTHENTICATED
          if(next.isLogin == undefined){
            canAccessUrl = true;
          }
          else if(user_authenticated==true){
            var user_data = JSON.parse(sessionStorage.getItem('userDataString'));
            var user_role= user_data.user_type;
            var user_active = user_data.detalles_usuario.activo;

            //GET USER TYPE 

            var user_role= user_data.user_type;

            if(next.isLogin == true){
              //DETERMINE IF VIEW CORRESPONDS TO USER ROLE
                if(user_role == next.viewRole || next.viewRole ==undefined){
                  
                  canAccessUrl = true;

                  //IF NEXT VIEW IS A CONDO VIEW, CHECK IF VIEW ES AN "ACTIVO" VIEW
                  if( next.viewRole == 'condominio' &&  next.activo==user_data.detalles_usuario.activo  || next.activo ==undefined){
                      canAccessUrl = true;
                  }else
                  {
                    canAccessUrl = false;
                  }
                }
              //DETERMINE IF VIEW CORRESPONDS TO USER ROLE
            }else{
              canAccessUrl = false;
            }
          }else{
            
            if((next.isLogin==false)){
              canAccessUrl = true;
            }
            //DETERMINE IF VIEW REQUIRED AUTHENTICATED USER
          }

          if (next.isPayed == true && user_data.user_type =='condominio' && user_data.detalles_usuario.retrasado == true){
            canAccessUrl= false;
          }
          if (user_authenticated== true){
            $rootScope.brandUrl = '#/' +this.getBaseUrl();
          }else{
            $rootScope.brandUrl = '#/landing_page';
          }
          if ( canAccessUrl == false){
            event.preventDefault();
            $window.location.href=$rootScope.brandUrl
          }

          return canAccessUrl;
        },
        logIn : function( credentials ){
            var deferred = $q.defer();
            var url = 'rest-auth/login/';
            $http.post(url, credentials).success(function(token){
              if( token!= null ){
                deferred.resolve(token.key);
                $window.sessionStorage.setItem('shoppingCart', '[]')
                $window.sessionStorage.setItem( 'token', token.key );

              }else{
                deferred.reject( 'email/password error' );
              }

            })
            .error( function( error,status ){
              if( error != null ){
             
                for(var field in error){
                  if(field === 'non_field_errors'){
                    errors[field] = error[field].join(', ')
                  }
                }
      
                  deferred.reject( errors );
                
              }    


            })
            return deferred.promise;
        },
        logOut : function(){
            var url = 'rest-auth/logout/'
            $http({
              method: 'POST',
              url: url
            }).then(function (response) {
              if (response.status == 200){
                $window.sessionStorage.clear();
                for (var prop in $rootScope) {

                   // Check is not $rootScope default properties, functions
                   if (typeof $rootScope[prop] !== 'function' && prop.indexOf('$') == -1 && prop.indexOf('$$') == -1) {

                      delete $rootScope[prop];

                   }
                } 
                $location.path('/');      
              }


                // this callback will be called asynchronously
                // when the response is available
              }, function errorCallback(response) {
                // called asynchronously if an error occurs
                // or server returns response with an error status.
              }); 
        },
        isAuthenticated : function(){
          var token = sessionStorage.getItem('token');
          return(token)? true : false;
        },
        updateSessionStorage : function( newUserDataObj ){
          sessionStorage.setItem('userDataString', JSON.stringify(newUserDataObj));
          return 'success';
          // var token = sessionStorage.getItem('token');
          // return(token)? true : false;
        },
        updateSessionStorageKey : function( obj, path, newVal ){
                var deferred = $q.defer();
            //function set(path, value) {
                var schema = obj;  // a moving reference to internal objects within obj
                var pList = String(path).split('.');
                var len = pList.length;
                for(var i = 0; i < len-1; i++) {
                    var elem = pList[i];
                    if( !schema[elem] ) schema[elem] = {}
                    schema = schema[elem];
                }

                schema[pList[len-1]] = newVal;
                deferred.resolve(schema)
                return deferred.promise;
            //}
        },
        getBaseUrl : function(  ){
          var user_logged_in = sessionStorage.getItem('token') ? sessionStorage.getItem('token'):null;
          var url = '/';
          if (user_logged_in) {
            var user_type= JSON.parse(sessionStorage.getItem('userDataString')).user_type;
            //var deferred = $q.defer();

            if (user_type =='condominio'){
              url ='inicio';
            }else if(user_type =='inquilino'){
              var inmueble_set =sessionStorage.getItem('inmueble');
              if(!inmueble_set){
                url ='select_inmueble';
              }else{
                url ='inquilino_inicio';
              }

            }else if(user_type =='affiliate'){
              url ='affiliate_inicio';
            }
            return url;
            //deferred.resolve(url)
            //return deferred.promise;     
          }

            //}
        },
        // getSessionStorage : function( ){
        //   var userDataString = sessionStorage.getItem( 'userDataString')
        //   if( userDataString ){
        //     return JSON.parse( userDataString );
        //   }
        //   return userDataString;
        // },
        userProfile : function()
        {
          var deferred = $q.defer();
          var userDataString = sessionStorage.getItem( 'userDataString');
          if( userDataString ){
            deferred.resolve(JSON.parse( userDataString));
            //return JSON.parse( userDataString );
          }else{
            //var deferred = $q.defer();
            //var token = {};
            //var token = sessionStorage.getItem('token');
            //var url = $location.protocol() + "://" + $location.host() + ":" + $location.port() + '/api/users/';
            //var url = 'api/users/'

            $http({
              method: 'GET',
              url: 'api/users/'
            }).then(function successCallback( response ) {
                // $window.sessionStorage.setItem('userDataString', JSON.stringify(response.data[0]));
                // var result = {};
                // result.status = 200;
                console.log(response)
                deferred.resolve( response.data[0] );
                // this callback will be called asynchronously
                // when the response is available
              }, function errorCallback(error) {
                deferred.resolve(error);
                // called asynchronously if an error occurs
                // or server returns response with an error status.
              });

            return deferred.promise;
          }
        }
      }

}]);

condominioAlDiaAppServices.filter('trustedhtml', 
   function($sce) { 
      return $sce.trustAsHtml; 
   }
);


condominioAlDiaAppServices.factory('arrayServices', function () {

      return {

        arrayFromObjArray: function(arrayOfObjects, key) {       

          var res = [];
          for (var i in arrayOfObjects){
            res.push(arrayOfObjects[i][key])

          }
          return res;


         },
        findObjectInArray: function(arrayOfObjects, key, value) {      

          for (var i in arrayOfObjects){
            if(arrayOfObjects[i][key] == value){
              return arrayOfObjects[i];
            }
          
          }
          return {};
         }



      }
});

condominioAlDiaAppServices.factory('screen_services', function ($window) {

      return {

        screen_width: function() {       
          return $window.innerWidth;
         }
      }
});