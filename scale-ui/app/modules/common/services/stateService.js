(function () {
    'use strict';

    angular.module('scaleApp').service('stateService', function ($location) {
        var queryString = $location.search(),
            version = '',
            jobsColDefs = [],
            jobsParams = {
                page: queryString.page ? parseInt(queryString.page) : 1,
                page_size: queryString.page_size ? parseInt(queryString.page_size) : 25,
                started: queryString.started ? queryString.started : moment.utc().subtract(1, 'weeks').startOf('d').toISOString(),
                ended: queryString.ended ? queryString.ended : moment.utc().endOf('d').toISOString(),
                order: queryString.order ? Array.isArray(queryString.order) ? queryString.order : [queryString.order] : ['-last_modified'],
                status: queryString.status ? queryString.status : null,
                error_category: queryString.error_category ? queryString.error_category : null,
                job_type_id: queryString.job_type_id ? parseInt(queryString.job_type_id) : null,
                job_type_name: queryString.job_type_name ? queryString.job_type_name : null,
                job_type_category: queryString.job_type_category ? queryString.job_type_category : null,
                url: null
            },
            recipesColDefs = [],
            jobTypesFailureRatesParams = {},
            recipesParams = {},
            ingestsColDefs = [],
            ingestsParams = {},
            showActiveWorkspaces = true;
        
        var updateQuerystring = function (data) {
            // set defaults
            data.page = data.page || 1;
            data.page_size = data.page_size || 25;
            data.started = data.started || moment.utc().subtract(1, 'weeks').startOf('d').toISOString();
            data.ended = data.ended || moment.utc().endOf('d').toISOString();
            data.order = data.order ? Array.isArray(data.order) ? data.order : [data.order] : null;
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
                updateQuerystring(data);
                jobsParams = data;
            },
            getJobTypesFailureRatesParams: function () {
                return jobTypesFailureRatesParams;
            },
            setJobTypesFailureRatesParams: function (data) {
                jobTypesFailureRatesParams = {
                    page: null,
                    page_size: null,
                    started: null,
                    ended: null,
                    name: data.name ? data.name : null,
                    category: null,
                    order: null
                };
                _.forEach(_.pairs(data), function (param) {
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
                return recipesParams;
            },
            setRecipesParams: function (data) {
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
                updateQuerystring(recipeParams);
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
                ingestsParams = {
                    page: data.page ? parseInt(data.page) : 1,
                    page_size: data.page_size ? parseInt(data.page_size) : 25,
                    started: data.started ? data.started : moment.utc().subtract(1, 'weeks').startOf('d').toISOString(),
                    ended: data.ended ? data.ended : moment.utc().endOf('d').toISOString(),
                    order: data.order ? Array.isArray(data.order) ? data.order : [data.order] : ['-ingest_started'],
                    status: data.status ? data.status : null
                };
                updateQuerystring(ingestsParams);
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
