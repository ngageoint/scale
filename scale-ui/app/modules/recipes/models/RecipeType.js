(function () {
    'use strict';

    angular.module('scaleApp').factory('RecipeType', function (scaleConfig, RecipeTypeDefinition) {
        var RecipeType = function (id, name, version, title, description, is_active, definition, revision_num, created,  last_modified, archived, trigger_rule) {
            this.id = id;
            this.name = name;
            this.version = version;
            this.title = title;
            this.description = description;
            this.is_active = is_active;
            this.definition = definition ? RecipeTypeDefinition.transformer(definition) : new RecipeTypeDefinition();
            this.revision_num = revision_num;
            this.created = created;
            this.last_modified = last_modified;
            this.archived = archived;
            this.trigger_rule = {
                type: trigger_rule ? trigger_rule.type : '',
                name: trigger_rule ? trigger_rule.name : '',
                is_active: trigger_rule ? trigger_rule.is_active : false,
                configuration: {
                    condition: {
                        media_type: trigger_rule ? trigger_rule.configuration.condition.media_type : '',
                        data_types: trigger_rule ? trigger_rule.configuration.condition.data_types : []
                    },
                    data: {
                        workspace_name: trigger_rule ? trigger_rule.configuration.data.workspace_name : '',
                        input_data_name: trigger_rule ? trigger_rule.configuration.data.input_data_name : ''
                    }
                }
            };
            this.modified = false;
        };

        // static methods, assigned to class
        RecipeType.build = function (data) {
            if (data) {
                return new RecipeType(
                    data.id,
                    data.name,
                    data.version,
                    data.title,
                    data.description,
                    data.is_active,
                    data.definition,
                    data.revision_num,
                    data.created,
                    data.last_modified,
                    data.archived,
                    data.trigger_rule
                );
            }
            return new RecipeType();
        };

        RecipeType.transformer = function (data) {
            if (angular.isArray(data)) {
                return data.map(RecipeType.build);
            }
            return RecipeType.build(data);
        };

        return RecipeType;
    });
})();
