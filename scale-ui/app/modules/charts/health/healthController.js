(function () {
    'use strict';

    angular.module('scaleApp').controller('aisHealthController', function ($scope, gaugeFactory) {
        var gauge = null,
            initialized = false;

        var initialize = function () {
            initialized = true;
            var scale = $scope.scale || 1;
            //$scope.gaugeSize = 150 * scale;
            //$scope.gaugeWidth = 25 * scale;
            $scope.donutSize = 275 * scale;
            $scope.donutWidth = 25 * scale;
            //gauge = gaugeFactory.createGauge($scope.type, 'Failure Rate')
        };

        /*var redrawGauge = function () {
            if (gauge) {
                gauge.redraw($scope.data.gaugeData);
            }
        };*/

        $scope.$watch('data', function (data) {
            if (data) {
                if (_.keys(data).length > 0) {
                    if (!initialized) {
                        initialize();
                    }
                    //redrawGauge();
                }
            }
        });
    });
})();