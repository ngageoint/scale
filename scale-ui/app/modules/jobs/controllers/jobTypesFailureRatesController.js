(function () {
    'use strict';
    
    angular.module('scaleApp').controller('jobTypesFailureRatesController', function ($scope, $location, scaleConfig, stateService, scaleService, subnavService, jobTypeService, metricsService, gridFactory, JobType, toastr, moment) {
        var vm = this,
            jobTypeViewAll = { name: 'VIEW ALL', title: 'VIEW ALL', version: '', id: 0 };

        vm.jobTypesParams = stateService.getJobTypesFailureRatesParams();

        var jobTypes = [],
            started = moment.utc().subtract(30, 'days').startOf('d').toISOString(),
            ended = moment.utc().endOf('d').toISOString(),
            filteredByJobType = vm.jobTypesParams.name ? true : false;

        vm.stateService = stateService;
        vm.scaleService = scaleService;
        vm.loading = true;
        vm.dates = [];
        vm.performanceData = [];
        vm.jobTypeValues = [jobTypeViewAll];
        vm.selectedJobType = null;
        vm.sortOrders = {
            twentyfour_hours: {
                system: {
                    direction: vm.jobTypesParams.order || 'desc',
                    icon: 'hidden'
                },
                algorithm: {
                    direction: vm.jobTypesParams.order || 'desc',
                    icon: 'hidden'
                },
                data: {
                    direction: vm.jobTypesParams.order || 'desc',
                    icon: 'hidden'
                },
                total: {
                    direction: vm.jobTypesParams.order || 'desc',
                    icon: 'hidden'
                },
                errorTotal: {
                    direction: vm.jobTypesParams.order || 'desc',
                    icon: 'hidden'
                }
            },
            fortyeight_hours: {
                system: {
                    direction: vm.jobTypesParams.order || 'desc',
                    icon: 'hidden'
                },
                algorithm: {
                    direction: vm.jobTypesParams.order || 'desc',
                    icon: 'hidden'
                },
                data: {
                    direction: vm.jobTypesParams.order || 'desc',
                    icon: 'hidden'
                },
                total: {
                    direction: vm.jobTypesParams.order || 'desc',
                    icon: 'hidden'
                },
                errorTotal: {
                    direction: vm.jobTypesParams.order || 'desc',
                    icon: 'hidden'
                }
            },
            thirty_days: {
                system: {
                    direction: vm.jobTypesParams.order || 'desc',
                    icon: 'hidden'
                },
                algorithm: {
                    direction: vm.jobTypesParams.order || 'desc',
                    icon: 'hidden'
                },
                data: {
                    direction: vm.jobTypesParams.order || 'desc',
                    icon: 'hidden'
                },
                total: {
                    direction: vm.jobTypesParams.order || 'desc',
                    icon: 'hidden'
                },
                errorTotal: {
                    direction: vm.jobTypesParams.order || 'desc',
                    icon: 'hidden'
                }
            }
        };
        vm.currSortField = '';
        vm.currSortErrorType = '';
        vm.subnavLinks = scaleConfig.subnavLinks.jobs;
        subnavService.setCurrentPath('jobs/failure-rates');

        var defaultColumnDefs = [
            {
                field: 'job_type',
                displayName: 'Job Type',
                cellTemplate: '<div class="ui-grid-cell-contents"><span ng-bind-html="row.entity.job_type.getIcon()"></span> {{ row.entity.job_type.title }} {{ row.entity.job_type.version }}</div>',
                filterHeaderTemplate: '<div class="ui-grid-filter-container"><select class="form-control input-sm" ng-model="grid.appScope.vm.selectedJobType" ng-options="jobType as (jobType.title + \' \' + jobType.version) for jobType in grid.appScope.vm.jobTypeValues"></select></div>',
                width: '16%',
                enableSorting: false
            },
            {
                field: 'twentyfour_hours',
                displayName: '24 Hours',
                enableSorting: false,
                enableFiltering: false,
                width: '28%',
                headerCellTemplate: 'gridHeader.html',
                cellTemplate: 'gridRow.html'
            },
            {
                field: 'fortyeight_hours',
                displayName: '48 Hours',
                enableSorting: false,
                enableFiltering: false,
                width: '28%',
                headerCellTemplate: 'gridHeader.html',
                cellTemplate: 'gridRow.html'
            },
            {
                field: 'thirty_days',
                displayName: '30 Days',
                enableSorting: false,
                enableFiltering: false,
                width: '28%',
                headerCellTemplate: 'gridHeader.html',
                cellTemplate: 'gridRow.html'
            }
        ];

        vm.gridOptions = gridFactory.defaultGridOptions();
        vm.gridOptions.columnDefs = defaultColumnDefs;
        vm.gridOptions.data = [];
        vm.gridOptions.onRegisterApi = function (gridApi) {
            //set gridApi on scope
            $scope.gridApi = gridApi;
            $scope.gridApi.selection.on.rowSelectionChanged($scope, function (row) {
                if ($scope.actionClicked) {
                    $scope.actionClicked = false;
                } else {
                    $scope.$apply(function () {
                        $location.path('/jobs/types/' + row.entity.job_type.id);
                    });
                }
            });
        };
        
        vm.setStyle = function (colField, errorType) {
            var errorValue = (colField[errorType] / colField.total).toFixed(2);
            var textColor = errorValue >= 0.5 ? '#fff' : '#000';
            var rgb = errorType === 'system' ? '103, 0, 13' : errorType === 'algorithm' ? '203, 24, 29' : '241, 105, 19';
            return 'background: rgba(' + rgb + ', ' + errorValue + '); color: ' + textColor;
        };

        vm.failRateStyle = function (error, total) {
            var percentage = ((error / total) * 100).toFixed(0);
            return percentage > 0 ? 'width: ' + percentage + '%' : 'display: none';
        };
        
        vm.getPercentageOfTotal = function (errorTotal, total) {
            if (total === 0) {
                return '0%';
            }
            return ((errorTotal / total) * 100).toFixed(0) + '%';
        };

        vm.filterResults = function (skipInit, skipSort) {
            stateService.setJobTypesFailureRatesParams(vm.jobTypesParams);
            _.forEach(_.pairs(vm.jobTypesParams), function (param) {
                $location.search(param[0], param[1]).replace();
            });
            if (!skipInit) {
                vm.gridOptions.data = [];
                vm.loading = true;
                initialize(skipSort);
            }
        };

        vm.updateJobType = function (value) {
            vm.jobTypesParams.name = value.name === 'VIEW ALL' ? null : value.name;
            vm.jobTypesParams.version = value.name === 'VIEW ALL' ? null : value.version;
            if (!vm.loading) {
                vm.filterResults(false, false);
            }
        };

        vm.sortBy = function (errorType, field, order) {
            order = order || vm.sortOrders[field][errorType].direction;
            vm.sortOrders[vm.currSortField][vm.currSortErrorType].icon = 'hidden';
            vm.gridOptions.data = _.sortByOrder(vm.performanceData, function (d) {
                if (errorType === 'errorTotal') {
                    if (d[field].total > 0) {
                        return d[field].errorTotal / d[field].total;
                    }
                    return 0;
                }
                return d[field][errorType];
            }, order);
            vm.currSortErrorType = errorType;
            vm.currSortField = field;
            vm.jobTypesParams.order = order;
            vm.jobTypesParams.orderField = field;
            vm.jobTypesParams.orderErrorType = errorType;

            if (order) {
                vm.sortOrders[field][errorType].icon = order === 'desc' ? 'fa-caret-down' : 'fa-caret-up';
                vm.sortOrders[field][errorType].direction = order === 'desc' ? 'asc' : 'desc';
            } else {
                vm.sortOrders[field][errorType].icon = vm.sortOrders[field][errorType].direction === 'desc' ? 'fa-caret-down' : 'fa-caret-up';
                vm.sortOrders[field][errorType].direction = vm.sortOrders[field][errorType].direction === 'desc' ? 'asc' : 'desc';
            }

            vm.filterResults(true);
            $scope.gridApi.core.refresh();
        };

        var formatData = function (data, numDays) {
            var dataArr = [];
            _.forEach(data, function (result) {
                var filteredResult = _.filter(result, function (d) {
                    var date = moment.utc(d.date, 'YYYY-MM-DD');
                    if (moment.utc().diff(moment.utc(date), 'd') <= numDays) {
                        return d;
                    }
                });
                dataArr.push(filteredResult);
            });
            return dataArr;
        };

        var formatColumn = function (cData, id) {
            var systemErrors = cData[0],
                algorithmErrors = cData[1],
                dataErrors = cData[2],
                totalCount = cData[3];

            var obj = {
                system: _.sum(_.map(_.filter(systemErrors, { id: id }), 'value')),
                algorithm: _.sum(_.map(_.filter(algorithmErrors, { id: id }), 'value')),
                data: _.sum(_.map(_.filter(dataErrors, { id: id }), 'value')),
                total: _.sum(_.map(_.filter(totalCount, { id: id }), 'value'))
            };
            obj.errorTotal = obj.system + obj.algorithm + obj.data;

            return obj;
        };

        var initialize = function (skipSort) {
            vm.performanceData = [];
            vm.jobTypeValues = [jobTypeViewAll];
            stateService.setJobTypesFailureRatesParams(vm.jobTypesParams);
            jobTypeService.getJobTypesOnce().then(function (jobTypesData) {
                if (vm.jobTypesParams.name && vm.jobTypesParams.version) {
                    jobTypes = _.filter(jobTypesData.results, { name: vm.jobTypesParams.name, version: vm.jobTypesParams.version });
                } else {
                    jobTypes = _.cloneDeep(jobTypesData.results);
                }
                vm.jobTypeValues.push(jobTypesData.results);
                vm.jobTypeValues = _.flatten(vm.jobTypeValues);
                vm.selectedJobType = _.find(vm.jobTypeValues, { name: vm.jobTypesParams.name, version: vm.jobTypesParams.version }) || jobTypeViewAll;
                vm.gridOptions.totalItems = jobTypesData.count;

                var metricsParams = {
                    page: null,
                    page_size: null,
                    started: started,
                    ended: ended,
                    choice_id: vm.selectedJobType.id > 0 ? [vm.selectedJobType.id] : _.map(jobTypes, 'id'),
                    column: ['error_system_count', 'error_algorithm_count', 'error_data_count', 'total_count'],
                    group: null,
                    dataType: 'job-types'
                };

                metricsService.getPlotData(metricsParams).then(function (data) {
                    if (data.results.length > 0) {
                        var data30Days = _.map(data.results, 'values'),
                            data48Hours = formatData(data30Days, 2),
                            data24Hours = formatData(data48Hours, 1);

                        _.forEach(jobTypes, function (jobType) {
                            vm.performanceData.push({
                                job_type: JobType.transformer(jobType),
                                twentyfour_hours: formatColumn(data24Hours, jobType.id),
                                fortyeight_hours: formatColumn(data48Hours, jobType.id),
                                thirty_days: formatColumn(data30Days, jobType.id)
                            });
                        });

                        vm.performanceData = _.sortByOrder(vm.performanceData, [function (d) {
                            if (d.twentyfour_hours.total > 0) {
                                return d.twentyfour_hours.errorTotal / d.twentyfour_hours.total;
                            }
                            return 0;
                        }, 'twentyfour_hours.total'], ['desc', 'desc']);

                        vm.gridOptions.minRowsToShow = vm.performanceData.length;
                        vm.gridOptions.virtualizationThreshold = vm.performanceData.length;
                        vm.gridOptions.data = vm.performanceData;
                        if (!skipSort) {
                            vm.currSortField = vm.jobTypesParams.orderField || 'twentyfour_hours';
                            vm.currSortErrorType = vm.jobTypesParams.orderErrorType || 'errorTotal';
                            if (vm.jobTypesParams.order && vm.jobTypesParams.orderField && vm.jobTypesParams.orderErrorType) {
                                vm.sortBy(vm.jobTypesParams.orderErrorType, vm.jobTypesParams.orderField, vm.jobTypesParams.order);
                            }
                        }
                    }

                    vm.loading = false;
                }).catch(function (error) {
                    vm.loading = false;
                    console.log(error);
                    toastr['error'](error);
                });
            });
        };
        
        initialize();

        $scope.$watch('vm.selectedJobType', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            if (vm.jobTypeValues.length > 1) {
                if (vm.loading) {
                    if (filteredByJobType) {
                        vm.updateJobType(newValue);
                    }
                } else {
                    filteredByJobType = newValue !== 'VIEW ALL';
                    vm.updateJobType(newValue);
                }
            }
        });
    });
})();
