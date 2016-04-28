(function () {
    'use strict';

    angular.module('scaleApp').controller('navController', function($scope, $location, $window, scaleConfig, scaleService, stateService, navService) {
        document.getElementsByTagName('body')[0].style.backgroundColor = scaleConfig.colors.nav_bg;

        $scope.version = '';
        $scope.activePage = 'overview';
        $scope.docsUrl = scaleConfig.urls.documentation;

        $scope.goto = function(loc) {
            $location.search('');
            $location.path(loc);
        };

        var locationUpdated = function() {
            $scope.activePage = navService.location;
        };

        var initialize = function() {
            navService.registerObserver(locationUpdated);

            scaleService.getVersion().then(function (data) {
                $scope.version = data.version;
                stateService.setVersion(data.version);
            });
        };
        initialize();
    });
})();
