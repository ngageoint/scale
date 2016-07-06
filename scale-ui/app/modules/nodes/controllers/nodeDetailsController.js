(function () {
    'use strict';

    angular.module('scaleApp').controller('nodeDetailsController', function($scope, $location, $routeParams, $timeout, navService, nodeService, scaleService) {
        var vm = this;
        
        vm.loading = true;
        vm.nodeId = $routeParams.id;
        vm.scaleService = scaleService;

        var getNodeDetails = function (nodeId) {
            nodeService.getNode(nodeId).then( function (data) {
                vm.node = data;
            }).finally(function () {
                vm.loading = false;
            });
        };

        var initialize = function() {
            navService.updateLocation('nodes');
            getNodeDetails(vm.nodeId);
        };

        initialize();
    });
})();
