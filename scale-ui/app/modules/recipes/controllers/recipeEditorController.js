(function(){
    'use strict';

    angular.module('scaleApp').controller('recipeEditorController', function($scope, $log, $location, $routeParams, $uibModal, navService, recipeService, RecipeType, subnavService, jobTypeService, scaleConfig) {

        $scope.date = new Date();
        $scope.recipes = null;
        $scope.recipeTypeId = parseInt($routeParams.id);

        $scope.jobTypeValues = [];

        $scope.subnavLinks = scaleConfig.subnavLinks.recipes;
        subnavService.setCurrentPath('recipes/builder');

        $scope.items = ['item1', 'item2', 'item3'];
        $scope.animationsEnabled = true;
        $scope.selected = null;

        var getJobTypes = function () {
            jobTypeService.getJobTypesOnce().then(function (data) {
                $scope.jobTypeValues = data;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        $scope.openAddJob = function (size) {
           var modalInstance = $uibModal.open({
             animation: $scope.animationsEnabled,
             templateUrl: 'addJobContent.html',
             scope: $scope,
             size: 'sm'
           });

           modalInstance.result.then(function () {
             $scope.addJobType($scope.selectedItem);
           }, function () {

           });
         };

         $scope.addJobType = function(selectedJobType){
             $scope.recipeType.definition.addJobType(selectedJobType);
             $scope.redrawGraph();
         };

         $scope.selectItem = function(item){
             $scope.selectedItem = item;
         };

        $scope.initialize = function() {
            getJobTypes();
            navService.updateLocation('recipes');
            if($scope.recipeTypeId){
                $scope.getRecipeTypeDetail($scope.recipeTypeId);
            }
            else{
                $scope.recipeType = RecipeType.new();
            }

        };

        $scope.getRecipeTypeDetail = function (id) {
            recipeService.getRecipeTypeDetail(id).then(function (data) {
                $scope.recipeType = data;
                if ($scope.redrawGraph) {
                    $scope.redrawGraph();
                }
            });
        };

        $scope.saveRecipeType = function(){
                console.log($scope.recipeType.name);
        };

        $scope.initialize();
    });
})();
