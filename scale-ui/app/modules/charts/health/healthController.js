(function () {
    'use strict';

    angular.module('scaleApp').controller('aisHealthController', function ($scope) {
        var vm = this,
            initialized = false;

        var initialize = function () {
            initialized = true;
            var scale = $scope.scale || 1;
            vm.donutSize = 275 * scale;
            vm.donutWidth = 25 * scale;
        };

        $scope.$watch('data', function (data) {
            if (data) {
                if (_.keys(data).length > 0) {
                    if (!initialized) {
                        initialize();
                    }
                }
            }
        });
    });
})();