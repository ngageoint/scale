(function () {
    'use strict';

    angular.module('scaleApp').controller('jobExecutionDetailController', function ($scope, $location, $routeParams, navService, jobExecutionService, nodeService, scaleConfig, subnavService) {
        var vm = this;
        
        vm.jobExecution = {};
        vm.jobExecutionId = $routeParams.id;
        vm.loading = true;
        vm.subnavLinks = scaleConfig.subnavLinks.jobs;
        subnavService.setCurrentPath('jobs/runs');

        var getJobExecutionDetail = function () {
            jobExecutionService.getJobExecutionDetail(id).then(function (data) {
                vm.jobExecution = data;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                vm.loading = false;
            });
        };

        var initialize = function () {
            getJobExecutionDetail($routeParams.id);
            navService.updateLocation('jobs');
        };

        initialize();
    });
})();