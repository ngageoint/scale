(function () {
    'use strict';

    angular.module('scaleApp').controller('strikesController', function ($scope, $route, $location, $routeParams, Strike, StrikeIngestFile, scaleConfig, navService, subnavService, strikeService, workspacesService, scaleService, stateService, userService, toastr) {
        var vm = this,
            currStrike = {};

        vm.loading = true;
        vm.scaleConfig = scaleConfig;
        vm.strikes = [];
        vm.workspaces = [];
        vm.newWorkspaces = [];
        vm.activeWorkspace = {};
        vm.localStrikes = [];
        vm.activeStrike = new Strike();
        vm.activeStrikeIngestFile = new StrikeIngestFile();
        vm.dataType = '';
        vm.availableWorkspaceTypes = _.cloneDeep(scaleConfig.workspaceTypes);
        vm.allowedMonitorTypes = _.cloneDeep(scaleConfig.allowedMonitorTypes);
        vm.addBtnClass = 'btn-primary';
        vm.addBtnIcon = 'fa-plus-circle';
        vm.saveBtnClass = 'btn-default';
        vm.mode = 'view';
        vm.user = userService.getUserCreds();
        vm.readonly = !(vm.user && vm.user.is_admin);
        vm.JSON = JSON;

        vm.cancelCreate = function () {
            vm.mode = 'view';
            // revert any changes to the strike
            vm.activeStrike = Strike.transformer(_.cloneDeep(currStrike));
            if ($routeParams.id === '0') {
                $location.path('/feed/strikes');
            }
        };

        vm.editStrike = function () {
            // store a reference of the strike as it currently exists in case the user cancels the edit
            currStrike = Strike.transformer(_.cloneDeep(vm.activeStrike));
            vm.mode = 'edit';
        };

        vm.saveStrike = function () {
            strikeService.saveStrike(vm.activeStrike).then(function (strike) {
                vm.activeStrike = Strike.transformer(strike);
                // only store the new workspace name, not the entire object
                _.forEach(vm.activeStrike.configuration.files_to_ingest, function (file) {
                    if (file.new_workspace) {
                        file.new_workspace = file.new_workspace.name;
                    }
                });
                if (scaleConfig.static) {
                    localStorage.setItem('strike' + vm.activeStrike.id, JSON.stringify(vm.activeStrike));
                }
                $route.reload();
            }).catch(function () {

            });
        };

        vm.clearLocalStrikes = function () {
            _.forEach(vm.localStrikes, function (strike) {
                localStorage.removeItem('strike' + strike.id);
            });
            $location.path('/feed/strikes');
        };

        vm.newStrike = function () {
            vm.mode = 'add';
            vm.loadStrike(0);
        };

        vm.loadStrike = function (id) {
            $location.path('feed/strikes/' + id);
        };

        var getWarningsHtml = function (warnings) {
            var warningsHtml = '';
            _.forEach(warnings, function (warning) {
                warningsHtml += '<b>' + warning.id + ':</b> ' + warning.details + '<br /><br />';
            });
            warningsHtml += '<button type="button" class="btn btn-default btn-xs clear">Hide</button>';
            return warningsHtml;
        };

        vm.validateStrike = function () {
            vm.loading = true;
            // only store the new workspace name, not the entire object
            _.forEach(vm.activeStrike.configuration.files_to_ingest, function (file) {
                if (file.new_workspace) {
                    file.new_workspace = file.new_workspace.name;
                }
            });
            strikeService.validateStrike(vm.activeStrike).then(function (data) {
                if (data.warnings && data.warnings.length > 0) {
                    // display the warnings
                    var warningsHtml = getWarningsHtml(data.warnings);
                    toastr['error'](warningsHtml);
                } else {
                    toastr['success']('Strike is valid.');
                }
            }).catch(function (error) {
                if (error && error.detail) {
                    toastr['error'](error.detail);
                } else {
                    toastr['error']('Error validating strike');
                }
            }).finally(function () {
                vm.loading = false;
            });
        };

        vm.disableSaveBtn = function (invalid) {
            var returnVal = !(!invalid && vm.activeStrike.configuration.files_to_ingest.length > 0);
            vm.saveBtnClass = returnVal ? 'btn-default' : 'btn-success';
            return returnVal;
        };

        vm.addStrikeIngestFile = function () {
            if (_.keys(vm.activeStrikeIngestFile).length > 0) {
                vm.activeStrike.configuration.files_to_ingest.push(StrikeIngestFile.transformer(vm.activeStrikeIngestFile));
                vm.activeStrikeIngestFile = new StrikeIngestFile();
            }
        };

        vm.deleteStrikeIngestFile = function (file) {
            _.remove(vm.activeStrike.configuration.files_to_ingest, function (f) {
                return angular.equals(f, file);
            });
        };

        vm.addDataType = function () {
            if (vm.dataType) {
                vm.activeStrikeIngestFile.data_types.push(vm.dataType);
                vm.dataType = '';
            }
        };

        vm.removeDataType = function (dataType) {
            _.remove(vm.activeStrikeIngestFile.data_types, function (d) {
                return d === dataType;
            });
        };

        vm.updateWorkspace = function () {
            if (vm.activeStrike) {
                var workspaceObj = _.find(vm.workspaces, {name: vm.activeStrike.configuration.workspace});
                if (workspaceObj) {
                    vm.newWorkspaces = _.cloneDeep(vm.workspaces);
                    _.remove(vm.newWorkspaces, workspaceObj);
                    getWorkspaceDetails(workspaceObj.id);
                }
            }
        };

        vm.formatJSON = function (file) {
            file = _.omit(file, '$$hashKey');
            if (file.new_workspace) {
                file.new_workspace = file.new_workspace.name;
            }
            return JSON.stringify(file, null, 4);
        };

        var getWorkspaceDetails = function (id) {
            vm.loading = true;
            workspacesService.getWorkspaceDetails(id).then(function (data) {
                vm.activeWorkspace = data;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                vm.loading = false;
            });
        };

        var getWorkspaces = function () {
            workspacesService.getWorkspaces().then(function (data) {
                vm.workspaces = data;
                vm.newWorkspaces = data;
                vm.updateWorkspace();
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                vm.loading = false;
            });
        };

        var getStrikes = function () {
            vm.loading = true;
            strikeService.getStrikes().then(function (data) {
                if (scaleConfig.static) {
                    var i = 0,
                        oJson = {},
                        sKey;
                    for (; sKey = localStorage.key(i); i++) {
                        oJson[sKey] = localStorage.getItem(sKey);
                    }
                    _.filter(_.pairs(oJson), function (o) {
                        if (_.contains(o[0], 'strike')) {
                            var type = JSON.parse(o[1]);
                            vm.localStrikes.push(type);
                            data.push(type);
                        }
                    });
                }
                vm.strikes = data;
                getWorkspaces();
            }).catch(function (error) {
                console.log(error);
                vm.loading = false;
            });
        };

        var initialize = function () {
            getStrikes();
            vm.activeStrike = null;
            vm.mode = 'view';

            if ($routeParams.id) {
                var id = parseInt($routeParams.id);
                if (id === 0) {
                    vm.mode = 'add';
                    vm.activeStrike = new Strike();
                } else {
                    strikeService.getStrikeDetails(id).then(function (data) {
                        vm.activeStrike = Strike.transformer(data);
                    });
                }
            }
            navService.updateLocation('feed');
            subnavService.setCurrentPath('feed/strikes');
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
