var condominioAlDiaAppDirectives = angular.module('condominioAlDiaAppDirectives',[]);

condominioAlDiaAppDirectives.directive('search', function($http, genericServices) {

      var directive = {};
      directive.restrict = 'E';
      directive.scope = {
        url : '@',
        list: '='
      };
      directive.templateUrl = 'static/ng_templates/directive_templates/search_directive.html';
      directive.link = function ( scope, element, attributes, ngModel ) {

          scope.search = function(){
            $http.get(scope.url+'?search='+scope.searchString).success(function(list){
              console.log(list)
              scope.list = list;
              scope.searchString  = '';
              genericServices.alertModal('Se han encontrado ' + list.length + ' resultados.');
            })           
          }

      };
      return directive;
});

condominioAlDiaAppDirectives.directive('searchDates', function($http, genericServices, $uibModal) {

      var directive = {};
      directive.restrict =  'A';
      directive.link = function ( scope, element, attributes, ngModel ) {
        element.on('click',function () {
          var modalInstance = $uibModal.open({
              ariaLabelledBy: 'modal-title',
              ariaDescribedBy: 'modal-body',
              animation: scope.animationsEnabled,
              templateUrl: 'static/ng_templates/modals/buscar_entre_fechas.html',
              controller: 'buscarEntreFechasController',
              size: 'md'

          });
          modalInstance.result.then(function (listaEstudios) {
              scope.resultsFor = $scope.searchParam;
              scope.searchParam = '';
              scope.listaEstudios = listaEstudios;
              scope.resultados = listaEstudios.length;

          })

        })
      };
      return directive;
});



condominioAlDiaAppDirectives.directive('loading', ['$http', function ($http) {
    return {
        restrict: 'A',
        scope:true,
        link: function (scope, elm, attrs) {
            scope.isLoading = function () {
                return $http.pendingRequests.length > 0;
            };
            scope.$watch(scope.isLoading, function (v) {
                if (v) {
                    elm.css('alerts_class', 'visible');
                    elm.css('visibility', 'visible');
                } else {
                    elm.css('alerts_class', 'hidden');
                    elm.css('visibility', 'hidden');

                }
            });
        }
    };
}]);



condominioAlDiaAppDirectives.directive('panelTable', function($http) {

      var directive = {};
      directive.restrict = 'E';
      directive.transclude= {
          extra: '?extraElement'
      };
      directive.scope = {
          panelTitle : '@',
          searchDateField: "@",
          searchUrl : '@?',

          placeholder :'@?',
          advancedSearch : '&?',
          resultsList: '=?',
          typeAheadModel: '=?'
      };
      directive.link = function(scope, element, attributes, ngModel, transclude ) { 
        scope.panelInput = {};
        scope.search = function(){
          var url = scope.searchUrl + scope.panelInput.search;
          $http.get(url).success(function(response ){
             scope.resultsList = response;
             scope.panelInput.search = '';
             alert("Se han encontronado " + String(response.length )+ " resultados")
          })       
        }
     

      }
      directive.templateUrl = '/static/ng_templates/directive_templates/panel-table.html';
      return directive;
});


condominioAlDiaAppDirectives.directive('ccValidate', function() {

    var directive = {};
    directive.require =  "ngModel";
    directive.restrict = 'A';
    // directive.scope = {
    //   otherModelValue: "=compareTo"
    // };

    directive.link = function(scope, element, attributes, ngModel) {
      ngModel.$validators.ccValidate = function(value) {
        if (value){
          // takes the form field value and returns true on valid number
            // accept only digits, dashes or spaces
            if (/[^0-9-\s]+/.test(value)) return false;

            // The Luhn Algorithm. It's so pretty.
            var nCheck = 0, nDigit = 0, bEven = false;
            value = value.replace(/\D/g, "");

            for (var n = value.length - 1; n >= 0; n--) {
              var cDigit = value.charAt(n),
                  nDigit = parseInt(cDigit, 10);

              if (bEven) {
                if ((nDigit *= 2) > 9) nDigit -= 9;
              }

              nCheck += nDigit;
              bEven = !bEven;
            }

            return (nCheck % 10) == 0;


        }
        return false;
      };
    }
    return directive;

}); 


condominioAlDiaAppDirectives.directive('noDupCobranza', function() {

    var directive = {};
    directive.require =  "ngModel";
    directive.restrict = 'A';
    // directive.scope = {
    //   otherModelValue: "=compareTo"
    // };

    directive.link = function(scope, element, attributes, ngModel) {
      ngModel.$validators.noDupCobranza = function(modelValue) {
        if (modelValue){
          //
          return true;
          // var total = parseFloat(modelValue) + parseFloat(scope.maxAlicuota)
          // if ( total >100){
          //   return false
          // }
        }
        return true;
      };
    }
    return directive;

});  


condominioAlDiaAppDirectives.directive('passwordMatch', function() {

    var directive = {};
    directive.require =  "ngModel";
    //directive.restrict = '';
    directive.scope = {
      otherModelValue: "=compareTo"
    };

    directive.link = function(scope, element, attributes, ngModel) {
          try {
            ngModel.$validators.passwordMatch = function(modelValue) {
                return modelValue === scope.otherModelValue;
            };
          } catch (err) {
            console.log('Oops,error');
          }

 
            scope.$watch("otherModelValue", function() {
                ngModel.$validate();
            });
    }
    return directive;

});  

condominioAlDiaAppDirectives.directive('differentThan', function() {

    var directive = {};
    directive.require =  "ngModel";
    //directive.restrict = '';
    directive.scope = {
      otherModelValue: "=notEqTo"
    };

    directive.link = function(scope, element, attributes, ngModel) {

          try {
            ngModel.$validators.different = function(modelValue) {
                return modelValue != scope.otherModelValue;
            };
          } catch (err) {
            console.log('Oops,error');
          }

          scope.$watch("otherModelValue", function() {
              ngModel.$validate();
          });
    }
    return directive;

});  

condominioAlDiaAppDirectives.directive('maxAlicuota', function() {

    var directive = {};
    directive.require =  "ngModel";
    directive.restrict = 'A';
    directive.scope = {
      maxAlicuota : '='
    };
    directive.link = function(scope, element, attributes, ngModel) {
      ngModel.$validators.maxAlicuota = function(modelValue) {
        var total = parseFloat(modelValue) + parseFloat(scope.maxAlicuota)
        if ( total >100){
          return false
        }
        return true;
      };
    }
    return directive;

});  


condominioAlDiaAppDirectives.directive('googleMapsAutocomplete', function() {
    var directive = {};
    directive.require =  "ngModel";
    directive.restrict = 'A';
    directive.scope = {
      'googleMapsAutocomplete' :'='
    };

    directive.link = function (scope, element, attrs, ngModel ){

      var placeSearch, autocomplete;
            var componentForm = {
              street_number: 'short_name',
              route: 'long_name',
              locality: 'long_name',
              administrative_area_level_1: 'short_name',
              country: 'long_name',
              postal_code: 'short_name'
            };

      scope.autocomplete = new google.maps.places.Autocomplete(
        /** @type {!HTMLInputElement} */(element[0]),
        {types: ['geocode']});

            //REMOVE ENTER KEY 
      google.maps.event.addDomListener(element[0], 'keydown', function(e) { 
        if (e.keyCode == 13) { 
            e.preventDefault(); 
        }
        scope.$apply()
      });



      google.maps.event.addListener(scope.autocomplete, 'place_changed', function() {
          scope.$apply(function() {
              scope.place = scope.autocomplete.getPlace();
              if(scope.place.geometry){
                var latitude = scope.place.geometry.location.lat();
                var longitude = scope.place.geometry.location.lng();
              }else{
                var latitude = '';
                var longitude = '';
              }

              scope.googleMapsAutocomplete = {
                  latitude:latitude,
                  longitude :longitude
              }
              ngModel.$setViewValue(element.val());
          });
      });


    };
    return directive;
});  

condominioAlDiaAppDirectives.directive("blackListArr", function() {
    return {
        restrict: "A",
        scope : {
          blackListArr:'=',
          blackListArr2:'='
        },
        require: "ngModel",
         
        link: function(scope, element, attributes, ngModel) {

            ngModel.$validators.blackListArr = function(modelValue) {
              if (modelValue){
                var notInCats =true;
                for(var i in scope.blackListArr2){
                  var item = scope.blackListArr2[i];
                  if(String(modelValue).toLowerCase().trim()==String(item.name).toLowerCase().trim()){
                    notInCats=false;
                  }
                }
                if( scope.blackListArr.indexOf(String(modelValue).toLowerCase().trim())==-1 && notInCats){
                  return true;
                }else{
                  return false;
                }
              }
              return true;
            }
        }
    };
});


condominioAlDiaAppDirectives.directive("blackList", function() {
    return {
        restrict: "A",
        scope : {
          blackList:'=',
          exception: '=?'
        },
        require: "ngModel",
         
        link: function(scope, element, attributes, ngModel) {

            ngModel.$validators.blackList = function(modelValue) {
              if (modelValue){
                for(var i in scope.blackList){
                  if (scope.blackList[i]['nombre_inmueble'].toUpperCase().replace(/^\s+|\s+$/g, '') == modelValue.toUpperCase().replace(/^\s+|\s+$/g, '')){
                    if(scope.exception){
                      if(scope.blackList[i].id==scope.exception){
                        return true;
                      }else{
                        return false;
                      }
                    }else{
                      return false;
                    }
                    
                  }
                }   
              }
              return true;
            }
        }
    };
});


condominioAlDiaAppDirectives.directive('emailAvailable', function($timeout, $q, $http) {
  return {
    restrict: 'AE',
    require: 'ngModel',
    link: function(scope, elm, attr, model) { 
      model.$asyncValidators.uniqueEmail = function(modelValue, viewValue) {
        var value = modelValue || viewValue;

        // Lookup user by username
        return $http.get('/api/verificar_correo/' + value).
           then(function resolved() {
             //username exists, this means validation fails
             return true;
           }, function rejected() {
             //username does not exist, therefore this validation passes
             return $q.reject('exists');
           });
      };

    }
  } 
});

condominioAlDiaAppDirectives.directive('rifAvailable', function($timeout, $q, $http) {
  return {
    restrict: 'AE',
    require: 'ngModel',
    link: function(scope, elm, attr, model) { 
      model.$asyncValidators.uniqueRif = function(modelValue, viewValue) {
        var value = modelValue || viewValue;

        // Lookup user by username
        return $http.get('/api/verificar_rif/' + value).
           then(function resolved(response) {
             //username exists, this means validation fails
             return true;
           }, function rejected(errors) {
            console.log(errors)
             //username does not exist, therefore this validation passes
             return $q.reject('exists');
           });
      };

    }
  } 
});

condominioAlDiaAppDirectives.directive("yearMonthDateInput", function() {
     var directive = {};
     directive.restrict = 'E';
     directive.transclude = true;
     directive.scope = {
        directivemodel : '=ngModel',
        minDate:'@', // YYYY/MM/DD(string)
        maxDate:'@',
        required:'@'
     };
      directive.require = '?ngModel';
      directive.templateUrl = 'static/ng_templates/directive_templates/yearmonthdateinput.html';
      directive.link = function(scope, element, attributes, ngModel) {

        if (!attributes.mindate){
            scope.mindate = new Date();
        }
        if (!attributes.maxdate){
            var now = new Date();
            scope.maxdate = now.addDays(5000);
        }
        scope.monthList = [
            { 'name': 'Enero', 'value' : 1 }, 
            { 'name': 'Febrero', 'value' : 2 },
            { 'name': 'Marzo', 'value' : 3 },
            { 'name': 'Abril', 'value' : 4 },
            { 'name': 'Mayo', 'value' : 5 },
            { 'name': 'Junio', 'value' : 6 },
            { 'name': 'Julio', 'value' : 7 },
            { 'name': 'Agosto', 'value' : 8 },
            { 'name': 'Septiembre', 'value' : 9 },
            { 'name': 'Octubre', 'value' : 10 },
            { 'name': 'Noviembre', 'value' : 11},
            { 'name': 'Diciembre', 'value' : 12 }
        ];

        //get year range
        scope.yearList = yearRange(scope.mindate, scope.maxdate);
        function yearRange(mindate, maxdate){
          var yearList = [];
          for (var i = mindate.getUTCFullYear(); i<=maxdate.getUTCFullYear(); i++){
            yearList.push(i);
          }
          return yearList;
        }

        scope.selectorsChange = function(source){
          if ( source == 'year' ){
            scope.month ='';
            scope.directivemodel = '';
          }
          if (scope.year && scope.month){
            scope.directivemodel = new Date(String(scope.year), scope.month-1, 1).toISODate();
          }else{
            scope.directivemodel = '';
          } 

        }

        scope.setnullification = function(year, month){
          if (scope.year){
            var selection_date = new Date(year, month-1, 1);
            if(selection_date !='Invalid Date' && selection_date && (selection_date > scope.maxdate || selection_date <= scope.mindate)){
              return  true; 
            }else if (selection_date =='Invalid Date'){
              return  false;
            }          
          }else{
            return false;
          }

        }

     };
     return directive;
});

condominioAlDiaAppDirectives.directive('maxDateToday', function() {

    var directive = {};
    directive.require =  "ngModel";
    //directive.restrict = '';
    // directive.scope = {
    //   maxDate: '@'
    // };
    directive.scope = false;
    directive.link = function(scope, element, attributes, ngModel) {
             
        ngModel.$validators.maxDateToday = function(modelValue) {
          return modelValue <= new Date();

        };

    }
    return directive;

}); 

condominioAlDiaAppDirectives.directive('minDateAllowed', function() {
    var directive = {};
    directive.require =  "ngModel";
    directive.scope = false;
    directive.link = function(scope, element, attributes, ngModel) {
        ngModel.$validators.minDateAllowed = function(modelValue) {
          return modelValue >= scope.minDate;
        };
    }
    return directive;
}); 

condominioAlDiaAppDirectives.directive('maxDateAllowed', function() {
    var directive = {};
    directive.require =  "ngModel";
    directive.scope = false;
    directive.link = function(scope, element, attributes, ngModel) {
        ngModel.$validators.maxDateAllowed = function(modelValue) {
          return modelValue <= scope.maxDate;
        };
    }
    return directive;

}); 



condominioAlDiaAppDirectives.directive('stringToNumber', function() {
  return {
    require: 'ngModel',
    link: function(scope, element, attrs, ngModel) {
      ngModel.$parsers.push(function(value) {
        return '' + value;
      });
      ngModel.$formatters.push(function(value) {
        return parseFloat(value);
      });
    }
  };
});


condominioAlDiaAppDirectives.directive('mustEqual', function() {

    var directive = {};
    directive.require =  "ngModel";
    directive.scope = {
      mustEqual: "="
    };

    directive.link = function(scope, element, attributes, ngModel) {
      ngModel.$validators.mustEqual = function(modelValue) {
        return parseFloat(scope.mustEqual) == parseFloat(modelValue);
        // var total = parseFloat(modelValue) + parseFloat(scope.maxAlicuota)
        // if ( total >100){
        //   return false
        // }
        // return true;
      };
    }
    return directive;

}); 



condominioAlDiaAppDirectives.directive('submitTimeout', function($timeout) {
  return {
    link: function(scope, element, attrs, ngModel) {

      element.bind('click ', function(){
        attrs.$set('disabled', 'disabled');
      $timeout(function() {
         attrs.$set('disabled', false);
      }, 5000);
      })


    }
  };
});


condominioAlDiaAppDirectives.directive('helpElementa', function($http, $uibModal, $location) {

      var directive = {};
      // directive.scope = {
      //   context : '=?'
      // };
      template: '<button>a</button>';
      directive.restrict =  'E';
      directive.link = function ( scope, element, attributes, ngModel ) {

        // scope.showModal=function(){
        //   var modalInstance = $uibModal.open({
        //       ariaLabelledBy: 'modal-title',
        //       ariaDescribedBy: 'modal-body',
        //       animation: true,
        //       template: 'static/ng_templates/modals/help_modal.html',
        //       controller: 'helpModalController',
        //       size: 'md',
        //       resolve: {

        //         help_items: function() {
        //             var url = 'api/help_items/';
        //             return $http({ 
        //                 method: 'GET', 
        //                 url: url
        //             }).then(function(response){
        //                 return response.data;
        //             })
        //         }
        //         // payment_type: function() {
        //         //   return 'cobranza';
        //         // },
        //         // cobranza_id: function() {
        //         //   return cobranza.id;
        //         // }                         
        //       }
        //   });
        // }
      };
      return directive;
});

condominioAlDiaAppDirectives.directive("helpElement", function( $uibModal, helpService, $rootScope) {
    var directive = {};
    directive.template= '<button title="Manual rapido (o presione F1)" type="button" ng-click="helpModal()" class="btn btn-info"><i class="fa fa-question"></i></button>';
    directive.link = function ( scope, element, attributes, ngModel ) {
      
      $rootScope.helpModalOpened = false;
      
      scope.helpModal=function(){
        helpService.check();
      }

    };
    return directive;
});

condominioAlDiaAppDirectives.directive('blogElement', function($http, genericServices, $uibModal) {

      var directive = {};
      directive.scope = {
        context : '='
      };
      directive.templateUrl = 'static/ng_templates/directive_templates/blog_element.html';
      directive.restrict =  'E';
      directive.link = function ( scope, element, attributes, ngModel ) {

        // scope.blog = scope.context.results;
        // scope.next_link = scope.context.next_link;
        // scope.current_page = scope.context.page;
        // scope.page_count = scope.context.page_count;

        // scope.getMore=function(){
        //   if( scope.context.next_link){
        //     $http.get( scope.context.next_link).success(function(context){
        //       console.log(context)
        //       scope.context = context;
        //       // for (var i in context.results){
        //       //   scope.blog.push(context.results[i])
        //       // }
        //       // scope.next_link = context.next_link;
        //       // scope.current_page =context.page;
        //       // scope.page_count = context.page_count;
        //     })
        //   }
          
        // }
      };
      return directive;
});


// condominioAlDiaAppDirectives.directive('resizer', ['$window', function ($window) {
//     return {
//         restrict: 'A',
//         link: function (scope, elem, attrs) {            
//             angular.element($window).on('resize', function () {
//                 $window.innerWidth > 500 ? 
//                     elem.addClass('large') : elem.removeClass('large')
//             });
//         }
//     }
// }]);

condominioAlDiaAppDirectives.directive("scroll", function ($window) {
    return function(scope, element, attrs) {
      
        angular.element($window).bind("scroll", function() {
            if (this.pageYOffset >= 100) {
                 scope.boolChangeClass = true;
                 console.log('Scrolled below header.');
             } else {
                 scope.boolChangeClass = false;
                 console.log('Header is in view.');
             }
            scope.$apply();
        });
    };
});

condominioAlDiaAppDirectives.directive("scrollBottom", function ($window) {
    return function(scope, element, attrs) {
      
        angular.element($window).bind("scroll", function() {
        var old = element.scrollTop;
        element.scrollTop += 50;
        if (element.scrollTop > old) {
            element.css('visibility', 'visible');
        } else {
            element.css('visibility', 'hidden');
        }
            scope.$apply();
        });
    };
});


// condominioAlDiaAppDirectives.directive('emptyToNull', function () {
//     return {
//         restrict: 'A',
//         require: 'ngModel',
//         link: function (scope, elem, attrs, ctrl) {
//             ctrl.$parsers.push(function(viewValue) {
//                 if(viewValue === "") {
//                     return null;
//                 }
//                 return viewValue;
//             });
//         }
//     };
// });

// condominioAlDiaAppDirectives.directive('nullToEmpty', function () {
//     return {
//         restrict: 'A',
//         require: 'ngModel',
//         link: function (scope, elem, attrs, ctrl) {
//             ctrl.$parsers.push(function(viewValue) {
//               console.log(viewValue)
//                 if(viewValue === null) {
//                     return '';
//                 }
//                 return viewValue;
//             });
//         }
//     };
// });

condominioAlDiaAppDirectives.directive('nullToEmpty', function() {

      var directive = {};
      directive.restrict = 'A';
      directive.require ='ngModel';
      directive.link = function ( scope, element, attributes, ngModel ) {

            // ngModel.$parsers.push(function(value) {
            //     if(value === 'null') {
            //         return '';
            //     }
            //     return value;
            // });
            ngModel.$formatters.push(function(value) {
                if(value === 'null'||value===null) {
                    return '';
                }
                return value;
            });
      };
      return directive;
});