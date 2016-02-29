(function () {
    'use strict';

    angular.module('scaleApp').controller('jobExecutionsController', function($scope, $location, navService, statsService, jobExecutionService, jobTypeService, uiGridConstants, scaleConfig, subnavService) {

        $scope.jobExecutions = [];
        $scope.loading = true;
        $scope.jobTypeValues = [];
        $scope.selectedJobType = '';
        $scope.jobStatus = scaleConfig.jobStatus;
        $scope.selectedJobStatus = '';
        $scope.subnavLinks = scaleConfig.subnavLinks.jobs;
        subnavService.setCurrentPath('jobs/executions');

        var gridFilter = {},
            gridPageNumber = 1;

        $scope.gridOptions = {
            enableRowSelection: true,
            enableRowHeaderSelection: false,
            enableHorizontalScrollbar: uiGridConstants.scrollbars.NEVER,
            multiSelect: false,
            enableFiltering: true,
            useExternalFiltering: true,
            enableSorting: true,
            minRowsToShow: 17,
            paginationPageSizes: [25,50,75],
            paginationPageSize: 25,
            useExternalPagination: true,
            columnDefs: [
                {
                    field: 'jobTypeId',
                    displayName: 'Job Type',
                    cellTemplate: '<div class="ui-grid-cell-contents"><span ng-bind-html="row.entity.getIcon()"></span> {{ row.entity.job.jobType.title }}</div>',
                    filterHeaderTemplate: '<div class="ui-grid-filter-container"><select class="form-control input-sm" ng-model="grid.appScope.selectedJobType"><option value="{{ grid.appScope.jobTypeValues[$index].id }}" ng-repeat="jobType in grid.appScope.jobTypeValues track by $index">{{ grid.appScope.jobTypeValues[$index].name }} {{ grid.appScope.jobTypeValues[$index].version }}</option></select>'
                },
                { field: 'created', enableFiltering: false, cellFilter: 'date:\'yyyy-MM-dd HH:mm:ss\'' },
                { field: 'lastModified', enableFiltering: false, cellFilter: 'date:\'yyyy-MM-dd HH:mm:ss\'' },
                {
                    field: 'status',
                    filterHeaderTemplate: '<div class="ui-grid-filter-container"><select class="form-control input-sm" ng-model="grid.appScope.selectedJobStatus"><option ng-repeat="status in grid.appScope.jobStatus track by $index">{{ status.toUpperCase() }}</option></select>'
                },
                { field: 'id', displayName: 'ID', enableFiltering: false }
            ],
            data: [],
            onRegisterApi: function (gridApi) {
                //set gridApi on scope
                $scope.gridApi = gridApi;
                $scope.gridApi.selection.on.rowSelectionChanged($scope, function (row) {
                    $scope.$apply(function () {
                        //$location.path('/jobexecutions/' + row.entity.id);
                        console.log(row);
                    });
                });
                $scope.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                    $scope.getPage(currentPage, pageSize);
                });
            }
        };

        $scope.$watch('selectedJobType', function (value) {
            if (!$scope.loading) {
                gridFilter.jobTypeId = value;
                $scope.getPage(gridPageNumber, $scope.gridOptions.paginationPageSize, gridFilter);
            }
        });

        $scope.$watch('selectedJobStatus', function (value) {
            if (!$scope.loading) {
                gridFilter.jobStatus = value;
                $scope.getPage(gridPageNumber, $scope.gridOptions.paginationPageSize, gridFilter);
            }
        });

        $scope.getPage = function (pageNumber, pageSize) {
            $scope.loading = true;
            gridPageNumber = pageNumber;
            jobExecutionService.getJobExecutions(pageNumber, pageSize, gridFilter).then(function (data) {
                var newData = [];
                for (var i = 0; i < $scope.gridOptions.paginationPageSize; i++) {
                    if (data.executions[i]) {
                        newData.push(data.executions[i]);
                    }
                }
                $scope.gridOptions.data = newData;
                $scope.gridOptions.totalItems = data.count;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        var getJobExecutions = function () {
            jobExecutionService.getJobExecutions(gridPageNumber, $scope.gridOptions.paginationPageSize, gridFilter).then(function (data) {
                window.localStorage['scale-jobexecutions-time'] = moment.utc().toISOString();
                window.localStorage['scale-jobexecutions'] = JSON.stringify(data);
                $scope.gridOptions.totalItems = data.count;
                $scope.gridOptions.data = data.executions;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                getJobTypes();
            });
        };

        var getJobTypes = function () {
            jobTypeService.getJobTypesOnce().then(function (data) {
                $scope.jobTypeValues = data.results;
                $scope.jobTypeValues.unshift({ name: '', version: '', id: null });
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        var initialize = function() {
            getJobExecutions();
            navService.updateLocation('jobs');
        };
        initialize();
    });
})();