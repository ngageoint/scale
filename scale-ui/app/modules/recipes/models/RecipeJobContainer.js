(function () {
    'use strict';

    angular.module('scaleApp').factory('RecipeJobContainer', function (RecipeJob) {
        var RecipeJobContainer = function (job_name, job) {
            this.job_name = job_name;
            this.job = RecipeJob.transformer(job);
        };

        // static methods, assigned to class
        RecipeJobContainer.build = function (data) {
            if (data) {
                return new RecipeJobContainer(
                    data.job_name,
                    data.job
                );
            }
            return new RecipeJobContainer();
        };

        RecipeJobContainer.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(RecipeJobContainer.build)
                    .filter(Boolean);
            }
            return RecipeJobContainer.build(data);
        };

        return RecipeJobContainer;
    });
})();