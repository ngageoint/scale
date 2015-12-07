(function () {
    'use strict';

    angular.module('scaleApp').controller('recipeDetailsController', function ($rootScope, $scope, $location, $routeParams, navService, recipeService, scaleConfig, subnavService, userService) {
        $scope.recipe = {};
        $scope.recipeId = $routeParams.id;
        $scope.subnavLinks = scaleConfig.subnavLinks.recipes;
        subnavService.setCurrentPath('recipes');
        $scope.loadingRecipeDetail = true;
        $scope.activeTab = 'status';
        $scope.lastStatusChange = '';

        var getRecipeDetail = function (recipeId) {
            $scope.loadingRecipeDetail = true;
            recipeService.getRecipeDetails(recipeId).then(function (data) {
                $scope.recipe = data;
                recipeService.getRecipeTypeDetail(data.recipe_type.id).then(function(recipeType){
                    $scope.recipeType = recipeType;
                }).catch(function(error){
                   console.log(error);
                });
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                $scope.loadingRecipeDetail = false;
            });
        };

        var initialize = function () {
            navService.updateLocation('recipes');
            $rootScope.user = userService.getUserCreds();

            getRecipeDetail($scope.recipeId);
        };



        $scope.switchTab = function (tab) {
            $('#' + $scope.activeTab).hide();
            $scope.activeTab = tab;
            $('#' + $scope.activeTab).show();
        };

        initialize();
    });
})();
