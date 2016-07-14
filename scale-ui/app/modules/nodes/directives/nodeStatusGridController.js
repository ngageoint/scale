(function () {
    'use strict';

    angular.module('scaleApp').controller('nodeStatusGridController', function ($scope) {
        var vm = this,
            cellSize = $scope.cellSize || '10px';

        vm.nodes = [];
        vm.hours = $scope.hours || 3;
        vm.cellStyle = {
            width: cellSize,
            height: cellSize
        };

        vm.getNodeClass = function (node) {
            if (!node.is_online) {
                return 'offline';
            } else {
                if (node.node.is_paused) {
                    return 'is-paused';
                } else if (node.node.is_paused_errors) {
                    return 'is-paused-errors';
                }
            }
            return 'online';
        };

        $scope.$watch('data', function (newValue) {
            vm.nodes = newValue;
        });
    });
})();