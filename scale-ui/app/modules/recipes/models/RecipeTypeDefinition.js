(function () {
    'use strict';

    angular.module('scaleApp').factory('RecipeTypeDefinition', function (scaleConfig, RecipeTypeDefinitionJob, JobTypeInputData) {

        var self = this;
        // private methods
        var RecipeTypeDefinition = function (input_data, version, jobs) {
            this.input_data = input_data ? JobTypeInputData.transformer(input_data) : [];
            this.version = version || '1.0';
            this.jobs = jobs ? RecipeTypeDefinitionJob.transformer(jobs) : [];
        };

        // public methods
        RecipeTypeDefinition.prototype = {
            addJob: function (jobType) {
                var job = {
                    dependencies: [],
                    recipe_inputs: [],
                    name: jobType.name,
                    job_type_id: jobType.id,
                    job_type: jobType
                };
                this.jobs.push(job);
            }
        };

        // static methods, assigned to class
        RecipeTypeDefinition.build = function (data) {
            if(data){
                return new RecipeTypeDefinition(
                    data.input_data,
                    data.version,
                    data.jobs
                );
            }
            return new RecipeTypeDefinition();
        };

        RecipeTypeDefinition.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(RecipeTypeDefinition.build);
            }
            return RecipeTypeDefinition.build(data);
        };

        return RecipeTypeDefinition;
    });
})();
