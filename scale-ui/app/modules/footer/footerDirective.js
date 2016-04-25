(function () {
    'use strict';

    angular.module('scaleApp').directive('scaleFooter', function () {
        return {
            restrict: 'E',
            templateUrl: 'modules/footer/footerTemplate.html',
            controller: 'footerController'
        }
    });
})();
