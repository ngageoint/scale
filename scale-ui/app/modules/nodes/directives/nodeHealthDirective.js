(function (){
    'use strict';

    angular.module('scaleApp').controller('aisNodeHealthController', function ($rootScope, $scope, nodeService) {
        var vm = this;
        
        vm.loadingNodeHealth = true;
        vm.nodeHealthError = null;
        vm.nodeHealthErrorStatus = null;
        vm.nodeHealth = {};
        vm.nodesOffline = 0;
        vm.nodesPausedErrors = 0;
        vm.nodesPaused = 0;
        vm.nodesOfflineAndPaused = 0;
        vm.nodesOfflineAndPausedErrors = 0;
        vm.healthyNodes = 0;
        vm.totalNodes = 0;

        var getNodeStatus = function () {
            vm.loadingNodeHealth = true;
            nodeService.getNodeStatus(null, null, $scope.duration, null).then(null, null, function (data) {
                if (data.$resolved) {
                    vm.totalNodes = data.results.length;

                    var nodesOffline = [],
                        nodesPausedErrors = [],
                        nodesPaused = [],
                        nodesOfflineAndPausedErrors = [],
                        nodesOfflineAndPaused = [];

                    _.forEach(data.results, function (n) {
                        if (!n.is_online) {
                            // node is offline
                            if (n.node.is_paused_errors) {
                                nodesOfflineAndPausedErrors.push(n);
                            } else if (n.node.is_paused) {
                                nodesOfflineAndPaused.push(n);
                            } else {
                                nodesOffline.push(n);
                            }
                        } else {
                            // node is online
                            if (n.node.is_paused_errors) {
                                nodesPausedErrors.push(n);
                            } else if (n.node.is_paused) {
                                nodesPaused.push(n);
                            }
                        }
                    });

                    vm.nodesOffline = nodesOffline.length;
                    vm.nodesPausedErrors = nodesPausedErrors.length;
                    vm.nodesPaused = nodesPaused.length;
                    vm.nodesOfflineAndPausedErrors = nodesOfflineAndPausedErrors.length;
                    vm.nodesOfflineAndPaused = nodesOfflineAndPaused.length;

                    // add the length of nodes both offline and paused to produce an accurate healthy count
                    vm.healthyNodes = vm.totalNodes - vm.nodesOffline - vm.nodesPausedErrors - vm.nodesPaused - vm.nodesOfflineAndPaused - vm.nodesOfflineAndPausedErrors;

                    var donutData = [];

                    // determine percentage of healthy nodes, and breakdown of why nodes are unhealthy
                    var gaugeData = vm.totalNodes > 0 ? ((vm.healthyNodes / vm.totalNodes) * 100).toFixed(2) : 0.00;

                    if (vm.nodesOffline > 0) {
                        donutData.push({
                            status: 'Offline',
                            count: vm.nodesOffline
                        });
                    }

                    if (vm.nodesPausedErrors > 0) {
                        donutData.push({
                            status: 'High Failure Rate',
                            count: vm.nodesPausedErrors
                        });
                    }

                    if (vm.nodesPaused > 0) {
                        donutData.push({
                            status: 'Paused',
                            count: vm.nodesPaused
                        });
                    }
                    
                    if (vm.nodesOfflineAndPaused) {
                        donutData.push({
                            status: 'Offline and Paused',
                            count: vm.nodesOfflineAndPaused
                        });
                    }

                    if (vm.nodesOfflineAndPausedErrors) {
                        donutData.push({
                            status: 'Offline and Paused due to Errors',
                            count: vm.nodesOfflineAndPausedErrors
                        });
                    }

                    vm.nodeHealth = {
                        gaugeData: gaugeData,
                        donutData: donutData
                    };
                } else {
                    if (data.statusText && data.statusText !== '') {
                        vm.nodeHealthErrorStatus = data.statusText;
                    }
                    vm.nodeHealthError = 'Unable to retrieve node health.';
                }
                vm.loadingNodeHealth = false;
            });
        };

        getNodeStatus();

        $rootScope.$on('updateNodeHealth', function () {
            getNodeStatus();
        });
    }).directive('aisNodeHealth', function(){
        /**
         * Usage: <ais-node-health />
         **/
         return {
             controller: 'aisNodeHealthController',
             controllerAs: 'vm',
             templateUrl: 'modules/nodes/directives/nodeHealthTemplate.html',
             restrict: 'E',
             scope: {
                 duration: '=',
                 showDescription: '='
             }
         };
    });
})();
