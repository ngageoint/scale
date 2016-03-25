(function () {
    'use strict';

    angular.module('scaleApp').service('loadService', function($http, $q, $resource, scaleConfig, poller, pollerFactory, QueueStatus) {
        var getJobLoadParams = function (page, page_size, started, ended, order, status, job_type_id, job_type_name, job_type_category, url) {
            return {
                started: started,
                ended: ended,
                job_type_id: job_type_id,
                job_type_name: job_type_name,
                job_type_category: job_type_category,
                page_size: 1000,
                url: url
            };
        };

        var getRequeueJobsParams = function (started, ended, job_status, job_type_ids, job_type_names, job_type_categories, priority, url) {
            return {
                started: started,
                ended: ended,
                job_status: job_status,
                job_ids: job_ids,
                job_type_ids: job_type_ids,
                job_type_names: job_type_names,
                job_type_categories: job_type_categories,
                priority: priority,
                url: url
            };
        };

        return {
            getQueue: function (pageNumber, pageSize) {
                var d = $q.defer();

                $http.get(scaleConfig.urls.getQueue(pageNumber, pageSize)).success(function (data) {
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });

                return d.promise;
            },
            getQueueStatus: function () {
                var queueStatusResource = $resource(scaleConfig.urls.getQueueStatus()),
                    queueStatusPoller = pollerFactory.newPoller(queueStatusResource, scaleConfig.pollIntervals.queueStatus);

                return queueStatusPoller.promise.then(null, null, function (result) {
                    if (result.$resolved) {
                        result.queue_status = QueueStatus.transformer(result.queue_status);
                    } else {
                        queueStatusPoller.stop();
                    }
                    return result;
                });
            },
            getQueueStatusOnce: function () {
                var d = $q.defer();

                $http.get(scaleConfig.urls.getQueueStatus()).success(function (data) {
                    var returnData = QueueStatus.transformer(data.queue_status);
                    d.resolve(returnData);
                }).error(function (error) {
                    d.reject(error);
                });

                return d.promise;
            },
            requeueJobs: function (params) {
                params = params || getRequeueJobsParams();
                params.url = params.url ? params.url : scaleConfig.urls.requeueJobs();

                var d = $q.defer();

                $http.post(params.url, params).success(function (result) {
                    d.resolve(result);
                }).error(function(error){
                    d.reject(error);
                });

                return d.promise;
            },
            getJobLoad: function (params) {
                params = params || getJobLoadParams();
                params.url = params.url ? params.url : scaleConfig.urls.getJobLoad();

                var jobLoadResource = $resource(params.url, params),
                    jobLoadPoller = pollerFactory.newPoller(jobLoadResource, scaleConfig.pollIntervals.jobLoad);

                return jobLoadPoller.promise.then(null, null, function (data) {
                    if (!data.$resolved) {
                        jobLoadPoller.stop();
                    }
                    return data;
                });
            },
            getJobLoadOnce: function (params) {
                params = params || getJobLoadParams();
                var d = $q.defer();

                $http({
                    url: params.url ? params.url : scaleConfig.urls.getJobLoad(),
                    method: 'GET',
                    params: params
                }).success(function (data) {
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });

                return d.promise;
            }
        };
    });
})();
