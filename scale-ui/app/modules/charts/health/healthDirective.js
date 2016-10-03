(function () {
    'use strict';

    angular.module('scaleApp').directive('aisHealth', function () {
        return {
            controller: 'aisHealthController',
            controllerAs: 'vm',
            templateUrl: 'modules/charts/health/healthTemplate.html',
            restrict: 'E',
            scope: {
                name: '=',
                data: '=',
                scale: '=',
                errorLabel: '=',
                type: '='
            }
        };
    });
})();
