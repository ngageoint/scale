(function () {
   'use struct';

   angular.module('scaleApp').constant('scaleConfigLocal', {
      urls: {
         prefixDev: '/scale/api/', //dev
         prefixProd: '/scale/api/', //scale3
         documentation: '/scale/docs/'
      }
   });
}) ();
