(function () {
    'use strict';

    angular.module('scaleApp').factory('Batch', function (scaleConfig, JobType, RecipeType) {
        var Batch = function (id, title, description, status, recipe_type, event, creator_job, definition, created_count, failed_count, total_count, created, last_modified) {
            this.id = id || null;
            this.title = title || null;
            this.description = description || null;
            this.status = status || null;
            this.recipe_type = recipe_type ? RecipeType.transformer(recipe_type) : null;
            this.event = event || null;
            this.creator_job = creator_job ? {
                id: creator_job.id,
                job_type: JobType.transformer(creator_job.job_type),
                job_type_rev: creator_job.job_type_rev,
                event: creator_job.event,
                status: creator_job.status,
                priority: creator_job.priority,
                num_exes: creator_job.num_exes
            } : {};
            this.definition = definition || null;
            this.created_count = created_count || 0;
            this.failed_count = failed_count || 0;
            this.total_count = total_count || 0;
            this.created = created;
            this.created_formatted = moment.utc(created).format(scaleConfig.dateFormats.day_second_utc);
            this.last_modified = last_modified;
            this.last_modified_formatted = moment.utc(last_modified).format(scaleConfig.dateFormats.day_second_utc);
        };

        Batch.prototype = {
            clean: function () {
                var returnObj = {
                    recipe_type_id: this.recipe_type.id,
                    title: this.title,
                    description: this.description,
                    definition: this.definition
                };
                // remove empty/null/undefined values from returnObj
                return _.pick(returnObj, _.identity);
            }
        };

        // static methods, assigned to class
        Batch.build = function (data) {
            if (data) {
                var returnObj = new Batch(
                    data.id,
                    data.title,
                    data.description,
                    data.status,
                    data.recipe_type,
                    data.event,
                    data.creator_job,
                    data.definition,
                    data.created_count,
                    data.failed_count,
                    data.total_count,
                    data.created,
                    data.last_modified
                );
                // remove empty/null/undefined values from returnObj
                return _.pick(returnObj, _.identity);
            }
            return new Batch();
        };

        Batch.transformer = function (data) {
            if (angular.isArray(data)) {
                return data.map(Batch.build);
            }
            return Batch.build(data);
        };

        return Batch;
    });
})();
