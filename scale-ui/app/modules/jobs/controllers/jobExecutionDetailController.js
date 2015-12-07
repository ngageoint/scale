(function () {
    'use strict';

    angular.module('scaleApp').controller('jobExecutionDetailController', function ($scope, $location, $routeParams, navService, jobExecutionService, nodeService, scaleConfig, subnavService) {
        $scope.jobExecution = {};
        $scope.jobExecutionId = $routeParams.id;
        $scope.loading = true;
        $scope.subnavLinks = scaleConfig.subnavLinks.jobs;
        subnavService.setCurrentPath('jobs/runs');

        var getJobExecutionDetail = function (jobExecutionId) {
            jobExecutionService.getJobExecutionDetail(id).then(function (data) {
                $scope.jobExecution = data;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        var initialize = function () {
            getJobExecutionDetail($routeParams.id);
            navService.updateLocation('jobs');
        };

        initialize();
    });
})();