(function () {
    'use strict';
    
    angular.module('scaleApp').controller('ingestRecordDetailsController', function ($scope, $routeParams, scaleConfig, navService, subnavService, feedService) {
        $scope.loading = false;
        $scope.subnavLinks = scaleConfig.subnavLinks.feed;
        $scope.ingestRecord = null;

        var getIngestRecordDetails = function () {
            $scope.loading = true;
            feedService.getSourceDetails($routeParams.file_name).then(function (data) {
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