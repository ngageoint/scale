(function () {
    'use strict';

    angular.module('scaleApp').service('stateService', function ($location) {
        var version = '',
            jobsColDefs = [],
            jobsParams = {},
            jobExecutionsParams = {},
            recipesColDefs = [],
            jobTypesFailureRatesParams = {},
            recipesParams = {},
            ingestsColDefs = [],
            ingestsParams = {},
            nodesColDefs = [],
            nodeStatusParams = {},
            showActiveWorkspaces = true,
            nodesParams = {},
            logArgs = [],
            jobExecutionLogPoller = {};

        var updateQuerystring = function (data) {
            // set defaults
            data.page = data.page || 1;
            data.page_size = data.page_size || 25;
            data.started = data.started || null;
            data.ended = data.ended || null;
            data.order = data.order ? Array.isArray(data.order) ? data.order : [data.order] : null;
            data.status = data.status || null;
            // check for params in querystring, and update as necessary
            _.forEach(_.pairs(data), function (param) {
                $location.search(param[0], param[1]);
            });
        };

        var initJobsParams = function (data) {
            return {
                page: data.page ? parseInt(data.page) : 1,
                page_size: data.page_size ? parseInt(data.page_size) : 25,
                started: data.started ? data.started : moment.utc().subtract(1, 'weeks').startOf('d').toISOString(),
                ended: data.ended ? data.ended : moment.utc().endOf('d').toISOString(),
                order: data.order ? Array.isArray(data.order) ? data.order : [data.order] : ['-last_modified'],
                status: data.status ? data.status : null,
                error_category: data.error_category ? data.error_category : null,
                job_type_id: data.job_type_id ? parseInt(data.job_type_id) : null,
                job_type_name: data.job_type_name ? data.job_type_name : null,
                job_type_category: data.job_type_category ? data.job_type_category : null,
                url: null
            };
        };

        var initJobExecutionsParams = function (data) {
            return {
                page: data.page ? parseInt(data.page) : 1,
                page_size: data.page_size ? parseInt(data.page_size) : 25,
                started: data.started ? data.started : moment.utc().subtract(1, 'weeks').startOf('d').toISOString(),
                ended: data.ended ? data.ended : moment.utc().endOf('d').toISOString(),
                order: data.order ? Array.isArray(data.order) ? data.order : [data.order] : ['-last_modified'],
                status: data.status ? data.status : null,
                job_type_id: data.job_type_id ? parseInt(data.job_type_id) : null,
                job_type_name: data.job_type_name ? data.job_type_name : null,
                job_type_category: data.job_type_category ? data.job_type_category : null,
                node_id: data.node_id ? data.node_id : null
            };
        };

        var initJobTypesFailureRatesParams = function (data) {
            return {
                page: null,
                page_size: null,
                started: null,
                ended: null,
                name: data.name ? data.name : null,
                category: null,
                order: null
            };
        };

        var initRecipesParams = function (data) {
            return {
                page: data.page ? parseInt(data.page) : 1,
                page_size: data.page_size ? parseInt(data.page_size) : 25,
                started: data.started ? data.started : moment.utc().subtract(1, 'weeks').startOf('d').toISOString(),
                ended: data.ended ? data.ended : moment.utc().endOf('d').toISOString(),
                order: data.order ? Array.isArray(data.order) ? data.order : [data.order] : ['-last_modified'],
                type_id: data.type_id ? parseInt(data.type_id) : null,
                type_name: data.type_name ? data.type_name : null,
                url: null
            };
        };

        var initIngestsParams = function (data) {
            return {
                page: data.page ? parseInt(data.page) : 1,
                page_size: data.page_size ? parseInt(data.page_size) : 25,
                started: data.started ? data.started : moment.utc().subtract(1, 'weeks').startOf('d').toISOString(),
                ended: data.ended ? data.ended : moment.utc().endOf('d').toISOString(),
                order: data.order ? Array.isArray(data.order) ? data.order : [data.order] : ['-ingest_started'],
                status: data.status ? data.status : null,
                file_name: data.file_name ? data.file_name : null
            };
        };

        var initNodesParams = function (data) {
            return {
                page: data.page ? parseInt(data.page) : 1,
                page_size: data.page_size ? parseInt(data.page_size) : 25,
                order: data.order ? Array.isArray(data.order) ? data.order : [data.order] : ['hostname'],
                include_inactive: data.include_inactive ? data.include_inactive : null
            };
        };

        var initNodeStatusParams = function (data) {
            return {
                page: data.page ? parseInt(data.page) : 1,
                page_size: data.page_size ? parseInt(data.page_size) : 25,
                started: data.started ? data.started : moment.utc().subtract(3, 'hours').toISOString(),
                ended: data.ended ? data.ended : moment.utc().toISOString()
            };
        };

        return {
            getVersion: function () {
                return version;
            },
            setVersion: function (data) {
                version = data;
            },
            getJobsColDefs: function () {
                return jobsColDefs;
            },
            setJobsColDefs: function (data) {
                jobsColDefs = data;
            },
            getJobsParams: function () {
                if (_.keys(jobsParams).length === 0) {
                    return initJobsParams($location.search());
                }
                return jobsParams;
            },
            setJobsParams: function (data) {
                jobsParams = initJobsParams(data);
                updateQuerystring(jobsParams);
            },
            getJobExecutionsParams: function () {
                if (_.keys(jobExecutionsParams).length === 0) {
                    return initJobExecutionsParams($location.search());
                }
                return jobExecutionsParams;
            },
            setJobExecutionsParams: function (data) {
                jobExecutionsParams = initJobExecutionsParams(data);
                updateQuerystring(jobExecutionsParams);
            },
            getJobTypesFailureRatesParams: function () {
                if (_.keys(jobTypesFailureRatesParams).length === 0) {
                    return initJobTypesFailureRatesParams($location.search());
                }
                return jobTypesFailureRatesParams;
            },
            setJobTypesFailureRatesParams: function (data) {
                jobTypesFailureRatesParams = initJobTypesFailureRatesParams(data);
                _.forEach(_.pairs(jobTypesFailureRatesParams), function (param) {
                    $location.search(param[0], param[1]);
                });
            },
            getRecipesColDefs: function () {
                return recipesColDefs;
            },
            setRecipesColDefs: function (data) {
                recipesColDefs = data;
            },
            getRecipesParams: function () {
                if (_.keys(recipesParams).length === 0) {
                    return initRecipesParams($location.search());
                }
                return recipesParams;
            },
            setRecipesParams: function (data) {
                recipesParams = initRecipesParams(data);
                updateQuerystring(recipesParams);
            },
            getIngestsColDefs: function () {
                return ingestsColDefs;
            },
            setIngestsColDefs: function (data) {
                ingestsColDefs = data;
            },
            getIngestsParams: function () {
                if (_.keys(ingestsParams).length === 0) {
                    return initIngestsParams($location.search());
                }
                return ingestsParams;
            },
            setIngestsParams: function (data) {
                ingestsParams = initIngestsParams(data);
                updateQuerystring(ingestsParams);
            },
            getNodesColDefs: function () {
                return nodesColDefs;
            },
            setNodesColDefs: function (data) {
                nodesColDefs = data;
            },
            getNodeStatusParams: function () {
                if (_.keys(nodeStatusParams).length === 0) {
                    return initNodeStatusParams($location.search());
                }
                return nodeStatusParams;
            },
            setNodeStatusParams: function (data) {
                nodeStatusParams = initNodeStatusParams(data);
                updateQuerystring(nodeStatusParams);
            },
            getShowActiveWorkspaces: function () {
                return showActiveWorkspaces;
            },
            setShowActiveWorkspaces: function (data) {
                showActiveWorkspaces = data;
            },
            getNodesParams: function () {
                if (_.keys(nodesParams).length === 0) {
                    return initNodesParams($location.search());
                }
                return nodesParams;
            },
            setNodesParams: function (data) {
                nodesParams = initNodesParams(data);
                updateQuerystring(nodesParams);
            },
            getLogArgs: function () {
                return logArgs;
            },
            setLogArgs: function (data) {
                logArgs = data;
            },
            getJobExecutionLogPoller: function () {
                return jobExecutionLogPoller;
            },
            setJobExecutionLogPoller: function (data) {
                jobExecutionLogPoller = data;
            }
        };
    });
})();
