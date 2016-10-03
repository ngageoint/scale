(function () {
    'use strict';

    angular.module('scaleApp').factory('RecipeDetails', function (RecipeData, RecipeTypeDefinition, RecipeType, RecipeTypeDetail, RecipeJobContainer, scaleConfig) {
        var RecipeDetails = function (id, created, completed, last_modified, data, recipe_type, recipe_type_rev, jobs) {
            this.id = id;
            this.created = created;
            this.completed = completed;
            this.completed_formatted = this.completed ? moment.utc(this.completed).format(scaleConfig.dateFormats.day_second_utc) : this.completed;
            this.last_modified = last_modified;
            this.data = RecipeData.transformer(data);
            this.recipe_type = RecipeType.transformer(recipe_type);
            this.recipe_type_rev = RecipeTypeDetail.transformer(recipe_type_rev);
            this.jobs = RecipeJobContainer.transformer(jobs);
        };

        // static methods, assigned to class
        RecipeDetails.build = function (data) {
            if (data) {
                return new RecipeDetails(
                    data.id,
                    data.created,
                    data.completed,
                    data.last_modified,
                    data.data,
                    data.recipe_type,
                    data.recipe_type_rev,
                    data.jobs
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
