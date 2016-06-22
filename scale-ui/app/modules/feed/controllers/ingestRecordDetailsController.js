(function () {
    'use strict';
    
    angular.module('scaleApp').controller('ingestRecordDetailsController', function ($scope, $routeParams, scaleConfig, scaleService, navService, subnavService, feedService) {
        $scope.loading = false;
        $scope.subnavLinks = scaleConfig.subnavLinks.feed;
        $scope.scaleService = scaleService;
        $scope.moment = moment;
        $scope.ingestRecord = null;

        var getIngestRecordDetails = function () {
            $scope.loading = true;
            feedService.getSourceDetails($routeParams.id).then(function (data) {
                $scope.ingestRecord = data;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        var initialize = function () {
            navService.updateLocation('feed');
            subnavService.setCurrentPath('feed/ingests');
            getIngestRecordDetails();
        };

        initialize();
    });
})();