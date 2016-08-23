(function () {
    'use strict';

    angular.module('scaleApp').service('jobExecutionService', function ($http, $q, $resource, poller, scaleConfig, JobExecution, JobExecutionLog) {

        var getJobExecutionsParams = function (page, page_size, started, ended, order, status, job_type_id, job_type_name, job_type_category, node_id) {
            return {
                page: page,
                page_size: page_size,
                started: started,
                ended: ended,
                order: order,
                status: status,
                job_type_id: job_type_id,
                job_type_name: job_type_name,
                job_type_category: job_type_category,
                node_id: node_id
            };
        };

        return {
            getJobExecutions: function (params) {
                params = params || getJobExecutionsParams();
                var d = $q.defer();

                $http({
                    url: scaleConfig.getUrlPrefix('job-executions') + 'job-executions/',
                    method: 'GET',
                    params: params
                }).success(function (data) {
                    data.results = JobExecution.transformer(data.results);
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getJobExecutionDetails: function (id) {
                var d = $q.defer();

                $http.get(scaleConfig.getUrlPrefix('job-executions') + 'job-executions/' + id + '/').success(function (data) {
                    d.resolve(JobExecution.transformer(data));
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getLogOnce: function(execId){
                var d = $q.defer();

                $http({
                    method: 'GET',
                    url: scaleConfig.getUrlPrefix('job-executions') + 'job-executions/' + execId + '/logs/combined/'
                }).success(function (data) {
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getLog: function(execId){
                var url = url || scaleConfig.getUrlPrefix('job-executions') + 'job-executions/' + execId + '/logs/combined/';

                // Update view. Since a promise can only be resolved or rejected once but we want
                // to keep track of all requests, poller service uses the notifyCallback. By default
                // poller only gets notified of success responses.
                var jobExecutionLogResource = $resource(url,{},{
                    get:{
                        method:'GET'
                    }
                });

                var jobExecutionLogPoller = poller.get(jobExecutionLogResource, {
                        action: 'get',
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
