(function () {
    'use strict';

    angular.module('scaleApp').controller('scanDetailsController', function ($scope, $route, $location, $routeParams, Scan, ScanIngestFile, scaleConfig, navService, subnavService, scanService, workspacesService, scaleService, stateService, userService, toastr) {
        var vm = this,
            currScan = {};

        vm.loading = true;
        vm.scaleConfig = scaleConfig;
        vm.workspaces = [];
        vm.newWorkspaces = [];
        vm.activeWorkspace = {};
        vm.localScans = [];
        vm.activeScan = new Scan();
        vm.activeScanIngestFile = new ScanIngestFile();
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
            // revert any changes to the scan
            vm.activeScan = Scan.transformer(_.cloneDeep(currScan));
            if ($routeParams.id === '0') {
                $location.path('/feed/scans');
            }
        };

        vm.editScan = function () {
            // store a reference of the scan as it currently exists in case the user cancels the edit
            currScan = Scan.transformer(_.cloneDeep(vm.activeScan));
            vm.mode = 'edit';
        };

        vm.saveScan = function () {
            scanService.saveScan(vm.activeScan).then(function (scan) {
                vm.activeScan = Scan.transformer(scan);
                // only store the new workspace name, not the entire object
                _.forEach(vm.activeScan.configuration.files_to_ingest, function (file) {
                    if (file.new_workspace) {
                        file.new_workspace = file.new_workspace.name;
                    }
                });
                if (scaleConfig.static) {
                    localStorage.setItem('scan' + vm.activeScan.id, JSON.stringify(vm.activeScan));
                }
                if ($routeParams.id === '0') {
                    $location.path('/feed/scans/' + vm.activeScan.id);
                } else {
                    $route.reload();
                }
            }).catch(function () {

            });
        };

        vm.clearLocalScans = function () {
            _.forEach(vm.localScans, function (scan) {
                localStorage.removeItem('scan' + scan.id);
            });
            $location.path('/feed/scans');
        };

        vm.newScan = function () {
            vm.mode = 'add';
            vm.loadScan(0);
        };

        vm.loadScan = function (id) {
            $location.path('feed/scans/' + id);
        };

        var getWarningsHtml = function (warnings) {
            var warningsHtml = '';
            _.forEach(warnings, function (warning) {
                warningsHtml += '<b>' + warning.id + ':</b> ' + warning.details + '<br /><br />';
            });
            warningsHtml += '<button type="button" class="btn btn-default btn-xs clear">Hide</button>';
            return warningsHtml;
        };

        vm.validateScan = function () {
            vm.loading = true;
            scanService.validateScan(vm.activeScan).then(function (data) {
                if (data.warnings && data.warnings.length > 0) {
                    // display the warnings
                    var warningsHtml = getWarningsHtml(data.warnings);
                    toastr['error'](warningsHtml);
                } else {
                    toastr['success']('Scan is valid.');
                }
            }).catch(function (error) {
                if (error && error.detail) {
                    toastr['error'](error.detail);
                } else {
                    toastr['error']('Error validating scan');
                }
            }).finally(function () {
                vm.loading = false;
            });
        };

        vm.disableSaveBtn = function (invalid) {
            var returnVal = !(!invalid && vm.activeScan.configuration.files_to_ingest.length > 0);
            vm.saveBtnClass = returnVal ? 'btn-default' : 'btn-success';
            return returnVal;
        };

        vm.addScanIngestFile = function () {
            if (_.keys(vm.activeScanIngestFile).length > 0) {
                vm.activeScan.configuration.files_to_ingest.push(ScanIngestFile.transformer(vm.activeScanIngestFile));
                vm.activeScanIngestFile = new ScanIngestFile();
            }
        };

        vm.deleteScanIngestFile = function (file) {
            _.remove(vm.activeScan.configuration.files_to_ingest, function (f) {
                return angular.equals(f, file);
            });
        };

        vm.addDataType = function () {
            if (vm.dataType) {
                vm.activeScanIngestFile.data_types.push(vm.dataType);
                vm.dataType = '';
            }
        };

        vm.removeDataType = function (dataType) {
            _.remove(vm.activeScanIngestFile.data_types, function (d) {
                return d === dataType;
            });
        };

        vm.updateWorkspace = function () {
            if (vm.activeScan) {
                var workspaceObj = _.find(vm.workspaces, {name: vm.activeScan.configuration.workspace});
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
            var jsonStr = JSON.stringify(file, null, 4);
            return jsonStr.replace(/\\\\/g, '\\');
        };

        var getWorkspaceDetails = function (id) {
            vm.loading = true;
            workspacesService.getWorkspaceDetails(id).then(function (data) {
                vm.activeWorkspace = data;
                if (vm.activeWorkspace.json_config.broker.type === 'host') {
                    vm.activeScan.configuration.scanner.type = 'dir';
                } else if (vm.activeWorkspace.json_config.broker.type === 's3') {
                    vm.activeScan.configuration.scanner.type = 's3';
                } else {
                    vm.activeScan.configuration.scanner.type = null;
                }
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

        var initialize = function () {
            getWorkspaces();
            vm.activeScan = null;
            vm.mode = 'view';

            if ($routeParams.id) {
                var id = parseInt($routeParams.id);
                if (id === 0) {
                    vm.mode = 'add';
                    vm.activeScan = new Scan();
                } else {
                    scanService.getScanDetails(id).then(function (data) {
                        vm.activeScan = Scan.transformer(data);
                    });
                }
            }
            navService.updateLocation('feed');
            subnavService.setCurrentPath('feed/scans');
        };

        initialize();
    });
})();
