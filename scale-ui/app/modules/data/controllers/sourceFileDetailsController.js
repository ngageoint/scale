(function () {
    'use strict';

    angular.module('scaleApp').controller('sourceFileDetailsController', function($scope, $location, $routeParams, navService, feedService, SourceFile) {
        var ctrl = this,
            sourceFileId = parseInt($routeParams.id);

        ctrl.loading = true;
        ctrl.sourceFile = null;
        ctrl.activeTab = 'jobs';

        $scope.jobsData = null;
        $scope.productsData = null;
        $scope.ingestsData = null;

        var getSourceJobs = function () {
            feedService.getSourceDescendants(ctrl.sourceFile.id, 'jobs').then(function (data) {
                $scope.jobsData = data;
            });
        };

        var getSourceProducts = function () {
            feedService.getSourceDescendants(ctrl.sourceFile.id, 'products').then(function (data) {
                $scope.productsData = data;
            });
        };

        var getSourceIngests = function () {
            feedService.getSourceDescendants(ctrl.sourceFile.id, 'ingests').then(function (data) {
                $scope.ingestsData = data;
            });
        };

        var getSourceFileDetails = function () {
            feedService.getSourceDetails(sourceFileId).then(function (data) {
                ctrl.sourceFile = SourceFile.transformer(data);
                getSourceIngests();
                getSourceProducts();
                getSourceJobs();
            }).finally(function () {
                ctrl.loading = false;
            });
        };

        var initialize = function() {
            navService.updateLocation('data');
            getSourceFileDetails();
        };

        initialize();

        ctrl.showGrid = function (gridType) {
            ctrl.activeTab = gridType;
        };
    });
})();
