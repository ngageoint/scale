(function () {
    'use strict';

    angular.module('scaleApp').controller('aisDonutController', function($scope, $element, scaleConfig) {
        var chart = null;

        var genChart = function () {
            if (chart) {
                //chart.data()
                //$scope.colData
                var oldData = [],
                    removeIds = [];

                // reassemble currently displayed data to match $scope.colData
                _.forEach(chart.data(), function (d) {
                    oldData.push([d.values[0].id, d.values[0].value]);
                });

                // determine which elements to remove
                _.forEach(oldData, function (od) {
                    var keep = _.find($scope.colData, function (cd) {
                        return cd[0] === od[0];
                    });
                    if (!keep) {
                        removeIds.push(od[0]);
                    }
                });

                // update chart
                //console.log(JSON.stringify($scope.colData));
                //console.log(JSON.stringify(removeIds));
                chart.load({
                    columns: $scope.colData,
                    unload: removeIds
                });
            } else {
                chart = c3.generate({
                    bindto: $element[0],
                    data: {
                        columns: $scope.colData,
                        type: $scope.type,
                        colors: {
                            down: scaleConfig.colors.chart_red,
                            warning: scaleConfig.colors.chart_yellow,
                            up: scaleConfig.colors.chart_green,
                            Completed: scaleConfig.colors.chart_green,
                            Done: '#3681bf',
                            Queue: scaleConfig.colors.chart_yellow,
                            Failed: scaleConfig.colors.chart_red,
                            Algorithm: '#444',
                            Data: '#888',
                            System: '#ccc',
                            Offline: scaleConfig.colors.chart_red,
                            'High Failure Rate': scaleConfig.colors.chart_orange,
                            Paused: scaleConfig.colors.chart_yellow
                        }
                    },
                    transition: {
                        duration: 700
                    },
                    pie: {
                        label: {
                            format: d3.format(',')
                        }
                    },
                    donut: {
                        label: {
                            format: $scope.showLabel ? d3.format(',') : function () {
                                return '';
                            }
                        },
                        width: $scope.width,
                        title: $scope.name
                    },
                    tooltip: {
                        format: {
                            value: d3.format(',')
                        }
                    },
                    size: {
                        height: $scope.size || 320
                    }
                });
            }
            $element[0].style.position = 'static';
        };

        var initColumnData = function(){
            $scope.colData = [];
            $scope.data.forEach(function(obj){
                $scope.colData.push([obj.status,obj.count]);
            });
        };

        var initialize = function() {
            initColumnData();
            genChart();
        };

        $scope.$watch('data', function (data) {
            if (data) {
                if (data.length > 0) {
                    initialize();
                } else {
                    $($element[0]).empty();
                }
            }
        });

        window.onresize = function() {
          var width = $($element[0]).width();
          console.log(width);
          genChart();
        }
    });
})();
