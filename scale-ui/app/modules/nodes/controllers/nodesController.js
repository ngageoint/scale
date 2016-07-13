(function () {
    'use strict';

    angular.module('scaleApp').controller('nodesController', function($scope, $location, $timeout, $aside, navService, nodeService, scaleService) {
        var vm = this;
        
        vm.loading = true;
        vm.hourValue = 3;
        vm.error = null;
        vm.errorStatus = null;
        vm.nodes = [];
        vm.asideState = {
            open: false
        };

        vm.viewDetails = function (id) {
            vm.loading = true;
            nodeService.getNode(id).then( function (data) {
                vm.asideState = {
                    open: true
                };

                var postClose = function () {
                    // do something here after aside is closed or dismissed
                    vm.asideState.open = false;
                };

                $aside.open({
                    templateUrl: 'nodeAside.html',
                    placement: 'top',
                    size: 'lg',
                    controllerAs: 'vmAside',
                    controller: ['$uibModalInstance', function ($uibModalInstance) {
                        var vmAside = this;

                        vmAside.node = data;
                        vmAside.scaleService = scaleService;

                        vmAside.ok = function (e) {
                            console.log('ok');
                            $uibModalInstance.close();
                            e.stopPropagation();
                        };
                        vmAside.cancel = function (e) {
                            console.log('cancel');
                            $uibModalInstance.dismiss();
                            e.stopPropagation();
                        };
                    }]
                }).result.then(postClose, postClose);
            }).finally(function () {
                vm.loading = false;
            });
        };

        vm.getNodeClass = function (node) {
            if (!node.is_online) {
                return 'offline';
            } else {
                if (node.node.is_paused) {
                    return 'is-paused';
                } else if (node.node.is_paused_errors) {
                    return 'is-paused-errors';
                }
            }
            return 'online';
        };

        var getNodeStatus = function () {
            nodeService.getNodeStatus(null, null, 'PT' + vm.hourValue + 'H', null).then(null, null, function (data) {
                if (data.$resolved) {
                    vm.error = null;
                    vm.nodes = data.results;
                } else {
                    if (data.statusText && data.statusText !== '') {
                        vm.errorStatus = data.statusText;
                    }
                    vm.error = 'Unable to retrieve nodes.';
                }
                vm.loading = false;
            });
        };

        var initialize = function() {
            getNodeStatus();
            navService.updateLocation('nodes');
        };

        initialize();
    });
})();