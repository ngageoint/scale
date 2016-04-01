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

        // Status service
        var statusOverrideUrl = 'test/data/status.json';
        var statusRegex = new RegExp('^' + scaleConfig.urls.getStatus(), 'i');
        $httpBackend.whenGET(statusRegex).respond(function() {
            return getSync(statusOverrideUrl);
        });

        // Job type status
        var jobTypeStatusOverrideUrl = 'test/data/jobTypeStatus.json';
        var jobTypeStatusRegex = new RegExp('^' + scaleConfig.urls.getJobTypeStatus(), 'i');
        $httpBackend.whenGET(jobTypeStatusRegex).respond(function() {
            return getSync(jobTypeStatusOverrideUrl);
        });

        // Job types
        var jobTypesOverrideUrl = 'test/data/jobTypes.json';
        var jobTypesRegex = new RegExp('^' + scaleConfig.urls.getJobTypes(), 'i');
        $httpBackend.whenGET(jobTypesRegex).respond(function() {
            return getSync(jobTypesOverrideUrl);
        });

        // Node status
        var nodeStatusOverrideUrl = 'test/data/nodeStatus.json';
        var nodeStatusRegex = new RegExp('^' + scaleConfig.urls.getNodeStatus(), 'i');
        $httpBackend.whenGET(nodeStatusRegex).respond(function() {
            return getSync(nodeStatusOverrideUrl);
        });

        // For everything else, don't mock
        $httpBackend.whenGET(/^\w+.*/).passThrough();
        $httpBackend.whenPOST(/^\w+.*/).passThrough();
    });
})();