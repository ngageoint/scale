(function () {
    'use strict';

    angular.module('scaleApp').controller('loadController', function($scope, $location, scaleService, stateService, navService, loadService, uiGridConstants, scaleConfig, subnavService, QueueStatus, gridFactory) {
        var vm = this;
        
        vm.loading = true;
        vm.queueStatusError = null;
        vm.queueStatusErrorStatus = null;
        vm.totalQueued = 0;
        vm.subnavLinks = scaleConfig.subnavLinks.load;
        subnavService.setCurrentPath('load/queued');
        
        var jobsParams = stateService.getJobsParams();

        vm.getPage = function (pageNumber, pageSize) {
            vm.loading = true;
            loadService.getQueueStatus(pageNumber - 1, pageSize).then(function (data) {
                var newData = [];
                for (var i = 0; i < vm.gridOptions.paginationPageSize; i++) {
                    newData.push(data.jobs[i]);
                }
                vm.gridOptions.minRowsToShow = newData.length;
                vm.gridOptions.virtualizationThreshold = newData.length;
                vm.gridOptions.data = newData;
            }).catch(function (error) {
                vm.status = 'Unable to load queue status: ' + error.message;
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
                    field: 'job_type.title',
                    displayName: 'Job Type',
                    enableFiltering: false,
                    cellTemplate: '<div class="ui-grid-cell-contents"><span ng-bind-html="row.entity.job_type.getIcon()"></span> {{ row.entity.job_type.title }}</div>'
                },
                { field: 'job_type.version', displayName: 'Version', enableFiltering: false },
                { field: 'highest_priority', enableFiltering: false },
                {
                    field: 'longestQueued',
                    displayName: 'Duration of Longest Queued Job',
                    enableFiltering: false,
                    cellTemplate: '<div class="ui-grid-cell-contents text-right">{{ row.entity.getDuration() }}</div>'
                },
                { field: 'count', enableFiltering: false }
            ];
            vm.gridOptions.data = [];
            vm.gridOptions.onRegisterApi = function (gridApi) {
                //set gridApi on scope
                vm.gridApi = gridApi;
                gridApi.selection.on.rowSelectionChanged($scope, function (row) {
                    stateService.setJobsParams({job_type_id: row.entity.job_type.id, status: 'QUEUED', page: jobsParams.page, page_size: jobsParams.page_size, order: jobsParams.order});
                    $location.path('/jobs');
                });
                vm.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                    vm.getPage(currentPage, pageSize);
                });
            };


            loadService.getQueueStatus(0, vm.gridOptions.paginationPageSize).then(null, null, function (result) {
                if (result.$resolved) {
                    vm.gridOptions.minRowsToShow = result.results.length;
                    vm.gridOptions.virtualizationThreshold = result.results.length;
                    vm.gridOptions.data = result.results;
                    vm.gridOptions.totalItems = result.results.length;
                    vm.totalQueued = _.sum(result.results, 'count');
                    console.log('queue status updated');
                } else {
                    if (result.statusText && result.statusText !== '') {
                        vm.queueStatusErrorStatus = result.statusText;
                    }
                    vm.queueStatusError = 'Unable to retrieve queue status.';
                }
                vm.loading = false
            });

            navService.updateLocation('load');
        };
        initialize();
    });
})();
