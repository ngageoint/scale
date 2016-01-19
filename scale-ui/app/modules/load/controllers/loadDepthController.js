(function () {
    'use strict';

    angular.module('scaleApp').controller('loadDepthController', function ($scope, $location, navService, scaleConfig, subnavService) {
        $scope.subnavLinks = scaleConfig.subnavLinks.load;
        subnavService.setCurrentPath('load/depth');

        $scope.loading = false;

        var initialize = function () {
            navService.updateLocation('load');
        };

        initialize();
    });
})();
