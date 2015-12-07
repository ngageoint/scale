(function () {
    'use strict';

    angular.module('scaleApp').factory('RecipeDetails', function (RecipeData, RecipeTypeDefinition, RecipeType, RecipeJobContainer, scaleConfig) {
        var RecipeDetails = function (id, created, completed, last_modified, data, recipe_type, jobs) {
            this.id = id;
            this.created = created;
            this.completed = completed;
            this.completed_formatted = this.completed ? moment.utc(this.completed).toISOString() : this.completed;
            this.last_modified = last_modified;
            this.data = RecipeData.transformer(data);
            this.recipe_type = RecipeType.transformer(recipe_type);
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
