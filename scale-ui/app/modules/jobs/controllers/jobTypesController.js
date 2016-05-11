(function () {
    'use strict';

    angular.module('scaleApp').controller('jobTypesController', function ($rootScope, $scope, $routeParams, $location, hotkeys, scaleService, navService, jobTypeService, scaleConfig, subnavService, nodeService, localStorage, userService) {
        $scope.containerStyle = '';
        $scope.requestedJobTypeId = parseInt($routeParams.id);
        $scope.jobTypes = [];
        $scope.jobTypeIds = [];
        $scope.jobTypeCount = 0;
        $scope.activeJobTypeDetails = {};
        $scope.activeJobTypeInterfaceValues = [];
        $scope.activeJobTypeErrors = [];
        $scope.activeJobTypeStats = {};
        $scope.showJobTypeErrors = false;
        $scope.loading = true;
        $scope.activeJobType = null;
        $scope.healthData6 = {};
        $scope.healthData12 = {};
        $scope.healthData24 = {};
        $scope.activityIcon = '<i class="fa fa-pulse">&#x' + scaleConfig.activityIconCode + '</i>';
        $scope.jobDetailsClass = 'hidden';
        $scope.pauseBtnClass = 'fa-pause';
        $scope.user = userService.getUserCreds();
        $scope.subnavLinks = scaleConfig.subnavLinks.jobs;
        subnavService.setCurrentPath('jobs/types');

        var jobTypeStats = {};

        $scope.viewDetails = function (id) {
            $scope.activeJobType = _.find($scope.jobTypes, 'id', id);
            $scope.activeJobType.created = formatDateTime($scope.activeJobType.created);
            $scope.activeJobType.lastModified = formatDateTime($scope.activeJobType.lastModified);

            $location.path('jobs/types/' + id);

            getJobTypeDetails($scope.activeJobType.id);

            //formatJobTypeStats();

            $scope.jobDetailsClass = 'visible';
        };

        $scope.togglePause = function () {
            $scope.activeJobType.is_paused = !$scope.activeJobType.is_paused;
            $scope.activeJobTypeDetails.is_paused = $scope.activeJobType.is_paused;
            $scope.loading = true;
            jobTypeService.updateJobType($scope.activeJobTypeDetails).then(function(data){
                $scope.activeJobTypeDetails = data;
                $scope.pauseBtnClass = $scope.getPauseButtonClass($scope.activeJobTypeDetails.is_paused);
                $scope.loading = false;
            }).catch(function (error) {
                console.log(error);
                toastr['error'](error);
                $scope.loading = false;
            });
        };

        $scope.getPauseButtonClass = function(is_paused){
            return is_paused ? 'fa-play' : 'fa-pause';
        }

        $scope.getJobTypeListItemClass = function(jobType){
            return jobType.is_paused ? 'paused' : '';
        }

        var formatDateTime = function (dt) {
            return moment.utc(dt).toISOString();
        };

        var getJobTypes = function () {
            jobTypeService.getJobTypesOnce().then(function (data) {
                $scope.jobTypes = data.results;
                $scope.jobTypeIds = _.pluck(data.results, 'id');
                $scope.jobTypeCount = data.count;
                if ($scope.requestedJobTypeId) {
                    $scope.viewDetails($scope.requestedJobTypeId);
                } else {
                    $scope.loading = false;
                }
                hotkeys.bindTo($scope)
                    .add({
                        combo: 'ctrl+up',
                        description: 'Previous Job Type',
                        callback: function () {
                            if ($scope.activeJobType) {
                                var idx = _.indexOf($scope.jobTypeIds, $scope.activeJobType.id);
                                if (idx > 0) {
                                    $scope.viewDetails($scope.jobTypeIds[idx - 1]);
                                }
                            }
                        }
                    }).add({
                        combo: 'ctrl+down',
                        description: 'Next Job Type',
                        callback: function () {
                            if ($scope.activeJobType) {
                                var idx = _.indexOf($scope.jobTypeIds, $scope.activeJobType.id);
                                if (idx < ($scope.jobTypeIds.length - 1)) {
                                    $scope.viewDetails($scope.jobTypeIds[idx + 1]);
                                }
                            }
                        }
                    });
            }).catch(function (error) {
                console.log(error);
                $scope.loading = false;
            });
        };

        var getJobTypeDetails = function (id) {
            $scope.loading = true;
            jobTypeService.getJobTypeDetails(id).then(function (data) {
                $scope.activeJobTypeDetails = data;
                $scope.activeJobTypeInterfaceValues = _.pairs(data.job_type_interface);
                $scope.pauseBtnClass = $scope.getPauseButtonClass($scope.activeJobTypeDetails.is_paused);
                // format error mapping
                $scope.activeJobTypeErrors = [];
                $scope.showJobTypeErrors = _.keys(data.error_mapping.exit_codes).length > 0;
                if ($scope.showJobTypeErrors) {
                    _.forEach(data.error_mapping.exit_codes, function (error_name) {
                        var error = _.find(data.errors, 'name', error_name),
                            exitCode = _.invert(data.error_mapping.exit_codes)[error_name];
                        $scope.activeJobTypeErrors.push({code: exitCode, data: error});
                    });
                }

                // format job type stats
                var performance = data.getPerformance(),
                    failures = data.getFailures();

                $scope.activeJobTypeStats = performance;

                $scope.healthData6 = {
                    gaugeData: performance.hour6.rate,
                    donutData: failures.hour6
                };
                $scope.healthData12 = {
                    gaugeData: performance.hour12.rate,
                    donutData: failures.hour12
                };
                $scope.healthData24 = {
                    gaugeData: performance.hour24.rate,
                    donutData: failures.hour24
                };
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        var initialize = function () {
            getJobTypes();
            navService.updateLocation('jobs');
        };

        initialize();

        angular.element(document).ready(function () {
            // set container heights equal to available page height
            var viewport = scaleService.getViewportSize(),
                offset = scaleConfig.headerOffset,
                containerMaxHeight = viewport.height - offset;

            $scope.containerStyle = 'height: ' + containerMaxHeight + 'px; max-height: ' + containerMaxHeight + 'px;';
        });
    });
})();
