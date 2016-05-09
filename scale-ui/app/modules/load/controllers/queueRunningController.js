(function(){
    'use strict';

    angular.module('scaleApp').controller('queueRunningController', function($scope, $location, scaleService, navService, jobService, gridFactory, uiGridConstants, scaleConfig, subnavService) {
        $scope.loading = true;
        $scope.runningJobsError = null;
        $scope.runningJobsErrorStatus = null;
        $scope.totalRunning = 0;
        $scope.gridStyle = '';
        $scope.subnavLinks = scaleConfig.subnavLinks.load;
        subnavService.setCurrentPath('load/running');

        $scope.getPage = function (pageNumber, pageSize){
            $scope.loading = true;
            jobService.getRunningJobsOnce(pageNumber - 1, pageSize).then(function (data) {
                var newData = [];
                for(var i = 0; i < $scope.gridOptions.paginationPageSize; i++){
                    newData.push(data.results[i]);
                }
                $scope.gridOptions.data = newData;
            }).catch(function(error){
                $scope.status = 'Unable to load queue running status: ' + error.message;
                console.error($scope.status);
            }).finally(function(){
                $scope.loading = false;
            });
        };

        var initialize = function() {
            $scope.gridOptions = gridFactory.defaultGridOptions();
            $scope.gridOptions.enableSorting = false;
            $scope.gridOptions.columnDefs = [
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
            $scope.gridOptions.data = [];
            $scope.gridOptions.onRegisterApi = function (gridApi) {
                // set gridApi on scope
                $scope.gridApi = gridApi;
                gridApi.selection.on.rowSelectionChanged($scope, function (row) {
                    $scope.$apply(function(){
                        $location.path('/jobs').search({job_type_id: row.entity.job_type.id, status: 'RUNNING'});
                    });
                });
                $scope.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                    $scope.getPage(currentPage, pageSize);
                });
            };

            jobService.getRunningJobs(0, $scope.gridOptions.paginationPageSize).then(null, null, function (data) {
                if (data.$resolved) {
                    $scope.gridOptions.data = data.results;
                    $scope.gridOptions.totalItems = data.results.length;
                    $scope.totalRunning = _.sum(data.results, 'count');
                    console.log('running jobs updated');
                } else {
                    if (data.statusText && data.statusText !== '') {
                        $scope.runningJobsErrorStatus = data.statusText;
                    }
                    $scope.runningJobsError = 'Unable to retrieve running jobs.';
                }
                $scope.loading = false;
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
