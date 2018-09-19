(function () {
    'use strict';

    angular.module('scaleApp').controller('nodeDetailsController', function($scope, $location, $routeParams, $timeout, navService, nodeService, scaleConfig, scaleService, statusService, jobTypeService, moment) {
        var vm = this,
            nodes = [],
            jobTypes = [];

        vm.scaleConfig = scaleConfig;
        vm.moment = moment;
        vm._ = _;
        vm.loading = true;
        vm.loadingStatus = true;
        vm.nodeStatus = null;
        vm.nodesError = null;
        vm.nodeId = parseInt($routeParams.id);
        vm.runningJobs = [];
        vm.completedJobs = [];
        vm.systemJobs = [];
        vm.algorithmJobs = [];
        vm.dataJobs = [];
        vm.scaleService = scaleService;

        var getNodes = function () {
            statusService.getStatus(true).then(null, null, function (data) {
                if (data.$resolved) {
                    vm.nodesError = null;
                    vm.runningJobs = [];
                    vm.completedJobs = [];
                    vm.systemJobs = [];
                    vm.algorithmJobs = [];
                    vm.dataJobs = [];
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
                    _.forEach(vm.nodeStatus.job_executions.failed.system.by_job_type, function (system) {
                        vm.systemJobs.push({
                            jobType: _.find(jobTypes, { id: system.job_type_id }),
                            count: system.count
                        });
                    });
                    _.forEach(vm.nodeStatus.job_executions.failed.algorithm.by_job_type, function (algorithm) {
                        vm.algorithmJobs.push({
                            jobType: _.find(jobTypes, { id: algorithm.job_type_id }),
                            count: algorithm.count
                        });
                    });
                    _.forEach(vm.nodeStatus.job_executions.failed.data.by_job_type, function (data) {
                        vm.dataJobs.push({
                            jobType: _.find(jobTypes, { id: data.job_type_id }),
                            count: data.count
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
