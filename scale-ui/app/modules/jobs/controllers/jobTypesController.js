(function () {
    'use strict';

    angular.module('scaleApp').controller('jobTypesController', function ($rootScope, $scope, $routeParams, $location, hotkeys, scaleService, navService, stateService, jobTypeService, scaleConfig, subnavService, nodeService, localStorage, userService) {
        var vm = this;
        
        vm.containerStyle = '';
        vm.requestedJobTypeId = parseInt($routeParams.id);
        vm.jobTypes = [];
        vm.jobTypeIds = [];
        vm.jobTypeCount = 0;
        vm.activeJobTypeDetails = {};
        vm.activeJobTypeInterfaceValues = [];
        vm.activeJobTypeErrors = [];
        vm.activeJobTypeStats = {};
        vm.jobTypesParams = stateService.getJobTypesParams();
        vm.showJobTypeErrors = false;
        vm.loading = true;
        vm.activeJobType = null;
        vm.healthData6 = {};
        vm.healthData12 = {};
        vm.healthData24 = {};
        vm.activityIcon = '<i class="fa fa-pulse">&#x' + scaleConfig.activityIconCode + '</i>';
        vm.jobDetailsClass = 'hidden';
        vm.pauseBtnClass = 'fa-pause';
        vm.user = userService.getUserCreds();
        vm.subnavLinks = scaleConfig.subnavLinks.jobs;
        subnavService.setCurrentPath('jobs/types');

        $scope.$watchCollection('vm.jobTypesParams',function(newValue){
            stateService.setJobTypesParams(newValue);
           console.log('toggle hide r&d: ' + newValue.hide_rd);
        });

        vm.viewDetails = function (id) {
            vm.activeJobType = _.find(vm.jobTypes, 'id', id);
            vm.activeJobType.created = formatDateTime(vm.activeJobType.created);
            vm.activeJobType.lastModified = formatDateTime(vm.activeJobType.lastModified);

            $location.path('jobs/types/' + id);

            getJobTypeDetails(vm.activeJobType.id);

            vm.jobDetailsClass = 'visible';
        };

        vm.togglePause = function () {
            vm.activeJobType.is_paused = !vm.activeJobType.is_paused;
            vm.activeJobTypeDetails.is_paused = vm.activeJobType.is_paused;
            vm.loading = true;
            jobTypeService.updateJobType(vm.activeJobTypeDetails).then(function(data){
                vm.activeJobTypeDetails = data;
                vm.pauseBtnClass = vm.getPauseButtonClass(vm.activeJobTypeDetails.is_paused);
                vm.loading = false;
            }).catch(function (error) {
                console.log(error);
                toastr['error'](error);
                vm.loading = false;
            });
        };

        vm.getPauseButtonClass = function(is_paused){
            return is_paused ? 'fa-play' : 'fa-pause';
        };

        vm.getJobTypeListItemClass = function(jobType){
            return jobType.is_paused ? 'paused' : '';
        };

        var formatDateTime = function (dt) {
            return moment.utc(dt).toISOString();
        };

        var getJobTypes = function () {
            jobTypeService.getJobTypesOnce().then(function (data) {
                vm.jobTypes = data.results;
                vm.jobTypeIds = _.pluck(vm.jobTypes, 'id');
                vm.jobTypeCount = data.count;
                if (vm.requestedJobTypeId) {
                    vm.viewDetails(vm.requestedJobTypeId);
                } else {
                    vm.loading = false;
                }
                hotkeys.bindTo($scope)
                    .add({
                        combo: 'ctrl+up',
                        description: 'Previous Job Type',
                        callback: function () {
                            if (vm.activeJobType) {
                                var idx = _.indexOf(vm.jobTypeIds, vm.activeJobType.id);
                                if (idx > 0) {
                                    vm.viewDetails(vm.jobTypeIds[idx - 1]);
                                }
                            }
                        }
                    }).add({
                        combo: 'ctrl+down',
                        description: 'Next Job Type',
                        callback: function () {
                            if (vm.activeJobType) {
                                var idx = _.indexOf(vm.jobTypeIds, vm.activeJobType.id);
                                if (idx < (vm.jobTypeIds.length - 1)) {
                                    vm.viewDetails(vm.jobTypeIds[idx + 1]);
                                }
                            }
                        }
                    });
            }).catch(function (error) {
                console.log(error);
                vm.loading = false;
            });
        };

        var getJobTypeDetails = function (id) {
            vm.loading = true;
            jobTypeService.getJobTypeDetails(id).then(function (data) {
                vm.activeJobTypeDetails = data;
                vm.activeJobTypeInterfaceValues = _.pairs(data.job_type_interface);
                vm.pauseBtnClass = vm.getPauseButtonClass(vm.activeJobTypeDetails.is_paused);
                // format error mapping
                vm.activeJobTypeErrors = [];
                vm.showJobTypeErrors = _.keys(data.error_mapping.exit_codes).length > 0;
                if (vm.showJobTypeErrors) {
                    _.forEach(data.error_mapping.exit_codes, function (error_name) {
                        var error = _.find(data.errors, 'name', error_name),
                            exitCode = _.invert(data.error_mapping.exit_codes)[error_name];
                        vm.activeJobTypeErrors.push({code: exitCode, data: error});
                    });
                }

                // format job type stats
                var performance = data.getPerformance(),
                    failures = data.getFailures();

                vm.activeJobTypeStats = performance;

                vm.healthData6 = {
                    gaugeData: performance.hour6.rate,
                    donutData: failures.hour6
                };
                vm.healthData12 = {
                    gaugeData: performance.hour12.rate,
                    donutData: failures.hour12
                };
                vm.healthData24 = {
                    gaugeData: performance.hour24.rate,
                    donutData: failures.hour24
                };
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                vm.loading = false;
            });
        };

        var initialize = function () {
            vm.jobTypesParams = stateService.getJobTypesParams();
            getJobTypes();
            navService.updateLocation('jobs');
        };

        initialize();

        angular.element(document).ready(function () {
            // set container heights equal to available page height
            var viewport = scaleService.getViewportSize(),
                offset = scaleConfig.headerOffset,
                containerMaxHeight = viewport.height - offset;

            vm.containerStyle = 'height: ' + containerMaxHeight + 'px; max-height: ' + containerMaxHeight + 'px;';
        });
    });
})();
