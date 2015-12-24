(function () {
	'use strict';

	angular.module('scaleApp').service('scaleConfig', function (scaleConfigLocal) {
		var cfg = {
			colors: {
				emo_1: '#556270',
				emo_2: '#4ecdc4',
				emo_3: '#c7f464',
				emo_4: '#ff6b6b',
				emo_5: '#c44d58',

				va_1: '#f2385a',
				va_2: '#f5a503',
				va_3: '#e9f1df',
				va_4: '#4ad9d9',
				va_5: '#3681bf',

				df_1: '#566669',
				df_2: '#bfe2ff',
				df_3: '#0a131a',
				df_4: '#122031',
				df_5: '#00010d',

				chart_blue: '#589ad0',
				chart_gray: '#cccccc',
				chart_gray_dark: '#aaaaaa',
				chart_green: '#8fca0e',
				chart_orange: '#ff7730',
				chart_purple: '#bf81bf',
				chart_red: '#f54d36',
				chart_white: '#fff',
				chart_yellow: '#ffc317',
				chart_pink: '#fb03b2',

				slate_blue_1: '#171C1C',
				slate_blue_2: '#0F181C',

				nav_bg: 'slate_blue_1',
				nav_txt: 'light',

				view_bg: 'light',
				view_txt: '#434649',

				accent_blue: 'va_5',

				patternDefault: ['#4D4D4D','#5DA5DA','#FAA43A','#60BD68','#F17CB0','#B2912F','#B276B2','#DECF3F','#F15854'],
				healthChart: ['#8fca0e','#f54d36','#ffc317','#ff7730','#3681bf','#999999','#D97BF9'],
				statusChart: ['#999999','#D97BF9','#f54d36','#ff7730','#8fca0e','#ffc317','#3681bf'],
				patternEmo: ['#556270','#4ecdc4','#c7f464','#ff6b6b','#c44d58'],
				patternVa: ['#f2385a','#f5a503','#e9f1df','#4ad9d9','#3681bf'],
				patternDf: ['#566669','#bfe2ff','#0a131a','#122031','#00010d'],
				patternD320: ['#1f77bf','#aec7e8','#ff7f0e','#ffbb78','#2ca02c','#98df8a','#d62728','#ff9896','#9467bd','#c5b0d5','#8c564b','#c49c94','#e377c2','#f7b6d2','#7f7f7f','#c7c7c7','#bcbd22','#dbdb8d','#17becf','#9edae5'],
			},

			queueThresholds: {
				success: 4,
				info: 8,
				warning: 12,
				danger: 16
			},

			jobTypes: [],

			mediaTypes: [
				{mimeType: 'text/csv', icon: 'fa-file-excel-o'},
				{mimeType: 'text/plain', icon: 'fa-file-text-o'},
				{mimeType: 'application/zip', icon: 'fa-file-archive-o'},
				{mimeType: 'application/json', icon: 'fa-file-code-o'},
				{mimeType: 'application/xml', icon: 'fa-file-excel-o'},
				{mimeType: 'application/vnd.geo+json', icon: 'fa-file-code-o'},
				{mimeType: 'application/vnd.google-earth.kml+xml', icon: 'fa-globe'},
				{mimeType: 'application/vnd.google-earth.kmz', icon: 'fa-globe'},
				{mimeType: 'image/png', icon: 'fa-file-image-o'},
				{mimeType: 'image/x-hdf5-image', icon: 'fa-file-image-o'},
				{mimeType: 'image/x-nitf-image', icon: 'fa-file-image-o'},
				{mimeType: 'image/tiff', icon: 'fa-file-image-o'},
				{mimeType: 'video/avi', icon: 'fa-file-video-o'},
				{mimeType: 'video/mp4', icon: 'fa-file-video-o'}
			],

			taskStatusStyles: {
                "SUCCEEDED" : "bar",
                "FAILED" : "bar-failed",
                "RUNNING" : "bar-running",
                "KILLED" : "bar-killed"
            },

			dateFormats: {
                "day": "YYYY-MM-DD",
                "day_hour": "YYYY-MM-DD HHZ",
                "day_minute": "YYYY-MM-DD HH:MM",
                "day_minute_utc": "YYYY-MM-DD HH:MM[Z]",
                "day_second": "YYYY-MM-DD HH:MM:SSZ",
                "day_second_utc": "YYYY-MM-DD HH:MM:SS[Z]",
                "day_millis": 'YYYY-MM-DD HH:mm:ss.SSS',
                "hour_minute": "HH:mm",
                "hour_seconds": "HH:mm:ss",
                "duration_hm": "HH:mm",
                "duration_hms": "HH:mm:ss"

            },

            jobStatus: ['VIEW ALL','COMPLETED','BLOCKED','QUEUED','RUNNING','FAILED','CANCELED','PENDING'],

			ingestStatus: ['VIEW ALL','TRANSFERRING','TRANSFERRED','DEFERRED','INGESTING','INGESTED','ERRORED','DUPLICATE'],

			axisTypes: ['linear', 'time'],

			executions: ['success','warning','error'],

			defaultIcon: 'gear',

			defaultIconCode: 'f013',

			activityIconCode: 'f110',

            urls: {
                prefixDev: 'http://127.0.0.1:9000/', // dev
                prefixV2: '',
                prefixV3: 'http://www.host.gov/scale-dev/api/',
                documentation: '/docs',

                getQueueStatus: function () {
                    return this.prefixV3 + 'queue/status/';
                },
                getQueueDepth: function (started, ended) {
                    return this.prefixV3 + 'queue/depth/?started=' + started + '&ended=' + ended;
                },
				requeueJob: function () {
					return this.prefixV3 + 'queue/requeue-job/'
				},
				getRecipeTypes: function () {
                    // return this.prefixDev + 'test/data/v3/recipeTypes.json';
                    return this.prefixV3 + 'recipe-types/';
                },
                saveRecipeType: function () {
                    return this.getRecipeTypes();
                    //return 'http://127.0.0.1:3000/api/recipe-types/';
                },
				validateRecipeType: function () {
					return this.prefixV3 + 'recipe-types/validation/';
				},
                getRecipeTypeDetail: function (id) {
                    return this.prefixV3 + 'recipe-types/' + id + '/';
                },
                getRecipes: function () {
                    //return this.prefixDev + 'test/data/v3/recipes.json';
					return this.prefixV3 + 'recipes/';
                },
				getRecipeDetails: function (id) {
                    //return this.prefixDev + 'test/data/v3/recipeDetails.json';
					return this.prefixV3 + 'recipes/' + id + '/';
                },
                getJobs: function () {
                    return this.prefixV3 + 'jobs/';
                },
				updateJob: function (id) {
					return this.prefixV3 + 'jobs/' + id + '/';
				},
				getRunningJobs: function (pageNumber, pageSize) {
					return this.prefixV3 + 'job-types/running/';
				},
				getJobTypes: function () {
					return this.prefixV3 + 'job-types/';
                },
                getJobTypeStatus: function () {
					return this.prefixV3 + 'job-types/status/';
				},
				getJobTypeDetails: function (id) {
                    return this.prefixV3 + 'job-types/' + id + '/';
                },
				updateJobType: function (id) {
                    return this.prefixV3 + 'job-types/' + id + '/';
                },
                getJobDetail: function (id) {
                    //return this.prefixDev + "test/data/v3/jobDetails.json";
					return this.prefixV3 + 'jobs/' + id + '/';
                },
                getJobExecutions: function () {
                    // var date_from = moment.utc().subtract(1, 'd').format('YYYY/MM/DD');
                    // var date_to = moment.utc().format('YYYY/MM/DD');
                    // var jobTypeId = filter.jobTypeId ? filter.jobTypeId : '';
                    // var jobStatus = filter.jobStatus ? filter.jobStatus : '';
                    //return this.prefixV3 + 'job-executions/?job_type_id=' + jobTypeId + '&page=' + pageNumber + '&page_size=' + pageSize + '&status=' + jobStatus;
					return this.prefixV3 + 'job-executions/';
                },
                getJobExecutionLog: function (execId) {
                    return this.prefixV3 + 'job-executions/' + execId + '/logs/';
                },
				getJobExecutionDetails: function (execId) {
					return this.prefixV3 + 'job-executions/' + execId + '/';
				},
                getMetricsDataTypes: function () {
                    return this.prefixV3 + 'metrics/';
				    //return this.prefixDev + 'test/data/v3/metricsDataTypes.json';
                },
                getMetricsDataTypeOptions: function (name) {
                    return this.prefixV3 + 'metrics/' + name + '/';
					//return this.prefixDev + 'test/data/v3/metricsJobTypes.json';
                },
                getMetricsPlotData: function (name) {
                    return this.prefixV3 + 'metrics/' + name + '/plot-data/';
					//return this.prefixDev + 'test/data/v3/metricsJobTypes.json';
                },
                getNodes: function () {
                    return this.prefixV3 + 'nodes/';
                },
                getNode: function (slaveId) {
                    return this.prefixV3 + 'nodes/' + slaveId + '/';
                },
                getNodeStatus: function () {
                    return this.prefixV3 + 'nodes/status/';
                },
				updateNode: function (id) {
					return this.prefixV3 + 'nodes/' + id + '/';
				},
                getStatus: function () {
                    return this.prefixV3 + 'status/';
                },
				getJobLoad: function () {
					return this.prefixV3 + 'load/';
				},
				getDataFeed: function() {
					return this.prefixV3 + 'ingests/status/';
				},
				getIngests: function(){
					return this.prefixV3 + 'ingests/';
				},
				updateScheduler: function () {
					return this.prefixV3 + 'scheduler/';
				}
            },
			defaultGaugeWidth: 160,
			pollIntervals: {
				// minutes * (seconds * milliseconds)
				runningJobs: 5 * (60 * 1000),
				jobs: 5 * (60 * 1000),
				jobTypes: 5 * (60 * 1000),
				jobExecutionLog: 5 * (60 * 1000),
				jobTypeStatus: 5 * (60 * 1000),
				nodes: 5 * (60 * 1000),
				nodeStatus: 5 * (60 * 1000),
				queueStatus: 5 * (60 * 1000),
				queueDepth: 5 * (60 * 1000),
                status: 5 * (60 * 1000),
				jobLoad: 5 * (60 * 1000)
            },
            subnavLinks: {
                jobs: [
                        { path: 'jobs', label: 'Jobs' },
                        { path: 'jobs/types', label: 'Job Types' }
                        //{ path: 'jobs/executions', label: 'Job Executions' }
                ],
                queue: [
                        { path: 'queue', label: 'Queued' },
                        { path: 'queue/running', label: 'Running' },
                        { path: 'queue/depth', label: 'Job Load' }
                ],
                recipes: [
                        { path: 'recipes', label: 'Recipes' },
                        { path: 'recipes/types', label: 'Recipe Types' }
                ],
				feed: [
                        { path: 'feed', label: 'Status' },
                        { path: 'feed/ingests', label: 'Ingest Records' }
                ]
            },
            headerOffset: 160
        };
        _.merge(cfg, scaleConfigLocal);
        return cfg;
	});
})();
