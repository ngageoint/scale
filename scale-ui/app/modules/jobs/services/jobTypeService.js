(function () {
    'use strict';

    angular.module('scaleApp').service('jobTypeService', function ($http, $q, $resource, poller, pollerFactory, scaleConfig, jobService, JobType, JobTypeDetails, JobTypeStatus) {
        /*var totalJobTypes = 5;

        var getTotalJobTypes = function () {
            return totalJobTypes;
        };

        var setTotalJobTypes = function () {
            totalJobTypes = Math.floor(Math.random() * (20 - 1 + 1)) + 1;
        };

        setInterval(function () {
            setTotalJobTypes();
        }, 3100);*/

        var getJobTypeParams = function (page, page_size, started, ended, name, category, order) {
            return {
                page: page,
                page_size: page_size ? page_size : 1000,
                started: started,
                ended: ended,
                name: name,
                category: category,
                order: order ? order : ['title', 'version']
            };
        };

        var getJobTypeStatusParams = function (page, page_size, started, ended) {
            return {
                page: page,
                page_size: page_size ? page_size : 1000,
                started: started,
                ended: ended
            };
        };

        return {
            getJobTypes: function (params) {
                params = params || getJobTypeParams();
                // var params = {
                //     order: order || ['name','version']
                // };

                var jobTypesResource = $resource(scaleConfig.getUrlPrefix('job-types') + 'job-types/', params),
                    jobTypesPoller = pollerFactory.newPoller(jobTypesResource, scaleConfig.pollIntervals.jobTypes);

                return jobTypesPoller.promise.then(null, null, function (data) {
                    if (data.$resolved) {
                        /*var returnResult = {
                            $resolved: true,
                            job_types: []
                        };
                        for (var i = 1; i < getTotalJobTypes(); i++) {
                            returnResult.job_types.push(
                                {
                                    "is_system": true,
                                    "paused": null,
                                    "disk": 64.0,
                                    "id": i,
                                    "docker_image": null,
                                    "archived": null,
                                    "uses_docker": false,
                                    "priority": 10,
                                    "version": "1.0",
                                    "icon_code": scaleConfig.jobTypes[i - 1].code,
                                    "description": "Ingests a source file into a workspace",
                                    "mem": 64.0,
                                    "is_active": true,
                                    "cpus": 1.0,
                                    "last_modified": "2015-03-11T00:00:00Z",
                                    "max_tries": 3,
                                    "is_paused": false,
                                    "name": scaleConfig.jobTypes[i - 1].title,
                                    "created": "2015-03-11T00:00:00Z",
                                    "timeout": 1800,
                                    "is_long_running": false
                                }
                            )
                        }
                        result = returnResult;*/

                        data.results = JobType.transformer(data.results);
                        return data;
                    } else {
                        jobTypesPoller.stop();
                        return data;
                    }
                });
            },
            getJobTypesOnce: function (params) {
                params = params || getJobTypeParams();

                var d = $q.defer();

                $http({
                    url: scaleConfig.getUrlPrefix('job-types') + 'job-types/',
                    method: 'GET',
                    params: params
                }).success(function (data) {
                    data.results = JobType.transformer(data.results);
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getJobTypeStatus: function (params) {
                params = params || getJobTypeStatusParams();

                var jobTypeStatusResource = $resource(scaleConfig.getUrlPrefix('job-types') + 'job-types/status/', params),
                    jobTypeStatusPoller = pollerFactory.newPoller(jobTypeStatusResource, scaleConfig.pollIntervals.jobTypeStatus);

                return jobTypeStatusPoller.promise.then(null, null, function (data) {
                    if (data.$resolved) {
                        /*var returndata = {
                            $resolved: true,
                            job_type_stats: []
                        };
                        for (var i = 0; i < getTotalJobTypes(); i++) {
                            returndata.job_type_stats.push(
                                {
                                    "id": i,
                                    "icon_code": "",
                                    "name": "",
                                    "version": "",
                                    "num_completed": Math.floor(Math.random() * (20000 - 10000 + 1)) + 10000,
                                    "num_canceled": Math.floor(Math.random() * (100 - 20 + 1)) + 20,
                                    "num_error_DATA": Math.floor(Math.random() * (9000 - 20 + 1)) + 20,
                                    "num_error_SYSTEM": Math.floor(Math.random() * (9000 - 20 + 1)) + 20,
                                    "num_error_ALGORITHM": Math.floor(Math.random() * (9000 - 20 + 1)) + 20
                                }
                            )
                        }
                        data = returndata;*/

                        data.results = JobTypeStatus.transformer(data.results);
                    } else {
                        jobTypeStatusPoller.stop();
                    }
                    return data;
                });
            },
            getJobTypeStatusOnce: function (params) {
                var d = $q.defer();

                params = params || getJobTypeStatusParams();

                $http({
                    url: scaleConfig.getUrlPrefix('job-types') + 'job-types/status/',
                    method: 'GET',
                    params: params
                }).success(function (data) {
                    data.results = JobTypeStatus.transformer(data.results);
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getJobTypeDetails: function (id) {
                var d = $q.defer();
                $http.get(scaleConfig.getUrlPrefix('job-types') + 'job-types/' + id + '/').success(function (data) {
                    d.resolve(JobTypeDetails.transformer(data));
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            updateJobType: function (data){
                var updatedJobType = function(data){
                    return {
                        error_mappings: data.error_mappings,
                        is_paused: data.is_paused
                    };
                };
                var updatedData = updatedJobType(data);
                var d = $q.defer();

                $http({
                    url: scaleConfig.getUrlPrefix('job-types') + 'job-types/' + data.id + '/',
                    method: 'PATCH',
                    data: updatedData
                }).success(function (result) {
                    d.resolve(JobTypeDetails.transformer(result));
                }).error(function (error) {
                    d.reject(error);
                });                
                return d.promise;
            }
        };
    });
})();
