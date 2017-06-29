(function () {
    'use strict';

    angular.module('scaleApp').controller('navController', function($scope, $location, $window, scaleConfig, scaleService, stateService, navService) {
        document.getElementsByTagName('body')[0].style.backgroundColor = scaleConfig.colors.nav_bg;

        var vm = this;

        vm.version = '';
        vm.activePage = 'overview';
        vm.docsUrl = scaleConfig.urls.documentation;

        vm.goto = function(loc) {
            $location.search('').replace();
            $location.path(loc);
        };

        var locationUpdated = function() {
            vm.activePage = navService.location;
        };

        var initialize = function() {
            navService.registerObserver(locationUpdated);

            scaleService.getVersion().then(function (data) {
                vm.version = data.version;
                stateService.setVersion(data.version);
            });
        };
        initialize();
    });
})();
