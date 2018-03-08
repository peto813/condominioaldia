var condominioAlDiaAppControllers = angular.module('condominioAlDiaAppControllers',['condominioAlDiaModalControllers']);

condominioAlDiaAppControllers.controller('testController', ['$scope','$http',
	function( $scope, $http ){
		$scope.test=function(){
			$http.get('api/test/').success(function(response){
				console.log(response)
			})
		}

}])


condominioAlDiaAppControllers.controller('instapagoController', ['$scope', '$uibModal','$http','payment_params','$location',function( $scope, $uibModal, $http,payment_params, $location ){

  	$scope.instapago = {};
  	$scope.instapago.monto = Math.abs(payment_params.balance);
  	$scope.instapago.description =payment_params.payment_type;
 	$scope.formats = ['MM-yy','dd-MMMM-yyyy', 'yyyy/MM/dd', 'dd.MM.yyyy', 'shortDate'];
 	$scope.format = $scope.formats[0];
    
    $scope.openInstaPagoVoucher = function(size, voucher){
	    var modalInstance = $uibModal.open({
	        ariaLabelledBy: 'modal-title',
	        ariaDescribedBy: 'modal-body',
	        animation: $scope.animationsEnabled,
			templateUrl: 'static/ng_templates/modals/instaPagoVoucherModal.html',
	        controller: 'voucherModalController',
	        size: size,
	        resolve: {//MAKES INMUEBLES LOCAL SCOPE PASSED TO MODAL CONTROLLER IN LINE 186
	          voucher: function(){
	            return String(voucher);
	          }             
	        }
	    });
		modalInstance.result.then(function (response) {
			if($scope.instapago.description =='pp'){
				$location.path('pagos_inquilino');
			}
		});
	}


  $scope.reset = function() {
    $scope.user = angular.copy($scope.master);
  };

  $scope.submitIstapago = function(){
  		$http.post('api/instapago/', $scope.instapago).success(function(response){
            if (response.code ==201){
              	$scope.voucher = '<h4 class="voucherHeader">'+ response.message +'</h4>'+response.voucher;
            	$scope.openInstaPagoVoucher('md',response.voucher )
            }else{
            	alert(response.message);
            }
  		})
      
  }

}]);

// instpagoAngularApp.controller('voucherModalController', function( $scope, postRequest, $uibModalInstance, voucher ) {
//   $scope.voucher = voucher;

//     $scope.cancel = function () {
//       $uibModalInstance.dismiss('cancel');
//       window.location = '/';
//     };


// });



condominioAlDiaAppControllers.controller('contactUsController', ['$scope', '$http',
	function( $scope, $http ){
		$scope.formData = {};
		$scope.sendEmail = function(){
			if ($scope.contactUsForm.$valid){
				$http.post('api/contactus/', $scope.formData).success( function( response, status ){
					if(status == 200){
						$scope.formData = {};
						$scope.contactUsForm.$setUntouched();
						$scope.contactUsForm.$setPristine();
						alert(response)
					}
				})
			}
		}
		//$scope.pageClass = 'page-home'
}])


// condominioAlDiaAppControllers.controller('egresos_detalladosController', ['$scope','$http','$window','$uibModal','context','genericServices','$filter','$rootScope',
// 	function( $scope, $http, $window,$uibModal, context, genericServices, $filter, $rootScope ){

// 		$scope.context= context;
// 		$scope.inmuebles = {};
// 		$scope.extra_col_map = [];//array of extra column objects

// 		//COLUMN TYPES ARE ORIGINAL AND EGRESO
// 		$scope.inmuebles.cols =[{name:'Inmueble', type:'original'}, {name:'Residente', type:'original'} ];
// 		$scope.added_cols_arr = [];//array of extra column names
// 		$scope.extraCols = [];

// 		//var original= $scope.inmuebles.cols.slice(0);
// 		$scope.inmuebles.rows = $scope.context.inmuebles;


// 		$scope.saveCol= function(){
// 			//LOOK FOR UNSAVED EGRESO COLUMNS
// 			if ($scope.added_cols_arr.length>0){
// 				//add pertinent inmuebles to the extra col map
// 				// $http.post('api/egresos_detallados/', $scope.extra_col_map).success(function(response){
// 				// })
// 			}
// 			return false;
// 		}

// 		$scope.redirect = function(){
// 			$window.location.href = '#/egresos';
// 		}

// 		$scope.getExtraColIndex= function(column){
// 			for ( var i in $scope.inmuebles.rows){
// 				for (var j in $scope.inmuebles.rows[i]['extra_cols']){
// 					if($scope.inmuebles.rows[i]['extra_cols'][j]['name']==column.name){
// 						return j;
// 					}
// 				}
// 			}
// 		}


// 		$scope.get_total=  function(column){
// 			var total=  0;
// 			switch(column.name) {
// 			    case 'Inmueble':
// 			    	total=  '-';
// 			        break;
// 			    case 'Residente':
// 					total=  '-';
// 			        break;
// 			    default:
// 			    	for (var i in $scope.filtered_inmuebles){
// 			    		for (var j in $scope.filtered_inmuebles[i]['extra_cols']){
// 			    			if($scope.filtered_inmuebles[i]['extra_cols'][j]['name']==column.name){
// 			    				total += $scope.filtered_inmuebles[i]['extra_cols'][j]['monto'];
// 			    			}
// 			    		}
// 			    	}
// 			    	total = $rootScope.userData.detalles_usuario.pais.moneda +' ' + $filter('number')(total,2)
// 			    	break;
// 			} 
// 			return total;
// 		}

// 		$scope.getData= function(row, column){
// 			switch(column.name) {
// 			    case 'Inmueble':
// 			    	return row.nombre_inmueble
// 			        break;

// 			    case 'Residente':
// 					return $filter('capfirstlettereachword')(row.propietario)
// 			        break;
// 			    case 'Balance Presente':
// 			    	var returnString= $rootScope.userData.detalles_usuario.pais.moneda +' ' +$filter('number')(row.deuda_actual,2);
// 					return returnString;
// 			        break;
// 			    case 'Pagos':
// 			    	var returnString= $rootScope.userData.detalles_usuario.pais.moneda +' ' +$filter('number')(row.pagos,2);
// 					return returnString;
// 			        break;
// 			    case 'Cuota':
// 			    	var returnString= $filter('number')(  row.cuota, 2)
// 					return $rootScope.userData.detalles_usuario.pais.moneda+' '+String(returnString);
// 			        break;
// 			    case 'Balance Nuevo':
// 			    	var deuda_actual = row.deuda_actual;
// 			    	var cuota=row.cuota;
// 			    	var pagos=row.pagos;
// 			    	var total_extra_cols = 0;
// 			    	for (var i in row.extra_cols){
// 			    		total_extra_cols+=row.extra_cols[i]['monto']
// 			    	}
// 			    	//var total=Math.abs(parseFloat(deuda_actual)+parseFloat(pagos)-(parseFloat(cuota)+parseFloat(total_extra_cols)));
// 			    	var total=parseFloat(deuda_actual)+parseFloat(pagos)-(parseFloat(cuota)+parseFloat(total_extra_cols));
// 			    	var returnString= $rootScope.userData.detalles_usuario.pais.moneda+' '+String($filter('number')(total,2))
// 					return returnString;
// 			        break;			        

// 			    default:
// 			    	var returnString = $filter('number')((row[column]['monto']), 2)
// 			    	return returnString
// 			    	break;
// 			} 
// 			return column;
// 		}


// 		$scope.addEgreso = function(){
// 	        var modalInstance = $uibModal.open({
// 	            ariaLabelledBy: 'modal-title',
// 	            ariaDescribedBy: 'modal-body',
// 	            animation: true,
// 	            templateUrl: 'static/ng_templates/modals/egresoDetalladoModal.html',
// 	            controller: 'egresoDetalladoModalController',
// 	            size: 'md',
// 	            resolve: {
// 		            // inmuebles: function() {
// 		            //     return $scope.inmuebles.rows
// 	            	// },
// 		            cuentas: function() {
// 		                return $scope.context.cuentas;
// 	            	}          	
// 	            }
// 	        });
// 		    modalInstance.result.then(function (extraColumnFormdata) {
// 		    	$scope.inmuebles.cols.splice($scope.inmuebles.cols.length, 0, extraColumnFormdata);
// 		    	//var extra_col_obj ={};
		    	
// 		    	for (var i in $scope.inmuebles.rows){
// 		    		var data = {
// 		    			name:extraColumnFormdata.name,
// 		    			monto:0
// 		    		};

// 		    		$scope.inmuebles.rows[i].extra_cols.push(data);
// 		    		if ($scope.added_cols_arr.indexOf(extraColumnFormdata.name)===-1){
// 		    			$scope.extra_col_map.push(extraColumnFormdata)
// 				    	$scope.added_cols_arr.push(extraColumnFormdata.name);
// 		    		}
// 		    	}
// 		      	genericServices.alertModal('Columna "'+ extraColumnFormdata.name +'" agregada a la tabla.');
// 		    });









// 		}

// }])


condominioAlDiaAppControllers.controller('resumen_condominioController', ['$scope','$http','context',
	function( $scope, $http, context ){
		$scope.context= context;
		$scope.get_total = function(){
			var total = $scope.context.pagos_recibidos+$scope.context.total_owed-($scope.context.egresos_totales_periodo+$scope.context.cobranzas_condo_sum);
			return total;
		}
		$scope.now=function(){
			return new Date();
		}

}])



condominioAlDiaAppControllers.controller('resumen_propietarioController', ['$scope','$http','context',
	function( $scope, $http, context ){

		$scope.context = context;
		$scope.active_month=new Date(context.maxDate);
		$scope.dt = new Date(context.maxDate).toUTC();
		$scope.maxDate = new Date(context.maxDate).toUTC();
		$scope.minDate = new Date(context.minDate).toUTC();
 		$scope.formats = ['dd-MMMM-yyyy', 'yyyy/MM/dd', 'dd.MM.yyyy', 'shortDate'];
 		$scope.format = $scope.formats[0];
		$scope.open1 = function() {
			$scope.popup1.opened = true;
		};
		$scope.popup1 = {
			opened: false
		};
		$scope.dateOptions = {
			minMode: 'year',
			initDate :$scope.maxDate,
			maxDate: $scope.maxDate,
			minDate: $scope.minDate
		};
        $scope.queryDate = function(){
            var url = 'api/resumen_propietario/?month_created=' + $scope.dt.toISOString();
            $http.get(url).success(function(context){
                $scope.cobranzas_data = context.data;
                $scope.maxDate = context.maxDate;
                $scope.minDate = context.minDate;
                $scope.active_month = new Date($scope.dt);
            })
        }

        $scope.getPDFReport= function(resumen){
        	var url = 'api/reporte_prop_pdf/?month_created='+ resumen.mes;
        	//
        	window.open(url);
        }
}])
condominioAlDiaAppControllers.controller('cobranzas_propietarioController', ['$scope','context','$http','$uibModal','$rootScope', '$filter',
	function( $scope, context, $http, $uibModal, $rootScope, $filter ){
		$scope.active_month = context.active_month;
		$scope.cobranzas_data = context.data;
		$scope.inmuebles = context.inmuebles;
		$scope.active_month=new Date(context.active_month);
		$scope.dt = new Date(context.maxDate).toUTC();
		$scope.maxDate = new Date(context.maxDate).toUTC();
		$scope.minDate = new Date(context.minDate).toUTC();
 		$scope.formats = ['dd-MMMM-yyyy', 'yyyy/MM/dd', 'dd.MM.yyyy', 'shortDate'];
 		$scope.format = $scope.formats[0];
		
 		$scope.getCobranzaMonto=function(cobranza){
 			var monto;
 			if(cobranza.porcentaje ){
 				monto ='% ' + String(cobranza.porcentaje*100)+ ' de cuota mensual';
 			}
 			else if(cobranza.monto && $rootScope.userData){
 				monto = 1
 				monto =String($rootScope.userData.detalles_usuario.pais.moneda)+' '+String($filter('number')(cobranza.monto, 2))
 			}
 			return monto;
 		}

		$scope.open1 = function() {
			$scope.popup1.opened = true;
		};
		$scope.popup1 = {
			opened: false
		};
		$scope.dateOptions = {
			minMode: 'month',
			initDate :$scope.maxDate,
			maxDate: $scope.maxDate,
			minDate: $scope.minDate
		};

		$scope.agregarPagoModal = function(cobranza){
			if (cobranza){
				if (cobranza.pagado ==false || cobranza.pagado ==true ){
					return false;
				}
			}
	        var modalInstance = $uibModal.open({
	            ariaLabelledBy: 'modal-title',
	            ariaDescribedBy: 'modal-body',
	            animation: true,
	            templateUrl: 'static/ng_templates/modals/propietarioPaymentMethodModal.html',
	            controller: 'pagoInquilinoModalController',
	            size: 'md',
	            resolve: {
		            balance: function() {
		            	return cobranza.monto;
	            	},
		            payment_type: function() {
		            	return 'cobranza';
	            	},
		            cobranza_id: function() {
		            	return cobranza.id;
	            	}         	   	        	
	            }
	        });
		    modalInstance.result.then(function (ingresos) {
		     // $scope.ingresos = ingresos;
		    });
		}

        $scope.queryDate = function(){
            var url = 'api/cobranzas_propietario/?month_created=' + $scope.dt.toISOString();
            $http.get(url).success(function(context){
                $scope.cobranzas_data = context.data;
                $scope.maxDate = context.maxDate;
                $scope.minDate = context.minDate;
                $scope.active_month = new Date($scope.dt);
            })
        }
}])


condominioAlDiaAppControllers.controller('CobranzasController', ['$scope','context','$uibModal','genericServices','$http','$filter','$rootScope',
	function( $scope, context, $uibModal, genericServices, $http,$filter,$rootScope ){

		$scope.active_month = context.active_month;
		$scope.cobranzas_data = context.data;
		$scope.inmuebles = context.inmuebles;
		$scope.active_month=new Date(context.active_month);
		$scope.dt = new Date(context.maxDate).toUTC();
		$scope.maxDate = new Date(context.maxDate).toUTC();
		$scope.minDate = new Date(context.minDate).toUTC();
 		$scope.formats = ['dd-MMMM-yyyy', 'yyyy/MM/dd', 'dd.MM.yyyy', 'shortDate'];
 		$scope.format = $scope.formats[0];
 		$scope.searchData ={};

		$scope.searchFuncComparator = function(actual, expected) {
		    return true;
		};

		function getCats(inmuebles){
			var categories_list = [];
			var id_list = [];
			for (var i in inmuebles){
				var categories = inmuebles[i].categories;
				for (var j in categories){
					var category = categories[j];
					if (id_list.indexOf(category.id)===-1){
						categories_list.push(category);
						id_list.push(category.id);
					}
				}
			}
			return categories_list;
		}
		$scope.categories = getCats($scope.inmuebles);


		/////////////////////////////
 		$scope.getRecipients= function(cobranza){
 			if(cobranza.recipiente =='especifico'){
 				var item = cobranza.destinatario[0]
 				var user = item.inquilino.user;
 				var response = user.first_name + ' '+user.last_name +'('+ item.nombre_inmueble +')';
 				return response;
 			}else{
 				return cobranza.recipiente;
 			}
 		}

 		$scope.getRecurrence=function(cobranza){
 			if (cobranza.recurrencia == 'una'){
 				cobranza='Una vez';
 			}else if(cobranza.recurrencia=='mensual'){
 				cobranza='Mensual';
 			}
 			return cobranza
 		}

 		$scope.getChargeType=function(cobranza){
 			var response;
 			if(cobranza.cobrar_cuando=='inmediato'){
 				response='inmedatamente';
 			}else if(cobranza.cobrar_cuando=='relacion'){
 				response='en proximo corte';
 			}
 			return response;
 		}

 		$scope.getCobranzaMonto=function(cobranza){
 			var monto;
 			if(cobranza.porcentaje ){
 				monto ='% ' + String(cobranza.porcentaje*100)+ ' de cuota mensual';
 			}
 			else if(cobranza.monto && $rootScope.userData){
 				monto = 1
 				monto =String($rootScope.userData.detalles_usuario.pais.moneda)+' '+String($filter('number')(cobranza.monto, 2))
 			}
 			return monto;
 		}

		$scope.any_checked= function(){
			for( var i in $scope.cobranzas_data){
				var item =  $scope.cobranzas_data[i];
				if(item.checked ==true){
					return false;
				}
			}
			return true;
		}

		$scope.open1 = function() {
			$scope.popup1.opened = true;
		};
		$scope.popup1 = {
			opened: false
		};
		$scope.dateOptions = {
			minMode: 'month',
			initDate :$scope.maxDate,
			maxDate: $scope.maxDate,
			minDate: $scope.minDate
		};

		$scope.cancelar = function(cobranza){
	 		var conrimationString  ="¿Esta seguro(a) de que desea cancelar esta cobranza?"
			genericServices.confirmModal(conrimationString)
				.then(function(confirmation){
					var data = {};
					var data_list=[];
					for (var i in $scope.cobranzas_data){
						var item =$scope.cobranzas_data[i];
						if(item.checked ==true){
							data_list.push(item.id);
						}
					}
					data['data_list'] = data_list;
					data['post_type']='delete';
		 			$http.post('api/cobranzas_condominio/?post_type=delete', data).success(function(cobranzas_data){
		 				$scope.cobranzas_data = cobranzas_data;
		 				genericServices.alertModal('Cobranza(s) borrada(s).');
		 			})
				});	
		}

		$scope.agregarCobranza= function(){
	        var modalInstance = $uibModal.open({
	            ariaLabelledBy: 'modal-title',
	            ariaDescribedBy: 'modal-body',
	            animation: true,
	            templateUrl: 'static/ng_templates/modals/cobranza_modal.html',
	            controller: 'cobranza_modalController',
	            size: 'md',
	            resolve: {
		            inmuebles: function() {
		            	return $scope.inmuebles;
	            	},
	            	categories:function(){
	            		return $scope.categories;
	            	}
	            }
	        });
		    modalInstance.result.then(function (response) {
		    	$scope.cobranzas_data= response;
	 			$scope.dt = $scope.maxDate;
	 			$scope.active_month = $scope.maxDate;
		      	genericServices.alertModal('¡ Cobranza registrada, el propietario ha sido notificado via correo electronico.');
		    });	
		}

        $scope.queryDate = function(){
            var url = 'api/cobranzas_condominio/?month_created=' + $scope.dt.toISOString();
            $http.get(url).success(function(context){
                $scope.cobranzas_data = context.data;
                $scope.maxDate = context.maxDate;
                $scope.minDate = context.minDate;
                $scope.active_month = new Date($scope.dt);
            })
        }
}])




condominioAlDiaAppControllers.controller('perfilController', ['$scope','perfilData','$uibModal','$http','genericServices','Upload','$rootScope',
	function( $scope, perfilData, $uibModal, $http, genericServices, Upload, $rootScope ){
		$scope.perfilData = perfilData;
		$scope.contactInfo = {};
		$scope.pwdData = {};
		$scope.contactInfo.telefono1 = perfilData.detalles_usuario.telefono1 ? perfilData.detalles_usuario.telefono1:'';
		$scope.contactInfo.telefono2 = perfilData.detalles_usuario.telefono2 ? perfilData.detalles_usuario.telefono2:'';
		$scope.contactInfo.logo = perfilData.detalles_usuario.logo;
		$scope.errors = {};

		$scope.otherElHeight= function(other_id){
			return String(document.getElementById(other_id).clientHeight) +'px';
		}

		$scope.pwdChange = function(){
			$scope.errors = {};
			$http.post('rest-auth/password/change/', $scope.pwdData).success(function(response){
				$scope.pwdData = {};
				$scope.cambioClaveForm.$setUntouched();
				$scope.cambioClaveForm.$setPristine();
				genericServices.alertModal('Contraseña modificada.');
			}).
			error(function(errors){
				$scope.errors = errors;
			})
		}


		$scope.updateContacInfo = function(file, error){

			var data = $scope.contactInfo;

			if (data.logo ==null){
				//if its null then it has no logo or it is erasing
				//delete data['logo']

			}else if(typeof data.logo =='string'){
				delete data['logo'];
				//when its string it has a logo
			}else if(typeof data.logo =='object'){
				//when it is an object its posting new logo
			}


			$scope.f = Upload.upload({
		      url: 'api/user_profile/ ',
		      data: data,
		      method: 'PATCH'
			}).then(function (contactInfo) {
		    	if( contactInfo.status == 200 ){
					var sessionData = JSON.parse(sessionStorage.getItem('userDataString'))
					sessionData.detalles_usuario.telefono1 = contactInfo.data.telefono1;
					sessionData.detalles_usuario.telefono2 = contactInfo.data.telefono2;
					sessionData.detalles_usuario.logo = contactInfo.data.logo;
		            if (contactInfo.data.logo){
		                //$rootScope.userData.detalles_usuario.logo= contactInfo.data.logo;
		                $scope.contactInfo.logo = contactInfo.data.logo;
		            }
					
					$scope.contactInfo.telefono1 = contactInfo.data.telefono1;
					$scope.contactInfo.telefono2 = contactInfo.data.telefono2;
					
					sessionStorage.setItem( 'userDataString', JSON.stringify(sessionData) );
					$scope.profileForm.$setPristine();
					$scope.profileForm.$setUntouched();
					genericServices.alertModal('Informacion de contacto modificada/agregada.');
		    	}

		    }, function (error) {
		        if (error.status > 0)
		            $scope.errorMsg = error.status + ': ' + error.data;
		    }, function (evt) {
		      // Math.min is to fix IE which reports 200% sometimes
		      Upload.progress = Math.min(100, parseInt(100.0 * evt.loaded / evt.total));
		    });
					    
		}


}])

condominioAlDiaAppControllers.controller('relacionMesController', ['$scope','$uibModal','context','$rootScope','$http','categories','$filter','$window',
	function( $scope, $uibModal, context, $rootScope, $http, categories, $filter, $window ){


		$scope.context = context;
		$scope.categories = categories;
		$scope.vals = {};
		//$scope.latest_bill = context.latest_bill;
		//$scope.property_bills = context.property_bills;
		$scope.active_month = new Date(context.month_query);
		$scope.month = new Date(context.month).toUTC();
		$scope.relation_month = new Date(context.relation_month).toUTC();
		//$scope.vals.dt = new Date(context.maxDate).toUTC();
		$scope.vals.dt = new Date(context.month_query).toUTC();
		$scope.maxDate = new Date(context.maxDate).toUTC();
		$scope.minDate = new Date(context.minDate).toUTC();
 		$scope.formats = ['dd-MMMM-yyyy', 'yyyy/MM/dd', 'dd.MM.yyyy', 'shortDate'];
 		$scope.format = $scope.formats[0];
 		//$scope.extra_cols =[];
 		$scope.nonEvaluatedIngresos= context.nonEvaluatedIngresos;
 		//$scope.columns = ['Inmueble', 'Propietario', 'Saldo', 'Pagos', 'Cuota', 'Total'];
 		//$scope.columns =context.columns;
 		//$scope.vals.filtered_bills = angular.copy(context.property_bills);
 		//var original= columns.slice(0);


 		$scope.get_cobranza= function(row){
 			var max_length =$scope.columns.length-6

			do {
				row.cobranzas.push({id:0})

			} while (row.cobranzas.length < max_length);
 			return row.cobranzas;
 		}

 		$scope.getRelacionPDF = function(){
			var url = 'api/relacion_pdf/?month_created=' + $scope.vals.dt.toISOString();		
			//$window.open(url);
			$window.open(url, '_blank'); // in new tab
			//$http.get(url)
 		}

		$scope.queryDate = function(){
			var url = 'api/relacion_mes/' + $scope.vals.dt.toISOString() +'/';
			$http.get(url).success(function(context){
 				$scope.extra_cols =[]
 				$scope.context = context;
				$scope.active_month = new Date($scope.vals.dt);
				$scope.context.property_bills = context.property_bills;
				$scope.columns = ['Inmueble', 'Propietario', 'Saldo', 'Pagos', 'Cuota', 'Total'];
				$scope.nonEvaluatedIngresos= context.nonEvaluatedIngresos;
			})
		}

		$scope.dateOptions = {
			minMode: 'month',
			initDate :$scope.maxDate,
			maxDate: $scope.maxDate,
			minDate: $scope.minDate
		};

		$scope.get_response = function(){
			if ($scope.nonEvaluatedIngresos == false){
 				alert('Tiene ingreso(s) que necesitan aprobacion.')
				$scope.proceed_url = ''
			}else{
				$scope.proceed_url = '#/relacion_mes2'
			}
		}


		$scope.accountingCell= function(column){
			var isAccountingCell=['Inmueble', 'Residente'];
			if( isAccountingCell.indexOf(column) === -1){
				return true;
			}
			return false;
		}

		$scope.getData= function(row, column){
			switch(column) {
			    case 'Inmueble':
			    	return row.nombre_inmueble
			        break;

			    case 'Residente':
			    	
					return $filter('capfirstlettereachword')(row.inmueble.inquilino.user.first_name+' '+ row.inmueble.inquilino.user.last_name);
			        break;
			    case 'Balance Presente':
			    	var returnString= $filter('number')(row.deuda_previa,2);
					return returnString;
			        break;
			    case 'Pagos':
			    	var returnString= $filter('number')(row.pagos,2);
					return returnString;
			        break;
			    case 'Cuota':
			    	var returnString= $filter('number')(  row.cuota, 2)
					return returnString;
			        break;
			    case 'Balance Nuevo':
			    	var total_cobranzas = 0;
			    	var deuda_actual = parseFloat(row.deuda_previa);
			    	var cuota=parseFloat(row.cuota);
			    	var pagos=parseFloat(row.pagos);

			    	for (var i in row.cobranzas){
			    		var item = row.cobranzas[i];
			    		
						var tipo_monto = item.tipo_monto;
						if (tipo_monto=='porcEgresos'){
							var total_egresos = parseFloat($scope.context.total_egresos);
							var amount = parseFloat(item.porcentaje) * total_egresos*parseFloat(row.inmueble.alicuota)/100;
						}else if(tipo_monto=='monto'){
							var amount = parseFloat(item.monto);
						}
			    		total_cobranzas+=amount;

			    	}
			    	var total=deuda_actual+pagos-(cuota+total_cobranzas);
			    	var returnString= String($filter('number')(total,2))
					return returnString;
			        break;			        

			  	default:
					for (var i in row.cobranzas){
						var item =row.cobranzas[i]
						if (item.asunto == column){
							var tipo_monto = item.tipo_monto;
							if (tipo_monto=='porcEgresos'){
								var total_egresos = parseFloat($scope.context.total_egresos);
								var returnString = parseFloat(item.porcentaje) * total_egresos*parseFloat(row.inmueble.alicuota)/100;
							}else if(tipo_monto=='monto'){
								var returnString = parseFloat(item.monto);
							}							
							break; 
						}
					}
					if(!returnString){
						var returnString = 0;
					}

			    	return $filter('number')(returnString, 2)
			    	break;
			} 
			return column;
		}

 		$scope.get_sum= function(filtered_bills, column){
 			var moneda= $rootScope.userData.detalles_usuario.pais.moneda;
 			sum = 0;
			switch(column) {
			    case 'Inmueble':
			    	return ''
			        break;
			    case 'Residente':
			    	return ''
			        break;
			    case 'Balance Presente':
			    	var total =  $filter('sumKeys')(filtered_bills, 'deuda_previa');
			    	var formatted = $filter('number')(total,2);
					return  String(formatted);
			        break;
			    case 'Pagos':
			    	var total =  $filter('sumKeys')(filtered_bills, 'pagos');
			    	var formatted = $filter('number')(total,2);
					return String(formatted);
			        break;
			    case 'Cuota':
			    	var total =  $filter('sumKeys')(filtered_bills, 'cuota');
			    	var formatted = $filter('number')(total,2);
					return String(formatted);
			        break;
			  	case 'Balance Nuevo':
			    	var total =  $filter('sumKeys')(filtered_bills, 'monto');
			    	var formatted = $filter('number')(total,2);
					return String(formatted);
			        break;			        

			  	default:
			  	 	var total = 0;
			  		for (var i in filtered_bills){
			  			var factura_propietario = filtered_bills[i];
			  			for (var j in factura_propietario.cobranzas){
			  				var cobranza = factura_propietario.cobranzas[j];
			  				if (String(cobranza.asunto).toLowerCase().trim()==String(column).toLowerCase().trim()){
			  					if(cobranza.tipo_monto ==='monto'){
									total +=parseFloat(cobranza.monto);
			  					}else if(cobranza.tipo_monto ==='porcEgresos'){
			  						var amount  = parseFloat($scope.context.total_egresos) * parseFloat(cobranza.porcentaje)*parseFloat(factura_propietario.inmueble.alicuota/100);
			  						total+=amount;
			  					}
			  					
			  				}
			  			}
			  		}
			    	var formatted = $filter('number')(total,2);
					return moneda +' ' + String(formatted);
			    	break;
			} 
			return 0;

 			//return sum;
 		}

		$scope.open1 = function() {
			$scope.popup1.opened = true;
		};
		$scope.popup1 = {
			opened: false
		};
		
}])

condominioAlDiaAppControllers.controller('pollsController', ['$scope', '$uibModal', 'polls_data', '$interval','$http','genericServices','$filter',
	function( $scope, $uibModal, polls_data, $interval, $http, genericServices, $filter ){

		var timer = $interval(function () {
            $scope.clock = new Date(Date.now());
            //$scope.clock=new Date();
         }, 1000);
		
		$scope.polls = polls_data.data;
		$scope.url = 'api/polls/';
		$scope.dt = new Date(polls_data.context.maxDate).toUTC();
		$scope.maxDate = new Date(polls_data.context.maxDate).toUTC();
		$scope.active_month = new Date(polls_data.context.active_month);
		$scope.minDate = new Date(polls_data.context.minDate).toUTC();
		//$scope.minDate = new Date('2016-11-01').toUTC();
 		$scope.formats = ['dd-MMMM-yyyy', 'yyyy/MM/dd', 'dd.MM.yyyy', 'shortDate'];
 		$scope.format = $scope.formats[0];


 		$scope.vote= function(poll){
	        var modalInstance = $uibModal.open({
	            ariaLabelledBy: 'modal-title',
	            ariaDescribedBy: 'modal-body',
	            animation: true,
	            templateUrl: 'static/ng_templates/modals/voteModal.html',
	            controller: 'voteModalController',
	            size: 'md',
	            resolve: {
		            poll: function() {
		            	return poll;
	            	}
	            }
	        });
		    modalInstance.result.then(function (polls) {
		      $scope.polls = polls;
		    });	
 		}

		$scope.verDetalles=function(poll){
	        var modalInstance = $uibModal.open({
	            ariaLabelledBy: 'modal-title',
	            ariaDescribedBy: 'modal-body',
	            animation: true,
	            templateUrl: 'static/ng_templates/modals/pollDetailsModal.html',
	            controller: 'pollDetailsModalController',
	            size: 'md',
	            resolve: {
		            poll: function() {
		            	return poll;
	            	}
	            }
	        });
		}

	    $scope.$on("$destroy", function() {
	        if (timer) {
	            $interval.cancel(timer);
	        }
	    });

	    $scope.pollStatus= function(poll){
		    var start = new Date(poll.start);
		    var end = new Date(poll.end);
	    	if($scope.clock  && ($scope.clock>=start) && ($scope.clock<end) && poll){
		    	var diff = (new Date(poll.end)-$scope.clock);
		    	var result = $filter('humanizetimedelta')(diff);
		    	return result
	    	}else if($scope.clock  && ($scope.clock<start) && poll){
	    		var result_date = $filter('date')(start, 'dd MMM yyyy');
	    		//return 'Empieza el '+result_date;
	    		return 'No ha empezado';
	    	}else if($scope.clock  && ($scope.clock>end) && poll){
	    		if(poll.active == true){
	    			// $http.post('api/close_expired_polls/').success(function(response, status){
	    			// 	if (status ==200){
	    			// 		return 'Finalizada'; 
	    			// 	}
	    			// })
	    			//HAVE SERVER CLOSE POLLS THAT ARE EXPIRED
	    		 }

	    		return 'Finalizada';
	    	}

	    	return false;
	    }

 		$scope.delPoll = function(poll){
 		var conrimationString  ="¿Esta seguro(a) de que desea borrar esta encuesta?"
		genericServices.confirmModal(conrimationString)
			.then(function(confirmation){
	 			$http.delete('api/polls/'+poll.id+'/').success(function(polls){
	 				$scope.polls = polls;
	 				$scope.dt = $scope.maxDate;
	 				$scope.active_month = $scope.maxDate;
	 				genericServices.alertModal('Encuesta borrada.');
	 			})
			});	

 		}

		$scope.timeDiff = function( pollend){
			if($scope.clock && pollend){
				return (new Date(pollend)-$scope.clock);	
			}

		}

		$scope.open1 = function() {
			$scope.popup1.opened = true;
		};

		$scope.popup1 = {
			opened: false
		};

		$scope.dateOptions = {
			minMode: 'month',
			initDate :$scope.maxDate,
			maxDate: $scope.maxDate,
			minDate: $scope.minDate
		};

		$scope.queryDate = function(){
			var url = 'api/polls/?month_created=' + $scope.dt.toISOString()
			$http.get(url).success(function(polls_queryset){
				$scope.polls = polls_queryset;
				$scope.active_month = new Date($scope.dt);
			})
		}

		$scope.addPoll= function(){

	        var modalInstance = $uibModal.open({
	            ariaLabelledBy: 'modal-title',
	            ariaDescribedBy: 'modal-body',
	            animation: true,
	            templateUrl: 'static/ng_templates/modals/addPollModal.html',
	            controller: 'addPollModalModalController',
	            size: 'md'
	        });
		    modalInstance.result.then(function (polls) {
		      	$scope.polls = polls;
	 			$scope.dt = $scope.maxDate;
	 			$scope.active_month = $scope.maxDate;
		      	genericServices.alertModal('¡ Encuesta registrada ! Los propietarios podran participar a partir de la fecha de inicio.');
		    });
		}

		$scope.today = function(){
			return new Date();
		}

}])

condominioAlDiaAppControllers.controller('facturacionCondoController', ['$scope','$uibModal','facturacion_data','$http','$filter','genericServices',
	function( $scope, $uibModal, facturacion_data, $http, $filter, genericServices ){

		$scope.facturas = facturacion_data.data
		$scope.dt = new Date(facturacion_data.context.maxDate).toUTC();
		$scope.url = 'api/factura_condominio/';
		$scope.maxDate = new Date(facturacion_data.context.maxDate).toUTC();
		$scope.minDate = new Date(facturacion_data.context.minDate).toUTC();
		$scope.active_month = new Date(facturacion_data.context.active_month);

		$scope.getStatus= function(factura){
			var message;
			if (factura.pago!=null){
				if(factura.pago.aprobado==true){
					message='Pago aprobado';
				}else if(factura.pago.aprobado==false){
					message='Pago rechazado';
				}else if(factura.pago.aprobado==null){
					message='Pago bajo evaluacion';
				}
			}else if(factura.pago==null){
				message='Pago requerido';
			}
			return message;
		}

		$scope.getTitle= function(factura){
			var title;
			if (factura.pago!=null){
				if(factura.pago.tipo_de_pago.metodo_pago.nombre=='Deposito/Transferencia'){
					title='Deposito/Transferencia';
				}else if(factura.pago.tipo_de_pago.metodo_pago.nombre=='Credit Card'){
					title='Tarjeta de credito';
				}
			}
			return title;
		}

		$scope.paymentDetails= function(factura){
			if (factura.pago){
		        var modalInstance = $uibModal.open({
		            ariaLabelledBy: 'modal-title',
		            ariaDescribedBy: 'modal-body',
		            animation: true,
		            templateUrl: 'static/ng_templates/modals/paymentDetailsModal.html',
		            controller: 'paymentDetailsModalController',
		            size: 'md',
		            resolve: {
			            payment: function($http) {
			            	return factura.pago;
		            	}
		            }
		        });				
			}else{
				var cutoff = new Date(factura.created).addMonths(1);
				cutoff = $filter('date')(cutoff, 'dd MMMM yyyy')
				genericServices.alertModal('Por favor efectue su pago antes de ' +cutoff);
			}
		}

		$scope.pagar= function(factura){
	        var modalInstance = $uibModal.open({
	            ariaLabelledBy: 'modal-title',
	            ariaDescribedBy: 'modal-body',
	            animation: true,
	            templateUrl: 'static/ng_templates/modals/paymentMethodModal.html',
	            controller: 'paymentMethodModalController',
	            size: 'md',
	            resolve: {
		            paymentMethods: function($http) {
		                var url = 'api/payment_methods/';
		                return $http({ 
		                    method: 'GET', 
		                    url: url
		                }).then(function(response){
		                    return response.data;
		                })
	            	},
	            	factura: function($http) {
	            		return factura;
	            	}
	            }
	        });
		}


		$scope.verFacturaPDF=function(factura){
			window.open('api/facturas/'+factura.id);
		}

		$scope.verDetalles=function(factura){
	        var modalInstance = $uibModal.open({
	            ariaLabelledBy: 'modal-title',
	            ariaDescribedBy: 'modal-body',
	            animation: true,
	            templateUrl: 'static/ng_templates/modals/facturaDetailsModal.html',
	            controller: 'facturaDetailsModalController',
	            size: 'md',
	            resolve: {
		            factura: function() {
		            	return factura;
	            	}
	            }
	        });
		}

		$scope.today = function(){
			return new Date();
		}
 		$scope.formats = ['dd-MMMM-yyyy', 'yyyy/MM/dd', 'dd.MM.yyyy', 'shortDate'];
 		$scope.format = $scope.formats[0];

		$scope.open1 = function() {
			$scope.popup1.opened = true;
		};

		$scope.popup1 = {
			opened: false
		};

		$scope.dateOptions = {
			minMode: 'year',
			initDate :$scope.maxDate,
			maxDate: $scope.maxDate,
			minDate: $scope.minDate
		};

		$scope.queryDate = function(){
			var url = 'api/factura_condominio/?year_created=' + $scope.dt.toISOString();
			$http.get(url).success(function(facturas_queryset){
				$scope.active_month = new Date($scope.dt);
				$scope.facturas = facturas_queryset;
			})
		}


}])

condominioAlDiaAppControllers.controller('quienesSomosController', ['$scope',
	function( $scope ){


}])

condominioAlDiaAppControllers.controller('negociosController', ['$scope','$http','genericServices','Upload','screen_services','$location',
	function( $scope, $http,genericServices, Upload,screen_services, $location ){


		$scope.affiliateData= {};

		$scope.screenSize= function(){
			return screen_services.screen_width();
		}

		$scope.registerAffiliate= function(file){

    	if ($scope.affiliateForm.$valid){
			$scope.f = file;
			$scope.affiliateData['client_type'] ='afiliado';
		    file.upload = Upload.upload({
		      url: 'rest-auth/registration/',
		      data: $scope.affiliateData

		    });

		    file.upload.then(function (response, status) {
		    	if( response.status == 201 ){
		    		var key = response.data;
		    		$location.path('registro_gracias');
		    	}

		    }, function (response) {
		      if (response.status > 0)
		        $scope.errorMsg = response.status + ': ' + response.data;
		    	$scope.showSuccessMessage = false;
		    }, function (evt) {
		      // Math.min is to fix IE which reports 200% sometimes
		      file.progress = Math.min(100, parseInt(100.0 * evt.loaded / evt.total));
		    });
		    }
		}

}])


condominioAlDiaAppControllers.controller('pagosDepTransController', ['$scope','$uibModal', 'context','genericServices',
	function( $scope, $uibModal,context, genericServices ){

		$scope.account = '';
		$scope.accounts= context.accounts;
		$scope.factura = context.factura;
		$scope.payment_method = context.payment_method;
		$scope.selectAccount=function(){
			for (var i in $scope.accounts){
				if($scope.accounts[i].id==$scope.bank){
					$scope.chosen_bank= $scope.accounts[i];
				}
			}
		}

		$scope.registerPaymentModal= function(){
	        var modalInstance = $uibModal.open({
	            ariaLabelledBy: 'modal-title',
	            ariaDescribedBy: 'modal-body',
	            animation: true,
	            templateUrl: 'static/ng_templates/modals/registerDepositModal.html',
	            controller: 'registerDepositModalController',
	            size: 'md',
	            resolve: {
		            chosen_bank: function($http) {
		            	return $scope.chosen_bank;
	            	},
		            factura: function($http) {
		            	return $scope.factura;
	            	},
		            payment_method: function($http) {
		            	return $scope.payment_method;
	            	}
	            }

	        });

			    modalInstance.result.then(function (response) {
			    	var message="Estimado usuario gracias por su pago, el mismo esta siendo validado por nuestros usuarios. Le dejaremos saber por correo electronico una vez haya sido aprobado.";
			    	genericServices.alertModal(message);

			    });
		}
}])


condominioAlDiaAppControllers.controller('sms_emailController', ['$scope','$http','genericServices','messages','$uibModal',
	function( $scope, $http, genericServices, messages,$uibModal ){

		$scope.messages = messages.data;
		$scope.msgsData = {};
		$scope.dt = new Date(messages.context.maxDate).toUTC();
		$scope.url = 'api/sms_email/';
		$scope.maxDate = new Date(messages.context.maxDate).toUTC();
		//$scope.minDate = new Date('2015-01-01')
		$scope.active_month = new Date();
		$scope.minDate = new Date(messages.context.minDate).toUTC();
 		$scope.formats = ['dd-MMMM-yyyy', 'yyyy/MM/dd', 'dd.MM.yyyy', 'shortDate'];
 		$scope.format = $scope.formats[0];
		$scope.inmuebles = messages.inmuebles;

 		$scope.get_info= function(inmueble){
 			if (inmueble){
 				return inmueble.inquilino.user.first_name + ' '+inmueble.inquilino.user.last_name+ ' ( ' +inmueble.nombre_inmueble +' )' ;
 			}
 			return '';
 		}
 		
 		$scope.get_formatter= function(inmueble_id){
 			var inmueble;
 		 	if (inmueble_id){
	 		 	for(var i in $scope.inmuebles){
	 		 		if($scope.inmuebles[i].id == inmueble_id){
	 		 			inmueble = $scope.inmuebles[i]
	 		 			return inmueble.inquilino.user.first_name + ' '+inmueble.inquilino.user.last_name+ ' ( ' +inmueble.nombre_inmueble +' )' ;
	 		 		}
	 		 	}		
 		 	}
 		}

//var _selected;

  // $scope.ngModelOptionsSelected = function(value) {
  //   if (arguments.length) {
  //     _selected = value;
  //   } else {
  //     return _selected;
  //   }
  // };

	  $scope.modelOptions = {
	    debounce: {
	      default: 500,
	      blur: 250
	    },
	    getterSetter: true
	  };

		$scope.open1 = function() {
			$scope.popup1.opened = true;
		};

		$scope.popup1 = {
			opened: false
		};

		$scope.dateOptions = {
			minMode: 'month',
			initDate :$scope.maxDate,
			maxDate: $scope.maxDate,
			minDate: $scope.minDate
		};

		$scope.queryDate = function(){
			var url = 'api/sms_email/?month_created=' + $scope.dt.toISOString();
			var data = {};
			$http.get(url).success(function(messages){
				$scope.active_month = new Date($scope.dt);
				$scope.messages = messages.data;
			})
		}

		$scope.today = function(){
			return new Date();
		}

		$scope.showMessage=function(message){
	        var modalInstance = $uibModal.open({
	            ariaLabelledBy: 'modal-title',
	            ariaDescribedBy: 'modal-body',
	            animation: true,
	            templateUrl: 'static/ng_templates/modals/message_detailModal.html',
	            controller: 'message_detailModalController',
	            size: 'md',
	            resolve: {
		            message: function() {
		            	return message;
	            	}
	            }
	        });

		}

		$scope.sendSmsEmail = function(){
			$http.post('api/sms_email/', $scope.msgsData).success(function(messages, status){
				if(status==200){
					$scope.messages = messages;
					$scope.msgsData = {};
					$scope.emailSmsForm.$setUntouched();
					$scope.emailSmsForm.$setPristine();
					genericServices.alertModal('Su mensaje ha sido enviado exitosamente.');					
				}

			})
		}

}])

condominioAlDiaAppControllers.controller('FaqController', ['$scope','faq',
	function( $scope, faq ){

	$scope.faq= faq;
	$scope.status = {
	    isCustomHeaderOpen: false,
	    isFirstOpen: true,
	    isFirstDisabled: false
	}

}])

condominioAlDiaAppControllers.controller('relacionMes2Controller', ['$scope','context','$filter','$rootScope','$uibModal','genericServices','$http','$location','categories',
	function( $scope, context,$filter, $rootScope, $uibModal, genericServices, $http, $location,categories){

		$scope.relacionDate = new Date(context.month).toUTC();
		$scope.categories = categories;
		$scope.comission = context.comission;
		$scope.cuentas = context.cuentas;
		$scope.inmuebles = {};
		//$scope.extraCols = [];
		$scope.total_egresos= parseFloat(context.total);
		//$scope.inmuebles.cols =['Inmueble', 'Residente', 'Balance Presente', 'Pagos', 'Cuota', 'Balance Nuevo' ];
		$scope.inmuebles.cols =context.columns;
		
		var original= ['Inmueble', 'Residente' ];
		$scope.inmuebles.rows = context.inmuebles;
		//$scope.newColumns = [];
		//$scope.propagate_val = 0;
		$scope.extra_col_map = [];

		// $scope.dataSetValid= function(){
		// 	var invalid=false;
		// 	for (var i in $scope.inmuebles.rows){
		// 		if ( $scope.inmuebles.rows[i]['extra_cols'].length>0 ){
		// 			for (var j in $scope.inmuebles.rows[i]['extra_cols']){
		// 				if($scope.inmuebles.rows[i]['extra_cols'][j]['monto']==undefined){
		// 					invalid= true;
		// 				}
		// 			}
		// 		}
		// 	}
		// 	return invalid;
		// }

		// $scope.getExtraColIndex= function(column){
		// 	for ( var i in $scope.inmuebles.rows){
		// 		for (var j in $scope.inmuebles.rows[i]['extra_cols']){
		// 			if($scope.inmuebles.rows[i]['extra_cols'][j]['titulo']==column){
		// 				return j;
		// 			}
		// 		}
		// 	}
		// }

		$scope.crearRelacion = function(){
			//genericServices.alertModal(egreso.detalles);
	        var modalInstance = $uibModal.open({
	            ariaLabelledBy: 'modal-title',
	            ariaDescribedBy: 'modal-body',
	            animation: true,
	            templateUrl: 'static/ng_templates/modals/relacion_mes_confirmation.html',
	            controller: 'relacion_mes_confirmationModalController',
	            size: 'lg',
	            resolve: {
		            context: function($http) {
		                var url = 'api/relacion_mes_summary/';
		                return $http({ 
		                    method: 'GET', 
		                    url: url
		                }).then(function(response){
		                    return response.data;
		                })
	            	}
	            }
	        });
		    modalInstance.result.then(function (response) {
		    	if (response == 'ok'){
					var conrimationString  ="Los cambios para este mes no podran ser modificados ¿Esta seguro(a) que desea crear la relacion de cuotas?";
					genericServices.confirmModal(conrimationString)
						.then(function(confirmation){
							var url = 'api/relacion_mes2/'
							var data = {};
							data['extra_col_map'] =$scope.extra_col_map;
							data['rows'] = $scope.inmuebles.rows;
							$http.post(url, data).then(
								function successCallback(response){
									if(response.status==200){
										genericServices.alertModal('¡La relacion de cuotas ha sido generada con exito! Los propietarios han recibido notificacion por correo electronico.');
										$location.path('relacion_mes');
									}
								}, 
								function errorCallback(response) {
									genericServices.alertModal(response.data, 'Alerta')
								}

								);

						});	
		    	}
		    });

		}


		$scope.isNormalCol= function(column){
			var response = false;
			for (var i in original){
				if(original[i]==column){
					response =true;
				}
			}
			return response
		}

		$scope.get_total=  function(column){
			var total=  0;
			switch(column) {
			    case 'Inmueble':
			    	total=  '-';
			        break;
			    case 'Residente':
					total=  '-';
			        break;
			    case 'Balance Presente':
			    	total=$filter('sumKeys')($scope.filtered_inmuebles, 'deuda_actual');
			    	total= $rootScope.userData.detalles_usuario.pais.moneda +' ' +$filter('number')(total,2);
			        break;
			    case 'Pagos':
			    	total=$filter('sumKeys')($scope.filtered_inmuebles, 'pagos');
			    	total= $rootScope.userData.detalles_usuario.pais.moneda +' ' +$filter('number')(total,2);
			        break;
			    case 'Cuota':
			    	total = $rootScope.userData.detalles_usuario.pais.moneda +' ' +$filter('number')( $filter('sumKeys')($scope.filtered_inmuebles, 'cuota') , 2) ;
			        break;
			    case 'Balance Nuevo':
			     	var balance = $filter('sumKeys')($scope.filtered_inmuebles, 'deuda_actual');
			    	var pagos = $filter('sumKeys')($scope.filtered_inmuebles, 'pagos');
			    	var cuota = $filter('sumKeys')($scope.filtered_inmuebles, 'cuota');
			    	//var total = 0;
			    	// for (var i in $scope.filtered_inmuebles){
			    	// 	for (var j in $scope.filtered_inmuebles[i].extra_cols){
			    	// 		total_extra_cols+=parseFloat($scope.filtered_inmuebles[i].extra_cols[j].monto);
			    	// 	}
			    	// }
			    	var total_cobranzas= 0;
			    	for (var i in $scope.filtered_inmuebles){
			    		var item = $scope.filtered_inmuebles[i]
			    		for( var j in item.cobranzas){
			    			var cobranza = item.cobranzas[j];
			    			//if(column ==cobranza.asunto){
								var tipo_monto = cobranza.tipo_monto;
								if (tipo_monto=='porcEgresos'){
									var total_egresos = $scope.total_egresos;
									var monto = parseFloat(cobranza.porcentaje) * total_egresos*parseFloat(item.alicuota)/100;
									total_cobranzas += monto;
								}else if(tipo_monto=='monto'){
									total_cobranzas +=parseFloat(cobranza.monto)
								}		

			    			//}
			    		}


			    	}

			    	total = $rootScope.userData.detalles_usuario.pais.moneda +' ' + $filter('number')(balance+pagos-(total_cobranzas+cuota),2);
			        break;
			    default:
			    	for (var i in $scope.filtered_inmuebles){
			    		var item = $scope.filtered_inmuebles[i]
			    		for( var j in item.cobranzas){
			    			var cobranza = item.cobranzas[j];
			    			if(column ==cobranza.asunto){
								var tipo_monto = cobranza.tipo_monto;
								if (tipo_monto=='porcEgresos'){
									var total_egresos = $scope.total_egresos;
									var monto = parseFloat(cobranza.porcentaje) * total_egresos*parseFloat(item.alicuota)/100;
									total += monto;
								}else if(tipo_monto=='monto'){
									total +=parseFloat(cobranza.monto)
								}		

			    			}
			    		}


			    	}
			    	total = $rootScope.userData.detalles_usuario.pais.moneda +' ' + $filter('number')(total,2)
			    	break;
			} 
			return total;
		}


		$scope.getData= function(row, column){
			switch(column) {
			    case 'Inmueble':
			    	return row.nombre_inmueble
			        break;

			    case 'Residente':
					return $filter('capfirstlettereachword')(row.propietario)
			        break;
			    case 'Balance Presente':
			    	var returnString= $filter('number')(row.deuda_actual,2);
					return returnString;
			        break;
			    case 'Pagos':
			    	var returnString= $filter('number')(row.pagos,2);
					return returnString;
			        break;
			    case 'Cuota':
			    	var returnString= $filter('number')(  row.cuota, 2)
					return returnString;
			        break;
			    case 'Balance Nuevo':
			    	var total_cobranzas = 0;
			    	var deuda_actual = parseFloat(row.deuda_actual);
			    	var cuota=parseFloat(row.cuota);
			    	var pagos=parseFloat(row.pagos);

			    	for (var i in row.cobranzas){
			    		var item = row.cobranzas[i];
			    		
						var tipo_monto = item.tipo_monto;
						if (tipo_monto=='porcEgresos'){
							var total_egresos = $scope.total_egresos;
							var amount = parseFloat(item.porcentaje) * total_egresos*parseFloat(row.alicuota)/100;
						}else if(tipo_monto=='monto'){
							var amount = parseFloat(item.monto);
						}
			    		total_cobranzas+=amount;

			    	}
			    	//var total=Math.abs(parseFloat(deuda_actual)+parseFloat(pagos)-(parseFloat(cuota)+parseFloat(total_extra_cols)));
			    	var total=deuda_actual+pagos-(cuota+total_cobranzas);
			    	var returnString= String($filter('number')(total,2))
					return returnString;
			        break;			        

			    default:
					for (var i in row.cobranzas){
						var item =row.cobranzas[i]
						if (item.asunto == column){
							var tipo_monto = item.tipo_monto;
							if (tipo_monto=='porcEgresos'){
								var total_egresos = $scope.total_egresos;
								var returnString = parseFloat(item.porcentaje) * total_egresos*parseFloat(row.alicuota)/100;
							}else if(tipo_monto=='monto'){
								var returnString = parseFloat(item.monto);
							}							
							break; 
						}
					}
					if(!returnString){
						var returnString = 0;
					}
			    	//var returnString = $filter('number')((row[column]['monto']), 2)
			    	//return returnString
			    	return $filter('number')(returnString, 2)
			    	break;
			} 
			return column;
		}

		//GET TOTAL CONDOMINIO DEBT
		$scope.get_debt = function(amount){
			var total = $filter('sumKeys')(amount, 'monto')
			return total * $scope.comission
		}

}])
// condominioAlDiaAppControllers.controller('relacionMes2Controller', ['$scope','context','$filter','$rootScope','$uibModal','genericServices','$http','$location','categories',
// 	function( $scope, context,$filter, $rootScope, $uibModal, genericServices, $http, $location,categories){
// 		$scope.relacionDate = new Date(context.month).toUTC();
// 		$scope.categories = categories;
// 		$scope.comission = context.comission;
// 		$scope.cuentas = context.cuentas;
// 		$scope.inmuebles = {};
// 		$scope.extraCols = [];
		
// 		//$scope.inmuebles.cols =['Inmueble', 'Residente', 'Balance Presente', 'Pagos', 'Cuota', 'Balance Nuevo' ];
// 		$scope.inmuebles.cols =context.cols;
		
// 		var original= $scope.inmuebles.cols.slice(0);
// 		$scope.inmuebles.rows = context.inmuebles;
// 		$scope.newColumns = [];
// 		$scope.propagate_val = 0;
// 		$scope.extra_col_map = [];
// 		$scope.dataSetValid= function(){
// 			var invalid=false;
// 			for (var i in $scope.inmuebles.rows){
// 				if ( $scope.inmuebles.rows[i]['extra_cols'].length>0 ){
// 					for (var j in $scope.inmuebles.rows[i]['extra_cols']){
// 						if($scope.inmuebles.rows[i]['extra_cols'][j]['monto']==undefined){
// 							invalid= true;
// 						}
// 					}
// 				}
// 			}
// 			return invalid;
// 		}

// 		$scope.getExtraColIndex= function(column){
// 			for ( var i in $scope.inmuebles.rows){
// 				for (var j in $scope.inmuebles.rows[i]['extra_cols']){
// 					if($scope.inmuebles.rows[i]['extra_cols'][j]['titulo']==column){
// 						return j;
// 					}
// 				}
// 			}
// 		}

// 		$scope.crearRelacion = function(){
// 			//genericServices.alertModal(egreso.detalles);
// 	        var modalInstance = $uibModal.open({
// 	            ariaLabelledBy: 'modal-title',
// 	            ariaDescribedBy: 'modal-body',
// 	            animation: true,
// 	            templateUrl: 'static/ng_templates/modals/relacion_mes_confirmation.html',
// 	            controller: 'relacion_mes_confirmationModalController',
// 	            size: 'lg',
// 	            resolve: {
// 		            context: function($http) {
// 		                var url = 'api/relacion_mes_summary/';
// 		                return $http({ 
// 		                    method: 'GET', 
// 		                    url: url
// 		                }).then(function(response){
// 		                    return response.data;
// 		                })
// 	            	}
// 	            }
// 	        });
// 		    modalInstance.result.then(function (response) {
// 		    	if (response == 'ok'){
// 					var conrimationString  ="Los cambios para este mes no podran ser modificados ¿Esta seguro(a) que desea crear la relacion de cuotas?";
// 					genericServices.confirmModal(conrimationString)
// 						.then(function(confirmation){
// 							var url = 'api/relacion_mes2/'
// 							var data = {};
// 							data['extra_col_map'] =$scope.extra_col_map;
// 							data['rows'] = $scope.inmuebles.rows;
// 							$http.post(url, data).then(
// 								function successCallback(response){
// 									if(response.status==200){
// 										genericServices.alertModal('¡La relacion de cuotas ha sido generada con exito! Los propietarios han recibido notificacion por correo electronico.');
// 										$location.path('relacion_mes');
// 									}
// 								}, 
// 								function errorCallback(response) {
// 									genericServices.alertModal(response.data, 'Alerta')
// 								}

// 								);

// 						});	
// 		    	}
// 		    	//DELETE FROM EXTRA_COLS OBJECT IN EACH ROW
// 		  //   	for (var i in $scope.inmuebles.rows){
// 		  //   		for(var j in $scope.inmuebles.rows[i]['extra_cols']){
// 		  //   			if($scope.inmuebles.rows[i]['extra_cols'][j]['titulo']==col_to_delete){
// 		  //   				$scope.inmuebles.rows[i]['extra_cols'].splice(j, 1);
// 		  //   			}
// 		  //   		}
// 		  //   	}
// 		  //   	//DELETE FROM COLUMNS
// 		  //   	var index = $scope.inmuebles.cols.indexOf(col_to_delete);
// 				// if (index > -1) {
// 				//     $scope.inmuebles.cols.splice(index, 1);
// 				// }
// 				// for(var p in $scope.inmuebles.rows){
// 				// }
// 		  //     	genericServices.alertModal('Columna "'+ col_to_delete +'" eliminada.');
// 		    });



// 		}

// 		$scope.propagate= function(){

// 			var rows_checked = [];
// 			for(var i in $scope.filtered_inmuebles){
// 				if($scope.filtered_inmuebles[i].ischecked===true){
// 					rows_checked.push($scope.filtered_inmuebles[i].id);
// 				}
// 			}

// 			if (rows_checked.length>0){
// 				var a= $scope.inmuebles.cols.filter( function( el ) {
// 					return original.indexOf( el ) < 0;
// 				} )

// 				if($scope.inmuebles.cols.length==original.length){
// 					genericServices.alertModal('Debe agregar al menos una columna extra para luego podra progagar gastos a traves de ella.');
// 					return false
// 				}

// 		        var modalInstance = $uibModal.open({
// 		            ariaLabelledBy: 'modal-title',
// 		            ariaDescribedBy: 'modal-body',
// 		            animation: true,
// 		            templateUrl: 'static/ng_templates/modals/propagate_modal.html',
// 		            controller: 'propagate_modalController',
// 		            size: 'md',
// 		            resolve: {
// 			            cols: function() {
// 			            	var val = $scope.inmuebles.cols.filter( function( el ) {
// 								return original.indexOf( el ) < 0;
// 							} )
// 			                return 	val;
// 		            	},
// 		            	rows_checked:function(){
// 			                return 	rows_checked;
// 		            	}
// 		            }
// 		        });

// 			    modalInstance.result.then(function (propagateObj) {
// 			    	$scope.propagate_val = parseFloat(propagateObj.monto);
// 			    	for(var i in $scope.filtered_inmuebles){
// 			    		for(var j in propagateObj.rows_checked){
// 			    			if ($scope.filtered_inmuebles[i].id==propagateObj.rows_checked[j]){
// 			    				for (var k in $scope.filtered_inmuebles[i]['extra_cols']){
// 			    					if($scope.filtered_inmuebles[i]['extra_cols'][k]['titulo']===propagateObj.columna){
// 			    						$scope.filtered_inmuebles[i]['extra_cols'][k]['monto'] = propagateObj.monto;
// 			    					}
// 			    				}
// 			    			}
// 			    		}
// 			    	}
// 			    $scope.propagate_val = 0;
// 			    });
// 			}else{
// 				genericServices.alertModal('Debe seleccionar al menos una fila!')
// 			}
// 		}

// 		$scope.delCol = function(){
// 	        var modalInstance = $uibModal.open({
// 	            ariaLabelledBy: 'modal-title',
// 	            ariaDescribedBy: 'modal-body',
// 	            animation: true,
// 	            templateUrl: 'static/ng_templates/modals/del_col_modal.html',
// 	            controller: 'delColController',
// 	            size: 'md',
// 	            resolve: {
// 		            cols: function() {
// 		            	var val = $scope.inmuebles.cols.filter( function( el ) {
// 							return original.indexOf( el ) < 0;
// 						} )
// 		                return 	val;
// 	            	}    	
// 	            }
// 	        });
// 		    modalInstance.result.then(function (col_to_delete) {
// 		    	//DELETE FROM EXTRA_COLS OBJECT IN EACH ROW
// 		    	for (var i in $scope.inmuebles.rows){
// 		    		for(var j in $scope.inmuebles.rows[i]['extra_cols']){
// 		    			if($scope.inmuebles.rows[i]['extra_cols'][j]['titulo']==col_to_delete){
// 		    				$scope.inmuebles.rows[i]['extra_cols'].splice(j, 1);
// 		    			}
// 		    		}
// 		    	}
// 		    	//DELETE FROM COLUMNS
// 		    	var index = $scope.inmuebles.cols.indexOf(col_to_delete);
// 				if (index > -1) {
// 				    $scope.inmuebles.cols.splice(index, 1);
// 				}
// 				for(var p in $scope.inmuebles.rows){
// 				}
// 		      	genericServices.alertModal('Columna "'+ col_to_delete +'" eliminada.');
// 		    });
// 		}

// 		$scope.isNormalCol= function(column){
// 			var response = false;
// 			for (var i in original){
// 				if(original[i]==column){
// 					response =true;
// 				}
// 			}
// 			return response
// 		}

// 		$scope.get_total=  function(column){
// 			var total=  0;
// 			switch(column) {
// 			    case 'Inmueble':
// 			    	total=  '-';
// 			        break;
// 			    case 'Residente':
// 					total=  '-';
// 			        break;
// 			    case 'Balance Presente':
// 			    	total=$filter('sumKeys')($scope.filtered_inmuebles, 'deuda_actual');
// 			    	total= $rootScope.userData.detalles_usuario.pais.moneda +' ' +$filter('number')(total,2);
// 			        break;
// 			    case 'Pagos':
// 			    	total=$filter('sumKeys')($scope.filtered_inmuebles, 'pagos');
// 			    	total= $rootScope.userData.detalles_usuario.pais.moneda +' ' +$filter('number')(total,2);
// 			        break;
// 			    case 'Cuota':
// 			    	total = $rootScope.userData.detalles_usuario.pais.moneda +' ' +$filter('number')( $filter('sumKeys')($scope.filtered_inmuebles, 'cuota') , 2) ;
// 			        break;
// 			    case 'Balance Nuevo':
// 			     	var balance = $filter('sumKeys')($scope.filtered_inmuebles, 'deuda_actual');
// 			    	var pagos = $filter('sumKeys')($scope.filtered_inmuebles, 'pagos');
// 			    	var cuota = $filter('sumKeys')($scope.filtered_inmuebles, 'cuota');
// 			    	var total_extra_cols = 0;
// 			    	for (var i in $scope.filtered_inmuebles){
// 			    		for (var j in $scope.filtered_inmuebles[i].extra_cols){
// 			    			total_extra_cols+=parseFloat($scope.filtered_inmuebles[i].extra_cols[j].monto);
// 			    		}
// 			    	}

// 			    	total = $rootScope.userData.detalles_usuario.pais.moneda +' ' + $filter('number')(Math.abs(balance+pagos-(total_extra_cols+cuota)),2);
// 			        break;
// 			    default:
// 			    	for (var i in $scope.filtered_inmuebles){
// 			    		for (var j in $scope.filtered_inmuebles[i]['extra_cols']){
// 			    			if($scope.filtered_inmuebles[i]['extra_cols'][j]['titulo']==column){
// 			    				total += $scope.filtered_inmuebles[i]['extra_cols'][j]['monto'];
// 			    			}
// 			    		}
// 			    	}
// 			    	total = $rootScope.userData.detalles_usuario.pais.moneda +' ' + $filter('number')(total,2)
// 			    	break;
// 			} 
// 			return total;
// 		}

// 		$scope.addColumnModal = function(){
// 	        var modalInstance = $uibModal.open({
// 	            ariaLabelledBy: 'modal-title',
// 	            ariaDescribedBy: 'modal-body',
// 	            animation: true,
// 	            templateUrl: 'static/ng_templates/modals/add_extra_column_modal.html',
// 	            controller: 'add_extra_column_modalController',
// 	            size: 'md',
// 	            resolve: {
// 		            inmuebles: function() {
// 		                return $scope.inmuebles.rows
// 	            	},
// 		            cuentas: function() {
// 		                return $scope.cuentas;
// 	            	}          	
// 	            }
// 	        });

// 		    modalInstance.result.then(function (extraColumnFormdata) {
// 		    	$scope.inmuebles.cols.splice(5, 0, extraColumnFormdata.titulo);
// 		    	//var extra_col_obj ={};
// 		    	$scope.added_cols_arr = [];
// 		    	for (var i in $scope.inmuebles.rows){
// 		    		var data = {
// 		    			titulo:extraColumnFormdata.titulo,
// 		    			monto:0
// 		    		};

// 		    		$scope.inmuebles.rows[i].extra_cols.push(data);
// 		    		if ($scope.added_cols_arr.indexOf(extraColumnFormdata.titulo)===-1){
// 		    			$scope.extra_col_map.push({
// 		    				titulo:extraColumnFormdata.titulo,
// 		    				banco: extraColumnFormdata.banco
// 		    			})
// 				    	$scope.added_cols_arr.push(extraColumnFormdata.titulo);
// 		    		}


// 		    		//extraColumnFormdata.banco
// 		    	}
// 		      	genericServices.alertModal('Columna "'+ extraColumnFormdata.titulo +'" agregada a la tabla.');
// 		    });

// 		}

// 		$scope.getData= function(row, column){

// 			switch(column) {
// 			    case 'Inmueble':
// 			    	return row.nombre_inmueble
// 			        break;

// 			    case 'Residente':
// 					return $filter('capfirstlettereachword')(row.propietario)
// 			        break;
// 			    case 'Balance Presente':
// 			    	var returnString= $rootScope.userData.detalles_usuario.pais.moneda +' ' +$filter('number')(row.deuda_actual,2);
// 					return returnString;
// 			        break;
// 			    case 'Pagos':
// 			    	var returnString= $rootScope.userData.detalles_usuario.pais.moneda +' ' +$filter('number')(row.pagos,2);
// 					return returnString;
// 			        break;
// 			    case 'Cuota':
// 			    	var returnString= $filter('number')(  row.cuota, 2)
// 					return $rootScope.userData.detalles_usuario.pais.moneda+' '+String(returnString);
// 			        break;
// 			    case 'Balance Nuevo':
// 			    	var deuda_actual = row.deuda_actual;
// 			    	var cuota=row.cuota;
// 			    	var pagos=row.pagos;
// 			    	var total_extra_cols = 0;
// 			    	for (var i in row.extra_cols){
// 			    		total_extra_cols+=row.extra_cols[i]['monto']
// 			    	}
// 			    	//var total=Math.abs(parseFloat(deuda_actual)+parseFloat(pagos)-(parseFloat(cuota)+parseFloat(total_extra_cols)));
// 			    	var total=parseFloat(deuda_actual)+parseFloat(pagos)-(parseFloat(cuota)+parseFloat(total_extra_cols));
// 			    	var returnString= $rootScope.userData.detalles_usuario.pais.moneda+' '+String($filter('number')(total,2))
// 					return returnString;
// 			        break;			        

// 			    default:
// 			    	var returnString = $filter('number')((row[column]['monto']), 2)
// 			    	return returnString
// 			    	break;
// 			} 
// 			return column;
// 		}

// 		//GET TOTAL CONDOMINIO DEBT
// 		$scope.get_debt = function(amount){
// 			var total = $filter('sumKeys')(amount, 'monto')
// 			return total * $scope.comission
// 		}

// 		$scope.checkUncheck = function(masterCheck){
// 		  	angular.forEach(  $scope.inmuebles.rows,function(value,key){
// 			    if(masterCheck){

// 			      value.ischecked = true;
// 			    }else{
// 			    value.ischecked = false;
// 				}
// 			})
//         }


// 		$scope.checkAll = function(){
// 			if($scope.checkAllStatus){
// 				for (var i in $scope.filtered_inmuebles){
// 					$scope.filtered_inmuebles[i].ischecked = true;
// 				}			
// 			}else{
// 				for (var i in $scope.filtered_inmuebles){
// 					$scope.filtered_inmuebles[i].ischecked = false;
// 				}		
// 			}
// 		}


// }])


condominioAlDiaAppControllers.controller('egresosController', ['$scope','$uibModal','genericServices','egresos','$http','$window',
	function( $scope, $uibModal, genericServices, egresos, $http,$window ){
		
		$scope.egresos = egresos.data;
		$scope.active_month=new Date(egresos.context.active_month);
		$scope.dt = new Date(egresos.context.maxDate).toUTC();
		$scope.url = 'api/egresos/';
		$scope.maxDate = new Date(egresos.context.maxDate).toUTC();
		$scope.minDate = new Date(egresos.context.minDate).toUTC();

		$scope.eliminarEgreso = function(egreso){
			var conrimationString  ="¿Esta seguro(a) de que desea borrar este egreso? ";
			genericServices.confirmModal(conrimationString)
				.then(function(confirmation){
					var url = 'api/egresos/'+egreso.id +'/';
					$http.delete(url).success(function(egresos_queryset){
						$scope.egresos = egresos_queryset;
						genericServices.alertModal('Egreso eliminado.')
					})
				});	
			}


		$scope.get_url= function(){
			$window.location.href = '#/egresos_detallados'
		}

		$scope.verDetalles= function(egreso){
			//genericServices.alertModal(egreso.detalles);
	        var modalInstance = $uibModal.open({
	            ariaLabelledBy: 'modal-title',
	            ariaDescribedBy: 'modal-body',
	            animation: true,
	            templateUrl: 'static/ng_templates/modals/egreso_details_modal.html',
	            controller: 'egreso_details_modallController',
	            size: 'md',
	            resolve: {
		            egreso: function() {
		            	return egreso;
	            	}
	            }
	        });
		}

		//$scope.perfilData = perfilData;
		$scope.EgresoModal = function(egreso){
			
	        var modalInstance = $uibModal.open({
	            ariaLabelledBy: 'modal-title',
	            ariaDescribedBy: 'modal-body',
	            animation: true,
	            templateUrl: 'static/ng_templates/modals/agregarEgresoModal.html',
	            controller: 'agregarEgresoModalController',
	            size: 'md',
	            resolve: {
		            context: function($http) {
		                var url = 'api/egresos_context_modal/';
		                return $http({ 
		                    method: 'GET', 
		                    url: url
		                }).then(function(response){
		                    return response.data;
		                })
	            	},
		            // tipos_egresos: function($http) {
		            //     var url = 'api/tipos_egresos/';
		            //     return $http({ 
		            //         method: 'GET', 
		            //         url: url
		            //     }).then(function(response){
		            //         return response.data;
		            //     })
	            	// },
		            minDate: function() {
		            	return new Date(new Date(egresos.context.active_month).getFullYear(), new Date(egresos.context.active_month).getMonth(), 1, 0, 0, 0);
	            	},
		            maxDate: function() {
		            	return $scope.maxDate;
	            	},
					tipo: function(){
						if (egreso){
							return 'modificar';
						}
					return 'agregar';
					},
					egreso: function(){
						if (egreso){
							var data = {
								id: String(egreso.id),
								tipo_egreso: String(egreso.tipo_egreso),
								monto: String(egreso.monto),
								fecha_facturacion: String(egreso.fecha_facturacion),
								banco:String(egreso.banco.id),
								nro_factura:String(egreso.nro_factura),
								detalles:String(egreso.detalles)
							};
							return data;
						}
					return {};
					} 
	            }
	        });
		    modalInstance.result.then(function (egresos_queryset) {
		    	$scope.dt =new Date(egresos.context.maxDate).toUTC();
				$scope.active_month=new Date(egresos.context.active_month);
		      	$scope.egresos = egresos_queryset;
		      	genericServices.alertModal('Egreso registrado!');
		    });
		}
 		$scope.formats = ['dd-MMMM-yyyy', 'yyyy/MM/dd', 'dd.MM.yyyy', 'shortDate'];
 		$scope.format = $scope.formats[0];
		$scope.open1 = function() {
			$scope.popup1.opened = true;
		};
		$scope.popup1 = {
			opened: false
		};

		$scope.dateOptions = {
			minMode: 'month',
			// dateDisabled: disabled,
			// formatYear: 'yy',
			initDate :$scope.maxDate,
			maxDate: $scope.maxDate,
			minDate: $scope.minDate
			// startingDay: 1
		};


		//verFacturaPDF
		$scope.getEgresosPDF = function(){
			var url = 'api/egresos_pdf/?month_created=' + $scope.dt.toISOString();
			window.open(url);
		}

		$scope.queryDate = function(){
			var url = 'api/egresos/?month_created=' + $scope.dt.toISOString();
			$http.get(url).success(function(egresos_queryset){
				$scope.active_month = new Date($scope.dt);
				$scope.egresos = egresos_queryset;
			})
		}

		$scope.can_post = function(){

			var can_post = ($scope.maxDate != $scope.dt);
			if(can_post){
				$scope.message = 'Solo puede cargar egresos para el mes mas reciente';
			}else{
				$scope.message = 'Cargar Egreso';
			}
			
			return can_post;
		}
}])


condominioAlDiaAppControllers.controller('ingresosController', ['$scope','$uibModal','ingresos','$http','genericServices','$rootScope',
	function( $scope, $uibModal, ingresos, $http, genericServices, $rootScope ){

		$scope.ingresos = ingresos.data;
		$scope.active_month = new Date(ingresos.context.active_month);
		$scope.dt = new Date(ingresos.context.maxDate).toUTC();
		$scope.url = 'api/ingresos/';
		$scope.maxDate = new Date(ingresos.context.maxDate).toUTC();
		$scope.minDate = new Date(ingresos.context.minDate).toUTC();
 		$scope.formats = ['dd-MMMM-yyyy', 'yyyy/MM/dd', 'dd.MM.yyyy', 'shortDate'];
 		$scope.format = $scope.formats[0];

		$scope.open1 = function() {
			$scope.popup1.opened = true;
		};

		$scope.popup1 = {
			opened: false
		};

		$scope.dateOptions = {
			minMode: 'month',
			// dateDisabled: disabled,
			// formatYear: 'yy',
			initDate :$scope.maxDate,
			maxDate: $scope.maxDate,
			minDate: $scope.minDate
			// startingDay: 1
		};
		$scope.queryDate = function(){
			var url = 'api/ingresos/?month_created=' + $scope.dt.toISOString()
			$http.get(url).success(function(ingresos_queryset){
				$scope.active_month = new Date($scope.dt);
				$scope.ingresos = ingresos_queryset;
			})
		}

		$scope.canApprove= function(ingreso){
			var can_approve = false;
			if (ingreso.aprobado==null && ingreso.cerrado==false){
				can_approve= true;	
			}
			return can_approve;
		}

		$scope.getRejectReason = function(ingreso, title){
			genericServices.alertModal(ingreso.razon_rechazo, title, 'md');
		}

		$scope.aprobarPago = function(ingreso){
		var conrimationString  ="¿Esta seguro(a) de que desea aprobar este ingreso? ";
		genericServices.confirmModal(conrimationString)
			.then(function(confirmation){
				var url = 'api/ingresos/' + ingreso.id +'/';
				var data = {};
				data.aprobado = true;
				$http.patch(url, data).success(function(ingresos_queryset){
					$scope.ingresos = ingresos_queryset;
					genericServices.alertModal('Ingreso ha sido aprobado, el propietario ha sido notificado por correo electronico.')
				})
			});	

		}

		$scope.rechazarPagoModal = function(ingreso){
	        var modalInstance = $uibModal.open({
	            ariaLabelledBy: 'modal-title',
	            ariaDescribedBy: 'modal-body',
	            animation: true,
	            templateUrl: 'static/ng_templates/modals/razonRechazoModal.html',
	            controller: 'razonRechazoModalController',
	            size: 'md',
	            resolve: {
	              ingreso: function(){
	                return ingreso;
	              }  
	            }
	        });
		    modalInstance.result.then(function (ingresos_queryset) {
		      
		    	//$scope.dt =new Date(ingresos.context.maxDate).toUTC();
				//$scope.active_month=new Date(ingresos.context.active_month);
		      	$scope.ingresos = ingresos_queryset;
				genericServices.alertModal('Ingreso ha sido rechazado, el propietario ha sido notificado por correo electronico.')

		    });
		}

		$scope.verIngreso = function(ingreso){
	        var modalInstance = $uibModal.open({
	            ariaLabelledBy: 'modal-title',
	            ariaDescribedBy: 'modal-body',
	            animation: true,
	            templateUrl: 'static/ng_templates/modals/detallesIngresoModal.html',
	            controller: 'detallesIngresoModalController',
	            size: 'md',
	            resolve: {
	              ingreso: function(){
	                return ingreso;
	              }  
	            }

	        });
	    }

		$scope.getPagador = function(ingreso){
			var pagador;
			if(ingreso.tipo_de_ingreso =='pp'){
				pagador= ingreso.propietario;
			}else{
				pagador=ingreso.pagador;
			}
			return pagador;			
		}

		$scope.getEstado = function(ingreso){
			var estado;
			if(ingreso.aprobado ==true){
				estado='Aprobado';
			}else if(ingreso.aprobado ==false){
				estado='Rechazado';
			}else{
				estado= 'Por evaluar';
			}
			return estado;
		}

		$scope.eliminarPago = function(ingreso){
		var conrimationString  ="¿Esta seguro(a) de que desea borrar este ingreso? ";
		genericServices.confirmModal(conrimationString)
			.then(function(confirmation){
				var url = 'api/ingresos/'+ingreso.id +'/';
				$http.delete(url).success(function(ingresos_queryset){
					$scope.ingresos = ingresos_queryset;
					genericServices.alertModal('Ingreso eliminado.')
				})
			});	
		}

		$scope.agregarPagoModal = function(ingreso){
	        var modalInstance = $uibModal.open({
	            ariaLabelledBy: 'modal-title',
	            ariaDescribedBy: 'modal-body',
	            animation: true,
	            templateUrl: 'static/ng_templates/modals/agregarpagoModal.html',
	            controller: 'agregarPagoModalController',
	            size: 'md',
	            resolve: {
		            context: function($http) {
		                var url = 'api/ingreso_condo_modal_context/';
		                return $http({ 
		                    method: 'GET', 
		                    url: url
		                }).then(function(response){
		                    return response.data;
		                })
	            	},
		            // inmuebles: function($http) {
		            //     var url = 'api/inmuebles/';
		            //     return $http({ 
		            //         method: 'GET', 
		            //         url: url
		            //     }).then(function(response){
		            //         return response.data;
		            //     })
	            	// },
		            // cuentas: function() {
		            //     var url = 'api/bancos/';
		            //     return $http({ 
		            //         method: 'GET', 
		            //         url: url
		            //     }).then(function(response){
		            //         return response.data;
		            //     })
	            	// }, 
		            minDate: function() {
		            	return new Date(new Date(ingresos.context.active_month).getFullYear(), new Date(ingresos.context.active_month).getMonth(), 1, 0, 0, 0);
	            	},
		            maxDate: function() {
		            	return $scope.maxDate;
	            	},
					tipo: function(){
						if (ingreso){
							return 'modificar'
						}
					return 'agregar';
					},
					ingreso: function(){
						if (ingreso){
							return ingreso;
						}
					return {};
					}  	        	
	            }
	        });
		    modalInstance.result.then(function (ingresos_queryset) {
		    	$scope.dt =new Date(ingresos.context.maxDate).toUTC();
				$scope.active_month=new Date(ingresos.context.active_month);
		      	$scope.ingresos = ingresos_queryset;
		      	genericServices.alertModal('Ingreso registrado.');
		    });
		}
}])

condominioAlDiaAppControllers.controller('carteleraController', ['$scope','cartelera','$uibModal','genericServices','$http',
	function( $scope, cartelera, $uibModal, genericServices, $http ){

	$scope.eliminarAnuncio = function(anuncio){
		var conrimationString  ="¿Esta seguro(a) de que desea borrar el anuncio " + String(anuncio.titulo)+ " de la cartelera?"
		genericServices.confirmModal(conrimationString)
		.then(function(confirmation){
			var url = 'api/cartelera/'+anuncio.id+'/'
				$http.delete(url).success(function(cartelera){
					$scope.cartelera = cartelera;
				})
		});	
	}

	$scope.verAnuncio = function(anuncio){
        var modalInstance = $uibModal.open({
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            animation: true,
            templateUrl: 'static/ng_templates/modals/anuncioModal.html',
            controller: 'anuncioModalController',
            size: 'lg',
            resolve: {
              anuncio: function(){
                return anuncio;
              }   
            }

        });
	    modalInstance.result.then(function (bancos) {
	      $scope.bancos = bancos;
	      alert('Cuenta bancaria registrada.');
	    });

	};


		$scope.cartelera = cartelera;

		$scope.carteleraModal = function(cartelera){
	        var modalInstance = $uibModal.open({
	            ariaLabelledBy: 'modal-title',
	            ariaDescribedBy: 'modal-body',
	            animation: true,
	            templateUrl: 'static/ng_templates/modals/carteleramodal.html',
	            controller: 'carteleraModalController',
	            size: 'lg'
	            // resolve: {
	            //   bancos: function(){
	            //     return $scope.bancos;
	            //   },
	            //   tipo: function(){
	            //   	if (cuenta){
	            //   		return 'modificar'
	            //   	}
	            //     return 'agregar';
	            //   },
	            //   cartelera: function(){
	            //   	if (cartelera){
	            //   		var data = {
	            //   			id: String(cartelera.id),
	            //   			titular: String(cartelera.titular),
	            //   			banco: String(cartelera.banco),
	            //   			nro_cuenta: String(cartelera.nro_cuenta)
	            //   		};
	            //   		return data;
	            //   	}
	            //     return {};
	            //   }                
	            // }

	        });
		    modalInstance.result.then(function (cartelera) {
		      $scope.cartelera = cartelera;
		      alert('Registro agregado a la cartelera.');
		    });
		}
}])


condominioAlDiaAppControllers.controller('bancosController', ['$scope','bancos','$uibModal','genericServices','$http','userSessionServices','$rootScope',
	function( $scope, bancos, $uibModal, genericServices,$http, userSessionServices, $rootScope ){

	$scope.bancos = bancos.bancos;
	$scope.fecha_cuenta = bancos.fecha_cuenta;
	$scope.bancos_pais = bancos.bancos_pais;
	$scope.eliminarBanco = function(banco){
		var conrimationString  ="¿Esta seguro(a) de que desea borrar a la cuenta de " + String(banco.banco)+ " de la lista de cuentas?"
		genericServices.confirmModal(conrimationString)
		.then(function(confirmation){
			var url = 'api/bancos/'+banco.id+'/'
				$http.delete(url).success(function(bancos){
					$scope.bancos = bancos;
				})
		});	
	}

	$scope.agregarBanco = function(cuenta){
        var modalInstance = $uibModal.open({
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            animation: true,
            templateUrl: 'static/ng_templates/modals/agregarEditarBanco.html',
            controller: 'agregarEditarBancoController',
            size: 'md',
            resolve: {
              bancos: function(){
                return $scope.bancos;
              },
              tipo: function(){
              	if (cuenta){
              		return 'modificar'
              	}
                return 'agregar';
              },
              cuenta: function(){
              	if (cuenta){
              		var data = {
              			id: String(cuenta.id),
              			titular: String(cuenta.titular),
              			banco: String(cuenta.banco),
              			nro_cuenta: String(cuenta.nro_cuenta),
              			balanceinicial:String(cuenta.balanceinicial),
              			banco_pais :String(cuenta.banco_pais)
              		};
              		return data;
              	}
                return {};
              },
              fecha_cuenta: function(){
              	return $scope.fecha_cuenta;
              },
              bancos_pais: function(){
              	return $scope.bancos_pais;
              }               
            }

        });
	    modalInstance.result.then(function (bancos) {
	      	$scope.bancos = bancos;
			var obj = JSON.parse(sessionStorage.getItem('userDataString'));
			var newVal = (bancos.length >0) ? true : false;
			obj.detalles_usuario.cuenta_bancaria = newVal;
			sessionStorage.setItem('userDataString', JSON.stringify(obj));
			$rootScope.alerts = [];

	      alert('Cuenta bancaria registrada.');
	    });

	};
}])



condominioAlDiaAppControllers.controller('juntaCondominioController', ['$scope','juntaCondominio','$http','$uibModal','tableServices','genericServices',
	function( $scope, juntaCondominio, $http, $uibModal,tableServices, genericServices ){
	
	$scope.juntaCondominio = juntaCondominio;


	$scope.agregarMiembro = function(){
        var modalInstance = $uibModal.open({
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            animation: true,
            templateUrl: 'static/ng_templates/modals/juntaCondominioModal.html',
            controller: 'agregarJuntaModalController',
            size: 'md',
            resolve: {
	            inmuebles: function($http) {
	                var url = 'api/inmuebles/';
	                return $http({ 
	                    method: 'GET', 
	                    url: url
	                }).then(function(response){
	                    return response.data;
	                })
            	}
            }

        });
	    modalInstance.result.then(function (juntaCondominio) {
	      $scope.juntaCondominio = juntaCondominio;
	      alert('Miembro de junta de condominio agregado');
	    });

	};


	$scope.borrarMiembro = function (inmueble){
		var checked_rows_id = tableServices.getCheckedRows( $scope.juntaCondominio, 'checked', 'id');
		var url = 'api/junta_condominio/' + String(inmueble.id) +'/';
		var data =  {};
		data.junta_de_condominio = false;
		data.cargo = '';
		// $http.patch( url, data ).success(function(juntaCondominio , status){
		// 	if(status==200){
				
		// 	}
		// })
		var conrimationString  ="¿Esta seguro(a) de que desea borrar a " + String(inmueble.inquilino.user.first_name)+ " de la junta de condomino?"
		genericServices.confirmModal(conrimationString)
		.then(function(confirmation){
			$http.patch(url, data).success(function(juntaCondominio, status){
				console.log(juntaCondominio)
				if(status == 200){
					$scope.juntaCondominio = juntaCondominio.data;
					alert('Miembro de junta de condominio eliminado exitosamente.');
				}
			})
		});	
	}

}])


condominioAlDiaAppControllers.controller('registroGraciasController', ['$scope',
	function( $scope ){
	
}])

condominioAlDiaAppControllers.controller('paginasAmarillasController', ['$scope','pagAmarillas','$rootScope','$uibModal','tableServices','genericServices',
	function( $scope, pagAmarillas, $rootScope,$uibModal, tableServices, genericServices ){

	$scope.pagAmarillas = pagAmarillas;

	// $scope.registrarPaginaAmarillaModal = function(){
 //        var modalInstance = $uibModal.open({
 //            ariaLabelledBy: 'modal-title',
 //            ariaDescribedBy: 'modal-body',
 //            animation: true,
 //            templateUrl: 'static/ng_templates/modals/paginasAmarillasModal.html',
 //            controller: 'paginasAmarillasModalController',
 //            size: 'md'
 //        });
	//     modalInstance.result.then(function (pagAmarillas) {
	// 	    $scope.pagAmarillas.push(pagAmarillas);
	// 		//$rootScope.alerts.push( { type: 'success', msg: 'Ha agregado el registro exitosamente.'  });
	// 	    alert('Registro agregado a paginas amarillas.');
	//     });

	// };

		$scope.checkAll = function(){
			$scope.selectAll = !$scope.selectAll;
			for (var i in $scope.pagAmarillas){
				//if($scope.listaInmuebles[i].quote_approved && $scope.listaInmuebles[i].quote_price && !$scope.listaInmuebles[i].quote_payed && $scope.itemInCart($scope.OrderBook[i].id)){
				$scope.pagAmarillas[i].checked = $scope.selectAll;
				//}
		
			}
		}



	$scope.eliminarRegistro = function(registro){
		var conrimationString  ="¿Esta seguro(a) de que desea borrar a " + String(registro.nombre)+ " de las paginas amarillas?"
		genericServices.confirmModal(conrimationString)
		.then(function(confirmation){
			var url = 'api/paginas_amarillas/'+registro.id+'/'
				$http.delete(url).success(function(pagAmarillas){
					$scope.pagAmarillas = pagAmarillas;
				})
		});	
	}

	$scope.agregarRegistro = function(registro){
        var modalInstance = $uibModal.open({
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            animation: true,
            templateUrl: 'static/ng_templates/modals/paginasAmarillasModal.html',
            controller: 'agregarPagAmarillasModalController',
            size: 'md',
            resolve: {
              pagAmarillas: function(){
                return $scope.pagAmarillas;
              },
              tipo: function(){
              	if (registro){
              		return 'modificar'
              	}
                return 'agregar';
              },
              registro: function(){
              	if (registro){
              		var data = {
              			id: String(registro.id),
              			nombre: String(registro.nombre),
              			mobil: String(registro.mobil),
              			fijo: String(registro.fijo),
              			oficio: String(registro.oficio),
              			email: String(registro.email)
              		};
              		return data;
              	}
                return {};
              }                
            }

        });
	    modalInstance.result.then(function (pagAmarillas) {
	      $scope.pagAmarillas = pagAmarillas;
	      
	    });

	};



}])



condominioAlDiaAppControllers.controller('inmueblesController', ['$scope','$uibModal','listaInmuebles','$http','tableServices','genericServices','userSessionServices','$rootScope','$location','categories',
	function( $scope, $uibModal, listaInmuebles, $http, tableServices, genericServices, userSessionServices, $rootScope, $location, categories ){

		$scope.listaInmuebles = listaInmuebles;
		$scope.selectedAll = false;
		$scope.parameters= $location.search()
		$scope.categories = categories;



		$scope.loadCSV= function(){
	        var modalInstance = $uibModal.open({
	            ariaLabelledBy: 'modal-title',
	            ariaDescribedBy: 'modal-body',
	            animation: true,
	            templateUrl: 'static/ng_templates/modals/loadCsvModal.html',
	            controller: 'loadCsvModalController',
	            size: 'md'
	        });
			modalInstance.result.then(function (response) {
              genericServices.alertModal(response.data, 'Atencion', 'md');
			});
		}


		$scope.get_categories = function(inmueble){
			if (inmueble.categories.length>0){
				return inmueble.categories.map(function(a) {return a.name;}).join();
			}else{
				return 'No aplica';
			}
			return '-';
		}

		$scope.inmueble_info=function(inmueble){
			if (inmueble.inquilino){
				return inmueble.propietario;
			}

			return 'Registre propietario';
		}

		$scope.addInmuebleCategory= function(){
	        var modalInstance = $uibModal.open({
	            ariaLabelledBy: 'modal-title',
	            ariaDescribedBy: 'modal-body',
	            animation: true,
	            templateUrl: 'static/ng_templates/modals/addInmuebleCategory.html',
	            controller: 'addInmuebleCategoryModalController',
	            size: 'md',
	            resolve: {
	                categories: function() {
	                	for (var i in $scope.categories){
	                		delete $scope.categories[i]['show']
	                	}
	                	return $scope.categories;
	                },
	                selection:function(){
	                	return tableServices.getCheckedRows( $scope.listaInmuebles, 'checked', 'id');
	                }
	            }

	        });
			modalInstance.result.then(function (inmuebles) {
				$scope.listaInmuebles =inmuebles;
			});
		}

		$scope.$on('uptate-data', function(event, args) {
			if (args.inmuebles){
				$scope.listaInmuebles = args.inmuebles;
			}
			$scope.categories=args.categories;
		    // do what you want to do
		});

		$scope.checkAll = function(){
			$scope.selectAll = !$scope.selectAll;
			for (var i in $scope.listaInmuebles){
				if($scope.listaInmuebles[i].inquilino!=null){
					$scope.listaInmuebles[i].checked = $scope.selectAll;
				}
		
			}
		}


		$scope.checkFilter1 = function(val){
			if(!val){
				$scope.disableFilter1=true;
			}else{
				$scope.disableFilter1=false;
			}
		}


		$scope.openUserInfoModal = function(inmueble){
			if(inmueble.inquilino){
		        var modalInstance = $uibModal.open({
		            ariaLabelledBy: 'modal-title',
		            ariaDescribedBy: 'modal-body',
		            animation: true,
		            templateUrl: 'static/ng_templates/modals/detallesPropietario.html',
		            controller: 'datosInquilinoModalController',
		            size: 'md',
		            resolve: {
		              inmueble: function(){
		                return inmueble;
		              }  
		            }

		        });
			}
			    // modalInstance.result.then(function (listaInmuebles) {
			    //   $scope.listaInmuebles = listaInmuebles;
			    // });
		}
		
		$scope.getTotalNoFilter = function(column){
			var total = 0;
			for(var i in $scope.listaInmuebles){
				total +=parseFloat($scope.listaInmuebles[i][column]);
			}
			return total;
		}

		$scope.getTotal = function(column){
			var total = 0;
			for(var i in $scope.inmuebles){
				total +=parseFloat($scope.inmuebles[i][column]);
			}
			return total;
		}

		$scope.eraseSelection = function (){
			var checked_rows_id = tableServices.getCheckedRows( $scope.listaInmuebles, 'checked', 'id');
			var url = 'api/borrarinmuebles/';
			if (checked_rows_id.length == 0){
				alert('Seleccione los inmuebles que quiere borrar');
				return false;
			}
			genericServices.confirmModal("¿Esta seguro(a) de que desea borrar los inmuebles seleccionados?")
			.then(function(confirmation){
				$http.post(url, checked_rows_id).success(function(context, status){
					//$scope.purchases = purchases;
					if(status == 200){
						$rootScope.userData.detalles_usuario.activo = context.condominio_activo;
						$scope.listaInmuebles= context.data;
						alert('Ha borrado los inmuebles seleccionados exitosamente.');
					}
				})
			});	
		}

		$scope.agregarInmuebleModal = function(inmueble){
	        var modalInstance = $uibModal.open({
	            ariaLabelledBy: 'modal-title',
	            ariaDescribedBy: 'modal-body',
	            animation: true,
	            templateUrl: 'static/ng_templates/modals/agregarInmuebleModal.html',
	            controller: 'agregarInmuebleModalController',
	            size: 'md',
	            resolve: {
	              listaInmuebles: function(){
	                return $scope.listaInmuebles;
	              },
	              total_inmuebles: function(){
	                return $scope.getTotal('alicuota');
	              },
	              tipo: function(){
	              	if (inmueble){
	              		return 'modificar'
	              	}
	                return 'agregar';
	              },
	              inmueble: function(){
	              	if (inmueble){

	              		var data = {
	              			balanceinicial: parseFloat(inmueble.balanceinicial),
	              			nombre_inmueble: String(inmueble.nombre_inmueble),
	              			alicuota: parseFloat(inmueble.alicuota),
	              			id: inmueble.id,
	              			may_modify_inmueble: inmueble.may_modify_inmueble
	              		};
	              		if(inmueble.inquilino){
	              			if(inmueble.inquilino.rif != null && inmueble.inquilino.rif != undefined &&  typeof inmueble.inquilino.rif == 'string' ){
	              				var rif =String(inmueble.inquilino.rif);
	              			}else{
	              				var rif ='';
	              			}
	              			data.arrendado= inmueble.arrendado,
	              			data.arrendatario= inmueble.arrendatario,
	              			data.cargo=inmueble.cargo,
	              			data.last_name= String(inmueble.inquilino.user.last_name),
	              			data.junta_de_condominio=inmueble.junta_de_condominio,
	              			data.email= String(inmueble.inquilino.user.email),
	              			data.rif=  rif,
	              			data.first_name= String(inmueble.inquilino.user.first_name)
	              		}
	              		return data;
	              	}
	                return {};
	              }                
	            }

	        });
			    modalInstance.result.then(function (listaInmuebles) {
			      $scope.listaInmuebles = listaInmuebles;
			    });
		}


}])

condominioAlDiaAppControllers.controller('sideBarController', ['$scope','$location','$location',
	function( $scope,$location, $location ){
	$scope.location = $location.path()
	$scope.status = {
		isCustomHeaderOpen: false,
		isFirstOpen: true,
		isFirstDisabled: false
	};

	$scope.change_view=function(view){
		$location.path(view);
	}


}])

condominioAlDiaAppControllers.controller('alertsController', ['$scope','$rootScope',
	function( $scope, $rootScope ){

		  //$scope.addAlert()

		  $scope.closeAlert = function(index) {
		    $scope.alerts.splice(index, 1);
		  };

}])





condominioAlDiaAppControllers.controller('pago_propietario_depController', ['$scope','bancos','$uibModal','$location',
	function( $scope, bancos, $uibModal, $location ){

		$scope.bancos =bancos;
		$scope.deuda = parseFloat(sessionStorage.getItem('deuda_actual'));
		$scope.moneda = sessionStorage.getItem('moneda');
		$scope.params = $location.search();//{balance:parseFloat(balance), payment_type:payment_type, cobranza_id: cobranza_id})

		$scope.registerPayment= function(){
            var modalInstance = $uibModal.open({
                ariaLabelledBy: 'modal-title',
                ariaDescribedBy: 'modal-body',
                animation: true,
                templateUrl: 'static/ng_templates/modals/register_prop_deposit_modal.html',
                controller: 'register_prop_deposit_modalController',
                size: 'md',
                resolve: {
                    context: function() {
                    	var context = $scope.chosen_bank;
                    	context['tipo_de_ingreso'] = $scope.params.payment_type;
                    	if($scope.params.payment_type=='cobranza'){
                    		context['cobranza_condominio'] = parseInt($scope.params.cobranza_id);
                    		context['monto'] = parseFloat($scope.params.balance);
                    	}
                        return context;
                    },
                    payment_type: function() {
                        return $scope.params.payment_type;
                    }                  
                }
            });
            modalInstance.result.then(function (cuentas) {
              $scope.cuentas=cuentas;
              genericServices.alertModal('Su pago ha sido registrado satisfactoriamente. Sera notificado(a) via correo electronico cuando su pago sea corroborado.');
            });
		}

		$scope.selectAccount=function(){
			for (var i in $scope.bancos){
				if($scope.bancos[i].id==$scope.bank){
					$scope.chosen_bank= $scope.bancos[i];
				}
			}
		}

}])


condominioAlDiaAppControllers.controller('reset_passwordController', ['$scope','$http','genericServices',
	function( $scope, $http, genericServices ){
		$scope.formData = {};
		$scope.recoverPwd = function(){
			if($scope.pwdRecoveryForm.$valid){
				var url = 'rest-auth/password/reset/';
				$http.post( url, $scope.formData ).success( function( response, status ){
					if(status == 200){
						$scope.formData = {};
						$scope.pwdRecoveryForm.$setUntouched();
						$scope.pwdRecoveryForm.$setPristine();
						genericServices.alertModal( response.detail );
					}

				})
				.error(function(errors){
					genericServices.alertModal( String(errors.email) );
				})				
			}

		}
		  //$scope.addAlert()
		  // $scope.closeAlert = function(index) {
		  //   $scope.alerts.splice(index, 1);
		  // };

}])


condominioAlDiaAppControllers.controller('ingresos_afiliadoController', ['$scope','$http','$location','context',
    function( $scope, $http, $location, context){

        $scope.ingresos_afiliado= context.data;
        $scope.country= null;
        $scope.active_month = new Date();
        $scope.dt = new Date();

        $scope.minDate= new Date(context.income_context.minDate).toUTC();
        $scope.maxDate= new Date().toUTC();


        $scope.countries = function(){
            var country_list =[];
            for (var i in $scope.ingresos_afiliado){
                if(country_list.indexOf($scope.ingresos_afiliado[i].pais)==-1){
                    country_list.push($scope.ingresos_afiliado[i].pais);
                }
            }
            return country_list;
        }

        $scope.queryDate = function(){
            var url = 'api/ingresos_afiliado/?month_created=' + $scope.dt.toISOString();
            $http.get(url).success(function(context){
                $scope.ingresos_afiliado = context.data;
                $scope.active_month = new Date($scope.dt);
            })
        }
        $scope.refresh = function(){
            $scope.ingresos_afiliado= context.data;
            $scope.dt = new Date(context.income_context.maxDate);
        }
        $scope.open1 = function() {
            $scope.popup1.opened = true;
        };
        $scope.popup1 = {
            opened: false
        };
        $scope.dateOptions = {
            minMode: 'month',
            // dateDisabled: disabled,
            // formatYear: 'yy',
            initDate :$scope.maxDate,
            maxDate: $scope.maxDate,
            minDate: $scope.minDate
            // startingDay: 1
        };
}])

condominioAlDiaAppControllers.controller('banco_afiliadoController', ['$scope','genericServices','context','$uibModal','$http',
    function( $scope, genericServices, context, $uibModal, $http){

        $scope.cuentas= context.accounts;
        $scope.affiliated_countries = context.countries;

        $scope.eliminarCuenta = function(cuenta){
            var conrimationString  ="¿Esta seguro(a) de que desea borrar esta cuenta?";
            genericServices.confirmModal(conrimationString)
            .then(function(confirmation){
                var url = 'api/banco_afiliado/'+cuenta.id+'/';
                    $http.delete(url).success(function(cuentas){
                        $scope.cuentas = cuentas;
                        genericServices.alertModal('Cuenta borrada exitosamente.')
                    })
            }); 
        }


        $scope.getPaises= function(){
            var modal_list= [];
            var acc_countries = [];
            

            for (var j in $scope.cuentas){
                acc_countries.push($scope.cuentas[j].pais);
            }
            for (var i in $scope.affiliated_countries){
                var addToList = true;
                for(var j in acc_countries){
                    if($scope.affiliated_countries[i].indexOf(acc_countries[j]) !=-1){
                        addToList= false;
                    }
                }
                if(addToList){
                    modal_list.push($scope.affiliated_countries[i])
                }
            }
            return modal_list;
        }

        $scope.registerAccountModal =function(modal_type, cuenta){
            var modalInstance = $uibModal.open({
                ariaLabelledBy: 'modal-title',
                ariaDescribedBy: 'modal-body',
                animation: true,
                templateUrl: 'static/ng_templates/modals/addAffiliateBankModal.html',
                controller: 'addAffiliateBankModalController',
                size: 'md',
                resolve: {
                    modal_type: function() {
                        return modal_type;
                    },
                    paises: function() {
                        if (cuenta){
                            return $scope.affiliated_countries;
                        }
                        return $scope.getPaises();
                    },
                    account_data:function() {
                        if(cuenta){
                            return cuenta;
                        }
                        return {};
                    }
                }
            });
            modalInstance.result.then(function (cuentas) {
              $scope.cuentas=cuentas;
              genericServices.alertModal('Su cuenta ha sido agregada satisfactoriamente.');
            });
        }
}])


condominioAlDiaAppControllers.controller('affiliateInicioController', ['$scope','$http','$location','affiliate_home','genericServices',
	function( $scope, $http, $location, affiliate_home, genericServices){


        $scope.affiliate_home= affiliate_home;
        $scope.condominios = affiliate_home.condominios
        $scope.popOverIsOpen= false;
        //$scope.register_bank = affiliate_home.register_bank;

        // if($scope.register_bank){
        //     genericServices.alertModal('Estimado usuario no olvide registrar una cuenta bancaria correspondiente a cada pais donde tiene condominios como afiliados.');
        // }

        $scope.membership= function(){
            var response;
            if($scope.condominios.length <=10){
                response = String(parseFloat($scope.condominios.length/10) *100)+ '%';
                $scope.percentage = response;
                return 'Miembro Gold';
            }else if($scope.condominios.length >10 && $scope.condominios.length <=25){
                response = String(parseFloat($scope.condominios.length/25) *100)+ '%';
                $scope.percentage = response;
                return 'Miembro Platinum';
            }else if($scope.condominios.length >25){
                $scope.percentage = '';
                return 'Miembro Diamond';
            }
        }

        $scope.copyToclipBoard= function(){
         var copyTextarea = document.querySelector('.js-copytextarea');
          copyTextarea.select();

          try {
            var successful = document.execCommand('copy');
            var msg = successful ? 'successful' : 'unsuccessful';
          } catch (err) {
            console.log('Oops, unable to copy');
          }
          //$scope.popOverIsOpen= true;
        }
		
}])

condominioAlDiaAppControllers.controller('inicioController', ['$scope','$http', 'userSessionServices', '$location','condo_home_screen_data','$uibModal','genericServices',
	function( $scope, $http, userSessionServices, $location, condo_home_screen_data, $uibModal, genericServices ){
		
		$scope.status ={};
		$scope.status.open1 =true;
		$scope.get_view = function(url){
			$location.path(url)
		}

		$scope.help= function(){
	        var modalInstance = $uibModal.open({
	            ariaLabelledBy: 'modal-title',
	            ariaDescribedBy: 'modal-body',
	            animation: true,
	            templateUrl: 'static/ng_templates/modals/help_modal.html',
	            controller: 'helpModalController',
	            size: 'sm'
	        });
		}


		$scope.condo_home_screen_data= condo_home_screen_data;
		$scope.active_month = new Date();
		$scope.dt = new Date().toUTC();
		$scope.minDate = new Date(condo_home_screen_data.minDate).toUTC();
		$scope.minDate = new Date('2015-01-01').toUTC();
		$scope.maxDate = new Date().toUTC();
 		$scope.formats = ['dd-MMMM-yyyy', 'yyyy/MM/dd', 'dd.MM.yyyy', 'shortDate'];
 		$scope.format = $scope.formats[0];

		$scope.open1 = function() {
			$scope.popup1.opened = true;
		};

		$scope.navigate_pagination= function(){
			var url = 'api/condo_home/?month_created=' + $scope.dt.toISOString()+'&page=' + String($scope.condo_home_screen_data.current_page)
			$http.get(url).success(function(response){
				$scope.active_month = new Date($scope.dt);
				$scope.condo_home_screen_data= response;	
			})
		}

		$scope.popup1 = {
			opened: false
		};

		$scope.dateOptions = {
			minMode: 'month',
			// dateDisabled: disabled,
			// formatYear: 'yy',
			initDate :$scope.maxDate,
			maxDate: $scope.maxDate,
			minDate: $scope.minDate
			// startingDay: 1
		};
		$scope.queryDate = function(){
			var url = 'api/condo_home/?month_created=' + $scope.dt.toISOString()
			$http.get(url).success(function(blog_context){
				$scope.active_month = new Date($scope.dt);
				$scope.condo_home_screen_data= blog_context
			})
		}


		$scope.blogModal= function(){
	        var modalInstance = $uibModal.open({
	            ariaLabelledBy: 'modal-title',
	            ariaDescribedBy: 'modal-body',
	            animation: true,
	            templateUrl: 'static/ng_templates/modals/addBlogModal.html',
	            controller: 'addBlogModalController',
	            size: 'md'
	        });
		    modalInstance.result.then(function (blog_context) {
				$scope.active_month = new Date();
				$scope.dt = new Date();
				$scope.condo_home_screen_data= blog_context
		      	genericServices.alertModal('Mensaje agregado al blog, todos los miembros de su condomino podran leer el mismo.');
		    });

		}
		
}])

condominioAlDiaAppControllers.controller('inquilino_inicioController', ['$scope','$uibModal','context','$http','genericServices',
	function($scope, $uibModal, context, $http, genericServices){
		//$scope.context = context;
		$scope.balance_actual=context.balance_actual;
		$scope.circulante = context.circulante;
		$scope.encuestas_vigentes = context.encuestas_vigentes;
		$scope.cobranzas_pendientes = context.cobranzas_pendientes;
		$scope.status = {};
		$scope.status.open1 = true;
		$scope.blog_context= context;
		$scope.cartelera = context.cartelera;
		$scope.myInterval = 0;
		$scope.playSlides = false;

		$scope.get_title=function(){
			if($scope.balance_actual<0){
				return 'deuda';
			}
			return 'balance';
		}

		$scope.setSlides = function(){
			$scope.playSlides = !$scope.playSlides;
			if ($scope.playSlides== true){
				$scope.myInterval = 3000;
			}else{
				$scope.myInterval = 0;
			}
		}

		//$scope.context= context;
		//$scope.blog_context= context.results;
		$scope.active_month = new Date();
		$scope.dt = new Date().toUTC();
		$scope.minDate = new Date(context.minDate).toUTC();
		$scope.minDate = new Date('2015-01-01').toUTC();
		$scope.maxDate = new Date().toUTC();
 		$scope.formats = ['dd-MMMM-yyyy', 'yyyy/MM/dd', 'dd.MM.yyyy', 'shortDate'];
 		$scope.format = $scope.formats[0];

		$scope.open1 = function() {
			$scope.popup1.opened = true;
		};

		$scope.popup1 = {
			opened: false
		};

		$scope.dateOptions = {
			minMode: 'month',
			// dateDisabled: disabled,
			// formatYear: 'yy',
			initDate :$scope.maxDate,
			maxDate: $scope.maxDate,
			minDate: $scope.minDate
			// startingDay: 1
		};

		$scope.navigate_pagination= function(){
			$http.get('api/inquilino_home/?month_created=' + $scope.dt.toISOString()+'&page=' + String($scope.blog_context.current_page)).success(function(response){
				$scope.active_month = new Date($scope.dt);
				$scope.blog_context= response;	
			})
		}


		$scope.queryDate = function(){
			var url = 'api/inquilino_home/?month_created=' + $scope.dt.toISOString()
			$http.get(url).success(function(blog_context){
				$scope.active_month = new Date($scope.dt);
				$scope.blog_context= blog_context
			})
		}




		$scope.blogModal= function(){
	        var modalInstance = $uibModal.open({
	            ariaLabelledBy: 'modal-title',
	            ariaDescribedBy: 'modal-body',
	            animation: true,
	            templateUrl: 'static/ng_templates/modals/addBlogModal.html',
	            controller: 'addBlogModalController',
	            size: 'md'
	        });
		    modalInstance.result.then(function (blog_context) {
				$scope.active_month = new Date();
				$scope.dt = new Date();
				$scope.blog_context= blog_context;
		      genericServices.alertModal('Mensaje agregado al blog, todos los miembros de su condomino podran leer el mismo.');
		    });

		}

}])

condominioAlDiaAppControllers.controller('pagos_inquilinoController', ['$scope','context','$http','$uibModal',
	function($scope,context, $http, $uibModal){

		$scope.moneda= sessionStorage.getItem('moneda');
		$scope.pagos = context.pagos;
		$scope.active_month = new Date(context.payment_param.active_month).toUTC();
        $scope.minDate= new Date(context.payment_param.minDate).toUTC();
        $scope.maxDate= new Date(context.payment_param.active_month).toUTC();
        $scope.dt = new Date(context.payment_param.active_month).toUTC();
        $scope.chosen_bank = {};
		$scope.verIngreso = function(ingreso){
	        var modalInstance = $uibModal.open({
	            ariaLabelledBy: 'modal-title',
	            ariaDescribedBy: 'modal-body',
	            animation: true,
	            templateUrl: 'static/ng_templates/modals/detallesIngresoModal.html',
	            controller: 'detallesIngresoModalController',
	            size: 'md',
	            resolve: {
	              ingreso: function(){
	                return ingreso;
	              }  
	            }

	        });
	    }

        $scope.getEstado= function(pago){
        	if (pago.aprobado){
        		if(pago.aprobado ==true){
        			return 'Aprobado';
        		}else{
        			return 'Rechazado';
        		}
        	}else{
        		return 'Por evaluar';
        	}
        }

		$scope.agregarPagoModal = function(){
	        var modalInstance = $uibModal.open({
	            ariaLabelledBy: 'modal-title',
	            ariaDescribedBy: 'modal-body',
	            animation: true,
	            templateUrl: 'static/ng_templates/modals/propietarioPaymentMethodModal.html',
	            controller: 'pagoInquilinoModalController',
	            size: 'md',
	            resolve: {
		            balance: function() {
		            	return sessionStorage.getItem('deuda_actual');
	            	},
		            payment_type: function() {
		            	return 'pp';
	            	},
		            cobranza_id: function() {
		            	return undefined;
	            	}         	   	        	     	        	
	            }
	        });
		    modalInstance.result.then(function (ingresos) {
		      $scope.ingresos = ingresos;
		    });
		}

        $scope.queryDate = function(){
            //var url = 'api/pago_inquilino/' + $scope.dt.toISOString();
			var url = 'api/pago_inquilino/?month_created=' + $scope.dt.toISOString()

            $http.get(url).success(function(pagos){
            	$scope.active_month = new Date($scope.dt);
                $scope.pagos = pagos;
                //$scope.active_month = new Date(context.income_context.active_month).toUTC()
            })
        }
        $scope.open1 = function() {
            $scope.popup1.opened = true;
        };
        $scope.popup1 = {
            opened: false
        };
        $scope.dateOptions = {
            minMode: 'month',
            // dateDisabled: disabled,
            // formatYear: 'yy',
            initDate :$scope.maxDate,
            maxDate: $scope.maxDate,
            minDate: $scope.minDate
            // startingDay: 1
        };

}])

condominioAlDiaAppControllers.controller('select_inmuebleController', ['$scope','context','$location','$uibModal','$http',
	function($scope, context, $location, $uibModal, $http){

		$scope.inmuebles= context;
		$scope.getCondoDetails= function(condominio){
	        var modalInstance = $uibModal.open({
	            ariaLabelledBy: 'modal-title',
	            ariaDescribedBy: 'modal-body',
	            animation: true,
	            templateUrl: 'static/ng_templates/modals/condo_detailsModal.html',
	            controller: 'condo_detailsModalController',
	            size: 'md',
	            resolve: {
		            condominio: function() {
		            	return condominio;
	            	}
	            }
	        });
		}

		$scope.getInmueble= function(inmueble){
			var inmueble_data = {};
			inmueble_data.inmueble = inmueble.id;
			var url = 'api/set_session/';
			$http.post(url, inmueble_data).success(function(response){
				sessionStorage.setItem('inmueble', inmueble.id);
				sessionStorage.setItem('nombre_inmueble', inmueble.nombre_inmueble);
				sessionStorage.setItem('condominio_nombre', inmueble.condominio.nombre);
				sessionStorage.setItem('deuda_actual', inmueble.deuda_actual);
				sessionStorage.setItem('moneda', inmueble.condominio.pais.moneda);
				sessionStorage.setItem('pais', inmueble.condominio.pais.nombre);
				sessionStorage.setItem('logo', inmueble.condominio.logo);
				$location.path('inquilino_inicio');
			})
		}

		//$scope.inmuebles= [];

}])




condominioAlDiaAppControllers.controller('landingPageController', ['$scope','$http', 'userSessionServices', '$location','screen_services','$window','$uibModal',
	function( $scope, $http, userSessionServices, $location, screen_services, $window, $uibModal ){


		$scope.loginForm = {};
		$scope.login = function(){
			if($scope.loginForm.$valid){
		        userSessionServices.logIn( $scope.loginFormulario )
			        .then(function( token ){
			        	userSessionServices.userProfile().then(function( response ){
			        		sessionStorage.setItem( 'userDataString', JSON.stringify( response ) );
			        		var path = userSessionServices.getBaseUrl();
			        		if(response.detalles_usuario.fast_help_popup==true){
						        var modalInstance = $uibModal.open({
						            ariaLabelledBy: 'modal-title',
						            ariaDescribedBy: 'modal-body',
						            animation: true,
						            templateUrl: 'static/ng_templates/modals/help_modal.html',
						            controller: 'helpModalController',
						            size: 'md',
						            // resolve: {
							           //  balance: function() {
							           //  	return cobranza.monto;
						            // 	},
							           //  payment_type: function() {
							           //  	return 'cobranza';
						            // 	},
							           //  cobranza_id: function() {
							           //  	return cobranza.id;
						            // 	}         	   	        	
						            // }
						        });
							    // modalInstance.result.then(function (ingresos) {
							    //  // $scope.ingresos = ingresos;
							    // });
			        		}
			        		$location.path(path);
			        	});
			        }).catch(function(errors){
			        	//$scope.errors = errors
						if(errors){
							for(var field in errors){
								if(field == 'non_field_errors'){
									if(errors[field] == 'E-mail is not verified.'){
										$scope.nonFieldErrors = 'No ha verificado su correo';
									}else{
										$scope.nonFieldErrors = errors[field];
									}
									
									//$scope.loginForm[field].$setValidity('serverValidation', false );
									//$scope.errors[field] = response[field].join(', ')
									//$scope.showServerError= true;
								}
							}
							
						}
			        })
			}
		}

		$scope.screenSize= function(){
			return screen_services.screen_width();
		}

}])

condominioAlDiaAppControllers.controller('registroController', ['$scope', 'listaPaises','Upload', '$timeout','$http','$location','genericServices',
	function( $scope, listaPaises, Upload, $timeout, $http, $location, genericServices ){

	$scope.listaPaises = listaPaises;
	$scope.formularioRegistro = {};
	$scope.googleOtherOriginData = {};
	$scope.pwd_regex ="^[a-zA-Z0-9]+$";
	$scope.url_param = $location.search();

	$scope.registerCondominio = function(file){
		//var param = $scope.url_param.affiliate ? (String($scope.url_param.affiliate+'/')) : '';
    	if ($scope.formRegistro.$valid){
			$scope.f = file;
			$scope.formularioRegistro['client_type'] ='condominio';
            $scope.formularioRegistro['affiliate'] =$scope.url_param.affiliate;
		    file.upload = Upload.upload({
		      //url: 'rest-auth/registration/'+ param,
              url: 'rest-auth/registration/',
		      data: $scope.formularioRegistro
		    });

		    file.upload.then(function (response, status) {
		    	if( response.status == 201 ){
		    		var key = response.data;
		    		$location.path('registro_gracias')
		    	}

		    }, function (response) {
		      if (response.status > 0)
		      	//genericServices.alertModal()
		        $scope.errorMsg = response.status + ': ' + response.data;
		    	$scope.showSuccessMessage = false;
		    }, function (evt) {
		      // Math.min is to fix IE which reports 200% sometimes
		      file.progress = Math.min(100, parseInt(100.0 * evt.loaded / evt.total));
		    });
		    }
	}

	$scope.placeHolderRif = function(){
		if($scope.formularioRegistro.pais){
			for (var pais in $scope.listaPaises){
				if( $scope.listaPaises[pais].nombre.trim().toLowerCase() == $scope.formularioRegistro.pais.trim().toLowerCase() ){
					var temp = $scope.listaPaises[pais];
					$scope.regex = temp.rif_regex;
					$scope.rif_placeholder = temp.rif_placeholder;
					$scope.nombre_registro_fiscal = temp.nombre_registro_fiscal;
					$scope.rif_format = temp.rif_format;
					//return $scope.listaPaises[pais].nombre_registro_fiscal;
				}
			}		
		}
		return 'Registro Fiscal';
	}
}])

condominioAlDiaAppControllers.controller('navBarController', ['$scope', '$http', 'userSessionServices', '$rootScope', '$window','$location',
	function( $scope, $http, userSessionServices, $rootScope, $window,$location){
		$scope.navbar_manipulated = false;
		$scope.salir = function(){
			userSessionServices.logOut();
		}
		$scope.toggleCollapse = function(){
			if($window.innerWidth<=768 && $scope.navbar_manipulated == false){
				$scope.navCollapsed = true;
				$scope.$apply();
			}
		}

		$scope.userName = function(){
			userdata = JSON.parse(sessionStorage.getItem('userDataString'))
			if( userdata ){
				if (userdata.last_name || userdata.first_name){
					var result = (userdata.first_name + ' '  + userdata.last_name);
					return result;
				}else if( userdata.email){
					return userdata.email;
				}else{
					return 'No name/email';			
				}
			}
		}

		if(document.documentElement.clientWidth <=768){
			$scope.navCollapsed = true;
		}


		$scope.navbarToggler = function(event){
			if(event.target.nodeName=='A'){
				if ($scope.navCollapsed == false){			
					$scope.navCollapsed = true;
				}				
			}

		}
		
		$scope.logout = function(){
			userSessionServices.logOut()
		}

	// switch($location.path()) {

	//     case '/bancos':
	// 		$scope.accordionOpen= true;
	//         break;

	//     case '/balance':
	// 		$scope.accordionOpen= true;
	//         break;
	//     case '/egresos':
	// 		$scope.accordionOpen= true;
	//         break;
	//     case '/ingresos':
	// 		$scope.accordionOpen= true;
	//         break;
	//     default:
	//     	break;
	// } 
	}

		
])


