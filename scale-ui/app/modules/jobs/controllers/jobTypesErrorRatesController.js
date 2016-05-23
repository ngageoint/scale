(function () {
    'use strict';
    
    angular.module('scaleApp').controller('jobTypesErrorRatesController', function ($scope, $location, scaleConfig, scaleService, subnavService, jobTypeService, metricsService, gridFactory, JobType, toastr, moment) {
        var vm = this;

        vm.jobTypeParams = {
            page: null,
            page_size: null,
            started: null,
            ended: null,
            name: null,
            category: null,
            order: null
        };

        // check for jobTypeParams in query string, and update as necessary
        _.forEach(_.pairs(vm.jobTypeParams), function (param) {
            var value = _.at($location.search(), param[0]);
            if (value.length > 0) {
                vm.jobTypeParams[param[0]] = value.length > 1 ? value : value[0];
            }
        });

        var started = moment.utc().subtract(30, 'd').toISOString(),
            ended = moment.utc().toISOString(),
            jobTypes = [],
            numDays = moment.utc(ended).diff(moment.utc(started), 'd'),
            filteredByJobType = vm.jobTypeParams.name ? true : false;

        vm.scaleService = scaleService;
        vm.loading = true;
        vm.dates = [];
        vm.performanceData = [];
        vm.jobTypeValues = [];
        vm.selectedJobType = vm.jobTypeParams.name || '';
        vm.gridStyle = '';
        vm.subnavLinks = scaleConfig.subnavLinks.jobs;
        subnavService.setCurrentPath('jobs/errors');

        var defaultColumnDefs = [
            {
                field: 'job_type',
                displayName: 'Job Type',
                cellTemplate: '<div class="ui-grid-cell-contents"><span ng-bind-html="row.entity.job_type.getIcon()"></span> {{ row.entity.job_type.title }} {{ row.entity.job_type.version }}</div>',
                filterHeaderTemplate: '<div class="ui-grid-filter-container"><select class="form-control input-sm" ng-model="grid.appScope.vm.selectedJobType"><option ng-if="grid.appScope.vm.jobTypeValues[$index]" ng-selected="{{ grid.appScope.vm.jobTypeValues[$index].name == grid.appScope.vm.selectedJobType }}" value="{{ grid.appScope.vm.jobTypeValues[$index].name }}" ng-repeat="jobType in grid.appScope.vm.jobTypeValues track by $index">{{ grid.appScope.vm.jobTypeValues[$index].title }} {{ grid.appScope.vm.jobTypeValues[$index].version }}</option></select></div>',
                enableSorting: false
            },
            {
                field: 'twentyfour_hours',
                displayName: '24 Hours',
                enableSorting: false,
                enableFiltering: false,
                headerCellTemplate: 'gridHeader.html',
                cellTemplate: 'gridRow.html'
            },
            {
                field: 'fortyeight_hours',
                displayName: '48 Hours',
                enableSorting: false,
                enableFiltering: false,
                headerCellTemplate: 'gridHeader.html',
                cellTemplate: 'gridRow.html'
            },
            {
                field: 'thirty_days',
                displayName: '30 Days',
                enableSorting: false,
                enableFiltering: false,
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
        
        vm.getPercentageOfTotal = function (errorTotal, total) {
            if (total === 0) {
                return '100%';
            }
            return ((errorTotal / total) * 100).toFixed(0) + '%';
        };

        vm.filterResults = function () {
            _.forEach(_.pairs(vm.jobTypeParams), function (param) {
                $location.search(param[0], param[1]);
            });
            vm.loading = true;
            initialize();
        };

        vm.updateJobType = function (value) {
            vm.jobTypeParams.name = value === 'VIEW ALL' ? null : value;
            if (!vm.loading) {
                vm.filterResults();
            }
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

        var initialize = function () {
            jobTypeService.getJobTypesOnce().then(function (jobTypesData) {
                jobTypes = _.cloneDeep(jobTypesData.results);
                vm.jobTypeValues = _.cloneDeep(jobTypesData.results);
                vm.jobTypeValues.unshift({ name: 'VIEW ALL', title: 'VIEW ALL', version: '', id: 0 });
                vm.gridOptions.totalItems = jobTypesData.count;

                var metricsParams = {
                    page: null,
                    page_size: null,
                    started: started,
                    ended: ended,
                    choice_id: _.map(jobTypes, 'id'),
                    column: ['system_error_count', 'algorithm_error_count', 'data_error_count', 'total_count'],
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

                        vm.performanceData = _.sortByOrder(vm.performanceData, function (d) {
                            if (d.twentyfour_hours.total > 0) {
                                return d.twentyfour_hours.errorTotal / d.twentyfour_hours.total;
                            }
                            return 1;
                        }, ['desc']);

                        vm.gridOptions.data = vm.performanceData;
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
            if (vm.loading) {
                if (filteredByJobType) {
                    vm.updateJobType(newValue);
                }
            } else {
                filteredByJobType = newValue !== 'VIEW ALL';
                vm.updateJobType(newValue);
            }
        });

        angular.element(document).ready(function () {
            // set container heights equal to available page height
            var viewport = scaleService.getViewportSize(),
                offset = scaleConfig.headerOffset,
                gridMaxHeight = viewport.height - offset;

            vm.gridStyle = 'height: ' + gridMaxHeight + 'px; max-height: ' + gridMaxHeight + 'px; overflow-y: auto;';
        });
    });
})();