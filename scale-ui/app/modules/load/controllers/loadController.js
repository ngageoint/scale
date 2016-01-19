(function () {
    'use strict';

    angular.module('scaleApp').controller('loadController', function($scope, $location, scaleService, navService, loadService, uiGridConstants, scaleConfig, subnavService, QueueStatus, gridFactory) {
        $scope.loading = true;
        $scope.queueStatusError = null;
        $scope.queueStatusErrorStatus = null;
        $scope.totalQueued = 0;
        $scope.gridStyle = '';
        $scope.subnavLinks = scaleConfig.subnavLinks.load;
        subnavService.setCurrentPath('load');

        $scope.getPage = function (pageNumber, pageSize) {
            $scope.loading = true;
            loadService.getQueue(pageNumber - 1, pageSize).then(function (data) {
                var newData = [];
                for (var i = 0; i < $scope.gridOptions.paginationPageSize; i++) {
                    newData.push(data.jobs[i]);
                }
                $scope.gridOptions.data = newData;
            }).catch(function (error) {
                $scope.status = 'Unable to load queue status: ' + error.message;
                console.error($scope.status);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        var initialize = function() {
            $scope.gridOptions = gridFactory.defaultGridOptions();
            $scope.gridOptions.enableSorting = false;
            $scope.gridOptions.columnDefs = [
                    {
                        field: 'job_type_name',
                        displayName: 'Job Type',
                        enableFiltering: false,
                        cellTemplate: '<div class="ui-grid-cell-contents"><span ng-bind-html="row.entity.getIcon()"></span> {{ row.entity.job_type_name }}</div>'
                    },
                    { field: 'job_type_version', enableFiltering: false },
                    { field: 'highest_priority', enableFiltering: false },
                    {
                        field: 'longestQueued',
                        displayName: 'Duration of Longest Queued Job',
                        enableFiltering: false,
                        cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.getDuration() }}</div>'
                    },
                    { field: 'count', enableFiltering: false },
                    { field: 'is_job_type_paused', enableFiltering: false }
                ];
            $scope.gridOptions.data = [];
            $scope.gridOptions.onRegisterApi = function (gridApi) {
                    //set gridApi on scope
                    $scope.gridApi = gridApi;
                    gridApi.selection.on.rowSelectionChanged($scope, function (row) {
                        console.log(row);
                        //$location.path('/jobs').search({job_type_id: row.entity.job_type_id, status: 'RUNNING'});
                    });
                    $scope.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                        $scope.getPage(currentPage, pageSize);
                    });
                };


            loadService.getQueueStatus(0, $scope.gridOptions.paginationPageSize).then(null, null, function (result) {
                if (result.$resolved) {
                    $scope.gridOptions.data = result.queue_status;
                    $scope.gridOptions.totalItems = result.queue_status.length;
                    $scope.totalQueued = _.sum(result.queue_status, 'count');
                    console.log('queue status updated');
                } else {
                    if (result.statusText && result.statusText !== '') {
                        $scope.queueStatusErrorStatus = result.statusText;
                    }
                    $scope.queueStatusError = 'Unable to retrieve queue status.';
                }
                $scope.loading = false
            });

            navService.updateLocation('queue');
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
