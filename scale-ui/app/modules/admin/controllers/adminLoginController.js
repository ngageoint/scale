(function () {
    'use strict';

    angular.module('scaleApp').controller('adminLoginController', function ($timeout, $location, stateService, userService) {

        var initialize = function () {
            var user = userService.getUserCreds();
            
            if (!user) {
                userService.login('admin');
            }

            $timeout(function () {
                // Any code in here will automatically have an $scope.apply() run afterwards
                $location.path('/');
            });
        };

        initialize();
    });
})();