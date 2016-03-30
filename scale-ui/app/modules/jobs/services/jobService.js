(function () {
    'use strict';

    angular.module('scaleApp').service('jobService', function($http, $q, $resource, scaleConfig, Job, JobDetails, RunningJob, poller, pollerFactory) {

        var getJobsParams = function (page, page_size, started, ended, order, status, job_type_id, job_type_name, job_type_category, url) {
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
                url: url
            };
        };

        var getJobUpdateData = function (status) {
            return {
                status: status
            };
        };

        return {
            getJobs: function (params) {
                params = params || getJobsParams();
                params.url = params.url ? params.url : scaleConfig.urls.apiPrefix + 'jobs/';

                var jobsResource = $resource(params.url, params),
                    jobsPoller = pollerFactory.newPoller(jobsResource, scaleConfig.pollIntervals.jobs);

                return jobsPoller.promise.then(null, null, function (data) {
                    if (data.$resolved) {
                        data.results = Job.transformer(data.results);
                    } else {
                        jobsPoller.stop();
                    }
                    return data;
                });
            },
            getJobsOnce: function (params) {
                params = params || getJobsParams();
                var d = $q.defer();

                $http({
                    url: params.url ? params.url : scaleConfig.urls.apiPrefix + 'jobs/',
                    method: 'GET',
                    params: params
                }).success(function (data) {
                    data.results = Job.transformer(data.results);
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });

                return d.promise;
            },
            getJobCountsByStatus: function (hour) {
                hour = hour || 3;
                var d = $q.defer();

                $http.get(scaleConfig.urls.getJobCountsByStatus(hour)).success(function (data) {
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getJobDetail: function (id) {
                var d = $q.defer();
                $http.get(scaleConfig.urls.apiPrefix + 'jobs/' + id + '/').success(function (data) {
                    d.resolve(JobDetails.transformer(data));
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getRunningJobs: function (pageNumber, pageSize) {
                var params = {
                    pageNumber: pageNumber,
                    pageSize: pageSize
                };
                var runningJobsResource = $resource(scaleConfig.urls.apiPrefix + 'job-types/running/', params),
                    runningJobsPoller = pollerFactory.newPoller(runningJobsResource, scaleConfig.pollIntervals.runningJobs);

                return runningJobsPoller.promise.then(null, null, function (data) {
                    if (data.$resolved) {
                        data.results = RunningJob.transformer(data.results);
                    } else {
                        runningJobsPoller.stop();
                    }
                    return data;
                });
            },
            getRunningJobsOnce: function (pageNumber, pageSize) {
                var params = {
                    pageNumber: pageNumber,
                    pageSize: pageSize
                };
                var d = $q.defer();

                $http.get(scaleConfig.urls.apiPrefix + 'job-types/running/', params).success(function (data) {
                    data.results = RunningJob.transformer(data.results);
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            updateJob: function (id, data) {
                data = data || getJobUpdateData();
                var d = $q.defer();

                $http({
                    url: scaleConfig.urls.apiPrefix + 'jobs/' + id + '/',
                    method: 'PATCH',
                    data: data
                }).success(function (result) {
                    d.resolve(result);
                }).error(function (error) {
                    d.reject(error);
                });

                return d.promise;
            }
        };
    });
})();
