(function () {
    'use strict';

    angular.module('scaleApp').directive('scaleNavigation', function () {
        return {
            restrict: 'E',
            templateUrl: 'modules/navigation/partials/navTemplate.html',
            controller: 'navController',
            controllerAs: 'vm'
        };
    });
})();
