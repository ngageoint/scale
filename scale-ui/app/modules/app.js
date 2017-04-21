(function () {
    'use strict';

    var app = angular.module('scaleApp', [
        'scaleConfigModule',
        'ngResource',
        'ngSanitize',
        'ngRoute',
        'emguo.poller',
        'ui.bootstrap',
        'ui.grid',
        'ui.grid.selection',
        'ui.grid.pagination',
        'ui.grid.resizeColumns',
        'ui.sortable',
        'cfp.hotkeys',
        'toggle-switch',
        'uiSwitch'
    ]);

    app.config(function($routeProvider, $resourceProvider, $provide, pollerConfig) {
        // Fix sourcemaps
        // @url https://github.com/angular/angular.js/issues/5217#issuecomment-50993513
        $provide.decorator('$exceptionHandler', function ($delegate) {
            return function (exception, cause) {
                $delegate(exception, cause);
                setTimeout(function() {
                    throw exception;
                });
            };
        });

        // stop pollers when route changes
        pollerConfig.stopOn = '$routeChangeStart';
        pollerConfig.smart = true;

        // preserve trailing slashes
        $resourceProvider.defaults.stripTrailingSlashes = false;

        //routing
        $routeProvider
            .when('/', {
                controller: 'ovController',
                controllerAs: 'vm',
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
                controllerAs: 'vm',
                templateUrl: 'modules/about/partials/aboutTemplate.html'
            })
            .when('/feed', {
                controller: 'feedDetailsController',
                controllerAs: 'vm',
                templateUrl: 'modules/feed/partials/feedDetailsTemplate.html',
                reloadOnSearch: false
            })
            .when('/feed/ingests', {
                controller: 'ingestRecordsController',
                controllerAs: 'vm',
                templateUrl: 'modules/feed/partials/ingestRecordsTemplate.html',
                reloadOnSearch: false
            })
            .when('/feed/ingests/:id', {
                controller: 'ingestRecordDetailsController',
                controllerAs: 'vm',
                templateUrl: 'modules/feed/partials/ingestRecordDetailsTemplate.html'
            })
            .when('/metrics', {
                controller: 'metricsController',
                controllerAs: 'vm',
                templateUrl: 'modules/metrics/partials/metricsTemplate.html',
                reloadOnSearch: false
            })
            .when('/nodes', {
                controller: 'nodesController',
                controllerAs: 'vm',
                templateUrl: 'modules/nodes/partials/nodesTemplate.html'
            })
            .when('/nodes/:id', {
                controller: 'nodeDetailsController',
                controllerAs: 'vm',
                templateUrl: 'modules/nodes/partials/nodeDetailsTemplate.html'
            })
            .when('/load/queued', {
                controller: 'loadController',
                controllerAs: 'vm',
                templateUrl: 'modules/load/partials/loadTemplate.html'
            })
            .when('/load/running', {
                controller: 'queueRunningController',
                controllerAs: 'vm',
                templateUrl: 'modules/load/partials/queueRunningTemplate.html'
            })
            .when('/load/depth', {
                controller: 'loadDepthController',
                controllerAs: 'vm',
                templateUrl: 'modules/load/partials/loadDepthTemplate.html'
            })
            .when('/recipes', {
                controller: 'recipesController',
                controllerAs: 'vm',
                templateUrl: 'modules/recipes/partials/recipesTemplate.html',
                reloadOnSearch: false
            })
            .when('/recipes/recipe/:id', {
                controller: 'recipeDetailsController',
                controllerAs: 'vm',
                templateUrl: 'modules/recipes/partials/recipeDetailsTemplate.html'
            })
            .when('/recipes/types/:id?', {
                controller: 'recipeTypesController',
                controllerAs: 'vm',
                templateUrl: 'modules/recipes/partials/recipeTypesTemplate.html'
            })
            .when('/jobs', {
                controller: 'jobsController',
                controllerAs: 'vm',
                templateUrl: 'modules/jobs/partials/jobsTemplate.html',
                reloadOnSearch: false
            })
            .when('/jobs/job/:id', {
                controller: 'jobDetailController',
                controllerAs: 'vm',
                templateUrl: 'modules/jobs/partials/jobDetailTemplate.html'
            })
            .when('/jobs/types/:id?', {
                controller: 'jobTypesController',
                controllerAs: 'vm',
                templateUrl: 'modules/jobs/partials/jobTypesTemplate.html',
                reloadOnSearch: false
            })
            .when('/jobs/failure-rates', {
                controller: 'jobTypesFailureRatesController',
                controllerAs: 'vm',
                templateUrl: 'modules/jobs/partials/jobTypesFailureRatesTemplate.html',
                reloadOnSearch: false
            })
            .when('/jobs/executions', {
                controller: 'jobExecutionsController',
                controllerAs: 'vm',
                templateUrl: 'modules/jobs/partials/jobExecutionsTemplate.html'
            })
            .when('/jobs/executions/:id', {
                controller: 'jobExecutionDetailController',
                controllerAs: 'vm',
                templateUrl: 'modules/jobs/partials/jobExecutionDetailTemplate.html'
            })
            .when('/workspaces/:id?', {
                controller: 'workspacesController',
                controllerAs: 'vm',
                templateUrl: 'modules/workspaces/partials/workspacesTemplate.html'
            })
            .when('/feed/strikes/:id?', {
                controller: 'strikesController',
                controllerAs: 'vm',
                templateUrl: 'modules/feed/partials/strikesTemplate.html'
            })
            .when('/batch', {
                controller: 'batchesController',
                controllerAs: 'vm',
                templateUrl: 'modules/batch/partials/batchesTemplate.html'
            })
            .when('/batch/:id', {
                controller: 'batchDetailsController',
                controllerAs: 'vm',
                templateUrl: 'modules/batch/partials/batchDetailsTemplate.html'
            })
            .otherwise({
                redirectTo: '/'
            });
    })
    .value('moment', window.moment)
    .value('localStorage', window.localStorage)
    .value('XMLHttpRequest', window.XMLHttpRequest)
    .value('toastr', window.toastr);
})();
