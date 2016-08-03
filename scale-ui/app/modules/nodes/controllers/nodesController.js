(function () {
    'use strict';

    angular.module('scaleApp').controller('nodesController', function($scope, $location, $timeout, navService, nodeService, stateService, userService, gridFactory) {
        var vm = this;

        vm.nodeStatus = [];
        vm.loading = true;
        vm.loadingStatus = true;
        vm.readonly = true;
        vm.nodesError = null;
        vm.nodesErrorStatus = null;
        vm.statusError = null;
        vm.statusErrorStatus = null;
        vm.nodeStatusParams = stateService.getNodeStatusParams();
        vm.actionClicked = false;
        vm.gridOptions = gridFactory.defaultGridOptions();
        vm.gridOptions.paginationCurrentPage = vm.nodeStatusParams.page || 1;
        vm.gridOptions.paginationPageSize = vm.nodeStatusParams.page_size || vm.gridOptions.paginationPageSize;
        vm.gridOptions.data = [];

        vm.colDefs = [
            {
                field: 'hostname',
                displayName: 'Hostname',
                enableFiltering: false,
                enableSorting: false,
                cellTemplate: '<div class="ui-grid-cell-contents"><div class="pull-right" ng-show="!grid.appScope.vm.readonly && grid.appScope.vm.nodeStatus.length > 0"><button class="btn btn-xs btn-default" ng-click="grid.appScope.vm.pauseNode(row.entity.id)"><i class="fa fa-pause"></i></button></div> {{ row.entity.hostname }}</div>'
            },
            {
                field: 'is_online',
                displayName: 'Status',
                enableFiltering: false,
                enableSorting: false,
                cellTemplate: '<div class="ui-grid-cell-contents" ng-show="row.entity.status"><span ng-bind-html="row.entity.statusLabel"></span></div>'
            },
            {
                field: 'created',
                displayName: 'Created (Z)',
                enableFiltering: false,
                enableSorting: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.created }}</div>'
            },
            {
                field: 'last_modified',
                displayName: 'Last Modified (Z)',
                enableFiltering: false,
                enableSorting: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.last_modified }}</div>'
            }
        ];

        vm.gridOptions.columnDefs = vm.colDefs;

        vm.pauseNode = function (id) {
            vm.actionClicked = true;
            var node = _.find(vm.nodeStatus, { node: { id: id } });
            node.pauseResumeCell();
        };

        vm.getStatusLabel = function (status) {
            var online = status.is_online ? '<span class="label label-online">Online</span>' : '<span class="label label-offline">Offline</span>';
            var paused = status.node.is_paused ? '<span class="label label-paused">Paused</span>' : '';
            var pausedErrors = status.node.is_paused_errors ? '<span class="label label-paused-errors">Paused with Errors</span>' : '';
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

        var getNodes = function () {
            nodeService.getNodes().then(null, null, function (data) {
                if (data.$resolved) {
                    vm.nodesError = null;
                    vm.gridOptions.totalItems = data.count;
                    vm.gridOptions.minRowsToShow = data.results.length;
                    vm.gridOptions.virtualizationThreshold = data.results.length;
                    vm.gridOptions.data = data.results;
                } else {
                    if (data.statusText && data.statusText !== '') {
                        vm.nodesErrorStatus = data.statusText;
                    }
                    vm.nodesError = 'Unable to retrieve nodes.';
                }
                vm.loading = false;
            })
        };

        var getNodeStatus = function () {
            nodeService.getNodeStatus(null, null, 'PT3H', null).then(null, null, function (data) {
                if (data.$resolved) {
                    vm.statusError = null;
                    vm.nodeStatus = data.results;
                } else {
                    if (data.statusText && data.statusText !== '') {
                        vm.statusErrorStatus = data.statusText;
                    }
                    vm.statusError = 'Unable to retrieve node status.';
                }
                vm.loadingStatus = false;
            });
        };

        var initialize = function () {
            var user = userService.getUserCreds();
            vm.readonly = !(user && user.is_admin);
            getNodes();
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

        $scope.$watchCollection('vm.nodeStatus', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            _.forEach(vm.gridOptions.data, function (node) {
                var status = _.find(newValue, { node: { id: node.id } });
                if (status) {
                    node.status = status;
                    node.statusLabel = vm.getStatusLabel(status);
                }
            });
        });
    });
})();