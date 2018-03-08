var condominioAlDiaModalControllers = angular.module('condominioAlDiaModalControllers',[]);


condominioAlDiaModalControllers.controller('agregarInmuebleModalController', function( $scope, $uibModalInstance, $http, listaInmuebles, userSessionServices, total_inmuebles, $rootScope, tipo, inmueble ) {
	var user_data = $rootScope.userData;
	$scope.may_modify_inmueble = inmueble.may_modify_inmueble;
	$scope.tipo = tipo;
	$scope.residenteForm = inmueble;
	$scope.listaInmuebles = listaInmuebles;
	$scope.nombre_registro_fiscal = user_data.detalles_usuario.pais.nombre_registro_fiscal;
	$scope.rif_format = user_data.detalles_usuario.pais.rif_format;
	$scope.pattern = user_data.detalles_usuario.pais.rif_regex;
	$scope.exception = null;

	if($scope.tipo == 'agregar'){
		$scope.total_inmuebles = total_inmuebles;
		$scope.listaInmuebles = listaInmuebles;
		$scope.residente_encontrado = false;
	}else if($scope.tipo == 'modificar'){
		$scope.exception = inmueble.id;
		$scope.residente_encontrado = true;
		$scope.total_inmuebles = total_inmuebles - $scope.residenteForm.alicuota;
		//var index = $scope.listaInmuebles.indexOf($scope.residenteForm.);
		//array.splice(index, 1);
	}

	$scope.resetField = function(master, slave, type){
		if($scope.residenteForm[master]==false){// && $scope.residenteForm.tipo=='agregar'
			$scope.residenteForm[slave] = '';
		}
	}
	

	$scope.checkInquilino = function(){
		$scope.formCondoInmueble.email.$setValidity('correoNoDisponible', true);
		if($scope.formCondoInmueble.email.$valid){
			var url = 'api/user_email/'+$scope.residenteForm.email;
			$http.get(url).success(function(response, status){
				console.log(response, status)
				if(status==200 ){

					if(response['detalles_usuario']['tipo_usuario'] == 'condominio'){
						$scope.formCondoInmueble.email.$setValidity('correoNoDisponible', false);
					}else{
						$scope.residenteForm.first_name= response['first_name'];
						$scope.residenteForm.last_name= response['last_name'];
						$scope.residenteForm.rif=response['detalles_usuario']['rif']
						$scope.residente_encontrado = true;
					}

				}else{
					$scope.residenteForm.rif = '';
					$scope.residenteForm.first_name = '';
					$scope.residente_encontrado = false;
				}
				
			}).error(function(errors){
					$scope.residente_encontrado = false;
				})
		}
		
	}

	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};

	$scope.crearResidente = function(){
		var APImethod;
			if($scope.tipo =='agregar'){
				APImethod = $http.post
				var url = 'api/inmuebles/';
			}else{
				APImethod = $http.patch;
				var url = 'api/inmuebles/' +$scope.residenteForm.id+'/';
			}
		
		APImethod(url, $scope.residenteForm).success(function(context, status){
			if(status == 200){
				$rootScope.userData.detalles_usuario.activo = context.condominio_activo;
				$uibModalInstance.close(context.data); 
			}else if(status == 203){
				console.log(JSON.stringify(response))
			}else if(status== 400){
				return false
			}
		})
	}
	//var $ctrl = this;

    // $scope.close = function () {
    // 	$uibModalInstance.close($location.path('/home')); 
    // };


});


condominioAlDiaModalControllers.controller('addPollModalModalController', function( $scope, $uibModalInstance, $http) {
	
	$scope.encuestaFormData= {};
	$scope.format = 'dd MMM yyyy';

	$scope.open = function() {
		$scope.popup1.opened = true;
	};

	$scope.popup1 = {
		opened: false
	};

	$scope.dateOptions = {
		minMode: 'day',
		initDate :new Date().toUTC(),
		maxDate: new Date().addDays(30).toUTC(),
		minDate: new Date().toUTC()
	}

	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};

	$scope.setEnd = function(){

		if($scope.duracion && $scope.encuestaFormData.start){
			var end = new Date(String($scope.encuestaFormData.start));
			$scope.encuestaFormData.end = end.addDays(parseInt($scope.duracion));
		}
		return false;
	}
	$scope.agregarEncuesta = function(){
		$http.post('api/polls/', $scope.encuestaFormData).success(function(polls, status){
			if (status==200){
				$uibModalInstance.close(polls);
			}
		})
	}
});


condominioAlDiaModalControllers.controller('loadCsvModalController', function( $scope, $uibModalInstance, $http, Upload, $window ) {
	
	$scope.formData= {};

	$scope.get_sample=function(sample_type){
		var url = 'api/inmuebles_csv_sample/?file_type=' +sample_type;
		console.log(url)
		$window.location.href = url;
	}

	$scope.postCSV= function(file){
		var url = 'api/inmuebles_csv_sample/';
    	if ($scope.csvForm.$valid){
			$scope.f = file;
			//$scope.formularioRegistro['client_type'] ='condominio';
            //$scope.formularioRegistro['affiliate'] =$scope.url_param.affiliate;
		    file.upload = Upload.upload({
		      //url: 'rest-auth/registration/'+ param,
              url: url,
		      data: $scope.formData
		    });

		    file.upload.then(function (response, status) {
		    	console.log(response, status)
		    	if( response.status == 200 ){
		    		$uibModalInstance.close(response)
		    	}

		    }, function (response) {
		      if (response.status > 0)
		      	console.log(response)
		      	//genericServices.alertModal()
		        $scope.errorMsg = response.status + ': ' + response.data;
		    	$scope.showSuccessMessage = false;
		    }, function (evt) {
		      // Math.min is to fix IE which reports 200% sometimes
		      file.progress = Math.min(100, parseInt(100.0 * evt.loaded / evt.total));
		    });
		    }
		// $http.post(url, $scope.formData).success(function(response){
		// 	$uibModalInstance.close(response);
		// })
	}

	//$scope.inmueble = inmueble;
	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};

});

condominioAlDiaModalControllers.controller('buscarEntreFechasController', function( $scope, $uibModalInstance ) {
	
	//$scope.inmueble = inmueble;
	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};

});
condominioAlDiaModalControllers.controller('voucherModalController', function( $scope, $uibModalInstance, voucher ) {
	
	//$scope.inmueble = inmueble;
	//$scope.voucher = "'"+String(voucher)+"'";
	$scope.voucher =String(voucher);
	$scope.cancel = function () {
		$uibModalInstance.close('next url');
	};

});



// condominioAlDiaModalControllers.controller('egresoDetalladoModalController', function( $scope, $uibModalInstance, cuentas ) {
	
// 	$scope.extraColumnFormdata= {};
// 	$scope.cuentas = cuentas;

// 	function get_banc_name(id){
// 		for (var i in $scope.cuentas){
// 			var item = $scope.cuentas[i];
// 			if(item.id == id){
// 				return item.banco;
// 			}
// 		}
// 		return undefined;
// 	}

// 	$scope.cancel = function () {
// 		$uibModalInstance.dismiss('cancel');
// 	};

// 	$scope.agregarColumna = function(){
// 		$scope.extraColumnFormdata.type='egreso';//EXTRA COL IS CONSIDERED EGRESO
// 		$scope.extraColumnFormdata.saved = false;
// 		$scope.extraColumnFormdata.banco_name= get_banc_name($scope.extraColumnFormdata.banco);
// 		$uibModalInstance.close($scope.extraColumnFormdata);
// 	}

// });

condominioAlDiaModalControllers.controller('addInmuebleCategoryModalController', function( $scope, $uibModalInstance,categories, $http, selection, $rootScope, genericServices ) {
	
	$scope.formData= {};
	$scope.rowActivation = {};
	$scope.categories =categories;
	$scope.selection= selection;
	$scope.modify=true;
	//$scope.inmuebles =[];
	$scope.black_list =['todos', 'especificos', 'especifico', 
	'retrasados', 'retrasado', 'todo', 'junta de condominio', 
	'junta', 'juntas', 'propietario', 'propietarios', 'no miembro', 
	'no miembros', 'no-miembros','arrendatario', 'arrendatarios'
	]


	$scope.master=angular.copy($scope.categories);

	$scope.eliminate = function(category){
			genericServices.confirmModal("¿Esta seguro(a) de que desea eliminar esta categoria? Los inmuebles asociados NO seran afectados, tan solo seran removidos de dicha categoria.")
			.then(function(confirmation){
				var url = 'api/inmueble_category/'+ category.id +'/';
				$http.delete(url).success(function(context){
					$scope.categories = context.categories;
					$scope.inmuebles = context.inmuebles;
					alert('Ha borrado los inmuebles seleccionados exitosamente.');
				})
			});	

	}


	$scope.deLink=function(category){
		//end result must refresh inmuebles
		if($scope.selection.length>0){
			genericServices.confirmModal("¿Esta seguro(a) de que desea desligar esta categoria? Los inmuebles asociados NO seran afectados, tan solo seran removidos de dicha categoria.")
			.then(function(confirmation){
				if($scope.selection.length>0){
					var data = {};
					data.selection= $scope.selection;
					data.id = category.id;
					var url ='api/remove_category/';
					$http.post(url, data).success(function(inmuebles, status){
						if(status==200){
							$scope.inmuebles = inmuebles;
							$uibModalInstance.close(inmuebles);
						}
					})
				}
			});	
		}else{
			alert('Debe seleccionar los inmuebles que desea sacar de la seccion "' + category.name.toLowerCase()+'".' );		
		}	

	}

	$scope.modify = function(category){
		if (category.name){
			category.show = false;
			var url = 'api/inmueble_category/'+ category.id +'/';
			$http.patch(url, category).success(function(response){
				$scope.categories = response.categories;
				$scope.inmuebles = response.inmuebles;
			})		
		}else{
			alert('Debe ingresar un valor.')
		}

	}


	$scope.assignCategory = function(category){
		if($scope.selection.length>0){
			var data = {};
			data.selection= $scope.selection;
			data.id = category.id;
			var url ='api/assign_category/';
			$http.post(url, data).success(function(inmuebles, status){
				if(status==200){
					$scope.inmuebles = inmuebles;
					$uibModalInstance.close(inmuebles);
				}else{
					alert(inmuebles)
				}
			})
		}else{
			alert('Debe seleccionar los inmuebles que desea catalogar como "' + category.name.toLowerCase()+'".' );
		}

	}

	$scope.cancel = function () {
		$uibModalInstance.dismiss();
	};



	$uibModalInstance.result.catch(function(){
		$rootScope.$broadcast('uptate-data', { categories: $scope.categories, inmuebles:$scope.inmuebles });
	})

	$scope.PostCategory= function(){
		var url = 'api/inmueble_category/';
		$http.post(url, $scope.formData).then(function(categories){
			console.log(categories)
			$scope.categories = categories.data;
			$scope.formData= {};
			$scope.categoriaInmuebleForm.$setUntouched();
			$scope.categoriaInmuebleForm.$setPristine();
		}, function(errors){
			console.log(errors.data)
		});	
		
	}

});

condominioAlDiaModalControllers.controller('message_detailModalController', function( $scope, $uibModalInstance, message ) {
	
	$scope.message = message;
	$scope.search = '';
	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};

});

condominioAlDiaModalControllers.controller('help_menuModalController', ['$scope','help_items','$uibModalInstance','$rootScope',
	function( $scope, help_items, $uibModalInstance, $rootScope){

		$scope.help_items = help_items;
		$rootScope.helpModalOpened =true;
		$scope.cancel = function () {
			$uibModalInstance.close('ok');//updates rootscope telling it modal has closed
		};

	$uibModalInstance.result.catch(function(){
		$rootScope.helpModalOpened =false;
	})

}])


condominioAlDiaModalControllers.controller('helpModalController', function( $scope, $uibModalInstance, $location, $http ) {

	$scope.accept= function(){
		$uibModalInstance.close(closeHelpTip());	
	}

	function closeHelpTip(){
		if($scope.dontShow == true){
			var url ="/api/tips/";
			var data = {};
			data.dontShow = $scope.dontShow;
			$http.post(url, data).success(function(response){
				console.log(response)
			})
		}
		return false;

	}




});



condominioAlDiaModalControllers.controller('condo_detailsModalController', function( $scope, $uibModalInstance, condominio) {
	$scope.condominio= condominio;

	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};
});




condominioAlDiaModalControllers.controller('addInmueblesModalAlertModalController', function( $scope, $uibModalInstance, $location ) {
	
	$scope.redirectClose= function(){
		$uibModalInstance.dismiss($location.path('inmuebles'));
	}

	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};

});

condominioAlDiaModalControllers.controller('relacion_mes_confirmationModalController', function( $scope, $uibModalInstance, context ) {
	
	// $scope.redirectClose= function(){
	// 	$uibModalInstance.dismiss($location.path('inmuebles'));
	// }

	$scope.relacionVerificationData = {}
	$scope.context = context;

	console.log(context)

	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};

	$scope.get_name =function(cuenta){
		return 'a' +String(cuenta.id)
	}

	$scope.crearRelacion = function(){
		var url = 'api/relacion_mes_summary/';
		$uibModalInstance.close('ok')
		// $http.post(url, $scope.relacionVerificationData).success(function(response){

		// })
	}

});



condominioAlDiaModalControllers.controller('add_extra_column_modalController', function( $scope, inmuebles, $uibModalInstance, cuentas ) {
	
	$scope.extraColumnFormdata = {};
	$scope.inmuebles = inmuebles;
	$scope.cuentas = cuentas;
	$scope.agregarColumna = function(){
		$uibModalInstance.close($scope.extraColumnFormdata);
	}

	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};

});


condominioAlDiaModalControllers.controller('delColController', function( $scope, cols, $uibModalInstance, genericServices ) {
	

	$scope.cols= cols;
	console.log(cols)

	$scope.delCol = function(){
		var conrimationString  ="¿Esta seguro(a) de que desea borrar esta columna? ";
		genericServices.confirmModal(conrimationString)
			.then(function(confirmation){
				$uibModalInstance.close($scope.columna)
			});	
	}

	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};

});

condominioAlDiaModalControllers.controller('facturaDetailsModalController', function( $scope, $uibModalInstance, factura ) {
	
	$scope.factura = factura;
	console.log(factura)
	$scope.search = '';
	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};

});

condominioAlDiaModalControllers.controller('egreso_details_modallController', function( $scope, $uibModalInstance, egreso ) {
	
	$scope.egreso = egreso;
	console.log(egreso)
	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};

});


condominioAlDiaModalControllers.controller('register_prop_deposit_modalController', function( $scope, $uibModalInstance, Upload, context, $location,genericServices, payment_type ) {
	
	$scope.context = context;
	console.log(context)
	$scope.context.payment_type = payment_type;
	$scope.depTransData= {};
	$scope.moneda= sessionStorage.getItem('moneda');
	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};

	$scope.registroPago=function(){
		//banco field must pass integer not bank name
		var url = 'api/pago_inquilino/';
		var data= $scope.context;
		data.banco = data.id;
		data.comprobante_pago = $scope.depTransData.comprobante_pago;
		data['cuenta_dep'] = $scope.context.id;
		data['nro_referencia'] = $scope.depTransData.nro_referencia;
		$scope.f = Upload.upload({
	      url: url,
	      data: data,
	      method: 'POST'
		}).then(function (response) {
	   	if( response.status == 200 ){
	   		$location.path('pagos_inquilino');
	   		$uibModalInstance.close(genericServices.alertModal('Su pago se ha registrado, una vez sea evaluado se le dejara saber via correo electronico el estado del mismo.'));
	   	}

	    }, function (error) {
	        if (error.status > 0)
	            $scope.errorMsg = error.status + ': ' + error.data;
	    }, function (evt) {
	      // Math.min is to fix IE which reports 200% sometimes
	      Upload.progress = Math.min(100, parseInt(100.0 * evt.loaded / evt.total));
	    });
	}


});



condominioAlDiaModalControllers.controller('paymentMethodModalController', function( $scope, $uibModalInstance, $location,paymentMethods, factura ) {
	
	$scope.paymentMethods = paymentMethods;
	$scope.factura= factura;

	$scope.getMethodID=function(payment_method){
		for(var i in $scope.paymentMethods){
			if($scope.paymentMethods[i].metodo_pago.nombre==payment_method){
				return $scope.paymentMethods[i].id;
			}
		}
	}
	$scope.getMethodID($scope.method)

	$scope.selectMethod= function(){

		switch($scope.method) {
		    case 'Deposito/Transferencia':
		    $uibModalInstance.close($location.path('pago_dep_trans').search({factura: $scope.factura.id, payment_method:$scope.getMethodID($scope.method)}));
		        break;
		    case 'Credit Card':
		        $uibModalInstance.close($location.path('pago_tdc'));
		        break;
		    default:
		        return false;
		} 
	}

	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};

});

condominioAlDiaModalControllers.controller('registerDepositModalController', function( $scope, $uibModalInstance, $http, chosen_bank, factura, Upload, payment_method, $location ) {


	$scope.chosen_bank= chosen_bank;
	$scope.factura= factura;
	$scope.payment_method= payment_method;
	$scope.depTransData = {};

	$scope.registroPago=function(){
		var url = 'api/pago_dep_trans/';
		var data= $scope.depTransData;
		data['banco'] = $scope.chosen_bank.id;
		data['factura'] = $scope.factura.id;
		data['tipo_de_pago'] = $scope.payment_method.id;

		$scope.f = Upload.upload({
	      url: url,
	      data: data,
	      method: 'POST'
		}).then(function (response) {
	   	if( response.status == 200 ){
	   		$location.path('facturacion_condominio');
	   		$uibModalInstance.close(response);
	   	}

	    }, function (error) {
	        if (error.status > 0)
	            $scope.errorMsg = error.status + ': ' + error.data;
	    }, function (evt) {
	      // Math.min is to fix IE which reports 200% sometimes
	      Upload.progress = Math.min(100, parseInt(100.0 * evt.loaded / evt.total));
	    });
	}

			    


	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};

});


condominioAlDiaModalControllers.controller('agregarEgresoModalController', function( $scope, $uibModalInstance, $http, minDate, maxDate,genericServices, egreso, tipo, context ) {

	$scope.format = 'dd-MM-yyyy';
	$scope.tipo = tipo;
	$scope.egresoFormData = egreso;
	$scope.egresoFormData.deudores = $scope.tipo=='modificar' ? egreso.deudores:'todos';
	$scope.maxDate = maxDate;
	$scope.minDate = minDate;
	$scope.tipos_egresos = context.tipos_egresos;
	$scope.egresoFormData.fecha_facturacion = $scope.tipo=='modificar' ? new Date($scope.egresoFormData.fecha_facturacion).toUTC() : '';
	$scope.cuentas = context.cuentas;
	
	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};

	$scope.open1 = function() {
		$scope.popup1.opened = true;
	};

	$scope.popup1 = {
		opened: false
	};
	$scope.dateOptions = {
		minMode: 'day',
		initDate :$scope.minDate,
		maxDate: $scope.maxDate,
		minDate: $scope.minDate
	};

	$scope.agregarEgreso = function(){
		var APImethod;
			if($scope.tipo =='agregar'){
				APImethod = $http.post
				var url ='api/egresos/';
			}else{
				APImethod = $http.patch;
				var url = 'api/egresos/' +$scope.egresoFormData.id+'/';
			}
		
		APImethod(url, $scope.egresoFormData).success(function(egresos, status){
			console.log(status)
			if(status == 200){
				console.log('a')
				$uibModalInstance.close(egresos); 
			}else if(status == 203){
				console.log('b')
				console.log(JSON.stringify(egresos))
			}else if(status== 400){
				console.log('c')
				return false;
			}
			console.log('d')
		})
		.error(function(errors){
			//$uibModalInstance.dismiss();
			genericServices.alertModal( errors.non_field_errors[0], 'Alerta' );
		})
	}

	// $scope.agregarEgreso = function(){
	// 	var url ='api/egresos/';
	// 	$http.post( url, $scope.egresoFormData ).success( function( egresos, status ){
	// 		if (status == 200){
	// 			$uibModalInstance.close(egresos); 
	// 		}else{
 // 				alert('Hubo un error al agregar el pago');
 // 			}
	// 	})
	// 	.error(function(errors){
	// 		$uibModalInstance.dismiss();
	// 		genericServices.alertModal( errors.non_field_errors[0], 'Alerta' );
	// 	})
	// }

});




condominioAlDiaModalControllers.controller('datosInquilinoModalController', function( $scope, $uibModalInstance, inmueble ) {
	$scope.inmueble = inmueble;
	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};
});

condominioAlDiaModalControllers.controller('addAffiliateBankModalController', function( $scope, $uibModalInstance,$http, modal_type, paises, account_data ) {

	
	$scope.tipo= modal_type;
	$scope.paises =paises;
	$scope.cuentaData= account_data;

	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};

	$scope.crearCuenta = function(){
		var APImethod;
			if($scope.tipo =='agregar'){
				APImethod = $http.post;
				var url = 'api/banco_afiliado/';
			}else{
				APImethod = $http.patch;
				var url = 'api/banco_afiliado/' +$scope.cuentaData.id+'/';
			}

		APImethod(url, $scope.cuentaData).success(function(cuentas, status){
			if(status == 200){
				$uibModalInstance.close(cuentas); 
			}else if(status== 400){
				return false
			}
		})
	}

});


condominioAlDiaModalControllers.controller('addBlogModalController', function( $scope, $uibModalInstance, $http, $filter ) {
	

	$scope.blogData = {};

	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};

	$scope.postBlog=function(){
		var url = 'api/condo_home/';
		$http.post(url, $scope.blogData).success(function(blog, status){
			if(status==200){
				$uibModalInstance.close(blog)
			}else if( status ==400){
				alert('Ha ocurrido un error');
			}

		})
		
	}
});


condominioAlDiaModalControllers.controller('paymentDetailsModalController', function( $scope, $uibModalInstance, payment, $window ) {
	
	$scope.payment = payment;
	console.log(payment)

	$scope.openComprobante = function( url ) {
		$window.open( url );
	};

	$scope.getEstado=function(){
			var message;
			if ($scope.payment!=null){
				if($scope.payment.aprobado==true){
					message='Pago aprobado';
				}else if($scope.payment.aprobado==false){
					message='Pago rechazado';
				}else if($scope.payment.aprobado==null){
					message='Pago bajo evaluacion';
				}
			}else if($scope.payment==null){
				message='Pago requerido';
			}
			
			return message;
	}

	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};
});



condominioAlDiaModalControllers.controller('propagate_modalController', function( $scope, $uibModalInstance, cols, rows_checked ) {
	$scope.cols=cols;
	$scope.propagateObj={};
	$scope.propagateObj.rows_checked= rows_checked;

	$scope.propagate = function(){
		$uibModalInstance.close($scope.propagateObj);
	}

	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};
});


condominioAlDiaModalControllers.controller('agregarPagoModalController', function( $scope, $uibModalInstance, $http, context, $filter, minDate, maxDate, genericServices, ingreso, tipo ) {
	
	$scope.inmuebles = context.inmuebles;
	$scope.cuentas = context.cuentas;
	$scope.bancos_pais = context.bancos;
	$scope.tipo = tipo;
	$scope.pagoFormData =ingreso;

	$scope.pagoFormData.tipo_de_ingreso= $scope.tipo=='modificar' ? ingreso.tipo_de_ingreso:'pp';
	$scope.format = 'dd-MM-yyyy';
	$scope.minDate = minDate;
	$scope.maxDate = maxDate;
	$scope.pagoFormData.cheque = $scope.pagoFormData.nro_cheque ? true:false;
	$scope.pagoFormData.fecha_facturacion = $scope.tipo=='modificar' ? new Date($scope.pagoFormData.fecha_facturacion).toUTC() : '';
	
	$scope.dateOptions = {
		minMode: 'day',
		initDate :$scope.minDate,
		maxDate: $scope.maxDate,
		minDate: $scope.minDate
	};


	$scope.get_inmueble = function(inmueble){
		for(var i in $scope.inmuebles){
			if($scope.inmuebles[i].id == inmueble){
				return $scope.inmuebles[i];
			}
		}
	}
	$scope.pagoFormData.inmuebleTA = $scope.tipo=='modificar' ? $scope.get_inmueble(ingreso.inmueble): '';


	$scope.get_bank = function(acc_number){
		for(var i in $scope.cuentas){
			if($scope.cuentas[i].nro_cuenta == acc_number){
				return String($scope.cuentas[i].id);
			}
		}
	}



	$scope.pagoFormData.cuenta_dep =$scope.tipo=='modificar' ? $scope.get_bank(ingreso.cuenta_dep): '';
	//$scope.pagoFormData.pagador =

	$scope.open1 = function() {
		$scope.popup1.opened = true;
	};

	$scope.popup1 = {
		opened: false
	};

	$scope.getName = function(inmueble){
		if (inmueble && inmueble.inquilino){
			return '('+ inmueble.nombre_inmueble+') '+inmueble.inquilino.user.first_name +' '+ inmueble.inquilino.user.last_name
		//return $filter('capfirstlettereachword')( inmueble);
		}
	}

	$scope.onSelect = function ($item, $model, $label) {
	    $scope.pagoFormData.inmueble = $item.id
	};

	$scope.resetFields = function(){
		if($scope.pagoFormData.cheque== false){
			$scope.pagoFormData.nro_cheque = '';
			$scope.pagoFormData.banco_cheque = '';
		}
	}

	$scope.getInmuebleInfo =function(inmueble){
		if (inmueble){
			console.log(inmueble)
			return ( inmueble.nombre_inmueble + ' ' + '('+ inmueble.inquilino.user.first_name + ' '+inmueble.inquilino.user.last_name +')' );
		}
		return false;
	}

	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};

	$scope.agregarPago = function(){
		var url ="api/ingresos/";
		var APImethod;
			if($scope.tipo =='agregar'){
				APImethod = $http.post
				var url = url;
			}else{
				APImethod = $http.patch;
				var url = url +$scope.pagoFormData.id+'/';
			}
		
		APImethod(url, $scope.pagoFormData).success(function(ingresos, status){
			if(status == 200){
				$uibModalInstance.close(ingresos); 
			}else{
				alert('Hubo un error al agregar el pago');
			}
		})

		.error(function(errors){
			//$uibModalInstance.dismiss();
			console.log(errors)
			//genericServices.alertModal( errors.non_field_errors[0], 'Alerta' );
		})	
	}
});


condominioAlDiaModalControllers.controller('alertModalController', function( $scope, $uibModalInstance, message, heading ) {
	
	$scope.message = message;
	$scope.heading = heading;
	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};

});

condominioAlDiaModalControllers.controller('pagoInquilinoModalController', function( $scope, $uibModalInstance,$location, balance, payment_type, cobranza_id, $rootScope ) {
	$scope.balance= parseFloat(balance)<=0 ? parseFloat(balance):0;
	$scope.moneda = sessionStorage.getItem('moneda');
	//sessionStorage.setItem('deuda_actual', balance);
	$scope.selectMethod= function(){
		var pais= sessionStorage.getItem('pais');
		if($scope.method =='pago_propietario_dep'){
			$uibModalInstance.close($location.path($scope.method).search({balance:parseFloat(balance), payment_type:payment_type, cobranza_id:cobranza_id}));
		}
		else if(pais =='Venezuela' && $scope.method =='pago_propietario_tdc'){
			$uibModalInstance.close($location.path('instapago').search({balance:parseFloat(balance), payment_type:payment_type, cobranza_id:cobranza_id}));

		}
	}

	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};

});


condominioAlDiaModalControllers.controller('razonRechazoModalController', function( $scope, $uibModalInstance, ingreso, $http ) {
	
	$scope.ingreso = ingreso;
	
	$scope.ingresoData = {};
	$scope.ingresoData.aprobado = false;
	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};

	$scope.rechazarPago  = function(){
		var url = 'api/ingresos/' + $scope.ingreso.id+ '/';
		$http.patch(url, $scope.ingresoData).success(function(ingresos){
			$uibModalInstance.close(ingresos); 
		})
	}

});


condominioAlDiaModalControllers.controller('pollDetailsModalController', function( $scope, $uibModalInstance, poll ) {
	
	$scope.poll = poll;
	$scope.get_status= function(poll){
		var status;
		if(poll.active==true){
			status = 'en curso';
		}else if(poll.active==false  && poll.ballot_close_timestamp){
			status = 'cerrada';
		}else if(poll.active==false  && !poll.ballot_close_timestamp){
			status ='esperando';
		}
		return status;
	}

	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};

});


condominioAlDiaModalControllers.controller('detallesIngresoModalController', function( $scope, $uibModalInstance, ingreso ) {
	
	$scope.ingreso = ingreso;

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
	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};

});


condominioAlDiaModalControllers.controller('anuncioModalController', function( $scope, $uibModalInstance, anuncio ) {
	$scope.anuncio = anuncio;
	
	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};
});

condominioAlDiaModalControllers.controller('cobranza_modalController', function( $scope, $uibModalInstance, inmuebles, $http, $location, categories ) {
	
	$scope.inmuebles= inmuebles;
	$scope.cobranza_data= {};
	//$scope.cobranza_data.monto = 0;
	$scope.categories =categories;

	$scope.checkMonto= function(){
		if($scope.cobranza_data.tipo_monto=='monto'){
			$scope.cobranza_data.monto = $scope.cobranza_data.montoMonto;
		}
		else if($scope.cobranza_data.tipo_monto=='porAlicuota'){
			$scope.cobranza_data.monto = $scope.cobranza_data.alicMonto;
		}
	}


	$scope.checkRadios = function(){
		console.log('run')

		$scope.cobranza_data.monto = 0;
		$scope.cobranza_data.montoMonto = '';
		$scope.cobranza_data.alicMonto = '';
	}

	// var _val=undefined;
 //    $scope.cobranza_data = {
 //      montoMonto: function(val) {
 //       // Note that newName can be undefined for two reasons:
 //       // 1. Because it is called as a getter and thus called with no arguments
 //       // 2. Because the property should actually be set to undefined. This happens e.g. if the
 //       //    input is invalid
 //       	if (val){
	//        if($scope.cobranza_data.tipo_monto =='monto'){
	//        	$scope.cobranza_data.monto = val;
	//        }
 //   		}
 //       return arguments.length ? (_val = val) : _val;
 //      }
 //     }
 //    $scope.cobranza_data = {
 //      alicMonto: function(val) {
 //      	if (val){
	//        if($scope.cobranza_data.tipo_monto =='porAlicuota'){
	//        	$scope.cobranza_data.monto = val;
	//        }
 //      	}
 //       // Note that newName can be undefined for two reasons:
 //       // 1. Because it is called as a getter and thus called with no arguments
 //       // 2. Because the property should actually be set to undefined. This happens e.g. if the
 //       //    input is invalid

 //       return arguments.length ? (_val = val) : _val;
 //      }
 //     }




	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};

	$scope.get_property= function(inmueble){
		if(inmueble && inmueble.inquilino){
			return "("+ String(inmueble.nombre_inmueble) +") "+inmueble.inquilino.user.first_name+' '+ inmueble.inquilino.user.last_name
		}
		return false;
	}

	$scope.onSelect = function ($item, $model, $label) {
	    $scope.cobranza_data.inmueble = parseInt($item.id)
	};

	$scope.post= function(){
		if($scope.CobranzaForm.$valid==true){
			var url ='api/cobranzas_condominio/';
			$http.post(url, $scope.cobranza_data).then(function(response){
				$uibModalInstance.close(response.data);
			}, function(errors){
				alert(errors.data.non_field_errors[0]);
			});
		}
		return false;

	}

	$scope.getUrl =function(url){
		$uibModalInstance.dismiss($location.path(url));
	}

});


condominioAlDiaModalControllers.controller('voteModalController', function( $scope, $uibModalInstance, poll, $http, genericServices ) {
	

	$scope.poll = poll;
	
	$scope.submitVote = function(poll, vote){
		var param;
		if(vote == true){
			param = 'a favor';
		}else{
			param = 'en contra';
		}
 		var conrimationString  ="¿Esta seguro(a) de que desea votar "+ param +" de esta encuesta?"
		genericServices.confirmModal(conrimationString)
			.then(function(confirmation){
				var data = {};
				data.vote = vote;
				data.poll = poll.id;
	 			$http.post('api/vote/', data).success(function(polls, status){
	 				genericServices.alertModal('Respuesta recibida.');
	 				$uibModalInstance.close(polls)
	 			})
			});	

 	}


	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};



});



condominioAlDiaModalControllers.controller('agregarEditarBancoController', function( $scope, $uibModalInstance, $http, cuenta, bancos, tipo, fecha_cuenta, $rootScope, bancos_pais ) {
	
	$scope.tipo = tipo;
	$scope.cuentaData = cuenta;
	$scope.cuentaData.titular = $rootScope.userData.first_name;
	$scope.bancos = bancos;
	$scope.fecha_cuenta = new Date(fecha_cuenta).toUTC();
	$scope.bancos_pais = bancos_pais;

	$scope.get_title = function(){
		if($scope.tipo=='agregar'){
			return 'Registro de cuenta';
		}else if($scope.tipo=='modificar'){
			return 'Modificacion de cuenta';
		}
	}

	$scope.crearCuenta = function(){
		var APImethod;
			if($scope.tipo =='agregar'){
				APImethod = $http.post
				var url = 'api/bancos/';
			}else{
				APImethod = $http.patch;
				var url = 'api/bancos/' +$scope.cuentaData.id+'/';
			}
		
		APImethod(url, $scope.cuentaData).success(function(banco, status){
			if(status == 200){
				$uibModalInstance.close(banco); 
			}else if(status == 203){
				console.log(JSON.stringify(banco))
			}else if(status== 400){
				return false
			}
		})
	}

	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};



});

condominioAlDiaModalControllers.controller('confirmModalController', function( $scope, $uibModalInstance, question ) {
	

	$scope.question = question;
	
	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};

	$scope.confirmationResponse = function(response){
		$uibModalInstance.close(response); 
	}


});

condominioAlDiaModalControllers.controller('carteleraModalController', function( $scope, $uibModalInstance, $http ) {

	$scope.carteleraData = {};
	

	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};

	$scope.submitCartelera = function(){
		var url = 'api/cartelera/';
		$http.post(url, $scope.carteleraData).success(function(response, status){
			if(status ==200){
				$uibModalInstance.close(response); 
			}else{
				alert('Ha ocurrido un error, contacte al administrador por favor');
			}
			
		})
	}
	// $scope.confirmationResponse = function(response){
	// 	$uibModalInstance.close(response); 
	// }


});



condominioAlDiaModalControllers.controller('agregarPagAmarillasModalController', function( $scope, $uibModalInstance, pagAmarillas, tipo, registro, $http ) {
	
	$scope.pagAmarillas = pagAmarillas;
	console.log(pagAmarillas)
	$scope.tipo = tipo;
	$scope.paginasAmarillasFormData = registro;
	
	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};

	$scope.confirmationResponse = function(response){
		$uibModalInstance.close(response); 
	}

	$scope.registrarPaginaAmarilla = function(){
		var APImethod;
			if($scope.tipo =='agregar'){
				APImethod = $http.post
				var url = 'api/paginas_amarillas/';
				var response_message = 'Registro Agregado.'; 
			}else{
				APImethod = $http.patch;
				var url = 'api/paginas_amarillas/' +$scope.paginasAmarillasFormData.id+'/';
				var response_message ='Registro modificado.'; 
			}
		
		APImethod(url, $scope.paginasAmarillasFormData).success(function(response, status){
			if(status == 200){
				alert(response_message);
				$uibModalInstance.close(response); 
			}else if(status == 203){
				console.log(JSON.stringify(response))
			}else if(status== 400){
				return false
			}
		})

		// $http.post('api/paginas_amarillas/', $scope.paginasAmarillasFormData).success(function(pagAmarillas){
		// 	$uibModalInstance.close(pagAmarillas);
		// })
		
	}
});



// condominioAlDiaModalControllers.controller('paginasAmarillasModalController', function( $scope, $uibModalInstance, $http ) {
	
// 	$scope.cancel = function () {
// 		$uibModalInstance.dismiss('cancel');
// 	};

// 	$scope.registrarPaginaAmarilla = function(){
// 		$http.post('api/paginas_amarillas/', $scope.paginasAmarillasFormData).success(function(pagAmarillas){
// 			$uibModalInstance.close(pagAmarillas);
// 		})
		
// 	}


// });




condominioAlDiaModalControllers.controller('agregarJuntaModalController', function( $scope, $uibModalInstance, inmuebles, $http ) {
	
	$scope.inmuebles= inmuebles;
	$scope.juntaCondominioFormData = {};
	//$scope.question = question;
	
	$scope.cancel = function () {
		$uibModalInstance.dismiss('cancel');
	};

	$scope.asignarMiembroJC = function(){
		var url = 'api/junta_condominio/' + $scope.juntaCondominioFormData.inmueble +'/';
		// var data = {};
		// data.cargo = $scope.juntaCondominioFormData.cargo;
		$scope.juntaCondominioFormData.junta_de_condominio = true;
		$http.patch( url, $scope.juntaCondominioFormData ).success(function(juntaCondominio , status){
			if(status==200){
				$uibModalInstance.close(juntaCondominio.data); 
			}
		})
	}
	// $scope.confirmationResponse = function(response){
	// 	$uibModalInstance.close(response); 
	// }


});

