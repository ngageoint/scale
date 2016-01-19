(function(){
    'use strict';

    angular.module('scaleApp').factory('RecipeTypeDefinitionJob', function (scaleConfig, JobTypeDetails) {
        // private methods
        var RecipeTypeDefinitionJob = function (recipe_inputs, name, job_type, dependencies) {
            this.recipe_inputs = recipe_inputs;
            this.name = name;
            this.job_type = job_type;
            //this.job_type = {
            //    name: job_type.name,
            //    version: job_type.version
            //};
            this.dependencies = dependencies || [];
        };

        // static methods, assigned to class
        RecipeTypeDefinitionJob.build = function (data) {
            if (data) {
                return new RecipeTypeDefinitionJob(
                    data.recipe_inputs,
                    data.name,
                    data.job_type,
                    data.dependencies
                );
            }
            return new RecipeTypeDefinitionJob();
        };

        RecipeTypeDefinitionJob.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(RecipeTypeDefinitionJob.build);
            }
            return RecipeTypeDefinitionJob.build(data);
        };


        return RecipeTypeDefinitionJob;

    });
})();
