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
        vm.schedulerStatus = '';
        vm.schedulerStatusClass = 'alert-success';
        vm.schedulerIsPaused = false;
        vm.user = userService.getUserCreds();
        vm.schedulerContainerClass = vm.user ? vm.user.is_admin ? 'col-xs-8 col-lg-10' : 'col-xs-12' : 'col-xs-12';
        vm.schedulerBtnClass = 'fa-pause';
        vm.toggleBtnClass = null;

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
            statusService.getStatus().then(null, null, function (result) {
                if (result.$resolved) {
                    vm.statusError = null;
                    vm.status = result;
                    vm.schedulerStatus = result.scheduler.state.name === 'PAUSED' ? 'Scheduler is Paused' : 'Scheduler is Running';
                    vm.schedulerStatusClass = result.scheduler.state.name === 'PAUSED' ? 'alert-warning' : 'alert-success';
                    vm.schedulerIsPaused = result.scheduler.state.name === 'PAUSED';
                    vm.schedulerBtnClass = result.scheduler.state.name === 'PAUSED' ? 'fa-play' : 'fa-pause';
                } else {
                    vm.statusError = result.statusText && result.statusText !== '' ? result.statusText : 'Unable to retrieve cluster status.';
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
