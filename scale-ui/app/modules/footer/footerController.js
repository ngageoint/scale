(function () {
    'use strict';

    angular.module('scaleApp').controller('footerController', function ($scope, scaleService, stateService) {
        $scope.version = '';

        scaleService.getVersion().then(function (data) {
            $scope.version = data.version;
            stateService.setVersion(data.version);
        });
    });
})();
