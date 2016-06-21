(function () {
    'use strict';

    angular.module('scaleApp').service('stateService', function ($location) {
        var queryString = $location.search(),
            version = '',
            jobsColDefs = [],
            jobsParams = {},
            recipesColDefs = [],
            jobTypesFailureRatesParams = {},
            recipesParams = {},
            ingestsColDefs = [],
            ingestsParams = {},
            showActiveWorkspaces = true;
        
        var updateQuerystring = function (data, defaultOrder) {
            // set defaults
            data.page = data.page || 1;
            data.page_size = data.page_size || 25;
            data.started = data.started || moment.utc().subtract(1, 'weeks').startOf('d').toISOString();
            data.ended = data.ended || moment.utc().endOf('d').toISOString();
            data.order = data.order ? Array.isArray(data.order) ? data.order : [data.order] : [defaultOrder];
            data.status = data.status || null;
            // check for params in querystring, and update as necessary
            _.forEach(_.pairs(data), function (param) {
                $location.search(param[0], param[1]);
            });
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
                return jobsParams;
            },
            setJobsParams: function (data) {
                updateQuerystring(data, '-last_modified');
                jobsParams = {
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
            },
            getJobTypesFailureRatesParams: function () {
                return jobTypesFailureRatesParams;
            },
            setJobTypesFailureRatesParams: function (data) {
                updateQuerystring(data, null);
                jobTypesFailureRatesParams = {
                    page: data.page ? parseInt(data.page) : null,
                    page_size: data.page_size ? parseInt(data.page_size) : null,
                    started: data.started ? data.started : null,
                    ended: data.ended ? data.ended : null,
                    name: data.name ? data.name : null,
                    category: data.category ? data.category : null,
                    order: data.order ? Array.isArray(data.order) ? data.order : [data.order] : null
                };
            },
            getRecipesColDefs: function () {
                return recipesColDefs;
            },
            setRecipesColDefs: function (data) {
                recipesColDefs = data;
            },
            getRecipesParams: function () {
                return recipesParams;
            },
            setRecipesParams: function (data) {
                updateQuerystring(data, '-last_modified');
                recipesParams = {
                    page: data.page ? parseInt(data.page) : 1,
                    page_size: data.page_size ? parseInt(data.page_size) : 25,
                    started: data.started ? data.started : moment.utc().subtract(1, 'weeks').startOf('d').toISOString(),
                    ended: data.ended ? data.ended : moment.utc().endOf('d').toISOString(),
                    order: data.order ? Array.isArray(data.order) ? data.order : [data.order] : ['-last_modified'],
                    type_id: data.type_id ? parseInt(data.type_id) : null,
                    type_name: data.type_name ? data.type_name : null,
                    url: null
                };
            },
            getIngestsColDefs: function () {
                return ingestsColDefs;
            },
            setIngestsColDefs: function (data) {
                ingestsColDefs = data;
            },
            getIngestsParams: function () {
                return ingestsParams;
            },
            setIngestsParams: function (data) {
                updateQuerystring(data, '-ingest_started');
                ingestsParams = {
                    page: data.page ? parseInt(data.page) : 1,
                    page_size: data.page_size ? parseInt(data.page_size) : 25,
                    started: data.started ? data.started : moment.utc().subtract(1, 'weeks').startOf('d').toISOString(),
                    ended: data.ended ? data.ended : moment.utc().endOf('d').toISOString(),
                    order: data.order ? Array.isArray(data.order) ? data.order : [data.order] : ['-ingest_started'],
                    status: data.status ? data.status : null
                };
            },
            getShowActiveWorkspaces: function () {
                return showActiveWorkspaces;
            },
            setShowActiveWorkspaces: function (data) {
                showActiveWorkspaces = data;
            }
        };
    });
})();
