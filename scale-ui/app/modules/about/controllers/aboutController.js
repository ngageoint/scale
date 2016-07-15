(function () {
    'use strict';

    angular.module('scaleApp').controller('aboutController', function($scope, $location, navService, stateService) {
        var vm = this;
        
        vm.stateService = stateService;
        vm.version = '';

        var initialize = function() {
            navService.updateLocation('about');
        };

        initialize();

        $scope.$watch('vm.stateService.getVersion()', function (newValue) {
            vm.version = newValue;
        });
    });
})();
