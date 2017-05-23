(function () {
    'use strict';

    angular.module('scaleApp').controller('nodeDetailsController', function($scope, $location, $routeParams, $timeout, navService, nodeService, scaleService, statusService, jobTypeService) {
        var vm = this,
            nodes = [],
            jobTypes = [];
        
        vm.loading = true;
        vm.loadingStatus = true;
        vm.nodeStatus = null;
        vm.nodesError = null;
        vm.nodeId = parseInt($routeParams.id);
        vm.runningJobs = [];
        vm.completedJobs = [];
        vm.failedJobs = [];
        vm.scaleService = scaleService;

        var getNodes = function () {
            statusService.getStatus(true).then(null, null, function (data) {
                if (data.$resolved) {
                    vm.nodesError = null;
                    vm.runningJobs = [];
                    vm.completedJobs = [];
                    nodes = data.nodes;
                    vm.nodeStatus = _.find(nodes, { id: vm.nodeId });
                    _.forEach(vm.nodeStatus.job_executions.running.by_job_type, function (running) {
                        vm.runningJobs.push({
                            jobType: _.find(jobTypes, { id: running.job_type_id }),
                            count: running.count
                        });
                    });
                    _.forEach(vm.nodeStatus.job_executions.completed.by_job_type, function (completed) {
                        vm.completedJobs.push({
                            jobType: _.find(jobTypes, { id: completed.job_type_id }),
                            count: completed.count
                        });
                    });
                } else {
                    if (data.statusText && data.statusText !== '') {
                        vm.nodesErrorStatus = data.statusText;
                    }
                    vm.nodesError = 'Unable to retrieve nodes.';
                }
                vm.loadingStatus = false;
            });
        };

        var getNodeDetails = function (nodeId) {
            nodeService.getNode(nodeId).then( function (data) {
                vm.node = data;
            }).finally(function () {
                vm.loading = false;
            });
        };

        var initialize = function() {
            navService.updateLocation('nodes');
            jobTypeService.getJobTypesOnce().then(function (data) {
                jobTypes = data.results;
                getNodeDetails(vm.nodeId);
                getNodes();
            });
        };

        initialize();
    });
})();
