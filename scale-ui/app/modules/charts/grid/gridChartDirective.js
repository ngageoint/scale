(function () {
    'use strict';

    angular.module('scaleApp').directive('aisGridChart', function () {
        return {
            controller: 'aisGridChartController',
            templateUrl: 'modules/charts/grid/gridChartTemplate.html',
            restrict: 'E',
            scope: {
                data: '=',
                icons: '=', // indicates whether cell-text is entirely made up of icons
                scale: '=', // multiplier to increase cell size
                reveal: '=', // if true, less data will show when zoomed out
                mode: '@', // valid values are zoom or tooltip
                columns: '=',
                rows: '=',
                showAxes: '='
            }
        };
    });
})();
