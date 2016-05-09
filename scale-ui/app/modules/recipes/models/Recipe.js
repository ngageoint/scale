(function () {
    'use strict';

    angular.module('scaleApp').factory('Recipe', function (scaleConfig, RecipeType, scaleService) {
        var Recipe = function (id, created, completed, last_modified, recipe_type) {
            this.id = id;
            this.created = created;
            this.created_formatted = moment.utc(created).format(scaleConfig.dateFormats.day_second_utc_nolabel);
            this.completed = completed;
            this.completed_formatted = completed ? moment.utc(completed).format(scaleConfig.dateFormats.day_second_utc_nolabel) : '';
            this.last_modified = last_modified;
            this.last_modified_formatted = moment.utc(last_modified).format(scaleConfig.dateFormats.day_second_utc_nolabel);
            this.last_status_change = last_modified ? moment.duration(moment.utc(last_modified).diff(moment.utc())).humanize(true) : '';
            this.recipe_type = RecipeType.transformer(recipe_type);
        };

        // public methods
        Recipe.prototype = {
            getDuration: function () {
                return scaleService.calculateDuration(this.created, this.last_modified);
            }
        };

        // static methods, assigned to class
        Recipe.build = function (data) {
            if (data) {
                return new Recipe(
                    data.id,
                    data.created,
                    data.completed,
                    data.last_modified,
                    data.recipe_type
                );
            }
            return new Recipe();
        };

        Recipe.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(Recipe.build)
                    .filter(Boolean);
            }
            return Recipe.build(data);
        };

        return Recipe;
    });
})();