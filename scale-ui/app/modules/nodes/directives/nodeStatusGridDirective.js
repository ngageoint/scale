(function () {
    'use strict';

    angular.module('scaleApp').directive('aisNodeStatusGrid', function () {
        return {
            controller: 'nodeStatusGridController',
            controllerAs: 'vm',
            templateUrl: 'modules/nodes/directives/nodeStatusGridTemplate.html',
            restrict: 'E',
            scope: {
                data: '=',
                hours: '=',
                cellSize: '@'
            }
        };
    });
})();