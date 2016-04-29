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

        // Running job types
        var runningJobsOverrideUrl = 'test/data/runningJobs.json';
        var runningJobsRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'job-types/running/', 'i');
        $httpBackend.whenGET(runningJobsRegex).respond(function () {
            return getSync(runningJobsOverrideUrl);
        });

        // Job Type Details
        var jobTypeDetailsOverrideUrl = 'test/data/job-types/jobType1.json';
        var jobTypeDetailsRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'job-types/.*/', 'i');
        $httpBackend.whenGET(jobTypeDetailsRegex).respond(function (method, url) {
            // get the jobType.id from the url
            url = url.toString();
            var id = url.substring(url.substring(0,url.lastIndexOf('/')).lastIndexOf('/')+1,url.length-1);
            jobTypeDetailsOverrideUrl = 'test/data/job-types/jobType' + id + '.json';
            return getSync(jobTypeDetailsOverrideUrl);
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

        // Node details
        var nodeOverrideUrl = 'test/data/node.json';
        var nodeRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'nodes/.*/', 'i');
        $httpBackend.whenGET(nodeRegex).respond(function () {
            return getSync(nodeOverrideUrl);
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

        // Recipe type validation service
        var recipeTypeValidationOverrideUrl = 'test/data/recipeTypeValidationSuccess.json';
        var recipeTypeValidationRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'recipe-types/validation/', 'i');
        $httpBackend.whenPOST(recipeTypeValidationRegex).respond(function () {
            return getSync(recipeTypeValidationOverrideUrl);
        });

        // Recipe Type Details
        var recipeTypeDetailsOverrideUrl = 'test/data/recipe-types/recipeType1.json';
        var recipeTypeDetailsRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'recipe-types/.*/', 'i');
        $httpBackend.whenGET(recipeTypeDetailsRegex).respond(function (method, url) {
            // get the recipeType.id from the url
            url = url.toString();
            var id = url.substring(url.substring(0,url.lastIndexOf('/')).lastIndexOf('/')+1,url.length-1);
            recipeTypeDetailsOverrideUrl = 'test/data/recipe-types/recipeType' + id + '.json';
            return getSync(recipeTypeDetailsOverrideUrl);
        });

        // Recipe Types service
        var recipeTypesOverrideUrl = 'test/data/recipeTypes.json';
        var recipeTypesRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'recipe-types/', 'i');
        $httpBackend.whenGET(recipeTypesRegex).respond(function () {
            return getSync(recipeTypesOverrideUrl);
        });

        // Save Recipe Type
        var recipeTypeSaveOverrideUrl = '';
        var recipeTypeSaveRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'recipe-types/', 'i');
        $httpBackend.whenPOST(recipeTypeSaveRegex).respond(function (method, url, data) {
            var recipeJobTypes = [],
                jobTypeData = getSync('test/data/jobTypes.json'),
                jobTypes = JSON.parse(jobTypeData[1]).results,
                recipeType = JSON.parse(data),
                uniqueRecipeTypeJobs = _.uniq(recipeType.definition.jobs, 'job_type');
            _.forEach(uniqueRecipeTypeJobs, function (job) {
                recipeJobTypes.push(_.find(jobTypes, function (jobType) {
                    return jobType.name === job.job_type.name && jobType.version === job.job_type.version;
                }));
            });
            recipeType.job_types = recipeJobTypes;
            return [200, JSON.stringify(recipeType), {}];
        });

        // Status service
        var statusOverrideUrl = 'test/data/status.json';
        var statusRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'status/', 'i');
        $httpBackend.whenGET(statusRegex).respond(function () {
            return getSync(statusOverrideUrl);
        });

        // Version
        var versionOverrideUrl = 'test/data/version.json';
        var versionRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'v3/version/', 'i');
        $httpBackend.whenGET(versionRegex).respond(function () {
            return getSync(versionOverrideUrl);
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
