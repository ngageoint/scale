(function () {
    'use strict';

    angular.module('scaleApp').controller('batchDetailsController', function ($scope, $routeParams, $location, scaleConfig, navService, userService, batchService, recipeService, jobTypeService, Batch, toastr, moment) {
        var vm = this;

        vm.scaleConfig = scaleConfig;
        vm.moment = moment;
        vm.loading = true;
        vm.mode = $routeParams.id > 0 ? 'details' : 'create';
        vm.readonly = true;
        vm.saveBtnClass = 'btn-default';
        vm.batch = $routeParams.id > 0 ? {} : new Batch();
        vm.recipeTypes = [];
        vm.selectedRecipeType = {};
        vm.jobTypes = [];
        vm.selectedJobTypes = [];
        vm.startTime = {
            hour: null,
            minute: null,
            second: null
        };
        vm.endTime = {
            hour: null,
            minute: null,
            second: null
        };
        vm.dateModelOptions = {
            timezone: '+000'
        };
        vm.dateRangeStartedPopup = {
            opened: false
        };
        vm.openDateRangeStartedPopup = function ($event) {
            $event.stopPropagation();
            vm.dateRangeStartedPopup.opened = true;
        };
        vm.dateRangeEndedPopup = {
            opened: false
        };
        vm.openDateRangeEndedPopup = function ($event) {
            $event.stopPropagation();
            vm.dateRangeEndedPopup.opened = true;
        };

        vm.cancelCreate = function () {
            vm.mode = 'view';
            if ($routeParams.id === '0') {
                $location.path('/batch');
            }
        };

        vm.disableSaveBtn = function (invalid) {
            var returnVal = !(!invalid);
            vm.saveBtnClass = returnVal ? 'btn-default' : 'btn-success';
            return returnVal;
        };

        var getWarningsHtml = function (warnings) {
            var warningsHtml = '';
            _.forEach(warnings, function (warning) {
                warningsHtml += '<b>' + warning.id + ':</b> ' + warning.details + '<br /><br />';
            });
            warningsHtml += '<button type="button" class="btn btn-default btn-xs clear">Hide</button>';
            return warningsHtml;
        };

        vm.getDateRange = function () {
            return moment.utc(vm.batch.definition.date_range.started).format(scaleConfig.dateFormats.day_second_utc) + ' &ndash; ' +  moment.utc(vm.batch.definition.date_range.ended).format(scaleConfig.dateFormats.day_second_utc);
        };

        vm.setTime = function (type) {
            if (type === 'started') {
                vm.startTime = {
                    hour: ('0' + moment.utc(vm.batch.definition.date_range[type]).hour()).slice(-2),
                    minute: ('0' + moment.utc(vm.batch.definition.date_range[type]).minute()).slice(-2),
                    second: ('0' + moment.utc(vm.batch.definition.date_range[type]).second()).slice(-2)
                };
            } else {
                vm.endTime = {
                    hour: ('0' + moment.utc(vm.batch.definition.date_range[type]).hour()).slice(-2),
                    minute: ('0' + moment.utc(vm.batch.definition.date_range[type]).minute()).slice(-2),
                    second: ('0' + moment.utc(vm.batch.definition.date_range[type]).second()).slice(-2)
                };
            }
        };

        vm.changeTime = function (type, unit) {
            if (vm.batch.definition.date_range) {
                if (vm[type][unit].length > 2) {
                    vm[type][unit] = ('0' + vm[type].hour).slice(-2);
                }
                if (!isNaN(vm[type][unit])) {
                    if (vm[type].hour > 23 || vm[type].hour < 0) {
                        vm[type].hour = vm[type].hour > 23 ? 23 : 0;
                    }
                    if (vm[type].minute > 59 || vm[type].minute < 0) {
                        vm[type].minute = vm[type].minute > 59 ? 59 : 0;
                    }
                    if (vm[type].second > 59 || vm[type].second < 0) {
                        vm[type].second = vm[type].second > 59 ? 59 : 0;
                    }
                    var timeSet = type === 'startTime' ? moment.utc(vm.batch.definition.date_range.started.toISOString()) : moment.utc(vm.batch.definition.date_range.ended.toISOString());
                    timeSet.set({
                        'hour': ('0' + vm[type].hour).slice(-2),
                        'minute': ('0' + vm[type].minute).slice(-2),
                        'second': ('0' + vm[type].second).slice(-2)
                    });
                    if (type === 'startTime') {
                        vm.batch.definition.date_range.started = timeSet.toDate();
                        console.log('start time: ' + vm.batch.definition.date_range.started.toISOString());
                    } else if (type === 'endTime') {
                        vm.batch.definition.date_range.ended = timeSet.toDate();
                        console.log('end time: ' + vm.batch.definition.date_range.ended.toISOString());
                    }
                }
            }
        };

        vm.keydown = function ($event, unit, type) {
            var max = 0;
            if (unit === 'hour') {
                max = 23;
            } else if (unit === 'minute' || unit === 'second') {
                max = 60;
            }
            if ($event.keyCode === 38) {
                // up arrow
                if (isNaN(vm[type][unit])) {
                    vm[type][unit] = ('0' + 0).slice(-2);
                }
                vm[type][unit] < max ? vm[type][unit]++ : vm[type][unit];
                vm[type][unit] = ('0' + vm[type][unit]).slice(-2);
                vm.changeTime(type, unit);
            } else if ($event.keyCode === 40) {
                // down arrow
                if (isNaN(vm[type][unit])) {
                    vm[type][unit] = ('0' + 0).slice(-2);
                }
                vm[type][unit] > 0 ? vm[type][unit]-- : vm[type][unit];
                vm[type][unit] = ('0' + vm[type][unit]).slice(-2);
                vm.changeTime(type, unit);
            }
        };

        vm.validateBatch = function () {
            vm.loading = true;
            batchService.validateBatch(vm.batch).then(function (data) {
                if (data.warnings && data.warnings.length > 0) {
                    // display the warnings
                    var warningsHtml = getWarningsHtml(data.warnings);
                    toastr['error'](warningsHtml);
                } else {
                    toastr['success']('Batch is valid.');
                }
            }).catch(function (error) {
                if (error && error.detail) {
                    toastr['error'](error.detail);
                } else {
                    toastr['error']('Error validating batch');
                }
            }).finally(function () {
                vm.loading = false;
            });
        };

        vm.saveBatch = function () {
            vm.loading = true;
            batchService.saveBatch(vm.batch).then(function (data) {
                toastr['success']('Batch successfully created.');
            }).catch(function (error) {
                if (error && error.detail) {
                    toastr['error'](error.detail);
                } else {
                    toastr['error']('Error creating batch');
                }
            }).finally(function () {
                vm.loading = false;
                $location.path('/batch');
            })
        };

        var getRecipeTypes = function () {
            return recipeService.getRecipeTypes().then(function (data) {
                vm.recipeTypes = data.results;
            }).catch(function (e) {
                console.log('Error retrieving recipe types: ' + e);
            });
        };

        var getBatch = function () {
            batchService.getBatchById($routeParams.id).then(function (data) {
                vm.loading = false;
                vm.batch = Batch.transformer(data);
            });
        };

        var initialize = function () {
            var user = userService.getUserCreds();
            vm.readonly = !(user && user.is_admin);
            navService.updateLocation('batch');

            if (vm.mode === 'create') {
                getRecipeTypes()
                    .then(function () {
                        vm.loading = false;
                    });
            } else if (vm.mode === 'details') {
                getBatch();
            }
        };

        initialize();

        $scope.$watchCollection('vm.batch.recipe_type', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            if (newValue) {
                vm.jobTypes = [];
                var recipeJobs = _.map(newValue.definition.jobs, 'job_type.name');
                _.forEach(recipeJobs, function (job) {
                    vm.jobTypes.push({
                        label: job,
                        title: job,
                        value: job
                    });
                });
            } else {
                vm.jobTypes = [];
            }
        });

        $scope.$watch('vm.batch.definition.date_range.started', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            if (!newValue) {
                vm.startTime = {
                    hour: null,
                    minute: null,
                    second: null
                };
            }
        });

        $scope.$watch('vm.batch.definition.date_range.ended', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            if (!newValue) {
                vm.endTime = {
                    hour: null,
                    minute: null,
                    second: null
                };
            }
        });
    });
})();
