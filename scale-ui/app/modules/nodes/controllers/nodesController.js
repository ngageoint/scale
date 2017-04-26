(function () {
    'use strict';

    angular.module('scaleApp').controller('nodesController', function($scope, $location, $timeout, $uibModal, navService, nodeService, stateService, userService, gridFactory, toastr, poller) {
        var vm = this;

        vm.nodesParams = stateService.getNodesParams();

        vm.stateService = stateService;
        vm.nodeStatus = [];
        vm.loading = true;
        vm.loadingStatus = true;
        vm.readonly = true;
        vm.nodesError = null;
        vm.nodesErrorStatus = null;
        vm.statusError = null;
        vm.statusErrorStatus = null;
        vm.actionClicked = false;
        vm.gridOptions = gridFactory.defaultGridOptions();
        vm.gridOptions.paginationCurrentPage = vm.nodesParams.page || 1;
        vm.gridOptions.paginationPageSize = vm.nodesParams.page_size || vm.gridOptions.paginationPageSize;
        vm.gridOptions.data = [];

        $scope.pauseReason = '';

        var filteredByOrder = vm.nodesParams.order ? true : false;

        vm.colDefs = [
            {
                field: 'hostname',
                displayName: 'Hostname',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents"><div class="pull-right" ng-show="!grid.appScope.vm.readonly && grid.appScope.vm.nodeStatus.length > 0"><button class="btn btn-xs btn-default" ng-click="grid.appScope.vm.pauseNode(row.entity)"><i class="fa" ng-class="{ \'fa-pause\': !row.entity.is_paused, \'fa-play\': row.entity.is_paused }"></i></button></div> {{ row.entity.hostname }}</div>'
            },
            {
                field: 'is_online',
                displayName: 'Status',
                enableFiltering: false,
                enableSorting: false,
                cellTemplate: '<div class="ui-grid-cell-contents" ng-show="row.entity.status"><span ng-bind-html="row.entity.statusLabel"></span></div>'
            },
            {
                field: 'id',
                displayName: 'Statistics',
                enableFiltering: false,
                enableSorting: false,
                cellTemplate: '<div class="ui-grid-cell-contents" ng-show="row.entity.status">{{ row.entity.status.getCellError() }} / {{ row.entity.status.getCellTotal() }}</div>'
            },
            {
                field: 'id',
                displayName: 'Current Jobs',
                enableFiltering: false,
                enableSorting: false,
                cellTemplate: '<div class="ui-grid-cell-contents" ng-show="row.entity.status"><span ng-bind-html="row.entity.status.getCellJobs()"></span></div>'
            }
        ];

        vm.gridOptions.columnDefs = vm.colDefs;

        vm.pauseNode = function (entity) {
            $scope.pauseReason = '';
            vm.actionClicked = true;
            var id = entity.id;
            var nodeStatus = _.find(vm.nodeStatus, { node: { id: id } });
            var curr_state = entity.is_paused;

            $scope.updateReason = function (value) {
                $scope.pauseReason = value;
            };

            var pauseResume = function () {

                nodeStatus.pauseResumeCell($scope.pauseReason).then(function (result) {
                    var node = _.find(vm.gridOptions.data, { id: result.id });
                    entity.is_paused = result.is_paused;
                    nodeStatus.node.is_paused = entity.is_paused;
                    entity.statusLabel = vm.getStatusLabel(nodeStatus);
                    if (curr_state === entity.is_paused) {
                        toastr.warning(entity.hostname + ' Status Unchanged');
                    } else if (entity.is_paused) {
                        toastr.info(node.hostname + ' Paused');
                    } else {
                        toastr.info(node.hostname + ' Resumed');
                    }
                });
            };

            // only prompt for reason when pausing (not resuming)
            if (!nodeStatus.node.is_paused && !nodeStatus.node.is_paused_errors) {
                var modalInstance = $uibModal.open({
                    animation: true,
                    templateUrl: 'pauseDialog.html',
                    scope: $scope
                });

                modalInstance.result.then(function () {
                    pauseResume();
                });
            } else {
                pauseResume();
            }
        };

        vm.getStatusLabel = function (status) {
            var online = status.is_online ? '<span class="label label-online">Online</span>' : '<span class="label label-offline">Offline</span>';
            var paused = status.node.is_paused ? '<span class="label label-paused">Paused</span>' : '';
            var pausedErrors = status.node.is_paused_errors ? '<span class="label label-paused-errors">Paused with Errors</span>' : '';
            return online + ' ' + paused + ' ' + pausedErrors;
        };

        vm.filterResults = function () {
            poller.stopAll();
            stateService.setNodesParams(vm.nodesParams);
            vm.loading = true;
            getNodes();
        };

        vm.updateColDefs = function () {
            vm.gridOptions.columnDefs = gridFactory.applySortConfig(vm.colDefs, vm.nodesParams);
        };

        vm.updateNodeOrder = function (sortArr) {
            vm.nodesParams.order = sortArr.length > 0 ? sortArr : null;
            filteredByOrder = sortArr.length > 0;
            vm.filterResults();
        };

        vm.gridOptions.onRegisterApi = function (gridApi) {
            //set gridApi on scope
            vm.gridApi = gridApi;
            vm.gridApi.selection.on.rowSelectionChanged($scope, function (row) {
                if (vm.actionClicked) {
                    vm.actionClicked = false;
                } else {
                    $location.search({});
                    $location.path('/nodes/' + row.entity.id);
                }
            });
            vm.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                vm.nodesParams.page = currentPage;
                vm.nodesParams.page_size = pageSize;
                vm.filterResults();
            });
            vm.gridApi.core.on.sortChanged($scope, function (grid, sortColumns) {
                _.forEach(vm.gridApi.grid.columns, function (col) {
                    col.colDef.sort = col.sort;
                });
                stateService.setNodesColDefs(vm.gridApi.grid.options.columnDefs);
                var sortArr = [];
                _.forEach(sortColumns, function (col) {
                    sortArr.push(col.sort.direction === 'desc' ? '-' + col.field : col.field);
                });
                vm.updateNodeOrder(sortArr);
            });
        };

        var getNodes = function () {
            nodeService.getNodes(vm.nodesParams).then(null, null, function (data) {
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
            stateService.setNodesParams(vm.nodesParams);
            vm.updateColDefs();
            var user = userService.getUserCreds();
            vm.readonly = !(user && user.is_admin);
            getNodes();
            getNodeStatus();
            navService.updateLocation('nodes');
        };

        initialize();

        $scope.$watchCollection('vm.stateService.getNodesColDefs()', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            vm.colDefs = newValue;
            vm.updateColDefs();
        });

        $scope.$watchCollection('vm.stateService.getNodesParams()', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            vm.nodesParams = newValue;
            vm.updateColDefs();
        });

        $scope.$watchCollection('vm.nodeStatus', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            _.forEach(vm.gridOptions.data, function (node) {
                var status = _.find(newValue, { node: { id: node.id } });
                if (status) {
                    node.status = status;
                    console.log('status changed');
                    node.statusLabel = vm.getStatusLabel(status);
                }
            });
        });
    });
})();
