(function () {
    'use strict';

    angular.module('scaleApp').factory('RecipeTypeValidation', function (RecipeTypeDefinition) {
        var RecipeTypeValidation = function (name, version, title, description, definition, trigger_type, trigger_config) {
            this.name = name;
            this.version = version;
            this.title = title;
            this.description = description;
            this.definition = definition ? RecipeTypeDefinition.transformer(definition) : new RecipeTypeDefinition();
            this.trigger_type = trigger_type;
            this.trigger_config = trigger_config;
        };

        // static methods, assigned to class
        RecipeTypeValidation.build = function (data) {
            if (data) {
                return new RecipeTypeValidation(
                    data.name,
                    data.version,
                    data.title,
                    data.description,
                    data.definition,
                    data.trigger_type,
                    data.trigger_config
                );
            }
            return new RecipeTypeValidation();
        };

        RecipeTypeValidation.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(RecipeTypeValidation.build);
            }
            return RecipeTypeValidation.build(data);
        };

        return RecipeTypeValidation;
    });
})();