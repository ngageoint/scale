(function () {
    'use strict';

    angular.module('scaleApp').service('stateService', function ($location) {
        var queryString = $location.search(),
            user = {},
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
            jobTypesFailureRatesParams = {
                page: queryString.page ? parseInt(queryString.page) : null,
                page_size: queryString.page_size ? parseInt(queryString.page_size) : null,
                started: queryString.started ? queryString.started : null,
                ended: queryString.ended ? queryString.ended : null,
                name: queryString.name ? queryString.name : null,
                category: queryString.category ? queryString.category : null,
                order: queryString.order ? Array.isArray(queryString.order) ? queryString.order : [queryString.order] : null
            },
            recipesParams = {
                page: queryString.page ? parseInt(queryString.page) : 1,
                page_size: queryString.page_size ? parseInt(queryString.page_size) : 25,
                started: queryString.started ? queryString.started : moment.utc().subtract(1, 'weeks').startOf('d').toISOString(),
                ended: queryString.ended ? queryString.ended : moment.utc().endOf('d').toISOString(),
                order: queryString.order ? Array.isArray(queryString.order) ? queryString.order : [queryString.order] : ['-last_modified'],
                type_id: queryString.type_id ? parseInt(queryString.type_id) : null,
                type_name: queryString.type_name ? queryString.type_name : null,
                url: null
            },
            ingestsColDefs = [],
            ingestsParams = {
                page: queryString.page ? parseInt(queryString.page) : 1,
                page_size: queryString.page_size ? parseInt(queryString.page_size) : 25,
                started: queryString.started ? queryString.started : moment.utc().subtract(1, 'weeks').startOf('d').toISOString(),
                ended: queryString.ended ? queryString.ended : moment.utc().endOf('d').toISOString(),
                order: queryString.order ? Array.isArray(queryString.order) ? queryString.order : [queryString.order] : ['-last_modified'],
                status: queryString.status ? queryString.status : null
            };
        
        var updateQuerystring = function (data) {
            // check for params in querystring, and update as necessary
            _.forEach(_.pairs(data), function (param) {
                $location.search(param[0], param[1]);
            });
        };

        return {
            getUser: function () {
                return user;
            },
            setUser: function (data) {
                user = data;
            },
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
                updateQuerystring(data);
                jobTypesFailureRatesParams = data;
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
                updateQuerystring(data);
                recipesParams = data;
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
                updateQuerystring(data);
                ingestsParams = data;
            }
        };
    });
})();
