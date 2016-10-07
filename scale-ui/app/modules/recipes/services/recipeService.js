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

        var getRecipeTypesParams = function (page, page_size, started, ended, order) {
            return {
                page: page,
                page_size: page_size,
                started: started,
                ended: ended,
                order: order ? order : ['title', 'version']
            };
        };

        return {
            getRecipeTypes: function (params) {
                params = params || getRecipeTypesParams();
                var d = $q.defer();

                $http({
                    url: scaleConfig.getUrlPrefix('recipe-types') + 'recipe-types/',
                    method: 'GET',
                    params: params
                }).success(function (data) {
                    data.results = RecipeType.transformer(data.results);
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });
                
                return d.promise;
            },

            getRecipeTypeDetail: function (id) {
              var d = $q.defer();

              $http.get(scaleConfig.getUrlPrefix('recipe-types') + 'recipe-types/' + id + '/').success(function (data) {
                  var returnData = RecipeTypeDetail.transformer(data);
                  d.resolve(returnData);
              });
              return d.promise;
            },

            getRecipes: function (params) {
                params = params || getRecipesParams();
                var d = $q.defer();

                $http({
                    url: params.url ? params.url : scaleConfig.getUrlPrefix('recipes') + 'recipes/',
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
                $http.get(scaleConfig.getUrlPrefix('recipes') + 'recipes/' + id + '/').success(function (details) {
                    console.log('getRecipeDetails');
                    console.log(details);
                    var result = RecipeDetails.transformer(details);
                    d.resolve(result);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },

            saveRecipeType: function (recipeType) {
                var d = $q.defer();
                var cleanRecipeType = RecipeTypeValidation.transformer(recipeType);

                if (!cleanRecipeType.id) {
                    $http.post(scaleConfig.getUrlPrefix('recipe-types') + 'recipe-types/', cleanRecipeType).success(function (result) {
                        d.resolve(result);
                    }).error(function(error){
                        d.reject(error);
                    });
                } else {
                    $http.patch(scaleConfig.getUrlPrefix('recipe-types') + 'recipe-types/' + cleanRecipeType.id + '/', cleanRecipeType).success(function (result) {
                        recipeType = result;
                        d.resolve(recipeType);
                    }).error(function(error){
                        d.reject(error);
                    });
                }

                return d.promise;
            },

            validateRecipeType: function (recipeType) {
                var d = $q.defer();
                var cleanRecipeType = RecipeTypeValidation.transformer(recipeType);

                $http.post(scaleConfig.getUrlPrefix('recipe-types') + 'recipe-types/validation/', cleanRecipeType).success(function (result) {
                    d.resolve(result);
                }).error(function(error){
                    d.reject(error);
                });

                return d.promise;
            }
        };
    });
})();
