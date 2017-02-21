(function () {
    'use strict';

    angular.module('scaleApp').controller('batchesController', function ($scope, navService, batchService) {

        var vm = this;

        // vm.getJobs = function () {
        //     jobService.getJobsOnce(vm.jobsParams).then(function (data) {
        //         vm.gridOptions.totalItems = data.count;
        //         vm.gridOptions.minRowsToShow = data.results.length;
        //         vm.gridOptions.virtualizationThreshold = data.results.length;
        //         vm.gridOptions.data = data.results;
        //     }).catch(function (error) {
        //         console.log(error);
        //     }).finally(function () {
        //         vm.loading = false;
        //     });
        // };

        vm.initialize = function () {
            batchService.getBatchesOnce().then(function(results) {
                console.log('Got results: ' + JSON.stringify(results));
            });
            navService.updateLocation('batch');
        };
        vm.initialize();
    });
})();
