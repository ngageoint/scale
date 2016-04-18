(function () {
    'use strict';

    angular.module('scaleApp').config(function ($provide) {
        $provide.decorator('$httpBackend', angular.mock.e2e.$httpBackendDecorator);
    }).run(function ($httpBackend, scaleConfig, XMLHttpRequest) {

        var getSync = function (url) {
            var request = new XMLHttpRequest();
            request.open('GET', url, false);
            request.send(null);
            return [request.status, request.response, {}];
        };

        // Ingests Status
        var ingestsStatusOverrideUrl = 'test/data/ingestStatus.json';
        var ingestsStatusRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'ingests/status/', 'i');
        $httpBackend.whenGET(ingestsStatusRegex).respond(function () {
            return getSync(ingestsStatusOverrideUrl);
        });


        // Job load
        var jobLoadRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'load/', 'i');
        $httpBackend.whenGET(jobLoadRegex).respond(function () {
            var numHours = moment.utc().endOf('d').diff(moment.utc().subtract(7, 'd').startOf('d'), 'h');
            var startTime = moment.utc().subtract(7, 'd').startOf('d');
            var data = {
                count: numHours,
                next: null,
                previous: null,
                results: []
            };

            for (var i = 0; i < data.count; i++) {
                data.results.push({
                    time: moment.utc(startTime).add(i, 'h').toISOString(),
                    pending_count: Math.floor(Math.random() * (100 - 20 + 1)) + 20,
                    queued_count: Math.floor(Math.random() * (100 - 20 + 1)) + 20,
                    running_count: Math.floor(Math.random() * (100 - 20 + 1)) + 20
                });
            }

            return [200, data, {}];
        });

        // Job details
        var jobDetailsOverrideUrl = 'test/data/jobDetails.json';
        var jobDetailsRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'jobs/.*/', 'i');
        $httpBackend.whenGET(jobDetailsRegex).respond(function () {
            return getSync(jobDetailsOverrideUrl);
        });

        // Jobs
        var jobsOverrideUrl = 'test/data/jobs.json';
        var jobsRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'jobs/', 'i');
        $httpBackend.whenGET(jobsRegex).respond(function () {
            return getSync(jobsOverrideUrl);
        });

        // Job type status
        var jobTypeStatusOverrideUrl = 'test/data/jobTypeStatus.json';
        var jobTypeStatusRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'job-types/status/', 'i');
        $httpBackend.whenGET(jobTypeStatusRegex).respond(function () {
            return getSync(jobTypeStatusOverrideUrl);
        });

        // Job types
        var jobTypesOverrideUrl = 'test/data/jobTypes.json';
        var jobTypesRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'job-types/', 'i');
        $httpBackend.whenGET(jobTypesRegex).respond(function () {
            return getSync(jobTypesOverrideUrl);
        });

        // Metrics Plot Data Detail
        var metricsPlotDataOverrideUrl = 'test/data/metricsJobTypesPlotData.json';
        var metricsPlotDataRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'metrics/.*/.*/','i');
        $httpBackend.whenGET(metricsPlotDataRegex).respond(function () {
            return getSync(metricsPlotDataOverrideUrl);
        });

        // Metrics Detail
        var metricsDetailOverrideUrl = 'test/data/metricsIngest.json';
        var metricsDetailRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'metrics/.*/','i');
        $httpBackend.whenGET(metricsDetailRegex).respond(function () {
            return getSync(metricsDetailOverrideUrl);
        });

        // Metrics
        var metricsOverrideUrl = 'test/data/metrics.json';
        var metricsRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'metrics/','i');
        $httpBackend.whenGET(metricsRegex).respond(function () {
            return getSync(metricsOverrideUrl);
        });

        // Node status
        var nodeStatusOverrideUrl = 'test/data/nodeStatus.json';
        var nodeStatusRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'nodes/status/', 'i');
        $httpBackend.whenGET(nodeStatusRegex).respond(function () {
            return getSync(nodeStatusOverrideUrl);
        });

        // Nodes
        var nodesOverrideUrl = 'test/data/nodes.json';
        var nodesRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'nodes/', 'i');
        $httpBackend.whenGET(nodesRegex).respond(function () {
            return getSync(nodesOverrideUrl);
        });

        // Queue Status service
        var queueStatusOverrideUrl = 'test/data/queueStatus.json';
        var queueStatusRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'queue/status/', 'i');
        $httpBackend.whenGET(queueStatusRegex).respond(function () {
            return getSync(queueStatusOverrideUrl);
        });

        // Recipes service
        var recipesOverrideUrl = 'test/data/recipes.json';
        var recipesRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'recipes/', 'i');
        $httpBackend.whenGET(recipesRegex).respond(function () {
            return getSync(recipesOverrideUrl);
        });

        // Recipe Type Detail service
        var recipeTypeDetailOverrideUrl = 'test/data/recipeTypeDetail.json';
        var recipeTypeDetailRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'recipe-types/.*/', 'i');
        $httpBackend.whenGET(recipeTypeDetailRegex).respond(function () {
            return getSync(recipeTypeDetailOverrideUrl);
        });

        // Recipe Types service
        var recipeTypesOverrideUrl = 'test/data/recipeTypes.json';
        var recipeTypesRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'recipe-types/', 'i');
        $httpBackend.whenGET(recipeTypesRegex).respond(function () {
            return getSync(recipeTypesOverrideUrl);
        });

        // Status service
        var statusOverrideUrl = 'test/data/status.json';
        var statusRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'status/', 'i');
        $httpBackend.whenGET(statusRegex).respond(function () {
            return getSync(statusOverrideUrl);
        });

        // Workspaces
        var workspacesOverrideUrl = 'test/data/workspaces.json';
        var workspacesRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'workspaces/', 'i');
        $httpBackend.whenGET(workspacesRegex).respond(function () {
            return getSync(workspacesOverrideUrl);
        });





        // For everything else, don't mock
        $httpBackend.whenGET(/^\w+.*/).passThrough();
        $httpBackend.whenPOST(/^\w+.*/).passThrough();
    });
})();