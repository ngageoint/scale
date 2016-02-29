(function () {
    'use strict';

    angular.module('scaleApp').factory('RecipeJob', function (JobType) {
        var RecipeJob = function (id, status, job_type) {
            this.id = id;
            this.status = status;
            this.job_type = JobType.transformer(job_type);
        };

        // static methods, assigned to class
        RecipeJob.build = function (data) {
            if (data) {
                return new RecipeJob(
                    data.id,
                    data.status,
                    data.job_type
                );
            }
            return new RecipeJob();
        };

        RecipeJob.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(RecipeJob.build)
                    .filter(Boolean);
            }
            return RecipeJob.build(data);
        };

        return RecipeJob;
    });
})();