(function () {
    'use strict';

    angular.module('scaleApp').service('stateService', function ($location) {
        var version = '',
            jobsColDefs = [],
            jobsParams = {},
            jobExecutionsParams = {},
            jobTypesParams = {},
            recipesColDefs = [],
            jobTypesFailureRatesParams = {},
            recipesParams = {},
            ingestsColDefs = [],
            ingestsParams = {},
            scansColDefs = [],
            scansParams = {},
            nodesColDefs = [],
            batchesColDefs = [],
            batchesParams = {},
            sourceFilesColDefs = [],
            sourceFilesParams = {},
            showActiveWorkspaces = true,
            nodesParams = {},
            logArgs = [],
            jobExecutionLogPoller = [];

        var updateQuerystring = function (data, excludeDefaults) {
            excludeDefaults = excludeDefaults || false;
            if (!excludeDefaults) {
                // set defaults
                data.page = data.page || 1;
                data.page_size = data.page_size || 25;
                data.started = data.started || null;
                data.ended = data.ended || null;
                data.order = data.order ? Array.isArray(data.order) ? data.order : [data.order] : null;
                data.status = data.status || null;
            }
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

        var initJobTypesParams = function (data){
            return {
                show_rd: typeof data.show_rd !== 'undefined' ? data.show_rd : true
            }
        };

        var initJobTypesFailureRatesParams = function (data) {
            return {
                page: null,
                page_size: null,
                started: null,
                ended: null,
                name: data.name ? data.name : null,
                version: data.version ? data.version : null,
                category: null,
                order: data.order ? data.order : 'desc',
                orderField: data.orderField ? data.orderField : 'twentyfour_hours',
                orderErrorType: data.orderErrorType ? data.orderErrorType : 'errorTotal'
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
                file_name: data.file_name ? data.file_name : null,
                strike_id: data.strike_id ? parseInt(data.strike_id) : null
            };
        };

        var initScansParams = function (data) {
            return {
                page: data.page ? parseInt(data.page) : 1,
                page_size: data.page_size ? parseInt(data.page_size) : 25,
                started: data.started ? data.started : moment.utc().subtract(1, 'weeks').startOf('d').toISOString(),
                ended: data.ended ? data.ended : moment.utc().endOf('d').toISOString(),
                name: data.name ? data.name : null,
                order: data.order ? Array.isArray(data.order) ? data.order : [data.order] : ['-last_modified']
            };
        };

        var initNodesParams = function (data) {
            return {
                // page: data.page ? parseInt(data.page) : 1,
                // page_size: data.page_size ? parseInt(data.page_size) : 25,
                order: data.order ? Array.isArray(data.order) ? data.order : [data.order] : ['hostname'],
                active: data.active || 'true',
                state: data.state || null
                // include_inactive: data.include_inactive ? data.include_inactive : null
            };
        };

        var initBatchesParams = function (data) {
            return {
                page: data.page ? parseInt(data.page) : 1,
                page_size: data.page_size ? parseInt(data.page_size) : 25,
                started: data.started ? data.started : moment.utc().subtract(1, 'weeks').startOf('d').toISOString(),
                ended: data.ended ? data.ended : moment.utc().endOf('d').toISOString(),
                order: data.order ? Array.isArray(data.order) ? data.order : [data.order] : ['-last_modified'],
                status: data.status ? data.status : null,
                recipe_type_id: data.recipe_type_id ? parseInt(data.recipe_type_id) : null,
                job_type_id: data.job_type_id ? parseInt(data.job_type_id) : null,
                url: null
            };
        };

        var initSourceFilesParams = function (data) {
            return {
                page: data.page ? parseInt(data.page) : 1,
                page_size: data.page_size ? parseInt(data.page_size) : 25,
                started: data.started ? data.started : moment.utc().subtract(1, 'weeks').startOf('d').toISOString(),
                ended: data.ended ? data.ended : moment.utc().endOf('d').toISOString(),
                time_field: data.time_field ? data.time_field : 'last_modified',
                order: data.order ? Array.isArray(data.order) ? data.order : [data.order] : ['-last_modified'],
                is_parsed: data.is_parsed ? data.is_parsed : null,
                file_name: data.file_name ? data.file_name : null
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
            getJobTypesParams: function () {
                if (_.keys(jobTypesParams).length === 0) {
                    jobTypesParams = initJobTypesParams($location.search());
                }
                //console.log(jobTypesParams);
                return jobTypesParams;
            },
            setJobTypesParams: function (data) {
                jobTypesParams = initJobTypesParams(data);
                updateQuerystring(jobTypesParams);
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
            getScansColDefs: function () {
                return scansColDefs;
            },
            setScansColDefs: function (data) {
                scansColDefs = data;
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
            getScansParams: function () {
                if (_.keys(scansParams).length === 0) {
                    return initScansParams($location.search());
                }
                return scansParams;
            },
            setScansParams: function (data) {
                scansParams = initScansParams(data);
                updateQuerystring(scansParams);
            },
            getNodesColDefs: function () {
                return nodesColDefs;
            },
            setNodesColDefs: function (data) {
                nodesColDefs = data;
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
                updateQuerystring(nodesParams, true);
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
                jobExecutionLogPoller.push(data);
            },
            getBatchesColDefs: function () {
                return batchesColDefs;
            },
            setBatchesColDefs: function (data) {
                batchesColDefs = data;
            },
            getBatchesParams: function () {
                if (_.keys(batchesParams).length === 0) {
                    return initBatchesParams($location.search());
                }
                return batchesParams;
            },
            setBatchesParams: function (data) {
                batchesParams = initBatchesParams(data);
                updateQuerystring(batchesParams);
            },
            getSourceFilesParams: function () {
                if (_.keys(sourceFilesParams).length === 0) {
                    return initSourceFilesParams($location.search());
                }
                return sourceFilesParams;
            },
            setSourceFilesParams: function (data) {
                sourceFilesParams = initSourceFilesParams(data);
                updateQuerystring(sourceFilesParams);
            }
        };
    });
})();
