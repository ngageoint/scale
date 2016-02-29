(function () {
    'use strict';

    angular.module('scaleApp').controller('aboutController', function($scope, $location, $window, navService) {
        var initialize = function() {
            navService.updateLocation('about');
        };
        initialize();
    });
})();
