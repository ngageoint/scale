(function () {
    'use strict';

    angular.module('scaleApp').controller('ovController', function($rootScope, $scope, navService, nodeService, jobService, jobTypeService, statusService, gaugeFactory, scaleConfig, scaleService, schedulerService, userService) {
        var vm = this;
        var memChart = null;
        var diskChart = null;
        var cpuChart = null;
        var gpuChart = null;
        var viewport = scaleService.getViewportSize();
        var chartHeight = viewport.height * 0.3;
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

        vm.date = new Date();
        vm.jobError = null;
        vm.jobErrorStatus = null;
        vm.loadingJobs = true;
        vm.loadingNodeHealth = true;
        vm.jobTypes = [];
        vm.nodes = [];
        vm.nodeHealthError = null;
        vm.nodeHealthErrorStatus = '';
        vm.hourValue = 3;
        vm.jobData = {
            data: null,
            status: null
        };
        vm.jobErrorBreakdown = [];
        vm.status = null;
        vm.statusError = null;
        vm.loadingStatus = true;
        vm.schedulerStatus = '';
        vm.schedulerStatusClass = 'alert-success';
        vm.cpuCalc = '';
        vm.memCalc = '';
        vm.diskCalc = '';
        vm.schedulerIsPaused = false;
        vm.user = userService.getUserCreds();
        vm.schedulerContainerClass = vm.user ? vm.user.is_admin ? 'col-xs-8 col-lg-10' : 'col-xs-12' : 'col-xs-12';
        vm.schedulerBtnClass = 'fa-pause';
        vm.toggleBtnClass = null;
        vm.memValue = null;
        vm.cpuValue = null;
        vm.diskValue = null;
        vm.gpuValue = null;

        vm.toggleScheduler = function () {
            vm.schedulerIsPaused = !vm.schedulerIsPaused;
            var schedulerData = {
                is_paused: vm.schedulerIsPaused
            };
            schedulerService.updateScheduler(schedulerData).then(function () {
                vm.schedulerStatus = vm.schedulerIsPaused ? 'Paused' : 'Running';
                vm.schedulerStatusClass = vm.schedulerIsPaused ? 'alert-warning' : 'alert-success';
                vm.schedulerBtnClass = vm.schedulerIsPaused ? 'fa-play' : 'fa-pause';
            }).catch(function (error) {
                console.log(error);
            });
        };

        var redrawGrid = function () {
            $scope.$broadcast('redrawGrid', vm.jobData);
        };

        var getJobTypes = function () {
            jobTypeService.getJobTypes().then(null, null, function (data) {
                if (data.$resolved) {
                    vm.jobError = null;
                    vm.jobData.data = data.results;
                    redrawGrid();
                } else {
                    if (data.statusText && data.statusText !== '') {
                        vm.jobErrorStatus = data.statusText;
                    }
                    vm.jobError = 'Unable to retrieve job types.';
                }
                vm.loadingJobs = false;
            });
        };

        var getStatus = function () {
            var cpuGauge = gaugeFactory.createGauge('cpu', 'CPU', 0, 100, 180),
                memGauge = gaugeFactory.createGauge('memory', 'Memory', 0, 100, 180),
                diskGauge = gaugeFactory.createGauge('disk', 'Disk', 0, 100, 180);

            statusService.getStatus().then(null, null, function (result) {
                if (result.$resolved) {
                    vm.statusError = null;
                    vm.status = result;
                    cpuGauge.redraw(result.getUsage(result.resources.cpus));
                    memGauge.redraw(result.getUsage(result.resources.mem));
                    diskGauge.redraw(result.getUsage(result.resources.disk));
                    vm.schedulerStatus = result.scheduler.state.name === 'PAUSED' ? 'Scheduler is Paused' : 'Scheduler is Running';
                    vm.schedulerStatusClass = result.scheduler.state.name === 'PAUSED' ? 'alert-warning' : 'alert-success';
                    vm.schedulerIsPaused = result.scheduler.state.name === 'PAUSED';
                    vm.schedulerBtnClass = result.scheduler.state.name === 'PAUSED' ? 'fa-play' : 'fa-pause';
                    memChartOptions.data.columns = [
                        ['Offered', result.resources.mem.offered],
                        ['Running', result.resources.mem.running],
                        ['Free', result.resources.mem.free],
                        ['Unavailable', result.resources.mem.unavailable]
                    ];
                    cpuChartOptions.data.columns = [
                        ['Offered', result.resources.cpus.offered],
                        ['Running', result.resources.cpus.running],
                        ['Free', result.resources.cpus.free],
                        ['Unavailable', result.resources.cpus.unavailable]
                    ];
                    diskChartOptions.data.columns = [
                        ['Offered', result.resources.disk.offered],
                        ['Running', result.resources.disk.running],
                        ['Free', result.resources.disk.free],
                        ['Unavailable', result.resources.disk.unavailable]
                    ];
                    gpuChartOptions.data.columns = [
                        ['Offered', result.resources.gpus.offered],
                        ['Running', result.resources.gpus.running],
                        ['Free', result.resources.gpus.free],
                        ['Unavailable', result.resources.gpus.unavailable]
                    ];
                    memChart = c3.generate(memChartOptions);
                    cpuChart = c3.generate(cpuChartOptions);
                    diskChart = c3.generate(diskChartOptions);
                    gpuChart = c3.generate(gpuChartOptions);
                    vm.memValue = scaleService.calculateFileSizeFromMib(result.resources.mem.total);
                    vm.cpuValue = result.resources.cpus.total;
                    vm.diskValue = scaleService.calculateFileSizeFromMib(result.resources.disk.total);
                    vm.gpuValue = result.resources.gpus.total;
                } else {
                    vm.statusError = result.statusText && result.statusText !== '' ? result.statusText : 'Unable to retrieve cluster status.';
                    cpuGauge.redraw(-1);
                    memGauge.redraw(-1);
                    diskGauge.redraw(-1);
                    vm.schedulerContainerClass = 'col-xs-12';
                    vm.schedulerStatus = 'Scheduler Status is Unknown';
                    vm.schedulerStatusClass = 'alert-danger';
                }
                vm.loadingStatus = false;
            });
        };

        var getNodeStatus = function () {
            statusService.getStatus(true).then(null, null, function (data) {
                if (data.$resolved) {
                    vm.nodeHealthError = null;
                    vm.nodes = _.filter(data.nodes, { is_active: true });
                } else {
                    if (data.statusText && data.statusText !== '') {
                        vm.nodeHealthErrorStatus = data.statusText;
                    }
                    vm.nodeHealthError = 'Unable to retrieve nodes.';
                }
                vm.loadingNodeHealth = false;
            });
        };

        $rootScope.$on('jobTypeStatus', function (event, data) {
            vm.jobData.status = data;
            redrawGrid();
        });

        var initialize = function () {
            getJobTypes();
            getStatus();
            getNodeStatus();
            navService.updateLocation('overview');
        };

        initialize();
    });
})();
