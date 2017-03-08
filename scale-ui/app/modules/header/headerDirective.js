(function () {
    'use strict';

    angular.module('scaleApp').controller('aisHeaderController', function ($scope, subnavService) {
        var vm = this;
        vm.currentPath = subnavService.getCurrentPath();
        vm.loadingClass = $scope.showSubnav ? 'loading-content-subnav' : 'loading-content';
    })
    .directive('aisHeader', function () {
        /**
         * Usage: <ais-header name={name}></ais-header>
         */
        return {
            controller: 'aisHeaderController',
            controllerAs: 'vm',
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
