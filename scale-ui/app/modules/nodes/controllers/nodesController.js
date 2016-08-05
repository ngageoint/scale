(function () {
    'use strict';

    angular.module('scaleApp').controller('nodesController', function($scope, $location, $timeout, navService, nodeService, stateService, userService, gridFactory) {
        var vm = this;

        vm.loading = true;
        vm.readonly = true;
        vm.nodeStatusParams = stateService.getNodeStatusParams();
        vm.actionClicked = false;
        vm.gridOptions = gridFactory.defaultGridOptions();
        vm.gridOptions.paginationCurrentPage = vm.nodeStatusParams.page || 1;
        vm.gridOptions.paginationPageSize = vm.nodeStatusParams.page_size || vm.gridOptions.paginationPageSize;
        vm.gridOptions.data = [];

        vm.colDefs = [
            {
                field: 'node.hostname',
                displayName: 'Hostname',
                enableFiltering: false,
                enableSorting: false,
                cellTemplate: '<div class="ui-grid-cell-contents"><div class="pull-right"><button ng-show="!grid.appScope.vm.readonly" class="btn btn-xs btn-default" ng-click="grid.appScope.vm.pauseNode(row.entity)"><i class="fa fa-pause"></i></button></div> {{ row.entity.node.hostname }}</div>'
            },
            {
                field: 'node.is_online',
                displayName: 'Status',
                enableFiltering: false,
                enableSorting: false,
                cellTemplate: '<div class="ui-grid-cell-contents"><span ng-bind-html="grid.appScope.vm.getStatusLabel(row.entity.is_online, row.entity.node.is_paused, row.entity.node.is_paused_errors)"></span></div>'
            },
            {
                field: 'node.created',
                displayName: 'Created (Z)',
                enableFiltering: false,
                enableSorting: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.node.created }}</div>'
            },
            {
                field: 'node.last_modified',
                displayName: 'Last Modified (Z)',
                enableFiltering: false,
                enableSorting: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.node.last_modified }}</div>'
            }
        ];

        vm.gridOptions.columnDefs = vm.colDefs;

        vm.pauseNode = function (node) {
            vm.actionClicked = true;
            node.pauseResumeCell();
        };

        vm.getStatusLabel = function (is_online, is_paused, is_paused_errors) {
            var online = is_online ? '<span class="label label-online">Online</span>' : '<span class="label label-offline">Offline</span>';
            var paused = is_paused ? '<span class="label label-paused">Paused</span>' : '';
            var pausedErrors = is_paused_errors ? '<span class="label label-paused-errors">Paused with Errors</span>' : '';
            return online + ' ' + paused + ' ' + pausedErrors;
        };

        vm.filterResults = function () {
            stateService.setNodeStatusParams(vm.nodeStatusParams);
            vm.loading = true;
            getNodeStatus();
        };

        vm.gridOptions.onRegisterApi = function (gridApi) {
            //set gridApi on scope
            vm.gridApi = gridApi;
            vm.gridApi.selection.on.rowSelectionChanged($scope, function (row) {
                if (vm.actionClicked) {
                    vm.actionClicked = false;
                } else {
                    $location.path('/nodes/' + row.entity.id);
                }
            });
            vm.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                vm.nodeStatusParams.page = currentPage;
                vm.nodeStatusParams.page_size = pageSize;
                vm.filterResults();
            });
        };

        var getNodeStatus = function () {
            nodeService.getNodeStatus(null, null, 'PT' + vm.hours + 'H', null).then(null, null, function (data) {
                if (data.$resolved) {
                    vm.error = null;
                    vm.gridOptions.totalItems = data.count;
                    vm.gridOptions.minRowsToShow = data.results.length;
                    vm.gridOptions.virtualizationThreshold = data.results.length;
                    vm.gridOptions.data = data.results;
                } else {
                    if (data.statusText && data.statusText !== '') {
                        vm.errorStatus = data.statusText;
                    }
                    vm.error = 'Unable to retrieve nodes.';
                }
                vm.loading = false;
            });
        };

        var initialize = function () {
            var user = userService.getUserCreds();
            vm.readonly = !(user && user.is_admin);
            getNodeStatus();
            navService.updateLocation('nodes');
        };

        initialize();

        $scope.$watchCollection('vm.stateService.getJobsParams()', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            vm.nodeStatusParams = newValue;
        });
    });
})();