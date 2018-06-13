(function () {
    'use strict';

    angular.module('scaleApp').controller('workspacesController', function ($scope, $location, $uibModal, $routeParams, scaleConfig, navService, workspacesService, scaleService, stateService, userService, gridFactory, Workspace, toastr) {
        var vm = this,
            currWorkspace = {},
            activeWorkspaces = [],
            inactiveWorkspaces = [];

        vm.loading = true;
        vm.scaleConfig = scaleConfig;
        vm.showActive = stateService.getShowActiveWorkspaces();
        vm.workspaces = [];
        vm.localWorkspaces = [];
        vm.activeWorkspace = {};
        vm.addBtnClass = 'btn-primary';
        vm.addBtnIcon = 'fa-plus-circle';
        vm.saveBtnClass = 'btn-default';
        vm.mode = 'view';
        vm.user = userService.getUserCreds();
        vm.readonly = !(vm.user && vm.user.is_admin);
        vm.brokerDescription = '';
        vm.availableWorkspaceTypes = _.cloneDeep(scaleConfig.workspaceTypes);

        vm.cancelCreate = function () {
            vm.mode = 'view';
            // revert any changes to the workspace
            vm.activeWorkspace = Workspace.transformer(_.cloneDeep(currWorkspace));
            if ($routeParams.id === '0') {
                $location.path('/workspaces');
            }
        };

        vm.editWorkspace = function () {
            // store a reference of the workspace as it currently exists in case the user cancels the edit
            currWorkspace = Workspace.transformer(_.cloneDeep(vm.activeWorkspace));
            vm.mode = 'edit';
        };

        vm.saveWorkspace = function () {
            workspacesService.saveWorkspace(vm.activeWorkspace).then(function (workspace) {
                vm.activeWorkspace = Workspace.transformer(workspace);
                if (scaleConfig.static) {
                    localStorage.setItem('workspace' + vm.activeWorkspace.id, JSON.stringify(vm.activeWorkspace));
                }
                vm.mode = 'view';
                getWorkspaces();
            }).catch(function () {
                
            });
        };

        vm.clearLocalWorkspaces = function () {
            _.forEach(vm.localWorkspaces, function (workspace) {
                localStorage.removeItem('workspace' + workspace.id);
            });
            $location.path('/workspaces');
        };
        
        vm.newWorkspace = function () {
            vm.mode = 'add';
            vm.loadWorkspace(0);
        };

        vm.loadWorkspace = function (id) {
            $location.path('workspaces/' + id);
        };

        var getWarningsHtml = function (warnings) {
            var warningsHtml = '';
            _.forEach(warnings, function (warning) {
                warningsHtml += '<b>' + warning.id + ':</b> ' + warning.details + '<br /><br />';
            });
            warningsHtml += '<button type="button" class="btn btn-default btn-xs clear">Hide</button>';
            return warningsHtml;
        };

        vm.validateWorkspace = function () {
            vm.loading = true;
            workspacesService.validateWorkspace(vm.activeWorkspace).then(function (data) {
                if (data.warnings && data.warnings.length > 0) {
                    // display the warnings
                    var warningsHtml = getWarningsHtml(data.warnings);
                    toastr['error'](warningsHtml);
                } else {
                    toastr['success']('Workspace is valid.');
                }
            }).catch(function (error) {
                if (error.detail) {
                    toastr['error'](error.detail);
                } else {
                    toastr['error'](error);
                }
            }).finally(function () {
                vm.loading = false;
            });
        };

        vm.toggleShowActive = function (value) {
            vm.showActive = value;
        };

        $scope.$watch('vm.activeWorkspace.json_config.broker.type', function (newValue) {
            if (newValue === 'nfs') {
                vm.brokerDescription = scaleConfig.nfsBrokerDescription;
            } else if (newValue === 'host') {
                vm.brokerDescription = scaleConfig.hostBrokerDescription;
            } else if (newValue === 's3') {
                vm.brokerDescription = scaleConfig.s3BrokerDescription;
            }
        });

        $scope.$watch('vm.showActive', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            vm.showActive = newValue;
            stateService.setShowActiveWorkspaces(newValue);
            vm.workspaces = vm.showActive ? _.cloneDeep(activeWorkspaces) : _.cloneDeep(inactiveWorkspaces);
        });

        var getWorkspaces = function () {
            vm.loading = true;
            workspacesService.getWorkspaces().then(function (data) {
                if (scaleConfig.static) {
                    var i = 0,
                        oJson = {},
                        sKey;
                    for (; sKey = localStorage.key(i); i++) {
                        oJson[sKey] = localStorage.getItem(sKey);
                    }
                    _.filter(_.pairs(oJson), function (o) {
                        if (_.contains(o[0], 'workspace')) {
                            var type = JSON.parse(o[1]);
                            vm.localWorkspaces.push(type);
                            data.push(type);
                        }
                    });
                }
                activeWorkspaces = _.filter(data, { 'is_active': true });
                inactiveWorkspaces = _.filter(data, { 'is_active': false });
                vm.workspaces = vm.showActive ? _.cloneDeep(activeWorkspaces) : _.cloneDeep(inactiveWorkspaces);
                vm.loading = false;
            }).catch(function (error) {
                vm.loading = false;
                console.log(error);
            });
        };

        var initialize = function () {
            getWorkspaces();
            vm.activeWorkspace = null;
            vm.mode = 'view';

            if ($routeParams.id) {
                var id = parseInt($routeParams.id);
                if (id === 0) {
                    vm.mode = 'add';
                    vm.activeWorkspace = new Workspace();
                } else {
                    // set activeWorkspace = workspace details for id
                    workspacesService.getWorkspaceDetails(id).then(function (data) {
                        vm.activeWorkspace = Workspace.transformer(data);
                    });
                }
            }
            navService.updateLocation('workspaces');
        };

        initialize();

        angular.element(document).ready(function () {
            // set container heights equal to available page height
            var viewport = scaleService.getViewportSize(),
                offset = scaleConfig.headerOffset,
                containerMaxHeight = viewport.height - offset + 60;

            vm.containerStyle = 'height: ' + containerMaxHeight + 'px; max-height: ' + containerMaxHeight + 'px;';
        });
    });
})();
