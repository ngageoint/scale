(function () {
   'use struct';

   angular.module('scaleApp').constant('scaleConfigLocal', {
      urls: {
         prefixDev: './api/', //dev
         prefixProd: './api/', //scale3
         documentation: './docs/'
      }
   });
}) ();
