(function () {
    'use strict';

    angular.module('scaleApp').config(function ($provide) {
        $provide.decorator('$httpBackend', angular.mock.e2e.$httpBackendDecorator);
    }).run(function ($httpBackend, $interval, scaleConfig, XMLHttpRequest, moment) {

        var getSync = function (url) {
            var request = new XMLHttpRequest();
            request.open('GET', url, false);
            request.send(null);
            return [request.status, request.response, {}];
        };

        var getUrlParams = function (url) {
            var obj = {};

            if (url && url.split('?').length > 1) {
                url.split('?')[1].split('&').forEach(function (item) {
                    var s = item.split('='),
                        k = s[0],
                        v = s[1] && decodeURIComponent(s[1]);
                    (k in obj) ? obj[k].push(v) : obj[k] = [v]
                });
            }

            return obj;
        };

        // Ingests Status
        var ingestsStatusRegex = new RegExp('^' + scaleConfig.getUrlPrefix('ingests') + 'ingests/status/', 'i');
        $httpBackend.whenGET(ingestsStatusRegex).respond(function () {
            var strikes = JSON.parse(getSync('test/data/ingestStrikes.json')[1]),
                startDate = moment.utc().subtract(1, 'w').startOf('d').toISOString(),
                endDate = moment.utc().add(1, 'd').startOf('d').toISOString(),
                numHours = moment.utc(endDate).diff(moment.utc(startDate), 'h'),
                thisTime = '',
                values = [],
                results = [];

            _.forEach(strikes.results, function (strike) {
                values = [];

                for (var i = 0; i < numHours; i++) {
                    thisTime = moment.utc(startDate).add(i, 'h').toISOString();
                    values.push({
                        time: thisTime,
                        files: Math.floor(Math.random() * (500 - 5 + 1)) + 5,
                        size: Math.floor(Math.random() * (500000000 - 5000000 + 1)) + 5000000
                    });
                }

                results.push({
                    strike: strike,
                    most_recent: moment.utc().startOf('h').toISOString(),
                    files: 2,
                    size: 123456789,
                    values: values
                });
            });

            var data = {
                count: 2,
                next: null,
                previous: null,
                results: results
            };

            return [200, data, {}];
        });

        // Ingests
        var ingestsOverrideUrl = 'test/data/ingests.json';
        var ingestsRegex = new RegExp('^' + scaleConfig.getUrlPrefix('ingests') + 'ingests/', 'i');
        $httpBackend.whenGET(ingestsRegex).respond(function (method, url) {
            var urlParams = getUrlParams(url),
                returnObj = getSync(ingestsOverrideUrl),
                ingests = JSON.parse(returnObj[1]);

            if (urlParams.order && urlParams.order.length > 0) {
                var orders = [],
                    fields = [];
                _.forEach(urlParams.order, function (o) {
                    var order = o.charAt(0) === '-' ? 'desc' : 'asc',
                        field = order === 'desc' ? urlParams.order[0].substring(1) : urlParams.order[0];

                    orders.push(order);
                    fields.push(field);
                });

                ingests.results = _.sortByOrder(ingests.results, fields, orders);
            }

            if (urlParams.page && urlParams.page.length > 0) {
                var page = parseInt(urlParams.page[0]),
                    pageSize = parseInt(urlParams.page_size[0]);

                if (page === 1) {
                    ingests.results = _.take(ingests.results, pageSize);
                } else {
                    var startIdx = (page - 1) * pageSize,
                        idxArray = [];

                    for (var i = startIdx; i < ingests.results.length - 1; i++) {
                        idxArray.push(i);
                    }

                    ingests.results = _.at(ingests.results, idxArray);
                }
            }

            if (urlParams.status) {
                ingests.results = _.filter(ingests.results, function (ingest) {
                    return ingest.status === urlParams.status[0];
                });
            }

            returnObj[1] = JSON.stringify(ingests);

            return returnObj;
        });

        // Source details
        var sourceDetailsOverrideUrl = 'test/data/sourceDetails.json';
        var sourceDetailsRegex = new RegExp('^' + scaleConfig.getUrlPrefix('sources') + 'sources/.*/', 'i');
        $httpBackend.whenGET(sourceDetailsRegex).respond(function (method, url) {
            // // get the jobType.id from the url
            // url = url.toString();
            // var filename = url.substring(url.substring(0,url.lastIndexOf('/')).lastIndexOf('/')+1,url.length-1);
            // sourceDetailsOverrideUrl = 'test/data/source-details/' + filename + '.json';
            return getSync(sourceDetailsOverrideUrl);
        });
        
        // Sources
        var sourcesOverrideUrl = 'test/data/sources.json';
        var sourcesRegex = new RegExp('^' + scaleConfig.getUrlPrefix('sources') + 'sources/', 'i');
        $httpBackend.whenGET(sourcesRegex).respond(function (method, url) {
            //return getSync(sourcesOverrideUrl);
            var urlParams = getUrlParams(url),
                returnObj = getSync(sourcesOverrideUrl),
                sources = JSON.parse(returnObj[1]);

            if (urlParams.file_name && urlParams.file_name.length > 0) {
                var orders = ['file_name'],
                    fields = ['asc'];

                sources.results = _.filter(sources.results, function (r) {
                    return r.file_name.toLowerCase().includes(urlParams.file_name[0].toLowerCase());
                });

                sources.results = _.sortByOrder(sources.results, fields, orders);
            }

            returnObj[1] = JSON.stringify(sources);

            return returnObj;
        });

        // Job load
        var jobLoadRegex = new RegExp('^' + scaleConfig.getUrlPrefix('load') + 'load/', 'i');
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
        $httpBackend.whenGET(jobDetailsRegex).respond(function (method, url) {
            // get the jobType.id from the url
            url = url.toString();
            var id = url.substring(url.substring(0,url.lastIndexOf('/')).lastIndexOf('/')+1,url.length-1);
            jobDetailsOverrideUrl = 'test/data/job-details/jobDetails' + id + '.json';
            return getSync(jobDetailsOverrideUrl);
        });

        // Jobs
        var jobsOverrideUrl = 'test/data/jobs.json';
        var jobsRegex = new RegExp('^' + scaleConfig.getUrlPrefix('jobs') + 'jobs/', 'i');
        $httpBackend.whenGET(jobsRegex).respond(function (method, url) {
            var urlParams = getUrlParams(url),
                returnObj = getSync(jobsOverrideUrl),
                jobs = JSON.parse(returnObj[1]);

            if (urlParams.order && urlParams.order.length > 0) {
                var orders = [],
                    fields = [];
                _.forEach(urlParams.order, function (o) {
                    var order = o.charAt(0) === '-' ? 'desc' : 'asc',
                        field = order === 'desc' ? urlParams.order[0].substring(1) : urlParams.order[0];

                    if (field === 'job_type') {
                        field = 'job_type.name';
                    }

                    orders.push(order);
                    fields.push(field);
                });

                jobs.results = _.sortByOrder(jobs.results, fields, orders);
            }

            if (urlParams.status) {
                jobs.results = _.filter(jobs.results, function (job) {
                    return job.status === urlParams.status[0];
                });
            }

            returnObj[1] = JSON.stringify(jobs);

            return returnObj;
        });

        // Job type status
        var jobTypeStatusOverrideUrl = 'test/data/jobTypeStatus.json';
        var jobTypeStatusRegex = new RegExp('^' + scaleConfig.getUrlPrefix('job-types') + 'job-types/status/', 'i');
        $httpBackend.whenGET(jobTypeStatusRegex).respond(function () {
            return getSync(jobTypeStatusOverrideUrl);
        });

        // Running job types
        var runningJobsOverrideUrl = 'test/data/runningJobs.json';
        var runningJobsRegex = new RegExp('^' + scaleConfig.getUrlPrefix('job-types') + 'job-types/running/', 'i');
        $httpBackend.whenGET(runningJobsRegex).respond(function () {
            return getSync(runningJobsOverrideUrl);
        });

        // Job Type Details
        var jobTypeDetailsOverrideUrl = 'test/data/job-types/jobType1.json';
        var jobTypeDetailsRegex = new RegExp('^' + scaleConfig.getUrlPrefix('job-types') + 'job-types/.*/', 'i');
        $httpBackend.whenGET(jobTypeDetailsRegex).respond(function (method, url) {
            // get the jobType.id from the url
            url = url.toString();
            var id = url.substring(url.substring(0,url.lastIndexOf('/')).lastIndexOf('/')+1,url.length-1);
            jobTypeDetailsOverrideUrl = 'test/data/job-types/jobType' + id + '.json';
            return getSync(jobTypeDetailsOverrideUrl);
        });

        // Job types
        var jobTypesOverrideUrl = 'test/data/jobTypes.json';
        var jobTypesRegex = new RegExp('^' + scaleConfig.getUrlPrefix('job-types') + 'job-types/', 'i');
        $httpBackend.whenGET(jobTypesRegex).respond(function (method, url) {
            var urlParams = getUrlParams(url),
                returnObj = getSync(jobTypesOverrideUrl),
                jobTypes = JSON.parse(returnObj[1]);

            if (urlParams.order && urlParams.order.length > 0) {
                var orders = [],
                    fields = [];
                _.forEach(urlParams.order, function (o) {
                    var order = o.charAt(0) === '-' ? 'desc' : 'asc',
                        field = order === 'desc' ? urlParams.order[0].substring(1) : urlParams.order[0];

                    orders.push(order);
                    fields.push(field);
                });

                jobTypes.results = _.sortByOrder(jobTypes.results, fields, orders);
            }

            returnObj[1] = JSON.stringify(jobTypes);

            return returnObj;
        });
        
        // Job execution logs
        var jobExecutionLogRegex = new RegExp('^' + scaleConfig.getUrlPrefix('job-executions') + 'job-executions/.*/logs/combined/', 'i');
        $httpBackend.whenGET(jobExecutionLogRegex).respond(function () {
            var log = [];
            var lines = Math.floor(Math.random() * ((500 - 5) + 1) + 5);
            for (var i = 0; i < lines; i++) {
                var rand = Math.floor(Math.random() * (2 - 1 + 1)) + 1;
                var lineType = rand === 1 ? 'stdout' : 'stderr';
                log.push({
                    message: 'This is a ' + lineType + ' message',
                    '@timestamp': moment.utc().toISOString(),
                    scale_order_num: i,
                    scale_task: '',
                    scale_job_exe: '',
                    scale_node: 'node' + i,
                    stream: lineType
                });
            }
            return [200, JSON.stringify(log), {}];
            // return getSync(jobExecutionLogsOverrideUrl);
        });
        // var jobExecutionLogsOverrideUrl = 'test/data/jobExecutionLogCombined.json';

        // Job execution Details
        var jobExecutionDetailsOverrideUrl = 'test/data/jobExecutionDetails.json';
        var jobExecutionDetailsRegex = new RegExp('^' + scaleConfig.getUrlPrefix('job-executions') + 'job-executions/.*/', 'i');
        $httpBackend.whenGET(jobExecutionDetailsRegex).respond(function () {
            return getSync(jobExecutionDetailsOverrideUrl);
        });


        // Metrics Plot Data Detail
        //var metricsPlotDataOverrideUrl = 'test/data/metricsJobTypesPlotData.json';
        var metricsPlotDataRegex = new RegExp('^' + scaleConfig.getUrlPrefix('metrics') + 'metrics/.*/.*/','i');
        $httpBackend.whenGET(metricsPlotDataRegex).respond(function (method, url) {
            var urlParams = getUrlParams(url),
                random = 0;

            var returnObj = {
                count: 28,
                next: null,
                previous: null,
                results: []
            };

            var numDays = moment.utc(urlParams.ended[0]).diff(moment.utc(urlParams.started[0]), 'd') + 1;

            _.forEach(urlParams.column, function (metric) {
                var maxRandom = metric === 'total_count' ? 1000 : 200;
                var minRandom = metric === 'total_count' ? 800 : 10;
                var returnResult = {
                    column: { title: _.startCase(metric) },
                    min_x: moment.utc(urlParams.started[0]).format('YYYY-MM-DD'),
                    max_x: moment.utc(urlParams.ended[0]).format('YYYY-MM-DD'),
                    min_y: 1,
                    max_y: 1000,
                    values: []
                };

                for (var i = 0; i < numDays; i++) {
                    if (urlParams.choice_id && urlParams.choice_id.length > 1) {
                        _.forEach(urlParams.choice_id, function (id) {
                            random = Math.floor(Math.random() * (5 - 1 + 1)) + 1;
                            if (random <= 4) {
                                var value = Math.floor(Math.random() * (maxRandom - minRandom + 1)) + minRandom;
                                returnResult.values.push({
                                    date: moment.utc(urlParams.started[0]).add(i, 'd').format('YYYY-MM-DD'),
                                    value: value,
                                    id: parseInt(id)
                                });
                            }
                        });
                    } else {
                        random = Math.floor(Math.random() * (5 - 1 + 1)) + 1;
                        if (random <= 4) {
                            returnResult.values.push({
                                date: moment.utc(urlParams.started[0]).add(i, 'd').format('YYYY-MM-DD'),
                                value: Math.floor(Math.random() * (maxRandom - minRandom + 1)) + minRandom
                            });
                        }
                    }
                }
                returnObj.results.push(returnResult);
            });

            return [200, returnObj, {}];
        });

        // Metrics Detail
        var metricsDetailRegex = new RegExp('^' + scaleConfig.getUrlPrefix('metrics') + 'metrics/.*/','i');
        $httpBackend.whenGET(metricsDetailRegex).respond(function (method, url) {
            var urlArr = url.split('/'),
                detailType = urlArr[urlArr.length - 2];

            if (detailType === 'job-types') {
                return getSync('test/data/metricsJobTypes.json');
            } else if (detailType === 'error-types') {
                return getSync('test/data/metricsErrorTypes.json');
            }
            return getSync('test/data/metricsIngest.json');
        });

        // Metrics
        var metricsOverrideUrl = 'test/data/metrics.json';
        var metricsRegex = new RegExp('^' + scaleConfig.getUrlPrefix('metrics') + 'metrics/','i');
        $httpBackend.whenGET(metricsRegex).respond(function () {
            return getSync(metricsOverrideUrl);
        });

        // Node status
        var nodeStatusOverrideUrl = 'test/data/nodeStatus.json';
        var nodeStatusRegex = new RegExp('^' + scaleConfig.getUrlPrefix('nodes') + 'nodes/status/', 'i');
        $httpBackend.whenGET(nodeStatusRegex).respond(function () {
            return getSync(nodeStatusOverrideUrl);
        });

        // Node details
        var nodeOverrideUrl = 'test/data/node.json';
        var nodeRegex = new RegExp('^' + scaleConfig.getUrlPrefix('nodes') + 'nodes/.*/', 'i');
        $httpBackend.whenGET(nodeRegex).respond(function () {
            return getSync(nodeOverrideUrl);
        });
        $httpBackend.whenPATCH(nodeRegex).respond(function () {
            return getSync(nodeOverrideUrl);
        });

        // Nodes
        var nodesOverrideUrl = 'test/data/nodes.json';
        var nodesRegex = new RegExp('^' + scaleConfig.getUrlPrefix('nodes') + 'nodes/', 'i');
        $httpBackend.whenGET(nodesRegex).respond(function () {
            return getSync(nodesOverrideUrl);
        });

        // Queue Status service
        var queueStatusOverrideUrl = 'test/data/queueStatus.json';
        var queueStatusRegex = new RegExp('^' + scaleConfig.getUrlPrefix('queue') + 'queue/status/', 'i');
        $httpBackend.whenGET(queueStatusRegex).respond(function () {
            return getSync(queueStatusOverrideUrl);
        });
        
        // Recipe Details
        var recipeDetailsOverrideUrl = 'test/data/recipeDetails.json';
        var recipeDetailsRegex = new RegExp('^' + scaleConfig.getUrlPrefix('recipes') + 'recipes/.*/', 'i');
        $httpBackend.whenGET(recipeDetailsRegex).respond(function (method, url) {
            // get the recipeDetail.id from the url
            url = url.toString();
            var id = url.substring(url.substring(0,url.lastIndexOf('/')).lastIndexOf('/')+1,url.length-1);
            recipeDetailsOverrideUrl = 'test/data/recipe-details/recipeDetail' + id + '.json';
            return getSync(recipeDetailsOverrideUrl);
        });

        // Recipes service
        var recipesOverrideUrl = 'test/data/recipes.json';
        var recipesRegex = new RegExp('^' + scaleConfig.getUrlPrefix('recipes') + 'recipes/', 'i');
        $httpBackend.whenGET(recipesRegex).respond(function (method, url) {
            var urlParams = getUrlParams(url),
                returnObj = getSync(recipesOverrideUrl),
                recipes = JSON.parse(returnObj[1]);

            if (urlParams.order && urlParams.order.length > 0) {
                var orders = [],
                    fields = [];
                _.forEach(urlParams.order, function (o) {
                    var order = o.charAt(0) === '-' ? 'desc' : 'asc',
                        field = order === 'desc' ? urlParams.order[0].substring(1) : urlParams.order[0];

                    if (field === 'recipe_type') {
                        field = 'recipe_type.name';
                    }

                    orders.push(order);
                    fields.push(field);
                });

                recipes.results = _.sortByOrder(recipes.results, fields, orders);
            }

            returnObj[1] = JSON.stringify(recipes);

            return returnObj;
        });

        // Recipe type validation service
        var recipeTypeValidationOverrideUrl = 'test/data/recipeTypeValidationSuccess.json';
        var recipeTypeValidationRegex = new RegExp('^' + scaleConfig.getUrlPrefix('recipe-types') + 'recipe-types/validation/', 'i');
        $httpBackend.whenPOST(recipeTypeValidationRegex).respond(function () {
            return getSync(recipeTypeValidationOverrideUrl);
        });

        // Recipe Type Details
        var recipeTypeDetailsOverrideUrl = 'test/data/recipe-types/recipeType1.json';
        var recipeTypeDetailsRegex = new RegExp('^' + scaleConfig.getUrlPrefix('recipe-types') + 'recipe-types/.*/', 'i');
        $httpBackend.whenGET(recipeTypeDetailsRegex).respond(function (method, url) {
            // get the recipeType.id from the url
            url = url.toString();
            var id = url.substring(url.substring(0,url.lastIndexOf('/')).lastIndexOf('/')+1,url.length-1);
            recipeTypeDetailsOverrideUrl = 'test/data/recipe-types/recipeType' + id + '.json';
            var returnValue = getSync(recipeTypeDetailsOverrideUrl);
            if (returnValue[0] !== 200) {
                returnValue = localStorage.getItem('recipeType' + id);
                return [200, JSON.parse(returnValue), {}];
            } else {
                return returnValue;
            }
        });

        // Recipe Types service
        var recipeTypesOverrideUrl = 'test/data/recipeTypes.json';
        var recipeTypesRegex = new RegExp('^' + scaleConfig.getUrlPrefix('recipe-types') + 'recipe-types/', 'i');
        $httpBackend.whenGET(recipeTypesRegex).respond(function (method, url) {
            var urlParams = getUrlParams(url),
                returnObj = getSync(recipeTypesOverrideUrl),
                recipeTypes = JSON.parse(returnObj[1]);

            if (urlParams.order && urlParams.order.length > 0) {
                var orders = [],
                    fields = [];
                _.forEach(urlParams.order, function (o) {
                    var order = o.charAt(0) === '-' ? 'desc' : 'asc',
                        field = order === 'desc' ? urlParams.order[0].substring(1) : urlParams.order[0];

                    orders.push(order);
                    fields.push(field);
                });

                recipeTypes.results = _.sortByOrder(recipeTypes.results, fields, orders);
            }

            returnObj[1] = JSON.stringify(recipeTypes);

            return returnObj;
        });

        // Save Recipe Type
        var recipeTypeSaveRegex = new RegExp('^' + scaleConfig.getUrlPrefix('recipe-types') + 'recipe-types/', 'i');
        $httpBackend.whenPOST(recipeTypeSaveRegex).respond(function (method, url, data) {
            var recipeJobTypes = [],
                recipeJobTypesDetails = [],
                jobTypeData = getSync('test/data/jobTypes.json'),
                jobTypes = JSON.parse(jobTypeData[1]).results,
                recipeType = JSON.parse(data),
                uniqueRecipeTypeJobs = _.uniq(recipeType.definition.jobs, 'job_type');
            _.forEach(uniqueRecipeTypeJobs, function (job) {
                recipeJobTypes.push(_.find(jobTypes, function (jobType) {
                    return jobType.name === job.job_type.name && jobType.version === job.job_type.version;
                }));
            });
            _.forEach(recipeJobTypes, function (jobType) {
                var jt = getSync('test/data/job-types/jobType' + jobType.id + '.json');
                recipeJobTypesDetails.push(JSON.parse(jt[1]));
            });
            var returnRecipe = {
                id: Math.floor(Math.random() * (10000 - 5 + 1)) + 5,
                name: recipeType.name,
                version: recipeType.version,
                title: recipeType.title,
                description: recipeType.description,
                is_active: true,
                definition: recipeType.definition,
                revision_num: 1,
                created: new Date().toISOString(),
                last_modified: new Date().toISOString(),
                archived: null,
                trigger_rule: recipeType.trigger_rule,
                job_types: recipeJobTypesDetails
            };
            return [200, JSON.stringify(returnRecipe), {}];
        });

        // Status service
        var statusOverrideUrl = 'test/data/status.json';
        var statusRegex = new RegExp('^' + scaleConfig.getUrlPrefix('status') + 'status/', 'i');
        $httpBackend.whenGET(statusRegex).respond(function () {
            return getSync(statusOverrideUrl);
        });

        // Version
        var versionOverrideUrl = 'test/data/version.json';
        var versionRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'v3/version/', 'i');
        $httpBackend.whenGET(versionRegex).respond(function () {
            return getSync(versionOverrideUrl);
        });

        // Workspace Details
        var workspaceDetailsOverrideUrl = 'test/data/workspaces/workspace1.json';
        var workspaceDetailsRegex = new RegExp('^' + scaleConfig.getUrlPrefix('workspaces') + 'workspaces/.*/', 'i');
        $httpBackend.whenGET(workspaceDetailsRegex).respond(function (method, url) {
            // get the workspace.id from the url
            url = url.toString();
            var id = url.substring(url.substring(0,url.lastIndexOf('/')).lastIndexOf('/')+1,url.length-1);
            workspaceDetailsOverrideUrl = 'test/data/workspaces/workspace' + id + '.json';
            var returnValue = getSync(workspaceDetailsOverrideUrl);
            if (returnValue[0] !== 200) {
                returnValue = localStorage.getItem('workspace' + id);
                return [200, JSON.parse(returnValue), {}];
            } else {
                return returnValue;
            }
        });


        // Workspaces
        var workspacesOverrideUrl = 'test/data/workspaces.json';
        var workspacesRegex = new RegExp('^' + scaleConfig.getUrlPrefix('workspaces') + 'workspaces/', 'i');
        $httpBackend.whenGET(workspacesRegex).respond(function () {
            return getSync(workspacesOverrideUrl);
        });

        // Save Workspace
        var getWorkspaceReturn = function (data, id) {
            var workspace = JSON.parse(data);

            return {
                id: id || Math.floor(Math.random() * (10000 - 5 + 1)) + 5,
                name: workspace.name,
                title: workspace.title,
                description: workspace.description,
                base_url: workspace.base_url,
                is_active: workspace.is_active || false,
                used_size: 0,
                total_size: 0,
                created: new Date().toISOString(),
                archived: null,
                last_modified: new Date().toISOString(),
                json_config: workspace.json_config
            };
        };
        var workspaceCreateRegex = new RegExp('^' + scaleConfig.getUrlPrefix('workspaces') + 'workspaces/', 'i');
        $httpBackend.whenPOST(workspaceCreateRegex).respond(function (method, url, data) {
            var returnWorkspace = getWorkspaceReturn(data);
            return [200, JSON.stringify(returnWorkspace), {}];
        });
        $httpBackend.whenPATCH(workspaceDetailsRegex).respond(function (method, url, data) {
            // get the workspace.id from the url
            url = url.toString();
            var id = url.substring(url.substring(0,url.lastIndexOf('/')).lastIndexOf('/')+1,url.length-1);
            var returnWorkspace = getWorkspaceReturn(data, id);
            return [200, JSON.stringify(returnWorkspace), {}];
        });

        // Strike Details
        var strikeDetailsOverrideUrl = 'test/data/strikes/strike1.json';
        var strikeDetailsRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'strikes/.*/', 'i');
        $httpBackend.whenGET(strikeDetailsRegex).respond(function (method, url) {
            // get the strike.id from the url
            url = url.toString();
            var id = url.substring(url.substring(0,url.lastIndexOf('/')).lastIndexOf('/')+1,url.length-1);
            strikeDetailsOverrideUrl = 'test/data/strikes/strike' + id + '.json';
            var returnValue = getSync(strikeDetailsOverrideUrl);
            if (returnValue[0] !== 200) {
                returnValue = localStorage.getItem('strike' + id);
                return [200, JSON.parse(returnValue), {}];
            } else {
                return returnValue;
            }
        });

        // Strikes
        var strikesOverrideUrl = 'test/data/strikes.json';
        var strikesRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'strikes/', 'i');
        $httpBackend.whenGET(strikesRegex).respond(function () {
            return getSync(strikesOverrideUrl);
        });

        // Save Strike
        var getStrikeReturn = function (data, id) {
            var strike = JSON.parse(data);

            return {
                id: id || Math.floor(Math.random() * (10000 - 5 + 1)) + 5,
                name: strike.name,
                title: strike.title,
                description: strike.description,
                job: null,
                created: new Date().toISOString(),
                last_modified: new Date().toISOString(),
                configuration: strike.configuration
            };
        };
        var strikeCreateRegex = new RegExp('^' + scaleConfig.urls.apiPrefix + 'strikes/', 'i');
        $httpBackend.whenPOST(strikeCreateRegex).respond(function (method, url, data) {
            var returnStrike = getStrikeReturn(data);
            return [200, JSON.stringify(returnStrike), {}];
        });
        $httpBackend.whenPATCH(strikeDetailsRegex).respond(function (method, url, data) {
            // get the strike.id from the url
            url = url.toString();
            var id = url.substring(url.substring(0,url.lastIndexOf('/')).lastIndexOf('/')+1,url.length-1);
            var returnStrike = getStrikeReturn(data, id);
            return [200, JSON.stringify(returnStrike), {}];
        });

        // For everything else, don't mock
        $httpBackend.whenGET(/^\w+.*/).passThrough();
        $httpBackend.whenPOST(/^\w+.*/).passThrough();
    });
})();
