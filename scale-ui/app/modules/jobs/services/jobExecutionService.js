(function () {
    'use strict';

    angular.module('scaleApp').service('jobExecutionService', function ($http, $q, $resource, poller, scaleConfig, JobExecution, JobExecutionLog) {

        var getJobExecutionsParams = function( pageNumber, pageSize, filter ){
            var params = {
                page: pageNumber,
                page_size: pageSize
            };
            var jobTypeId = filter.job_type_id ? filter.jobTypeId : '';
            var jobStatus = filter.status ? filter.jobStatus : '';

            if (jobStatus && jobStatus !== '') {
                params.job_status = jobStatus;
            }
            return params;
        };

        return {
            getJobExecutions: function (pageNumber, pageSize, filter) {
                var jobExecutions = [],
                    d = $q.defer();

                var params = getJobExecutionsParams(pageNumber, pageSize, filter);
                $http({
                    url: scaleConfig.urls.apiPrefix + 'job-executions/',
                    method: 'GET',
                    params: params
                }).success(function (data) {
                    jobExecutions.executions = JobExecution.transformer(data.results);
                    jobExecutions.count = data.count;
                    d.resolve(jobExecutions);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getJobExecutionDetails: function (id) {
                var d = $q.defer();

                $http.get(scaleConfig.urls.apiPrefix + 'job-executions/' + id + '/').success(function (data) {
                    d.resolve(JobExecution.transformer(data));
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getLogOnce: function(execId){
                var d = $q.defer();

                $http.get(scaleConfig.urls.apiPrefix + 'job-executions/' + execId + '/logs/').success(function (data) {
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getLog: function(execId){
                var url = url || scaleConfig.urls.apiPrefix + 'job-executions/' + execId + '/logs/';

                // Update view. Since a promise can only be resolved or rejected once but we want
                // to keep track of all requests, poller service uses the notifyCallback. By default
                // poller only gets notified of success responses.
                var jobExecutionLogResource = $resource(url);
                var jobExecutionLogPoller = poller.get(jobExecutionLogResource, {
                        delay: scaleConfig.pollIntervals.jobExecutionLog
                    });

                return jobExecutionLogPoller.promise.then(null, null, function (result) {
                    if(result.$resolved){
                        result.execution_log = JobExecutionLog.transformer(result);
                        if(result.execution_log.status === 'COMPLETED' || result.execution_log.status === 'FAILED'){
                            jobExecutionLogPoller.stop();
                        }
                        return result;
                    } else {
                        jobExecutionLogPoller.stop();
                        return result;
                    }

                });
            }
        };
    });
})();
