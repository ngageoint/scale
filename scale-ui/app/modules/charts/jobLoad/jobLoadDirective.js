(function () {
    'use strict';

    angular.module('scaleApp').directive('aisJobLoad', function () {
        return {
            controller: 'aisJobLoadController',
            controllerAs: 'vm',
            templateUrl: 'modules/charts/jobLoad/jobLoadTemplate.html',
            restrict: 'E',
            scope: {
                showFilter: '=', // show time range filter UI
                cullLegend: '=', // only show job types in legend whose value is > 0
                hideTitle: '=',
                autoHeight: '='
            }
        };
    });
})();
