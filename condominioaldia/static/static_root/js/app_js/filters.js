
condominioAlDiaApp = angular.module('condominioAlDiaAppFilters',[]);

condominioAlDiaApp.filter('accounting', function() {
    return function(value, currency, show_currency) {
        if (show_currency!=false){
          var currency = currency +' ';
        }else{
          var currency = '';
        }

        if (value){
          if (value[0] == String('-')){
            return ' '+String(value).replace('-', '( '+ String(currency)) + (')')
          }
          return  String(currency) + value
        }
    }; 

});

condominioAlDiaApp.filter('capitalize', function() {
    return function(input) {
      return (!!input) ? input.charAt(0).toUpperCase() + input.substr(1).toLowerCase() : '';
    }
});

condominioAlDiaApp.filter('toString', function() {
    return function(input) {
            if (!input)
                return; 

            return String(input)
          }
});


condominioAlDiaApp.filter('customFilterRelacion1', function() {
    return function(arr, search_param, custom_categories) {
      if(!search_param){
        return arr;
      }else{

        function get_for_param(arr, search_param){
          var filtered= [];
          for (var i in arr){
            item = arr[i].inmueble;
            if(item[search_param] ==true){
              filtered.push(arr[i]);
            }
          }
          return filtered;
        }

        var standard_search_param = ['junta_de_condominio', 'no_miembro', 'no_arrendado', 'arrendado']
        if (standard_search_param.indexOf(search_param)!=-1){
          return get_for_param(arr, search_param);
        }else if(custom_categories.length>0){
          filtered = [];
          for(var i in arr){
            var inmueble = arr[i].inmueble;
            if(inmueble.categories.length >0){
              for ( var j in inmueble.categories){
                var category = inmueble.categories[j];
                if(category.id ==search_param){
                  filtered.push(arr[i]);
                  break;
                }
              }
            }
          }
          return filtered;

        }else if(!custom_categories.length>0){//RETURN ALL IF NO CUSTOM FILTER APPLLIED
          return arr;
        }//RETURN NONE IF INVALID LOGIC APPLIED TO FILTERING
        return [];
      }
    }
});



condominioAlDiaApp.filter('customCheckFilter',function(){

    return function(input,masterCheck,stdsearch){

        angular.forEach(input,function(value,key){
         if(stdsearch){
                if(masterCheck){
                    value.ischecked = true;
                }else{
                value.ischecked = false;
                }
         }

        })
        return input;
    }


})

condominioAlDiaApp.filter('customFilterInmueble', function() {
    return function(arr, search_param, custom_categories) {
      if(!search_param){
        return arr;
      }else{

        function get_for_param(arr, search_param){
          var filtered= [];
          for (var i in arr){
            item = arr[i];
            if(item[search_param] ==true){
              filtered.push(item);
            }
          }
          return filtered;
        }

        var standard_search_param = ['junta_de_condominio', 'no_miembro', 'no_arrendado', 'arrendado']
        if (standard_search_param.indexOf(search_param)!=-1){
          return get_for_param(arr, search_param);
        }else if(custom_categories.length>0){

          filtered = [];
          for(var i in arr){
            var inmueble = arr[i];
            if(inmueble.categories.length >0){
              for ( var j in inmueble.categories){
                var category = inmueble.categories[j];
                if(category.id ==search_param){
                  filtered.push(inmueble);
                  break;
                }
              }
            }
          }
          return filtered;

        }else if(!custom_categories.length>0){//RETURN ALL IF NO CUSTOM FILTER APPLLIED
          return arr;
        }//RETURN NONE IF INVALID LOGIC APPLIED TO FILTERING
        return [];
      }
    }
});

condominioAlDiaApp.filter('capfirstlettereachword', function() {
    return function(input) {
      if (input){
            var splitStr = input.toLowerCase().split(' ');
            for (var i = 0; i < splitStr.length; i++) {
                splitStr[i] = splitStr[i].charAt(0).toUpperCase() + splitStr[i].substring(1);     
            }
            return splitStr.join(' ');      
      }

    };
})

condominioAlDiaApp.filter('toJsonObj', function() {
    return function(input) {
        return JSON.parse(input);
    };
})

condominioAlDiaApp.filter('unique', function() {
      return function uniq_fast(a) {
      var seen = {};
      var out = [];
      var len = a.length;
      var j = 0;
      for(var i = 0; i < len; i++) {
           var item = a[i];
           if(seen[item] !== 1) {
                 seen[item] = 1;
                 out[j++] = item;
           }
      }
      return out;
  }
});


condominioAlDiaApp.filter('sumKeys', function() {
    return function(array, key) {
      var total = 0;
      for (var i in array){
        total = parseFloat(array[i][key]) +total;
      }
      return total;
    };
})

condominioAlDiaApp.filter('resumenCondoCustomListFilter', function() {
    return function(array, search_criteria) {

      var new_arr = [];
      if (search_criteria) {
        for (var i in array){

          var add_to_arr = false;
          var item = array[i];
          console.log(search_criteria)
          console.log(item.categorias)
          if (item.categorias.indexOf(search_criteria.toLowerCase())!=-1 ){
            var add_to_arr = true;
          }
          // else if (item.cobrar_cuando==search_criteria ){
          //   var add_to_arr = true;
          // }else if (item.recurrencia==search_criteria ){
          //   var add_to_arr = true;
          // }
          if (add_to_arr==true){
            new_arr.push(item);
          }
        }
        return new_arr;
      } else {
        return array;
      }
    };
})

condominioAlDiaApp.filter('cobranzaCustomListFilter', function() {
    return function(array, search_criteria) {

      var new_arr = [];
      if (search_criteria) {
        for (var i in array){

          var add_to_arr = false;
          var item = array[i];
          if (item.recipiente==search_criteria ){
            var add_to_arr = true;
          }else if (item.cobrar_cuando==search_criteria ){
            var add_to_arr = true;
          }else if (item.recurrencia==search_criteria ){
            var add_to_arr = true;
          }
          if (add_to_arr==true){
            new_arr.push(item);
          }
        }
        return new_arr;
      } else {
        return array;
      }
    };
})


condominioAlDiaApp.filter('cobranzaCustomFilter', function() {
    return function(array, search_criteria) {

      var new_arr = [];
      if (search_criteria) {
        for (var i in array){

          var add_to_arr = false;
          var item = array[i];
          if (item.recipiente==search_criteria|| String(item.recipiente).toLowerCase().indexOf(search_criteria.toLowerCase())!=-1 ){
            var add_to_arr = true;
          }else if (item.asunto==search_criteria|| String(item.asunto).toLowerCase().indexOf(search_criteria.toLowerCase())!=-1 ){
            var add_to_arr = true;
          }else if (item.monto==search_criteria|| String(item.monto).toLowerCase().indexOf(search_criteria.toLowerCase())!=-1 ){
            var add_to_arr = true;
          }
          if (add_to_arr==true){
            new_arr.push(item);
          }
        }
        return new_arr;
      } else {
        return array;
      }
    };
})

condominioAlDiaApp.filter('recipient_trans', function() {
    return function(value) {
      switch(value) {

          case 'TP':
          return 'Todos los propietarios';
              break;

          case 'Propietarios sin deuda':
          return '';
              break;

          case 'PCD':
          return 'Propietarios con deuda';
              break;

          case 'PP':
          return 'propietario particular';
              break;

          case 'JC':
          return 'Junca de condominio';
              break;

          case 'NBM':
          return 'Todos menos la junta';
              break;    

          default:
            break;
      } 
      //return 'total';
    };
})


condominioAlDiaApp.filter('string_to_date', function() {//takes a
  return function(input) {

          var dateVal = new Date( input );
          return dateVal;

    }
  })

condominioAlDiaApp.filter('abs', function() {//takes a
  return function(input) {
          return Math.abs(input);

    }
  })

condominioAlDiaApp.filter('debtor', function() {//takes a
  return function(input) {
        if (input =='todos'){
          return 'todos los propietarios';
        }else{
          return 'propietarios particulares';
        }
    }
  })


condominioAlDiaApp.filter('humanizetimedelta', function() {//takes a
  return function(input) {
    var delta = input;
    if (input!=null){
      if (input<0){
        return 'cerrada'
      }

      var delta =  (delta)/1000;
      // calculate (and subtract) whole days
      var days = Math.floor(delta / 86400);
      delta -= days * 86400;

      // calculate (and subtract) whole hours
      var hours = Math.floor(delta / 3600) % 24;
      delta -= hours * 3600;

      // calculate (and subtract) whole minutes
      var minutes = Math.floor(delta / 60) % 60;
      delta -= minutes * 60;
      // what's left is seconds
      var seconds = delta % 60;  // in theory the modulus is not required
      result = {};
      result.days = days;
      result.hours = hours;
      result.minutes = minutes;
      result.seconds = seconds;
      // if( scope.startdate > scope.endate ){
      //     alert(expired);
      //     return false;
      // }
          if (delta < 0 ){
            return 'Concluida';
          }
          else if (days > 1){
              var difference = String(days) + ' dias ' +  String(hours) + ' horas ';
          }else if(days == 1){
              difference = String(days) + ' dia ' +  String(hours) + ' horas ';
          }else if( days < 1){
              var difference = String(hours) + ' horas ' + String(minutes) + ' minutos ' + String(seconds.toFixed(0)) + ' s';
          }else if(hours == 1){
              var difference = String(hours) + ' hora ' +  String(minutes) + ' minutos ' + String(seconds.toFixed(0)) + ' s';
          }else if( hours < 1){
              var difference = String(minutes) + ' minutos ';
          }else if( minutes == 1){
              var difference = String(minutes) + ' minuto ';
          }

      return difference;
    }
  }
  })

    condominioAlDiaApp.filter("timeago", function () {
        //time: the time
        //local: compared to what time? default: now
        //raw: wheter you want in a format of "5 minutes ago", or "5 minutes"
        return function (time, local, raw) {
            if (!time) return "nunca";

            if (!local) {
                (local = Date.now())
            }

            if (angular.isDate(time)) {
                time = time.getTime();
            } else if (typeof time === "string") {
                time = new Date(time).getTime();
            }

            if (angular.isDate(local)) {
                local = local.getTime();
            }else if (typeof local === "string") {
                local = new Date(local).getTime();
            }

            if (typeof time !== 'number' || typeof local !== 'number') {
                return;
            }

            var
                offset = Math.abs((local - time) / 1000),
                span = [],
                MINUTE = 60,
                HOUR = 3600,
                DAY = 86400,
                WEEK = 604800,
                MONTH = 2629744,
                YEAR = 31556926,
                DECADE = 315569260;

            if (offset <= MINUTE)              span = [ '', raw ? 'ahora' : 'menos de un minuto' ];
            else if (offset < (MINUTE * 60))   span = [ Math.round(Math.abs(offset / MINUTE)), 'min' ];
            else if (offset < (HOUR * 24))     span = [ Math.round(Math.abs(offset / HOUR)), 'hr' ];
            else if (offset < (DAY * 7))       span = [ Math.round(Math.abs(offset / DAY)), 'dia' ];
            else if (offset < (WEEK * 52))     span = [ Math.round(Math.abs(offset / WEEK)), 'semana' ];
            else if (offset < (YEAR * 10))     span = [ Math.round(Math.abs(offset / YEAR)), 'año' ];
            else if (offset < (DECADE * 100))  span = [ Math.round(Math.abs(offset / DECADE)), 'decada' ];
            else                               span = [ '', 'mucho tiempo' ];

            span[1] += (span[0] === 0 || span[0] > 1) ? 's' : '';
            span = span.join(' ');

            if (raw === true) {
                return span;
            }
            return (time <= local) ? 'hace '+ span  : 'en ' + span;
        }
    })