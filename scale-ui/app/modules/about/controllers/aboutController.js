(function () {
    'use strict';

    angular.module('scaleApp').controller('aboutController', function($scope, $location, $window, navService, scaleService) {
        $scope.version = '';

        var initialize = function() {
            navService.updateLocation('about');
            scaleService.getVersion().then(function (data) {
                $scope.version = data.version;
            });
        };

        initialize();
    });
})();
