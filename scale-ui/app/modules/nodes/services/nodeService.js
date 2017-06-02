(function () {
    'use strict';

    angular.module('scaleApp').service('nodeService', function ($http, $q, $resource, scaleConfig, Node, poller, pollerFactory) {
        var getNodesParams = function (order, active) {
            return {
                order: order,
                active: active
            };
        };

        return {
            getNodes: function (params) {
                params = params || getNodesParams();

                var nodesResource = $resource(scaleConfig.getUrlPrefix('nodes') + 'nodes/', params),
                    nodesPoller = pollerFactory.newPoller(nodesResource, scaleConfig.pollIntervals.nodes);

                return nodesPoller.promise.then(null, null, function (data) {
                    if (data.$resolved) {
                        data.results = Node.transformer(data.results);
                    } else {
                        nodesPoller.stop();
                    }
                    return data;
                });
            },
            getNodesOnce: function (params) {
                params = params || getNodesParams();
                var d = $q.defer();

                $http({
                    url: params.url ? params.url : scaleConfig.getUrlPrefix('nodes') + 'nodes/',
                    method: 'GET',
                    params: params
                }).success(function (data) {
                    var returnData = Node.transformer(data.nodes);
                    d.resolve(returnData);
                }).error(function (error) {
                    d.reject(error);
                });

                return d.promise;
            },
            getNode: function (slaveId) {
                var d = $q.defer();
                $http.get(scaleConfig.getUrlPrefix('nodes') + 'nodes/' + slaveId + '/').success(function (data) {
                    var returnData = Node.transformer(data);
                    d.resolve(returnData);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getNodeData: function (slaveId, since) {
                var data = {},
                    self = this;

                since = since || 'PT3H';

                return self.getNodes().then(function (nodes) {
                    data.nodes = nodes;
                    return self.getNodeStatus(since).then(function (stats) {
                        data.stats = stats;
                        return data;
                    });
                });
            }
        };

    });
})();
