(function () {
    'use strict';

    angular.module('scaleApp').controller('ovController', function($rootScope, $scope, navService, nodeService, jobService, jobTypeService, statusService, gaugeFactory, scaleConfig, scaleService, schedulerService, userService) {
        $scope.date = new Date();
        $scope.jobError = null;
        $scope.jobErrorStatus = null;
        $scope.loadingJobs = true;
        $scope.jobTypes = [];
        $scope.hourValue = 3;
        $scope.jobData = {
            data: null,
            status: null
        };
        $scope.jobErrorBreakdown = [];
        $scope.status = null;
        $scope.statusError = null;
        $scope.loadingStatus = true;
        $scope.masterStatus = '';
        $scope.masterStatusClass = 'alert-success';
        $scope.schedulerStatus = '';
        $scope.schedulerStatusClass = 'alert-success';
        $scope.memCalc = '';
        $scope.diskCalc = '';
        $scope.schedulerIsPaused = false;
        $scope.user = userService.getUserCreds();
        $scope.schedulerContainerClass = $scope.user ? $scope.user.is_admin ? 'col-xs-8 col-lg-10' : 'col-xs-12' : 'col-xs-12';
        $scope.schedulerBtnClass = 'fa-pause';

        $scope.toggleScheduler = function () {
            $scope.schedulerIsPaused = !$scope.schedulerIsPaused;
            var schedulerData = {
                is_paused: $scope.schedulerIsPaused
            };
            schedulerService.updateScheduler(schedulerData).then(function (data) {
                $scope.schedulerStatus = data.is_paused ? 'Paused' : 'Running';
                $scope.schedulerStatusClass = data.is_paused ? 'alert-warning' : 'alert-success';
                $scope.schedulerBtnClass = data.is_paused ? 'fa-play' : 'fa-pause';
            }).catch(function (error) {
                console.log(error);
            });
        };

        var redrawGrid = function () {
            $scope.$broadcast('redrawGrid', $scope.jobData);
        };

        var getJobTypes = function () {
            jobTypeService.getJobTypes({ page_size: 1000 }).then(null, null, function (data) {
                if (data.$resolved) {
                    $scope.jobError = null;
                    $scope.jobData.data = data.results;
                    redrawGrid();
                } else {
                    if (data.statusText && data.statusText !== '') {
                        $scope.jobErrorStatus = data.statusText;
                    }
                    $scope.jobError = 'Unable to retrieve job types.'
                }
                $scope.loadingJobs = false
            });
        };

        var getStatus = function () {
            var cpuGauge = gaugeFactory.createGauge('cpu', 'CPU', 0, 100, 180),
                memGauge = gaugeFactory.createGauge('memory', 'Memory', 0, 100, 180),
                diskGauge = gaugeFactory.createGauge('disk', 'Disk', 0, 100, 180);

            statusService.getStatus().then(null, null, function (result) {
                if (result.$resolved) {
                    $scope.statusError = null;
                    $scope.status = result;
                    cpuGauge.redraw(result.getCpuUsage());
                    memGauge.redraw(result.getMemUsage());
                    diskGauge.redraw(result.getDiskUsage());
                    $scope.masterStatus = result.master.is_online ? 'Master is Online' : 'Master is Offline';
                    $scope.masterStatusClass = result.master.is_online ? 'alert-success' : 'alert-danger';
                    if (result.scheduler.is_online) {
                        $scope.schedulerStatus = result.scheduler.is_paused ? 'Scheduler is Paused' : 'Scheduler is Running';
                        $scope.schedulerStatusClass = result.scheduler.is_paused ? 'alert-warning' : 'alert-success';
                        $scope.schedulerIsPaused = result.scheduler.is_paused;
                        $scope.schedulerBtnClass = result.scheduler.is_paused ? 'fa-play' : 'fa-pause';
                    } else {
                        $scope.schedulerStatus = result.scheduler.is_paused ? 'Scheduler is Offline; Paused' : 'Scheduler is Offline';
                        $scope.schedulerStatusClass = 'alert-danger';
                        $scope.schedulerIsPaused = result.scheduler.is_paused;
                        $scope.schedulerBtnClass = result.scheduler.is_paused ? 'fa-play' : 'fa-pause';
                    }
                    if (result.resources.scheduled.mem && result.resources.total.mem) {
                        $scope.memCalc = scaleService.calculateFileSizeFromMib(result.resources.scheduled.mem) + ' / ' + scaleService.calculateFileSizeFromMib(result.resources.total.mem);
                    }
                    if (result.resources.scheduled.disk && result.resources.total.disk) {
                        $scope.diskCalc = scaleService.calculateFileSizeFromMib(result.resources.scheduled.disk) + ' / ' + scaleService.calculateFileSizeFromMib(result.resources.total.disk);
                    }
                } else {
                    $scope.statusError = result.statusText && result.statusText !== '' ? result.statusText : 'Unable to retrieve cluster status.';
                    cpuGauge.redraw(-1);
                    memGauge.redraw(-1);
                    diskGauge.redraw(-1);
                    $scope.masterStatus = 'Master Status is Unknown';
                    $scope.masterStatusClass = 'alert-danger';
                    $scope.schedulerContainerClass = 'col-xs-12';
                    $scope.schedulerStatus = 'Scheduler Status is Unknown';
                    $scope.schedulerStatusClass = 'alert-danger';
                }
                $scope.loadingStatus = false;
            });
        };

        $rootScope.$on('jobTypeStatus', function (event, data) {
            $scope.jobData.status = data;
            redrawGrid();
        });

        var initialize = function () {
            getJobTypes();
            getStatus();
            navService.updateLocation('overview');
        };

        initialize();
    });
})();
