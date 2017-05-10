(function () {
    'use strict';

    angular.module('scaleApp').controller('ovController', function($rootScope, $scope, navService, nodeService, jobService, jobTypeService, statusService, gaugeFactory, scaleConfig, scaleService, schedulerService, userService) {
        var vm = this;
        
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
        vm.masterStatus = '';
        vm.masterStatusClass = 'alert-success';
        vm.schedulerStatus = '';
        vm.schedulerStatusClass = 'alert-success';
        vm.memCalc = '';
        vm.diskCalc = '';
        vm.schedulerIsPaused = false;
        vm.user = userService.getUserCreds();
        vm.schedulerContainerClass = vm.user ? vm.user.is_admin ? 'col-xs-8 col-lg-10' : 'col-xs-12' : 'col-xs-12';
        vm.schedulerBtnClass = 'fa-pause';

        vm.toggleScheduler = function () {
            vm.schedulerIsPaused = !vm.schedulerIsPaused;
            var schedulerData = {
                is_paused: vm.schedulerIsPaused
            };
            schedulerService.updateScheduler(schedulerData).then(function (data) {
                vm.schedulerStatus = data.is_paused ? 'Paused' : 'Running';
                vm.schedulerStatusClass = data.is_paused ? 'alert-warning' : 'alert-success';
                vm.schedulerBtnClass = data.is_paused ? 'fa-play' : 'fa-pause';
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
                    cpuGauge.redraw(result.getCpuUsage());
                    memGauge.redraw(result.getMemUsage());
                    diskGauge.redraw(result.getDiskUsage());
                    vm.masterStatus = result.master.is_online ? 'Master is Online' : 'Master is Offline';
                    vm.masterStatusClass = result.master.is_online ? 'alert-success' : 'alert-danger';
                    if (result.scheduler.is_online) {
                        vm.schedulerStatus = result.scheduler.is_paused ? 'Scheduler is Paused' : 'Scheduler is Running';
                        vm.schedulerStatusClass = result.scheduler.is_paused ? 'alert-warning' : 'alert-success';
                        vm.schedulerIsPaused = result.scheduler.is_paused;
                        vm.schedulerBtnClass = result.scheduler.is_paused ? 'fa-play' : 'fa-pause';
                    } else {
                        vm.schedulerStatus = result.scheduler.is_paused ? 'Scheduler is Offline; Paused' : 'Scheduler is Offline';
                        vm.schedulerStatusClass = 'alert-danger';
                        vm.schedulerIsPaused = result.scheduler.is_paused;
                        vm.schedulerBtnClass = result.scheduler.is_paused ? 'fa-play' : 'fa-pause';
                    }
                    if (result.resources.scheduled.mem && result.resources.total.mem) {
                        vm.memCalc = scaleService.calculateFileSizeFromMib(result.resources.scheduled.mem) + ' / ' + scaleService.calculateFileSizeFromMib(result.resources.total.mem);
                    }
                    if (result.resources.scheduled.disk && result.resources.total.disk) {
                        vm.diskCalc = scaleService.calculateFileSizeFromMib(result.resources.scheduled.disk) + ' / ' + scaleService.calculateFileSizeFromMib(result.resources.total.disk);
                    }
                } else {
                    vm.statusError = result.statusText && result.statusText !== '' ? result.statusText : 'Unable to retrieve cluster status.';
                    cpuGauge.redraw(-1);
                    memGauge.redraw(-1);
                    diskGauge.redraw(-1);
                    vm.masterStatus = 'Master Status is Unknown';
                    vm.masterStatusClass = 'alert-danger';
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
                    vm.nodes = data.nodes;
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
