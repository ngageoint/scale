(function () {
    'use strict';

    angular.module('scaleApp').controller('aisJobHealthController', function ($rootScope, $scope, jobTypeService) {
        var vm = this;
        
        vm.loadingJobHealth = true;
        vm.jobHealthError = null;
        vm.jobHealthErrorStatus = null;
        vm.jobHealth = {};

        var getJobTypeStatus = function () {
            jobTypeService.getJobTypeStatus({
                page: null,
                page_size: 1000,
                started: $scope.duration,
                ended: null
            }).then(null, null, function (data) {
                if (data.$resolved) {
                    vm.jobHealthError = null;
                    vm.jobTypeStatus = data.results;
                    vm.total = 0;
                    vm.failed = 0;

                    var performance = {},
                        failures = [];

                    _.forEach(data.results, function (status) {
                        performance = status.getPerformance();
                        vm.total = vm.total + performance.total;
                        vm.failed = vm.failed + performance.failed;
                        failures.push(status.getFailures());
                    });

                    var failureData = [],
                        systemFailures = 0,
                        dataFailures = 0,
                        algorithmFailures = 0;

                    _.forEach(failures, function (f) {
                        _.forEach(f, function (type) {
                            if (type.status === 'SYSTEM') {
                                systemFailures = systemFailures + type.count;
                            } else if (type.status === 'DATA') {
                                dataFailures = dataFailures + type.count;
                            } else if (type.status === 'ALGORITHM') {
                                algorithmFailures = algorithmFailures + type.count;
                            }
                        });
                    });

                    if (systemFailures > 0 || dataFailures > 0 || algorithmFailures > 0) {
                        if (systemFailures > 0) {
                            failureData.push({
                                status: 'SYSTEM',
                                count: systemFailures
                            });
                        }
                        if (algorithmFailures > 0) {
                            failureData.push({
                                status: 'ALGORITHM',
                                count: algorithmFailures
                            });
                        }
                        if (dataFailures > 0) {
                            failureData.push({
                                status: 'DATA',
                                count: dataFailures
                            });
                        }
                    }

                    vm.jobHealth = {
                        gaugeData: vm.total === 0 ? 0 : 100 - ((vm.failed / vm.total) * 100).toFixed(2),
                        donutData: failureData
                    };

                    if ($scope.broadcastData) {
                        $rootScope.$broadcast('jobTypeStatus', vm.jobTypeStatus);
                    }
                } else {
                    if (data.statusText && data.statusText !== '') {
                        vm.jobHealthErrorStatus = data.statusText;
                    }
                    vm.jobHealthError = 'Unable to retrieve job statistics.';
                }
                vm.loadingJobHealth = false;
            });
        };

        getJobTypeStatus();
    }).directive('aisJobHealth', function(){
        /**
         * Usage: <ais-job-health />
         **/
        return {
            controller: 'aisJobHealthController',
            controllerAs: 'vm',
            templateUrl: 'modules/jobs/directives/jobHealthTemplate.html',
            restrict: 'E',
            scope: {
                duration: '=',
                broadcastData: '=', // set to true when using another widget in the same view that also calls getJobTypeStatus
                showDescription: '='
            }
        };
    });
})();