(function () {
    'use strict';

    angular.module('scaleApp').controller('loadDepthController', function ($scope, $location, navService, scaleConfig, subnavService) {
        var vm = this;
        
        vm.subnavLinks = scaleConfig.subnavLinks.load;
        subnavService.setCurrentPath('load/depth');

        vm.loading = false;

        var initialize = function () {
            navService.updateLocation('load');
        };

        initialize();
    });
})();
