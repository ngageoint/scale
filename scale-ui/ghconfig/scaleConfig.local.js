(function () {
    'use strict';

    angular.module('scaleApp').constant('scaleConfigLocal', {
        urls: {
            prefixDev: '/scale-ui/', // dev
            prefixV2: '',
            prefixV3: '/scale-ui/',

            getQueueStatus: function () {
                return this.prefixDev + 'test/data/v3/queueStatus.json';
            },
            getQueueDepth: function (queryBy, dateFrom, dateTo) {
                return this.prefixDev + 'test/data/v3/queueDepthCombined.json';
            },
            requeueJob: function () {
                //return this.prefixV3 + 'queue/requeue-job/'
            },
            getRecipeTypes: function () {
                return this.prefixDev + 'test/data/v3/recipeTypes.json';
            },
            saveRecipeType: function () {
                return this.getRecipeTypes();
                //return 'http://127.0.0.1:3000/api/recipe-types/';
            },
            validateRecipeType: function () {
                //return this.prefixV3 + 'recipe-types/validation/';
            },
            getRecipeTypeDetail: function (id) {
                if (id===1) {
                    return this.prefixDev + 'test/data/v3/recipeDetailSimple.json';
                } else {
                    return this.prefixDev + 'test/data/v3/recipeDetailComplex.json';
                }

            },
            getRecipes: function () {
                return this.prefixDev + 'test/data/v3/recipes.json';
                //return this.prefixV3 + 'recipes/';
            },
            getRecipeDetails: function (id) {
                return this.prefixDev + 'test/data/v3/recipeDetails.json';
                //return this.prefixV3 + 'recipes/' + id + '/';
            },
            getJobs: function () {
                return this.prefixDev + 'test/data/v3/jobs.json';
            },
            updateJob: function (id) {
                //return this.prefixV3 + 'jobs/' + id + '/';
            },
            getRunningJobs: function (pageNumber, pageSize) {
                return this.prefixDev + 'test/data/v3/runningJobs.json';
            },
            getJobTypes: function (order) {
                order = order || 'name,version';
                return this.prefixDev + 'test/data/v3/jobTypes.json';
            },
            getJobTypeStatus: function () {
                return this.prefixDev + 'test/data/v3/jobTypeStatus.json';
            },
            getJobTypeDetails: function (id) {
                return this.prefixDev + "test/data/v3/jobTypeDetails.json";
            },
            updateJobType: function (id) {
                //return this.prefixV3 + 'job-types/' + id + '/';
            },
            getJobDetail: function (id) {
                return this.prefixDev + "test/data/v3/jobDetails.json";
            },
            getJobExecutions: function (pageNumber, pageSize, filter) {
                return this.prefixDev + 'test/data/v3/jobExecutions.json';
            },
            getJobExecutionLog: function (execId) {
                return this.prefixDev + 'test/data/v3/jobExecutionLog.json';
            },
            getJobExecutionDetails: function (execId) {
                return this.prefixDev + 'test/data/v3/jobExecutionDetails.json';
            },
            getMetricsDataTypes: function () {
                return this.prefixDev + 'test/data/v3/metrics.json';
            },
            getMetricsDataTypeOptions: function (name) {
                if (name === 'job-types') {
                    return this.prefixDev + 'test/data/v3/metricsJobTypes.json';
                } else if (name === 'ingest') {
                    return this.prefixDev + 'test/data/v3/metricsIngest.json';
                }
            },
            getMetricsPlotData: function (dataType) {
                return this.prefixDev + 'test/data/v3/metricsJobTypesPlotData.json';
            },
            getNodes: function () {
                return this.prefixDev + 'test/data/v3/nodes.json';
            },
            getNode: function (slaveId) {
                return this.prefixDev + 'test/data/v3/node.json';
            },
            getNodeStatus: function (page, page_size, started, ended) {
                return this.prefixDev + 'test/data/v3/nodeStatus.json';
            },
            updateNode: function (id) {
                //return this.prefixV3 + 'nodes/' + id + '/';
            },
            getStatus: function () {
                return this.prefixDev + 'test/data/v3/status.json';
            },
            /*getJobLoad: function () {
             //return this.prefixV3 + 'load/';
             },*/
            getDataFeed: function() {
                return this.prefixDev + 'test/data/v3/ingestStatus.json';
                //return this.prefixV3 + 'ingests/status/';
            },
            getIngests: function(){
                return this.prefixDev + 'test/data/v3/ingests.json';
                //return this.prefixV3 + 'ingests/';
            },
            updateScheduler: function () {
                //return this.prefixV3 + 'scheduler/';
            }
        }
    });
})();
