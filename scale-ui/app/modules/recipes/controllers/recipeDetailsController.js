(function () {
    'use strict';

    angular.module('scaleApp').controller('recipeDetailsController', function ($rootScope, $scope, $location, $routeParams, navService, recipeService, scaleConfig, subnavService, userService, RecipeTypeDetail) {

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
                // attach revision interface to each job type
                var jobTypes = [];
                _.forEach(data.jobs, function (jobData) {
                    var jobType = jobData.job.job_type;
                    jobType.interface = jobData.job.job_type_rev.interface;
                    jobTypes.push(jobType);
                });
                // build recipe type details with revision definition and adjusted job types
                vm.recipeType = new RecipeTypeDetail(
                    data.recipe_type.id,
                    data.recipe_type.name,
                    data.recipe_type.version,
                    data.recipe_type.title,
                    data.recipe_type.description,
                    data.recipe_type.is_active,
                    data.recipe_type_rev.definition,
                    data.recipe_type.created,
                    data.recipe_type.last_modified,
                    data.recipe_type.archived,
                    data.recipe_type.trigger_rule,
                    jobTypes,
                    data.recipe_type
                );
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
