(function () {
    'use strict';

    angular.module('scaleApp').controller('logoutController', function ($timeout, $rootScope, $location, userService) {

        var initialize = function () {
            userService.logout();
            $timeout(function(){
                // Any code in here will automatically have an $scope.apply() run afterwards
                $location.path("/");
            });
        };

        initialize();
    });
})();