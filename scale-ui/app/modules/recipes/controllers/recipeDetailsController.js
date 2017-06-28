(function () {
    'use strict';

    angular.module('scaleApp').controller('recipeDetailsController', function ($rootScope, $scope, $location, $routeParams, navService, recipeService, scaleConfig, subnavService, userService) {

        var vm = this;

        vm.recipe = {};
        vm.recipeId = $routeParams.id;
        vm.subnavLinks = scaleConfig.subnavLinks.recipes;
        subnavService.setCurrentPath('recipes');
        vm.loadingRecipeDetail = true;
        vm.activeTab = 'status';
        vm.lastStatusChange = '';

        vm.getRecipeDetail = function (recipeId) {
            vm.loadingRecipeDetail = true;
            recipeService.getRecipeDetails(recipeId).then(function (data) {
                vm.recipe = data;
                recipeService.getRecipeTypeDetail(data.recipe_type_rev.recipe_type.id).then(function(recipeType){
                    vm.recipeType = recipeType;
                }).catch(function(error){
                   console.log(error);
                });
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                vm.loadingRecipeDetail = false;
            });
        };

        vm.initialize = function () {
            navService.updateLocation('recipes');
            vm.getRecipeDetail(vm.recipeId);
        };



        vm.switchTab = function (tab) {
            $('#' + vm.activeTab).hide();
            vm.activeTab = tab;
            $('#' + vm.activeTab).show();
        };

        vm.initialize();
    });
})();
