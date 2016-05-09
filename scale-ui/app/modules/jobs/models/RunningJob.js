(function () {
    'use strict';

    angular.module('scaleApp').factory('RunningJob', function (scaleConfig, scaleService, JobType) {
        var RunningJob = function (count, longest_running, job_type) {
            this.count = count;
            this.longest_running = longest_running;
            this.job_type = JobType.transformer(job_type);
        };

        // public methods
        RunningJob.prototype = {
            getDuration: function () {
                return scaleService.calculateDuration(this.longest_running, moment.utc().toISOString());
            },
            getIcon: function () {
                var icon = this.job_type.icon_code ? '<i class="fa">&#x' + this.job_type.icon_code + '</i>' : '<i class="fa">&#x' + scaleConfig.defaultIconCode + '</i>';
                return icon;
            }
        };

        // static methods, assigned to class
        RunningJob.build = function (data) {
            if (data) {
                return new RunningJob(
                    data.count,
                    data.longest_running,
                    data.job_type
                );
            }
            return new RunningJob();
        };

        RunningJob.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(RunningJob.build)
                    .filter(Boolean);
            }
            return RunningJob.build(data);
        };

        return RunningJob;
    });
})();