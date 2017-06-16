(function () {
    'use strict';

    angular.module('scaleApp').controller('sourceFileDetailsController', function($scope, $location, $routeParams, navService, feedService, SourceFile) {
        var vm = this,
            sourceFileId = parseInt($routeParams.id);

        vm.loading = true;
        vm.sourceFile = null;

        var getSourceFileDetails = function () {
            feedService.getSourceDetails(sourceFileId).then( function (data) {
                vm.sourceFile = SourceFile.transformer(data);
            }).finally(function () {
                vm.loading = false;
            });
        };

        var initialize = function() {
            navService.updateLocation('data');
            getSourceFileDetails();
        };

        initialize();
    });
})();
