(function () {
    'use strict';

    angular.module('scaleApp').controller('workspacesController', function($scope, $location, $uibModal, $routeParams, scaleConfig, navService, workspacesService, scaleService, userService, gridFactory, Workspace, toastr) {
        $scope.loading = true;
        $scope.workspaces = [];
        $scope.addBtnClass = 'btn-primary';
        $scope.addBtnIcon = 'fa-plus-circle';
        $scope.saveBtnClass = 'btn-default';
        $scope.mode = 'view';
        $scope.user = userService.getUserCreds();
        $scope.readonly = !($scope.user && $scope.user.is_admin);

        $scope.availableWorkspaceTypes = scaleConfig.workspaceTypes;

        var wsParams = {
            page: null, page_size: null, started: null, ended: null, order: null, status: null, error_category: null, job_type_id: null, job_type_name: null, job_type_category: null, url: null
        };
        
        $scope.cancelCreate = function() {
            //disableSaveWorkspace();
            $location.path('workspaces');
        };

        $scope.editWorkspace = function() {
            $scope.mode = 'edit';
        };

        $scope.saveWorkspace = function() {
            workspacesService.saveWorkspace($scope.activeWorkspace).then(function(workspace) {
                debugger;
                $scope.loadWorkspace(workspace.id);
            }).fail(function() {

            });
        };

        $scope.newWorkspace = function() {
            $scope.mode = 'add';
            $scope.loadWorkspace(0);
            disableSaveWorkspace();
        };

        $scope.loadWorkspace = function(id) {
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

        $scope.$watchCollection('activeWorkspace', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            console.log(newValue.json_config);
            if (newValue.validate()) {
                enableSaveWorkspace();
            } else {
                disableSaveWorkspace();
            }
        });

        var getWorkspaces = function () {
            $scope.loading = true;
            workspacesService.getWorkspaces().then(function (data) {
                $scope.workspaces = data;
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
                console.log(id);
                if (id === 0) {
                    $scope.mode = 'add';
                    $scope.activeWorkspace = new Workspace();
                    disableSaveWorkspace();
                } else {
                    // set activeWorkspace = workspace details for id
                    workspacesService.getWorkspaceDetails(id).then(function(data) {
                        $scope.activeWorkspace = data;
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