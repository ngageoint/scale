'use strict';

angular.module('scaleApp').directive('aisRadialPercentage', function () {
    return {
        controller: 'aisRadialPercentageController',
        restrict: 'E',
        scope: {
            percentage: '@'
        }
    };
});
