(function () {
    'use strict';

    angular.module('scaleApp').directive('aisDonut', function () {
        return {
            controller: 'aisDonutController',
            restrict: 'E',
            scope: {
                data: '=',
                type: '=',
                size: '=',
                showLabel: '=',
                width: '=',
                name: '='
            }
        };
    });
})();
