(function () {
    'use strict';

    angular.module('scaleApp').controller('jobDetailController', function ($scope, $rootScope, $location, $routeParams, $uibModal, stateService, navService, jobService, jobExecutionService, nodeService, loadService, scaleConfig, subnavService, userService, scaleService, toastr) {
        var vm = this;
        
        vm.job = {};
        vm.jobId = $routeParams.id;
        vm.subnavLinks = scaleConfig.subnavLinks.jobs;
        subnavService.setCurrentPath('jobs');
        vm.loadingJobDetail = false;
        vm.latestExecution = null;
        vm.executionLog = null;
        vm.executionDetails = null;
        vm.selectedExecutionDetailValues = null;
        vm.timeline = [];
        vm.readonly = true;
        vm.jobErrorCreated = '';
        vm.jobErrorLastModified = '';
        vm.lastStatusChange = '';
        vm.triggerOccurred = '';

        vm.showLog = function (execution) {
            jobExecutionService.getJobExecutionDetails(execution.id).then(function(result){
                vm.selectedExecutionLog = result;
            });

            $uibModal.open({
                animation: true,
                templateUrl: 'showLog.html',
                scope: $scope,
                windowClass: 'log-modal-window'
            });
        };

        vm.showExecutionDetails = function (executionId) {
            jobExecutionService.getJobExecutionDetails(executionId).then(function (data) {
                vm.selectedExecutionDetails = data;
                vm.selectedExecutionDetailValues = _.pairs(data);
                $uibModal.open({
                    animation: true,
                    templateUrl: 'showExecutionDetails.html',
                    scope: $scope,
                    size: 'lg'
                });
            }).catch(function (error) {
                console.log(error);
            });
        };

        vm.requeueJob = function (jobId) {
            vm.loading = true;
            loadService.requeueJobs({ job_ids: [jobId] }).then(function (data) {
                toastr['success']('Requeued Job');
                vm.job.status = data.job_status;
                getJobDetail(jobId);
            }).catch(function (error) {
                toastr['error']('Requeue request failed');
                console.log(error);
            }).finally(function () {
                vm.loading = false;
            });
        };

        vm.cancelJob = function (job) {
            vm.loading = true;
            vm.actionClicked = true;
            vm.loading = true;
            var originalStatus = job.status;
            job.status = 'CANCEL';
            jobService.updateJob(job.id, { status: 'CANCELED' }).then(function () {
                toastr['success']('Job Canceled');
                job.status = 'CANCELED';
            }).catch(function (error) {
                toastr['error'](error);
                console.log(error);
                job.status = originalStatus;
            }).finally(function () {
                vm.loading = false;
            });
        };
        
        vm.calculateFileSize = function (size) {
            return scaleService.calculateFileSizeFromBytes(size);
        };

        var getJobDetail = function (jobId) {
            vm.loadingJobDetail = true;
            jobService.getJobDetail(jobId).then(function (data) {
                vm.job = data;
                vm.timeline = calculateTimeline(data);
                vm.latestExecution = data.getLatestExecution();
                vm.jobErrorCreated = data.error ? moment.utc(data.error.created).toISOString() : '';
                vm.lastStatusChange = data.last_status_change ? moment.duration(moment.utc(data.last_status_change).diff(moment.utc())).humanize(true) : '';
                vm.triggerOccurred = data.event.occurred ? moment.duration(moment.utc(data.event.occurred).diff(moment.utc())).humanize(true) : '';
                vm.inputs = data.inputs;
                vm.outputs = data.outputs;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                vm.loadingJobDetail = false;
            });
        };

        var calculateTimeline = function (job) {
            var tl = [];
            tl.push({ taskName: 'Created', started: job.created ? moment.utc(job.created).toDate() : job.created, ended: job.queued ? moment.utc(job.queued).toDate() : job.queued });
            tl.push({ taskName: 'Queued', started: job.queued ? moment.utc(job.queued).toDate() : job.queued, ended: job.started ? moment.utc(job.started).toDate() : job.started });
            tl.push({ taskName: 'Executed', started: job.started ? moment.utc(job.started).toDate() : job.started, ended: job.ended ? moment.utc(job.ended).toDate() : job.ended });

            return tl;
        };

        var initialize = function () {
            navService.updateLocation('jobs');
            var user = userService.getUserCreds();
            vm.readonly = !(user && user.is_admin);
            getJobDetail(vm.jobId);
        };

        initialize();
    });
})();
