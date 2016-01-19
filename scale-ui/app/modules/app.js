(function () {
    'use strict';

    var app = angular.module('scaleApp', [
        'ngResource',
        'ngSanitize',
        'ngRoute',
        'emguo.poller',
        'ui.bootstrap',
        'ui.grid',
        'ui.grid.selection',
        'ui.grid.pagination',
        'ui.grid.resizeColumns',
        'cfp.hotkeys'
    ]);

    app.config(function($routeProvider, $resourceProvider, pollerConfig) {
        // stop pollers when route changes
        pollerConfig.stopOnRouteChange = true;
        pollerConfig.smart = true;

        // preserve trailing slashes
        $resourceProvider.defaults.stripTrailingSlashes = false;

        //routing
        $routeProvider
            .when('/', {
                controller: 'ovController',
                templateUrl: 'modules/overview/partials/ovTemplate.html'
            })
            .when('/admin/login',{
                controller: 'adminLoginController',
                templateUrl: 'modules/admin/partials/adminLoginTemplate.html'
            })
            .when('/admin/logout',{
                controller: 'logoutController',
                templateUrl: 'modules/admin/partials/adminLoginTemplate.html'
            })
            .when('/about', {
                controller: 'aboutController',
                templateUrl: 'modules/about/partials/aboutTemplate.html'
            })
            .when('/feed', {
                controller: 'feedDetailsController',
                templateUrl: 'modules/feed/partials/feedDetailsTemplate.html',
                reloadOnSearch: false
            })
            .when('/feed/ingests', {
                controller: 'ingestRecordsController',
                templateUrl: 'modules/feed/partials/ingestRecordsTemplate.html',
                reloadOnSearch: false
            })
            .when('/metrics', {
                controller: 'metricsController',
                templateUrl: 'modules/metrics/partials/metricsTemplate.html',
                reloadOnSearch: false
            })
            .when('/nodes', {
                controller: 'nodesController',
                templateUrl: 'modules/nodes/partials/nodesTemplate.html'
            })
            .when('/nodes/:id', {
                controller: 'nodeDetailsController',
                templateUrl: 'modules/nodes/partials/nodeDetailsTemplate.html'
            })
            .when('/load', {
                controller: 'loadController',
                templateUrl: 'modules/load/partials/loadTemplate.html'
            })
            .when('/load/running', {
                controller: 'queueRunningController',
                templateUrl: 'modules/load/partials/queueRunningTemplate.html'
            })
            .when('/load/depth', {
                controller: 'loadDepthController',
                templateUrl: 'modules/load/partials/loadDepthTemplate.html'
            })
            .when('/recipes', {
                controller: 'recipesController',
                templateUrl: 'modules/recipes/partials/recipesTemplate.html',
                reloadOnSearch: false
            })
            .when('/recipes/recipe/:id', {
                controller: 'recipeDetailsController',
                templateUrl: 'modules/recipes/partials/recipeDetailsTemplate.html'
            })
            .when('/recipes/types/:id?', {
                controller: 'recipeTypesController',
                templateUrl: 'modules/recipes/partials/recipeTypesTemplate.html'
            })
            .when('/recipes/builder', {
                controller: 'recipeEditorController',
                templateUrl: 'modules/recipes/partials/recipeEditorTemplate.html'
            })
            .when('/recipes/builder/:id', {
                controller: 'recipeEditorController',
                templateUrl: 'modules/recipes/partials/recipeEditorTemplate.html'
            })
            .when('/jobs', {
                controller: 'jobsController',
                templateUrl: 'modules/jobs/partials/jobsTemplate.html',
                reloadOnSearch: false
            })
            .when('/jobs/job/:id', {
                controller: 'jobDetailController',
                templateUrl: 'modules/jobs/partials/jobDetailTemplate.html'
            })
            .when('/jobs/types/:id?', {
                controller: 'jobTypesController',
                templateUrl: 'modules/jobs/partials/jobTypesTemplate.html'
            })
            .when('/jobs/executions', {
                controller: 'jobExecutionsController',
                templateUrl: 'modules/jobs/partials/jobExecutionsTemplate.html'
            })
            .when('/jobs/executions/:id', {
                controller: 'jobExecutionDetailController',
                templateUrl: 'modules/jobs/partials/jobExecutionDetailTemplate.html'
            })
            .otherwise({
                redirectTo: '/'
            });
    })
    .value('moment', window.moment)
    .value('localStorage', window.localStorage);
})();
