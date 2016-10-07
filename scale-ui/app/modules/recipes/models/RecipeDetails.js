(function () {
    'use strict';

    angular.module('scaleApp').factory('RecipeDetails', function (RecipeData, RecipeTypeDefinition, RecipeType, RecipeTypeDetail, RecipeJobContainer, scaleConfig) {
        var RecipeDetails = function (id, created, completed, last_modified, data, recipe_type, recipe_type_rev, jobs,
                                      is_superseded, root_superseded_recipe, superseded_recipe,
                                      superseded_by_recipe, superseded) {
            this.id = id;
            this.created = created;
            this.completed = completed;
            this.completed_formatted = this.completed ? moment.utc(this.completed).format(scaleConfig.dateFormats.day_second_utc) : this.completed;
            this.last_modified = last_modified;
            this.data = RecipeData.transformer(data);
            this.recipe_type = RecipeType.transformer(recipe_type);
            this.recipe_type_rev = RecipeTypeDetail.transformer(recipe_type_rev);
            this.jobs = RecipeJobContainer.transformer(jobs);
            this.is_superseded = is_superseded;
            this.root_superseded_recipe = root_superseded_recipe;
            this.superseded_recipe = superseded_recipe;
            this.superseded_by_recipe = superseded_by_recipe;
            this.superseded = superseded;
        };

        // static methods, assigned to class
        RecipeDetails.build = function (data) {
            if (data) {
              console.log(data);
                return new RecipeDetails(
                  data.id,
                  data.created,
                  data.completed,
                  data.last_modified,
                  data.data,
                  data.recipe_type,
                  data.recipe_type_rev,
                  data.jobs,
                  data.is_superseded,
                  data.root_superseded_recipe,
                  data.superseded_recipe,
                  data.superseded_by_recipe,
                  data.superseded
                );
            }
            return new RecipeDetails();
        };

        RecipeDetails.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                  .map(RecipeDetails.build)
                  .filter(Boolean);
            }
            return RecipeDetails.build(data);
        };

        return RecipeDetails;
    });
})();
