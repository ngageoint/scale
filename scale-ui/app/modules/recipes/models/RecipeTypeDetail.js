(function () {
    'use strict';

    angular.module('scaleApp').factory('RecipeTypeDetail', function (scaleConfig, RecipeTypeDefinition, JobTypeDetails) {
        var RecipeTypeDetail = function (id, name, version, title, description, is_active, definition, created, last_modified, archived, trigger_rule, job_types) {
            this.id = id;
            this.name = name;
            this.version = version;
            this.title = title;
            this.description = description;
            this.is_active = is_active;
            this.definition = RecipeTypeDefinition.transformer(definition);
            this.created = created;
            this.last_modified = last_modified;
            this.archived = archived;
            this.trigger_rule = trigger_rule;
            this.job_types = JobTypeDetails.transformer(job_types);
            this.modified = false;
        };

        // static methods, assigned to class
        RecipeTypeDetail.build = function (data) {
            if (data) {
                return new RecipeTypeDetail(
                    data.id,
                    data.name,
                    data.version,
                    data.title,
                    data.description,
                    data.is_active,
                    data.definition,
                    data.created,
                    data.last_modified,
                    data.archived,
                    data.trigger_rule,
                    data.job_types
                );
            }
            return new RecipeTypeDetail();
        };

        RecipeTypeDetail.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(RecipeTypeDetail.build);
            }
            return RecipeTypeDetail.build(data);
        };

        return RecipeTypeDetail;
    });
})();
