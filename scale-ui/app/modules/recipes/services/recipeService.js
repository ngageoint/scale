(function () {
    'use strict';
    /**
     *
     */
    angular.module('scaleApp').service('recipeService', function ($http, $q, $timeout, scaleConfig, RecipeType, RecipeTypeDetail, Recipe, RecipeDetails, RecipeTypeValidation) {
        var getRecipesParams = function (page, page_size, started, ended, order, completed, recipe_type_id, recipe_type_name, url) {
            return {
                page: page,
                page_size: page_size,
                started: started,
                ended: ended,
                order: order,
                completed: completed,
                recipe_type_id: recipe_type_id,
                recipe_type_name: recipe_type_name,
                url: url
            };
        };

        return {
            getRecipeTypes: function () {
                var d = $q.defer();
                $http.get(scaleConfig.urls.getRecipeTypes()).success(function (data) {
                    d.resolve(RecipeType.transformer(data.results));
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },

            getRecipeTypeDetail: function (id) {
              var d = $q.defer();

              $http.get(scaleConfig.urls.getRecipeTypeDetail(id)).success(function (data) {
                var returnData = RecipeTypeDetail.transformer(data);
                d.resolve(returnData);
              });
              return d.promise;
            },

            getRecipes: function (params) {
                params = params || getRecipesParams();
                var d = $q.defer();

                $http({
                    url: params.url ? params.url : scaleConfig.urls.getRecipes(),
                    method: 'GET',
                    params: params
                }).success(function (data) {
                    data.results = Recipe.transformer(data.results);
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });

                return d.promise;
            },

            getRecipeDetails: function (id) {
                var d = $q.defer();
                $http.get(scaleConfig.urls.getRecipeDetails(id)).success(function (data) {
                    var result = RecipeDetails.transformer(data);
                    d.resolve(result);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },

            saveRecipeType: function(recipeType) {
                var d = $q.defer();
                var cleanRecipeType = RecipeTypeValidation.transformer(recipeType);

                if(!cleanRecipeType.id){
                    $http.post(scaleConfig.urls.saveRecipeType(),cleanRecipeType).success(function(result){
                        recipeType.id = result;
                        d.resolve(recipeType);
                    }).error(function(error){
                        d.reject(error);
                    });
                } else {
                    $http.patch(scaleConfig.urls.saveRecipeType() + cleanRecipeType.id + '/',cleanRecipeType).success(function(result){
                        recipeType = result;
                        d.resolve(recipeType);
                    }).error(function(error){
                        d.reject(error);
                    });
                }

                return d.promise;
            },

            validateRecipeType: function(recipeType) {
                var d = $q.defer();
                var cleanRecipeType = RecipeTypeValidation.transformer(recipeType);

                $http.post(scaleConfig.urls.validateRecipeType(),cleanRecipeType).success(function(result){
                    d.resolve(result);
                }).error(function(error){
                    d.reject(error);
                })

                return d.promise;
            }
        };
    });
})();
