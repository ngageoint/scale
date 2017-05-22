(function () {
    'use strict';

    angular.module('scaleApp').controller('nodesController', function($scope, $location, $timeout, $uibModal, navService, nodeService, nodeUpdateService, statusService, stateService, userService, jobTypeService, gridFactory, toastr, poller) {
        var vm = this;

        vm.nodesParams = stateService.getNodesParams();

        vm.stateService = stateService;
        vm.loading = true;
        vm.loadingStatus = true;
        vm.readonly = true;
        vm.actionClicked = false;
        vm.gridOptions = gridFactory.defaultGridOptions();
        vm.gridOptions.data = [];
        vm.showActive = vm.nodesParams.active === 'true';

        $scope.pauseReason = '';

        var allNodes = [];
        var filteredByOrder = vm.nodesParams.order ? true : false;
        var jobTypes = null;

        vm.colDefs = [
            {
                field: 'hostname',
                displayName: 'Hostname',
                enableFiltering: false,
                width: '25%',
                cellTemplate: 'hostname.html'
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
        ];

        vm.gridOptions.columnDefs = vm.colDefs;

        vm.toggleActive = function (entity) {
            vm.actionClicked = true;
            var isActive = !entity.is_active;
            nodeUpdateService.updateNode(entity, { pause_reason: '', is_paused: entity.is_paused, is_active: isActive }).then(function (result) {
                var node = _.find(vm.gridOptions.data, { id: result.id });
                entity.is_active = result.is_active;
                if (entity.is_active) {
                    toastr.info(node.hostname + ' Activated');
                } else {
                    toastr.info(node.hostname + ' Deactivated');
                }
            });
        };

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
                    if (entity.is_paused) {
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

        vm.updateNodeActive = function () {
            formatResults();
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

        var formatResults = function () {
            vm.nodes = _.filter(allNodes, { is_active: vm.showActive });
            var order = $location.search().order;
            if (order) {
                var fieldArr = [];
                var directionArr = [];
                _.forEach(order, function (o) {
                    fieldArr.push(_.startsWith(o, '-') ? _.tail(o).join('') : o);
                    directionArr.push(_.startsWith(order, '-') ? 'desc' : 'asc');
                });
                vm.nodes = _.sortByOrder(vm.nodes, fieldArr, directionArr);
            }
            _.forEach(vm.nodes, function (node) {
                node.running_jobs = getRunningJobs(node);
            });
            vm.gridOptions.totalItems = vm.nodes.length;
            vm.gridOptions.minRowsToShow = vm.nodes.length;
            vm.gridOptions.virtualizationThreshold = vm.nodes.length;
            vm.gridOptions.data = vm.nodes;
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
                    allNodes = data.nodes;
                    formatResults();
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
        });

        $scope.$watch('vm.showActive', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            vm.nodesParams.active = newValue.toString();
            vm.showActive = newValue;
            formatResults();
            stateService.setNodesParams(vm.nodesParams);
        });
    });
})();
