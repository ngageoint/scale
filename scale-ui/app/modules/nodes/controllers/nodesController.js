(function () {
    'use strict';

    angular.module('scaleApp').controller('nodesController', function($scope, $location, $timeout, $uibModal, navService, nodeService, nodeUpdateService, statusService, stateService, userService, jobTypeService, gridFactory, toastr, poller) {
        var vm = this;

        vm.nodesParams = stateService.getNodesParams();

        vm.stateService = stateService;
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
        var jobTypes = null;

        vm.colDefs = [
            {
                field: 'hostname',
                displayName: 'Hostname',
                enableFiltering: false,
                width: '25%',
                cellTemplate: '<div class="ui-grid-cell-contents"><div class="pull-right" ng-show="!grid.appScope.vm.readonly"><button class="btn btn-xs btn-default" ng-click="grid.appScope.vm.pauseNode(row.entity)"><i class="fa" ng-class="{ \'fa-pause\': row.entity.state.name !== \'PAUSED\', \'fa-play\': row.entity.state.name === \'PAUSED\' }"></i></button></div> {{ row.entity.hostname }}</div>'
            },
            {
                field: 'state',
                displayName: 'State',
                enableFiltering: false,
                enableSorting: false,
                width: '10%',
                cellTemplate: '<div class="ui-grid-cell-contents"><div class="pull-right"><span class="fa fa-exclamation-triangle error" ng-show="row.entity.errors.length > 0" tooltip-append-to-body="true" uib-tooltip="{{ row.entity.errors.length === 1 ? row.entity.errors[0].description : row.entity.errors.length + \' Errors\' }}"></span> <span class="fa fa-exclamation-triangle warning" ng-show="row.entity.warnings.length > 0" tooltip-append-to-body="true" uib-tooltip="{{ row.entity.warnings.length === 1 ? row.entity.warnings[0].description : row.entity.warnings.length + \' Warnings\' }}"></span></div><span ng-bind-html="row.entity.state.title" tooltip-append-to-body="true" uib-tooltip="{{ row.entity.state.description }}"></span></div>'
            },
            {
                field: 'job_executions',
                displayName: 'Job Executions',
                enableFiltering: false,
                enableSorting: false,
                width: '15%',
                cellTemplate: 'jobExecutions.html',
                headerCellTemplate: 'jobExecutionsHeader.html'
            },
            {
                field: 'running_jobs',
                displayName: 'Running Jobs',
                enableFiltering: false,
                enableSorting: false,
                cellTemplate: 'runningJobs.html'
            }
            // {
            //     field: 'id',
            //     displayName: 'Statistics',
            //     enableFiltering: false,
            //     enableSorting: false,
            //     cellTemplate: '<div class="ui-grid-cell-contents" ng-show="row.entity.status">{{ row.entity.status.getCellError() }} / {{ row.entity.status.getCellTotal() }}</div>'
            // },
            // {
            //     field: 'id',
            //     displayName: 'Current Jobs',
            //     enableFiltering: false,
            //     enableSorting: false,
            //     cellTemplate: '<div class="ui-grid-cell-contents" ng-show="row.entity.status"><span ng-bind-html="row.entity.status.getCellJobs()"></span></div>'
            // }
        ];

        vm.gridOptions.columnDefs = vm.colDefs;

        vm.pauseNode = function (entity) {
            $scope.pauseReason = '';
            vm.actionClicked = true;

            $scope.updateReason = function (value) {
                $scope.pauseReason = value;
            };

            var pauseResume = function () {
                var isPaused = entity.state.name !== 'PAUSED';
                nodeUpdateService.updateNode(entity, { pause_reason: $scope.pauseReason, is_paused: isPaused, is_active: entity.is_active }).then(function (result) {
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
            if (entity.state.name !== 'PAUSED') {
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

        var getRunningJobs = function (entity) {
            var runningJobs = [];
            _.forEach(entity.job_executions.running.by_job_type, function (jobType) {
                runningJobs.push({
                    jobType: _.find(jobTypes, { id: jobType.job_type_id }),
                    count: jobType.count
                });
            });
            return runningJobs;
        };

        var getNodes = function () {
            statusService.getStatus(true).then(null, null, function (data) {
                if (data.$resolved) {
                    vm.nodesError = null;
                    vm.nodes = _.filter(data.nodes, { is_active: true });
                    var order = $location.search().order;
                    if (order) {
                        var fieldArr = [];
                        var directionArr = [];
                        _.forEach(order, function (o) {
                            fieldArr.push(_.startsWith(o, '-') ? _.tail(o).join('') : o);
                            directionArr.push(_.startsWith(order, '-') ? 'desc' : 'asc');
                        });
                        console.log(fieldArr + ', ' + directionArr);
                        vm.nodes = _.sortByOrder(vm.nodes, fieldArr, directionArr);
                    }
                    _.forEach(vm.nodes, function (node) {
                        node.running_jobs = getRunningJobs(node);
                    });
                    vm.gridOptions.totalItems = data.nodes.length;
                    vm.gridOptions.minRowsToShow = data.nodes.length;
                    vm.gridOptions.virtualizationThreshold = data.nodes.length;
                    vm.gridOptions.data = vm.nodes;
                } else {
                    if (data.statusText && data.statusText !== '') {
                        vm.nodesErrorStatus = data.statusText;
                    }
                    vm.nodesError = 'Unable to retrieve nodes.';
                }
                vm.loading = false;
            });
        };

        var initialize = function () {
            jobTypeService.getJobTypesOnce().then(function (data) {
                jobTypes = data.results;
                getNodes();
            });
            stateService.setNodesParams(vm.nodesParams);
            vm.updateColDefs();
            var user = userService.getUserCreds();
            vm.readonly = !(user && user.is_admin);
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

        $scope.$watchCollection('vm.nodes', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            vm.gridOptions.data = vm.nodes;
            // _.forEach(vm.gridOptions.data, function (node) {
            //     var status = _.find(newValue, { node: { id: node.id } });
            //     if (status) {
            //         node.status = status;
            //         console.log('status changed');
            //         node.statusLabel = vm.getStatusLabel(status);
            //     }
            // });
        });
    });
})();
