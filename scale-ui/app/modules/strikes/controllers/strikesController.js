(function () {
    'use strict';

    angular.module('scaleApp').controller('strikesController', function ($scope, $route, $location, $routeParams, Strike, StrikeIngestFile, scaleConfig, navService, strikeService, workspacesService, scaleService, stateService, userService, toastr) {
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
                $location.path('/strikes');
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
            $location.path('/strikes');
        };

        vm.newStrike = function () {
            vm.mode = 'add';
            vm.loadStrike(0);
        };

        vm.loadStrike = function (id) {
            $location.path('strikes/' + id);
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
            strikeService.validateStrike(vm.activeStrike).then(function (data) {
                if (data.warnings && data.warnings.length > 0) {
                    // display the warnings
                    var warningsHtml = getWarningsHtml(data.warnings);
                    toastr['error'](warningsHtml);
                } else {
                    toastr['success']('Strike is valid.');
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

        var getWorkspaces = function () {
            workspacesService.getWorkspaces().then(function (data) {
                vm.workspaces = data;
                vm.newWorkspaces = data;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                vm.loading = false;
            });
        };

        var getWorkspaceDetails = function (id) {
            vm.loading = true;
            workspacesService.getWorkspaceDetails(id).then(function (data) {
                vm.activeWorkspace = data;
                if (vm.activeWorkspace.json_config.broker.type === 'host') {
                    vm.activeStrike.configuration.monitor.type = 'dir-watcher';
                } else if (vm.activeWorkspace.json_config.broker.type === 's3') {
                    vm.activeStrike.configuration.monitor.type = 's3';
                }
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
            navService.updateLocation('strikes');
        };

        initialize();

        angular.element(document).ready(function () {
            // set container heights equal to available page height
            var viewport = scaleService.getViewportSize(),
                offset = scaleConfig.headerOffset,
                containerMaxHeight = viewport.height - offset + 60;

            vm.containerStyle = 'height: ' + containerMaxHeight + 'px; max-height: ' + containerMaxHeight + 'px;';
        });

        $scope.$watchCollection('vm.activeStrike.configuration.workspace', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            getWorkspaceDetails(newValue.id);
            vm.newWorkspaces = [];
            _.forEach(vm.workspaces, function (workspace) {
                if (!angular.equals(workspace, newValue)) {
                    vm.newWorkspaces.push(workspace);
                }
            });
        });
    });
})();