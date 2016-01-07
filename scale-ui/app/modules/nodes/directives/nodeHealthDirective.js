(function (){
    'use strict';

    angular.module('scaleApp').controller('aisNodeHealthController', function ($rootScope, $scope, nodeService) {
        $scope.loadingNodeHealth = true;
        $scope.nodeHealthError = null;
        $scope.nodeHealthErrorStatus = null;
        $scope.nodeHealth = {};
        $scope.nodesOffline = 0;
        $scope.nodesPausedErrors = 0;
        $scope.nodesPaused = 0;
        $scope.nodesOfflineAndPaused = 0;
        $scope.nodesOfflineAndPausedErrors = 0;
        $scope.healthyNodes = 0;
        $scope.totalNodes = 0;

        var getNodeStatus = function () {
            $scope.loadingNodeHealth = true;
            nodeService.getNodeStatus(null, null, $scope.duration, null).then(null, null, function (data) {
                if (data.$resolved) {
                    $scope.totalNodes = data.results.length;

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

                    $scope.nodesOffline = nodesOffline.length;
                    $scope.nodesPausedErrors = nodesPausedErrors.length;
                    $scope.nodesPaused = nodesPaused.length;
                    $scope.nodesOfflineAndPausedErrors = nodesOfflineAndPausedErrors.length;
                    $scope.nodesOfflineAndPaused = nodesOfflineAndPaused.length;

                    // add the length of nodes both offline and paused to produce an accurate healthy count
                    $scope.healthyNodes = $scope.totalNodes - $scope.nodesOffline - $scope.nodesPausedErrors - $scope.nodesPaused - $scope.nodesOfflineAndPaused - $scope.nodesOfflineAndPausedErrors;

                    var donutData = [];

                    // determine percentage of healthy nodes, and breakdown of why nodes are unhealthy
                    var gaugeData = $scope.totalNodes > 0 ? (($scope.healthyNodes / $scope.totalNodes) * 100).toFixed(2) : 0.00;

                    if ($scope.nodesOffline > 0) {
                        donutData.push({
                            status: 'Offline',
                            count: $scope.nodesOffline
                        });
                    }

                    if ($scope.nodesPausedErrors > 0) {
                        donutData.push({
                            status: 'High Failure Rate',
                            count: $scope.nodesPausedErrors
                        });
                    }

                    if ($scope.nodesPaused > 0) {
                        donutData.push({
                            status: 'Paused',
                            count: $scope.nodesPaused
                        });
                    }

                    $scope.nodeHealth = {
                        gaugeData: gaugeData,
                        donutData: donutData
                    };
                } else {
                    if (data.statusText && data.statusText !== '') {
                        $scope.nodeHealthErrorStatus = data.statusText;
                    }
                    $scope.nodeHealthError = 'Unable to retrieve node health.';
                }
                $scope.loadingNodeHealth = false;
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
             templateUrl: 'modules/nodes/directives/nodeHealthTemplate.html',
             restrict: 'E',
             scope: {
                 duration: '=',
                 showDescription: '='
             }
         };
    });
})();
