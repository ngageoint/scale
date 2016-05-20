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

        var started = moment.utc().subtract(3, 'd').toISOString(),
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

        var formatData = function (jobType, systemErrors, dataErrors, algorithmErrors) {
            var currDate = '',
                currSystem = 0,
                currData = 0,
                currAlgorithm = 0,
                currValue = {},
                format = d3.format(',');

            currValue.job_type = JobType.transformer(jobType);
            for (var i = 0; i <= numDays; i++) {
                currDate = moment.utc(started).add(i, 'd').format('YYYY-MM-DD');
                currSystem = _.find(systemErrors.values, { date: currDate, id: jobType.id });
                currData = _.find(dataErrors.values, { date: currDate, id: jobType.id });
                currAlgorithm = _.find(algorithmErrors.values, { date: currDate, id: jobType.id });
                currValue[currDate] = {
                    date: currDate,
                    system: currSystem ? currSystem.value : 0,
                    data: currData ? currData.value : 0,
                    algorithm: currAlgorithm ? currAlgorithm.value : 0
                };
                currValue[currDate].total = parseInt(format(currValue[currDate].system + currValue[currDate].data + currValue[currDate].algorithm));
            }

            return currValue;
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
                    column: ['system_error_count', 'data_error_count', 'algorithm_error_count'],
                    group: null,
                    dataType: 'job-types'
                };

                metricsService.getPlotData(metricsParams).then(function (data) {
                    if (data.results.length > 0) {
                        var currDate = '',
                            systemErrors = _.find(data.results, {column: {title: 'System Error Count'}}),
                            dataErrors = _.find(data.results, {column: {title: 'Data Error Count'}}),
                            algorithmErrors = _.find(data.results, {column: {title: 'Algorithm Error Count'}});

                        _.forEach(jobTypes, function (jobType) {
                            vm.performanceData.push(formatData(jobType, systemErrors, dataErrors, algorithmErrors));
                        });

                        vm.gridOptions.data = vm.performanceData;

                        for (var i = 0; i <= numDays; i++) {
                            currDate = moment.utc(started).add(i, 'd').format('YYYY-MM-DD');
                            vm.gridOptions.columnDefs.push({
                                field: currDate,
                                enableSorting: false,
                                enableFiltering: false,
                                cellTemplate: '<div class="ui-grid-cell-contents">' +
                                '<div ng-show="COL_FIELD.system > 0 || COL_FIELD.data > 0 || COL_FIELD.algorithm > 0">' +
                                '<div class="label label-system" ng-show="COL_FIELD.system > 0">{{ COL_FIELD.system }}</div> ' +
                                '<div class="label" ng-show="COL_FIELD.system === 0">&nbsp;</div> ' +
                                '<div class="label label-data" ng-show="COL_FIELD.data > 0">{{ COL_FIELD.data }}</div> ' +
                                '<div class="label" ng-show="COL_FIELD.data === 0">&nbsp;</div> ' +
                                '<div class="label label-algorithm" ng-show="COL_FIELD.algorithm > 0">{{ COL_FIELD.algorithm }}</div>' +
                                '<div class="label" ng-show="COL_FIELD.algorithm === 0">&nbsp;</div> ' +
                                '</div>' +
                                '<div class="text-center" ng-show="COL_FIELD.system === 0 && COL_FIELD.data === 0 && COL_FIELD.algorithm === 0"><strong>No Errors</strong></div>' +
                                '</div>'
                            });
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