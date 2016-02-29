(function () {
    'use strict';

    angular.module('scaleApp').controller('aisHeaderController', function($scope, $element, subnavService) {
        $scope.date = new Date();
        $scope.currentPath = subnavService.getCurrentPath();
    })
    .directive('aisHeader', function () {
        /**
         * Usage: <ais-header name={name}></ais-header>
         */
        return {
            controller: 'aisHeaderController',
            restrict: 'E',
            templateUrl: 'modules/header/headerTemplate.html',
            scope: {
                name: '=',
                hideTitle: '=',
                loading: '=', // optional - will overlay a loading spinner on the page based on the passed-in value
                showSubnav: '=',
                subnavLinks: '='
            }
        };

    });
})();
