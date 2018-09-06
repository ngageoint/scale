(function () {
    'use strict';

    angular.module('scaleApp').controller('aisResourceController', function ($scope, scaleConfig, scaleService) {
        var vm = this;
        var cpuChart = null;
        var memChart = null;
        var diskChart = null;
        var gpuChart = null;
        var viewport = scaleService.getViewportSize();
        var chartHeight = viewport.height * 0.3;
        var cpuChartOptions = {
            bindto: '#cpuChart',
            data: {
                columns: [],
                type: 'pie'
            },
            legend: {
                hide: true
            },
            size: {
                height: chartHeight
            },
            color: {
                pattern: [scaleConfig.colors.chart_blue, scaleConfig.colors.chart_green, scaleConfig.colors.chart_blue_light, scaleConfig.colors.chart_gray_dark]
            }
        };
        var memChartOptions = {
            bindto: '#memChart',
            data: {
                columns: [],
                type: 'pie'
            },
            legend: {
                hide: true
            },
            size: {
                height: chartHeight
            },
            color: {
                pattern: [scaleConfig.colors.chart_blue, scaleConfig.colors.chart_green, scaleConfig.colors.chart_blue_light, scaleConfig.colors.chart_gray_dark]
            }
        };
        var diskChartOptions = {
            bindto: '#diskChart',
            data: {
                columns: [],
                type: 'pie'
            },
            legend: {
                hide: true
            },
            size: {
                height: chartHeight
            },
            color: {
                pattern: [scaleConfig.colors.chart_blue, scaleConfig.colors.chart_green, scaleConfig.colors.chart_blue_light, scaleConfig.colors.chart_gray_dark]
            }
        };
        var gpuChartOptions = {
            bindto: '#gpuChart',
            data: {
                columns: [],
                type: 'pie'
            },
            legend: {
                hide: true
            },
            size: {
                height: chartHeight
            },
            color: {
                pattern: [scaleConfig.colors.chart_blue, scaleConfig.colors.chart_green, scaleConfig.colors.chart_blue_light, scaleConfig.colors.chart_gray_dark]
            }
        };

        vm.memValue = null;
        vm.cpuValue = null;
        vm.diskValue = null;
        vm.gpuValue = null;

        $scope.$watchCollection('data', function () {
            if ($scope.data) {
                vm.memValue = scaleService.calculateFileSizeFromMib($scope.data.resources.mem.total);
                vm.cpuValue = $scope.data.resources.cpus.total;
                vm.diskValue = scaleService.calculateFileSizeFromMib($scope.data.resources.disk.total);
                vm.gpuValue = $scope.data.resources.gpus.total;
                cpuChartOptions.data.columns = [
                    ['Offered', $scope.data.resources.cpus.offered],
                    ['Free', $scope.data.resources.cpus.free],
                    ['Running', $scope.data.resources.cpus.running],
                    ['Unavailable', $scope.data.resources.cpus.unavailable]
                ];
                memChartOptions.data.columns = [
                    ['Offered', $scope.data.resources.mem.offered],
                    ['Free', $scope.data.resources.mem.free],
                    ['Running', $scope.data.resources.mem.running],
                    ['Unavailable', $scope.data.resources.mem.unavailable]
                ];
                diskChartOptions.data.columns = [
                    ['Offered', $scope.data.resources.disk.offered],
                    ['Free', $scope.data.resources.disk.free],
                    ['Running', $scope.data.resources.disk.running],
                    ['Unavailable', $scope.data.resources.disk.unavailable]
                ];
                gpuChartOptions.data.columns = [
                    ['Offered', $scope.data.resources.gpus.offered],
                    ['Free', $scope.data.resources.gpus.free],
                    ['Running', $scope.data.resources.gpus.running],
                    ['Unavailable', $scope.data.resources.gpus.unavailable]
                ];
                cpuChart = c3.generate(cpuChartOptions);
                memChart = c3.generate(memChartOptions);
                diskChart = c3.generate(diskChartOptions);
                gpuChart = c3.generate(gpuChartOptions);
            }
        });
    }).directive('aisResource', function () {
        return {
            templateUrl: 'modules/common/directives/aisResourceTemplate.html',
            controller: 'aisResourceController',
            controllerAs: 'vm',
            restrict: 'E',
            scope: {
                data: '='
            }
        };
    });
})();
