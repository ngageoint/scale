(function () {
    'use strict';
    
    angular.module('scaleApp').controller('fileTraceController', function ($scope, scaleConfig, navService, subnavService, feedService) {
        $scope.loading = false;
        $scope.loadingSourceFiles = false;
        $scope.noResults = null;
        $scope.subnavLinks = scaleConfig.subnavLinks.feed;
        $scope.filename = '';
        $scope.sourceFile = null;

        $scope.search = function () {
            $scope.loading = true;
            feedService.getSourceDetails($scope.filename).then(function (data) {
                $scope.sourceFile = data;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                $scope.loading = false;
            });
        };
        
        $scope.getSources = function (filename) {
            $scope.loadingSourceFiles = true;
            return feedService.getSources({file_name: filename}).then(function (data) {
                $scope.noResults = data.results.length <= 0;
                return _.map(data.results, 'file_name');
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                $scope.loadingSourceFiles = false;
            });
        };

        var initialize = function () {
            navService.updateLocation('feed');
            subnavService.setCurrentPath('feed/trace');
        };

        initialize();
    });
})();