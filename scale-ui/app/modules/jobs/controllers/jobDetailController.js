(function () {
    'use strict';

    angular.module('scaleApp').controller('jobDetailController', function ($scope, $rootScope, $location, $routeParams, $uibModal, navService, jobService, jobExecutionService, nodeService, loadService, scaleConfig, subnavService, userService, scaleService, toastr) {
        $scope.job = {};
        $scope.jobId = $routeParams.id;
        $scope.subnavLinks = scaleConfig.subnavLinks.jobs;
        subnavService.setCurrentPath('jobs');
        $scope.loadingJobDetail = false;
        $scope.latestExecution = null;
        $scope.executionLog = null;
        $scope.executionDetails = null;
        $scope.selectedExectuionDetailValues = null;
        $scope.timeline = [];
        $scope.readonly = true;
        $scope.jobErrorCreated = '';
        $scope.jobErrorLastModified = '';
        $scope.lastStatusChange = '';
        $scope.triggerOccurred = '';

        $scope.showLog = function (execution) {
            $scope.selectedExecutionLog = execution;
            var modalInstance = $uibModal.open({
                animation: true,
                templateUrl: 'showLog.html',
                scope: $scope,
                //size: 'lg',
                windowClass: 'log-modal-window'
            });
        };

        $scope.showExecutionDetails = function (executionId) {
            jobExecutionService.getJobExecutionDetails(executionId).then(function (data) {
                $scope.selectedExecutionDetails = data;
                $scope.selectedExecutionDetailValues = _.pairs(data);
                var modalInstance = $uibModal.open({
                    animation: true,
                    templateUrl: 'showExecutionDetails.html',
                    scope: $scope,
                    size: 'lg'
                });
            });
        };

        $scope.mediaTypeClass = function (mediaType) {
            var mediaTypeCfg = _.find(scaleConfig.mediaTypes, 'mimeType', mediaType);
            if (mediaTypeCfg) {
                return mediaTypeCfg.icon;
            } else {
                return null;
            }
        };

        $scope.requeueJob = function (jobId) {
            $scope.loading = true;
            loadService.requeueJobs({ job_ids: [jobId] }).then(function (data) {
                toastr['success']('Requeued Job');
                $scope.job.status = data.job_status;
                getJobDetail(jobId);
            }).catch(function (error) {
                toastr['error']('Requeue request failed');
                console.log(error);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        $scope.cancelJob = function (job) {
            $scope.loading = true;
            $scope.actionClicked = true;
            $scope.loading = true;
            var originalStatus = job.status;
            job.status = 'CANCEL';
            jobService.updateJob(job.id, { status: 'CANCELED' }).then(function (data) {
                toastr['success']('Job Canceled');
                job.status = 'CANCELED';
            }).catch(function (error) {
                toastr['error'](error);
                console.log(error);
                job.status = originalStatus;
            }).finally(function () {
                $scope.loading = false;
            });
        };
        
        $scope.calculateFileSize = function (size) {
            return scaleService.calculateFileSizeFromBytes(size);
        };

        var getJobDetail = function (jobId) {
            $scope.loadingJobDetail = true;
            jobService.getJobDetail(jobId).then(function (data) {
                $scope.job = data;
                $scope.timeline = calculateTimeline(data);
                // $scope.publishedProducts = _.where(data.products, { 'is_published': true });
                // $scope.unpublishedProducts = _.where(data.products, { 'is_published': false });
                // $scope.publishedProductsGrouped = _.pairs(_.groupBy($scope.publishedProducts, 'job_exe.id'));
                $scope.latestExecution = data.getLatestExecution();
                $scope.jobErrorCreated = data.error ? moment.utc(data.error.created).toISOString() : '';
                $scope.lastStatusChange = data.last_status_change ? moment.duration(moment.utc(data.last_status_change).diff(moment.utc())).humanize(true) : '';
                $scope.triggerOccurred = data.event.occurred ? moment.duration(moment.utc(data.event.occurred).diff(moment.utc())).humanize(true) : '';
                $scope.inputs = data.inputs;
                $scope.outputs = data.outputs;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                $scope.loadingJobDetail = false;
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

            $rootScope.user = userService.getUserCreds();
            if($rootScope.user){
                $scope.readonly = false;
            }

            getJobDetail($scope.jobId);
        };

        initialize();
    });
})();
