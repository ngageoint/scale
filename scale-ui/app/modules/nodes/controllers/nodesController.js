(function () {
    'use strict';

    angular.module('scaleApp').controller('nodesController', function($scope, $location, $timeout, navService, nodeService) {
        $scope.nodeCounts = [];
        $scope.loading = true;
        $scope.hourValue = 3;
        $scope.nodesError = null;
        $scope.nodesErrorStatus = null;
        $scope.nodeStatusError = null;
        $scope.nodeStatusErrorStatus = null;
        $scope.nodeData = {
            data: null,
            status: null
        };

        var debounceTimer = {};

        var debounceBroadcast = function (message, args) {
            if (debounceTimer[message]) {
                $timeout.cancel(debounceTimer[message]);
            }
            debounceTimer[message] = $timeout(function () {
                $scope.$broadcast(message, args);
            }, 500);
        };

        $scope.redrawGrid = function () {
            debounceBroadcast('redrawGrid', $scope.nodeData);
        };

        var getNodes = function () {
            nodeService.getNodes().then(null, null, function (data) {
                if (data.$resolved) {
                    $scope.nodesError = null;
                    $scope.nodeData.data = data.results;
                    $scope.redrawGrid();
                } else {
                    if (data.statusText && data.statusText !== '') {
                        $scope.nodesErrorStatus = data.statusText;
                    }
                    $scope.nodesError = 'Unable to retrieve nodes.';
                }
            });
        };

        var getNodeStatus = function () {
            nodeService.getNodeStatus(null, null, 'PT' + $scope.hourValue + 'H', null).then(null, null, function (data) {
                if (data.$resolved) {
                    $scope.nodeStatusError = null;
                    $scope.nodeData.status = data.results;
                    $scope.redrawGrid();
                } else {
                    if (data.statusText && data.statusText !== '') {
                        $scope.nodeStatusErrorStatus = data.statusText;
                    }
                    $scope.nodeStatusError = 'Unable to retrieve node status.';
                }
            });
        };

        var initialize = function() {
            getNodes();
            getNodeStatus();
            _.defer(function () {
                $scope.loading = false;
            });
            navService.updateLocation('nodes');
        };

        initialize();
    });
})();