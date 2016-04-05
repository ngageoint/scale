(function () {
    'use strict';

    angular.module('scaleApp').service('nodeService', function ($http, $q, $resource, scaleConfig, Node, NodeStatus, poller, pollerFactory) {
        /*var totalNodes = 5;

        var getTotalNodes = function () {
            return totalNodes;
        };

        var setTotalNodes = function () {
            totalNodes = Math.floor(Math.random() * (20 - 1 + 1)) + 1;
        };

        setInterval(function () {
            setTotalNodes();
        }, 3100);*/

        var getNodeStatusParams = function (page, page_size, started, ended) {
            var params = {};

            if(page) { params.page = page; }
            if(page_size) { params.page_size = page_size; }
            if(started) { params.started = started; }
            if(ended) { params.ended = ended; }

            return params;
        };

        return {
            getNodes: function () {
                var nodesResource = $resource(scaleConfig.urls.apiPrefix + 'nodes/'),
                    nodesPoller = pollerFactory.newPoller(nodesResource, scaleConfig.pollIntervals.nodes);

                return nodesPoller.promise.then(null, null, function (data) {
                    if (data.$resolved) {
                        /*var returnResult = {
                            $resolved: true,
                            nodes: []
                        };
                        var newData = {};
                        for (var i = 0; i < getTotalNodes(); i++) {
                            newData = {
                                "id": i,
                                "hostname": "node" + i + ".local",
                                "port": 5051,
                                "slave_id": "20150616-103050-1800454536-5050-6193-S2",
                                "total_cpus": 2.0,
                                "total_mem": 6793.0,
                                "total_disk": 94639.0,
                                "is_paused": false,
                                "created": "2015-06-15T17:18:52.414Z",
                                "last_modified": "2015-06-15T17:18:52.414Z"
                            };
                            returnResult.nodes.push(newData);
                        }
                        result = returnResult;*/

                        data.results = Node.transformer(data.results);
                    } else {
                        nodesPoller.stop();
                    }
                    return data;
                });
            },
            getNodesOnce: function () {
                var d = $q.defer();
                $http.get(scaleConfig.urls.apiPrefix + 'nodes/').success(function (data) {
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
                        /*var returnResult = {
                            $resolved: true,
                            node_stats: []
                        };
                        var newData = {};
                        for (var i = 0; i < getTotalNodes(); i++) {
                            newData = {
                                "hostname": "node" + i + ".local",
                                "jobs_completed": Math.floor(Math.random() * (100 - 20 + 1)) + 20,
                                "system_failures": Math.floor(Math.random() * (20 - 0 + 1)) + 0,
                                "id": i
                            };
                            returnResult.node_stats.push(newData);
                        }
                        result = returnResult;*/

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
