(function () {
    'use strict';

    angular.module('scaleApp').controller('batchesController', function ($scope, navService) {

        var vm = this;

        vm.initialize = function () {
            navService.updateLocation('batch');
        };
        vm.initialize();
    });
})();
