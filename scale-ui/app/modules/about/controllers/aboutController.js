(function () {
    'use strict';

    angular.module('scaleApp').controller('aboutController', function($scope, $location, $window, navService, stateService) {
        $scope.stateService = stateService;
        $scope.version = '';

        var initialize = function() {
            navService.updateLocation('about');
        };

        initialize();

        $scope.$watch('stateService.getVersion()', function (newValue) {
            $scope.version = newValue;
        });
    });
})();
