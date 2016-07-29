(function () {
    'use strict';

    angular.module('scaleApp').controller('nodeStatusGridController', function ($scope, $location) {
        var vm = this,
            cellSize = $scope.cellSize || '10px';

        vm.nodes = [];
        vm.hours = $scope.hours || 3;
        vm.cellStyle = {
            width: cellSize,
            height: cellSize
        };

        vm.getNodeClass = function (node) {
            console.log('getNodeClass');
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

        vm.viewNode = function (id) {
            $location.path('nodes/' + id);
        };

        $scope.$watch('data', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            _.forEach(newValue, function (node) {
                if (!node.is_online) {
                    node.class = 'offline';
                } else {
                    if (node.node.is_paused) {
                        node.class = 'is-paused';
                    } else if (node.node.is_paused_errors) {
                        node.class = 'is-paused-errors';
                    } else {
                        node.class = 'online';
                    }
                }
            });
            vm.nodes = newValue;
        });
    });
})();