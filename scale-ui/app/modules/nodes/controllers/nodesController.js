(function () {
    'use strict';

    angular.module('scaleApp').controller('nodesController', function($scope, $location, $timeout, navService, nodeService) {
        var vm = this;
        
        vm.nodeCounts = [];
        vm.loading = true;
        vm.hourValue = 3;
        vm.nodesError = null;
        vm.nodesErrorStatus = null;
        vm.nodeStatusError = null;
        vm.nodeStatusErrorStatus = null;
        vm.nodeData = {
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

        vm.redrawGrid = function () {
            debounceBroadcast('redrawGrid', vm.nodeData);
        };

        var getNodes = function () {
            nodeService.getNodes().then(null, null, function (data) {
                if (data.$resolved) {
                    vm.nodesError = null;
                    vm.nodeData.data = data.results;
                    vm.redrawGrid();
                } else {
                    if (data.statusText && data.statusText !== '') {
                        vm.nodesErrorStatus = data.statusText;
                    }
                    vm.nodesError = 'Unable to retrieve nodes.';
                }
            });
        };

        var getNodeStatus = function () {
            nodeService.getNodeStatus(null, null, 'PT' + vm.hourValue + 'H', null).then(null, null, function (data) {
                if (data.$resolved) {
                    vm.nodeStatusError = null;
                    vm.nodeData.status = data.results;
                    vm.redrawGrid();
                } else {
                    if (data.statusText && data.statusText !== '') {
                        vm.nodeStatusErrorStatus = data.statusText;
                    }
                    vm.nodeStatusError = 'Unable to retrieve node status.';
                }
            });
        };

        var initialize = function() {
            getNodes();
            getNodeStatus();
            _.defer(function () {
                vm.loading = false;
            });
            navService.updateLocation('nodes');
        };

        initialize();
    });
})();