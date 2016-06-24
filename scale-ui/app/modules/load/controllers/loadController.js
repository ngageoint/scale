(function () {
    'use strict';

    angular.module('scaleApp').controller('loadController', function($scope, $location, scaleService, stateService, navService, loadService, uiGridConstants, scaleConfig, subnavService, QueueStatus, gridFactory) {
        $scope.loading = true;
        $scope.queueStatusError = null;
        $scope.queueStatusErrorStatus = null;
        $scope.totalQueued = 0;
        $scope.subnavLinks = scaleConfig.subnavLinks.load;
        subnavService.setCurrentPath('load/queued');
        
        var jobsParams = stateService.getJobsParams();

        $scope.getPage = function (pageNumber, pageSize) {
            $scope.loading = true;
            loadService.getQueueStatus(pageNumber - 1, pageSize).then(function (data) {
                var newData = [];
                for (var i = 0; i < $scope.gridOptions.paginationPageSize; i++) {
                    newData.push(data.jobs[i]);
                }
                $scope.gridOptions.minRowsToShow = newData.length;
                $scope.gridOptions.virtualizationThreshold = newData.length;
                $scope.gridOptions.data = newData;
            }).catch(function (error) {
                $scope.status = 'Unable to load queue status: ' + error.message;
                console.error($scope.status);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        var initialize = function () {
            $scope.gridOptions = gridFactory.defaultGridOptions();
            $scope.gridOptions.enableSorting = false;
            $scope.gridOptions.columnDefs = [
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
            $scope.gridOptions.data = [];
            $scope.gridOptions.onRegisterApi = function (gridApi) {
                    //set gridApi on scope
                    $scope.gridApi = gridApi;
                    gridApi.selection.on.rowSelectionChanged($scope, function (row) {
                        $scope.$apply(function () {
                            stateService.setJobsParams({job_type_id: row.entity.job_type.id, status: 'QUEUED', page: jobsParams.page, page_size: jobsParams.page_size, order: jobsParams.order});
                            $location.path('/jobs');
                        });
                    });
                    $scope.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                        $scope.getPage(currentPage, pageSize);
                    });
                };


            loadService.getQueueStatus(0, $scope.gridOptions.paginationPageSize).then(null, null, function (result) {
                if (result.$resolved) {
                    $scope.gridOptions.minRowsToShow = result.results.length;
                    $scope.gridOptions.virtualizationThreshold = result.results.length;
                    $scope.gridOptions.data = result.results;
                    $scope.gridOptions.totalItems = result.results.length;
                    $scope.totalQueued = _.sum(result.results, 'count');
                    console.log('queue status updated');
                } else {
                    if (result.statusText && result.statusText !== '') {
                        $scope.queueStatusErrorStatus = result.statusText;
                    }
                    $scope.queueStatusError = 'Unable to retrieve queue status.';
                }
                $scope.loading = false
            });

            navService.updateLocation('load');
        };
        initialize();

        angular.element(document).ready(function () {
            // set container heights equal to available page height
            var viewport = scaleService.getViewportSize(),
                offset = scaleConfig.headerOffset,
                gridMaxHeight = viewport.height - offset;

            $scope.gridStyle = 'height: ' + gridMaxHeight + 'px; max-height: ' + gridMaxHeight + 'px; overflow-y: auto;';
        });
    });
})();
