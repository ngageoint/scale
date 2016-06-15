(function () {
    'use strict';

    angular.module('scaleApp').controller('workspacesController', function ($scope, $location, $uibModal, $routeParams, scaleConfig, navService, workspacesService, scaleService, stateService, userService, gridFactory, Workspace, toastr) {
        var currWorkspace = {},
            activeWorkspaces = [],
            inactiveWorkspaces = [];

        $scope.loading = true;
        $scope.scaleConfig = scaleConfig;
        $scope.showActive = stateService.getShowActiveWorkspaces();
        $scope.workspaces = [];
        $scope.localWorkspaces = [];
        $scope.addBtnClass = 'btn-primary';
        $scope.addBtnIcon = 'fa-plus-circle';
        $scope.saveBtnClass = 'btn-default';
        $scope.mode = 'view';
        $scope.user = userService.getUserCreds();
        $scope.readonly = !($scope.user && $scope.user.is_admin);
        $scope.brokerDescription = '';
        $scope.availableWorkspaceTypes = _.cloneDeep(scaleConfig.workspaceTypes);

        $scope.cancelCreate = function () {
            $scope.mode = 'view';
            $scope.activeWorkspace = Workspace.transformer(_.cloneDeep(currWorkspace));
            disableSaveWorkspace();
            if ($routeParams.id === '0') {
                $location.path('/workspaces');
            }
        };

        $scope.editWorkspace = function () {
            currWorkspace = Workspace.transformer(_.cloneDeep($scope.activeWorkspace));
            $scope.mode = 'edit';
        };

        $scope.saveWorkspace = function () {
            workspacesService.saveWorkspace($scope.activeWorkspace).then(function (workspace) {
                $scope.activeWorkspace = Workspace.transformer(workspace);
                if (scaleConfig.static) {
                    localStorage.setItem('workspace' + $scope.activeWorkspace.id, JSON.stringify($scope.activeWorkspace));
                }
                $scope.mode = 'view';
                disableSaveWorkspace();
                getWorkspaces();
                //$location.path('/workspaces/' + $scope.activeWorkspace.id);
            }).catch(function () {
                
            });
        };

        $scope.clearLocalWorkspaces = function () {
            _.forEach($scope.localWorkspaces, function (workspace) {
                localStorage.removeItem('workspace' + workspace.id);
            });
            $location.path('/workspaces');
        };
        
        $scope.newWorkspace = function () {
            $scope.mode = 'add';
            $scope.loadWorkspace(0);
        };

        $scope.loadWorkspace = function (id) {
            $location.path('workspaces/' + id);
        };

        var enableSaveWorkspace = function () {
            if ($scope.activeWorkspace) {
                $scope.activeWorkspace.modified = true;
                $scope.saveBtnClass = 'btn-success';
            }
        };

        var disableSaveWorkspace = function () {
            $scope.activeWorkspace.modified = false;
            $scope.saveBtnClass = 'btn-default';
        };

        var getWarningsHtml = function (warnings) {
            var warningsHtml = '';
            _.forEach(warnings, function (warning) {
                warningsHtml += '<b>' + warning.id + ':</b> ' + warning.details + '<br /><br />';
            });
            warningsHtml += '<button type="button" class="btn btn-default btn-xs clear">Hide</button>';
            return warningsHtml;
        };

        $scope.validateWorkspace = function () {
            $scope.loading = true;
            workspacesService.validateWorkspace($scope.activeWorkspace).then(function (data) {
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
                $scope.loading = false;
            });
        };

        $scope.$watch('activeWorkspace.json_config.broker.type', function (newValue) {
            if (newValue === 'nfs') {
                $scope.brokerDescription = scaleConfig.nfsBrokerDescription;
            } else if (newValue === 'host') {
                $scope.brokerDescription = scaleConfig.hostBrokerDescription;
            } else if (newValue === 's3') {
                $scope.brokerDescription = scaleConfig.s3BrokerDescription;
            }
        });

        $scope.$watchCollection('activeWorkspace', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            if (newValue.hasRequired()) {
                enableSaveWorkspace();
            } else {
                disableSaveWorkspace();
            }
        });

        $scope.$watch('showActive', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            $scope.showActive = newValue;
            stateService.setShowActiveWorkspaces(newValue);
            $scope.workspaces = $scope.showActive ? _.cloneDeep(activeWorkspaces) : _.cloneDeep(inactiveWorkspaces);
        });

        var getWorkspaces = function () {
            $scope.loading = true;
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
                            $scope.localWorkspaces.push(type);
                            data.push(type);
                        }
                    });
                }
                activeWorkspaces = _.filter(data, { 'is_active': true });
                inactiveWorkspaces = _.filter(data, { 'is_active': false });
                $scope.workspaces = $scope.showActive ? _.cloneDeep(activeWorkspaces) : _.cloneDeep(inactiveWorkspaces);
                $scope.loading = false;
            }).catch(function (error) {
                $scope.loading = false;
                console.log(error);
            });
        };

        var initialize = function () {
            getWorkspaces();
            $scope.activeWorkspace = null;
            $scope.mode = 'view';

            if ($routeParams.id) {
                var id = parseInt($routeParams.id);
                if (id === 0) {
                    $scope.mode = 'add';
                    $scope.activeWorkspace = new Workspace();
                    disableSaveWorkspace();
                } else {
                    // set activeWorkspace = workspace details for id
                    workspacesService.getWorkspaceDetails(id).then(function (data) {
                        $scope.activeWorkspace = Workspace.transformer(data);
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

            $scope.containerStyle = 'height: ' + containerMaxHeight + 'px; max-height: ' + containerMaxHeight + 'px;';
        });
    });
})();