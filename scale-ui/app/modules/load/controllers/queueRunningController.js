(function () {
    'use strict';

    angular.module('scaleApp').controller('queueRunningController', function($scope, $location, scaleService, stateService, navService, jobService, gridFactory, uiGridConstants, scaleConfig, subnavService) {
        var vm = this;
        
        vm.loading = true;
        vm.runningJobsError = null;
        vm.runningJobsErrorStatus = null;
        vm.totalRunning = 0;
        vm.subnavLinks = scaleConfig.subnavLinks.load;
        subnavService.setCurrentPath('load/running');

        var jobsParams = stateService.getJobsParams();

        vm.getPage = function (pageNumber, pageSize){
            vm.loading = true;
            jobService.getRunningJobsOnce(pageNumber - 1, pageSize).then(function (data) {
                var newData = [];
                for(var i = 0; i < vm.gridOptions.paginationPageSize; i++){
                    newData.push(data.results[i]);
                }
                vm.gridOptions.minRowsToShow = newData.length;
                vm.gridOptions.virtualizationThreshold = newData.length;
                vm.gridOptions.data = newData;
            }).catch(function (error) {
                vm.status = 'Unable to load queue running status: ' + error.message;
                console.error(vm.status);
            }).finally(function () {
                vm.loading = false;
            });
        };

        var initialize = function () {
            vm.gridOptions = gridFactory.defaultGridOptions();
            vm.gridOptions.enableSorting = false;
            vm.gridOptions.columnDefs = [
                {
                    field: 'title',
                    displayName: 'Job Type',
                    enableFiltering: false,
                    cellTemplate: '<div class="ui-grid-cell-contents"><span ng-bind-html="row.entity.getIcon()"></span> {{ row.entity.job_type.title }}</div>'
                },
                {field: 'job_type.version', displayName: 'Version', enableFiltering: false},
                {field: 'count', displayName: 'Number of Jobs', enableFiltering: false},
                {
                    field: 'longestRunning',
                    displayName: 'Duration of Longest Running Job',
                    enableFiltering: false,
                    cellTemplate: '<div class="ui-grid-cell-contents text-right">{{ row.entity.getDuration() }}</div>'
                }
            ];
            vm.gridOptions.data = [];
            vm.gridOptions.onRegisterApi = function (gridApi) {
                // set gridApi on scope
                vm.gridApi = gridApi;
                gridApi.selection.on.rowSelectionChanged($scope, function (row) {
                    stateService.setJobsParams({job_type_id: row.entity.job_type.id, status: 'RUNNING', page: jobsParams.page, page_size: jobsParams.page_size, order: jobsParams.order});
                    $location.path('/jobs');
                });
                vm.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                    vm.getPage(currentPage, pageSize);
                });
                vm.gridApi.core.on.rowsRendered($scope, function () {
                    if (gridApi.grid.renderContainers.body.visibleRowCache.length === 0) { return; }
                    $('.ui-grid-pager-panel').remove();
                });
            };

            jobService.getRunningJobs(0, vm.gridOptions.paginationPageSize).then(null, null, function (data) {
                if (data.$resolved) {
                    vm.gridOptions.minRowsToShow = data.results.length;
                    vm.gridOptions.virtualizationThreshold = data.results.length;
                    vm.gridOptions.data = data.results;
                    vm.gridOptions.totalItems = data.results.length;
                    vm.totalRunning = _.sum(data.results, 'count');
                    console.log('running jobs updated');
                } else {
                    if (data.statusText && data.statusText !== '') {
                        vm.runningJobsErrorStatus = data.statusText;
                    }
                    vm.runningJobsError = 'Unable to retrieve running jobs.';
                }
                vm.loading = false;
            });
            navService.updateLocation('load');
        };
        initialize();
    });
})();
