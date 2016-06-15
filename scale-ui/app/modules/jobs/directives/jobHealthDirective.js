(function () {
    'use strict';

    angular.module('scaleApp').controller('aisJobHealthController', function ($rootScope, $scope, jobTypeService) {
        $scope.loadingJobHealth = true;
        $scope.jobHealthError = null;
        $scope.jobHealthErrorStatus = null;
        $scope.jobHealth = {};

        var getJobTypeStatus = function () {
            jobTypeService.getJobTypeStatus({
                page: null,
                page_size: 1000,
                started: $scope.duration,
                ended: null
            }).then(null, null, function (data) {
                if (data.$resolved) {
                    $scope.jobHealthError = null;
                    $scope.jobTypeStatus = data.results;
                    $scope.total = 0;
                    $scope.failed = 0;

                    var performance = {},
                        failures = [];

                    _.forEach(data.results, function (status) {
                        performance = status.getPerformance();
                        $scope.total = $scope.total + performance.total;
                        $scope.failed = $scope.failed + performance.failed;
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

                    $scope.jobHealth = {
                        gaugeData: $scope.total === 0 ? 0 : 100 - (($scope.failed / $scope.total) * 100).toFixed(2),
                        donutData: failureData
                    };

                    if ($scope.broadcastData) {
                        $rootScope.$broadcast('jobTypeStatus', $scope.jobTypeStatus);
                    }
                } else {
                    if (data.statusText && data.statusText !== '') {
                        $scope.jobHealthErrorStatus = data.statusText;
                    }
                    $scope.jobHealthError = 'Unable to retrieve job statistics.';
                }
                $scope.loadingJobHealth = false;
            });
        };

        getJobTypeStatus();
    }).directive('aisJobHealth', function(){
        /**
         * Usage: <ais-job-health />
         **/
        return {
            controller: 'aisJobHealthController',
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