(function () {
    'use strict';

    angular.module('scaleApp').service('nodeService', function ($http, $q, $resource, scaleConfig, Node, NodeStatus, poller, pollerFactory) {
        var getNodesParams = function (page, page_size, started, ended, order, include_inactive, url) {
            return {
                page: page,
                page_size: page_size,
                started: started,
                ended: ended,
                order: order,
                include_inactive: include_inactive,
                url: url
            };
        };

        var getNodeStatusParams = function (page, page_size, started, ended) {
            var params = {};

            if(page) { params.page = page; }
            if(page_size) { params.page_size = page_size; }
            if(started) { params.started = started; }
            if(ended) { params.ended = ended; }

            return params;
        };

        return {
            getNodes: function (params) {
                params = params || getNodesParams();
                params.url = params.url ? params.url : scaleConfig.urls.apiPrefix + 'nodes/';

                var nodesResource = $resource(params.url, params),
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
                    url: params.url ? params.url : scaleConfig.urls.apiPrefix + 'nodes/',
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
                $http.get(scaleConfig.urls.apiPrefix + 'nodes/' + slaveId + '/').success(function (data) {
                    var returnData = Node.transformer(data);
                    d.resolve(returnData);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getNodeStatus: function (page, page_size, started, ended) {
                var params = getNodeStatusParams(page, page_size, started, ended);

                var nodeStatusResource = $resource(scaleConfig.urls.apiPrefix + 'nodes/status/', params),
                    nodeStatusPoller = pollerFactory.newPoller(nodeStatusResource, scaleConfig.pollIntervals.nodeStatus);

                return nodeStatusPoller.promise.then(null, null, function (data) {
                    if (data.$resolved) {
                        data.results = NodeStatus.transformer(data.results);
                    } else {
                        nodeStatusPoller.stop();
                    }
                    return data;
                });
            },
            getNodeStatusOnce: function (page, page_size, started, ended) {
                var d = $q.defer();
                var params = getNodeStatusParams(page, page_size, started, ended);
                $http({
                    url: scaleConfig.urls.apiPrefix + 'nodes/status/',
                    method: 'GET',
                    params: params
                }).success(function (data) {
                    data.results = NodeStatus.transformer(data.results);
                    d.resolve(data);
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
