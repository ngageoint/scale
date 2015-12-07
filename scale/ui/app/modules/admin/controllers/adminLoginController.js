(function () {
    'use strict';

    angular.module('scaleApp').controller('adminLoginController', function ($timeout, $rootScope, $location, userService) {

        var initialize = function () {
            $rootScope.user = userService.getUserCreds();
            if(!$rootScope.user){
                $rootScope.user = userService.login('admin');
            }

            console.log($rootScope.user);

            $timeout(function(){
                // Any code in here will automatically have an $scope.apply() run afterwards
                $location.path("/");
            });
        };

        initialize();
    });
})();