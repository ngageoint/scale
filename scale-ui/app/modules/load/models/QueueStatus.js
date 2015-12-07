(function () {
    'use strict';

    angular.module('scaleApp').factory('QueueStatus', function (scaleConfig, scaleService) {
        var QueueStatus = function (count, longest_queued, job_type_name, job_type_version, highest_priority, is_job_type_paused) {
            this.count = count;
            this.longest_queued = longest_queued;
            this.job_type_name = job_type_name;
            this.job_type_version = job_type_version;
            this.highest_priority = highest_priority;
            this.is_job_type_paused = is_job_type_paused;
        };

        // public methods
        QueueStatus.prototype = {
            getIcon: function () {
                var configJobType = _.find(scaleConfig.jobTypes, 'title', this.job_type_name);
                return configJobType ? '<i class="fa">&#x' + configJobType.code + '</i>' : '<i class="fa">&#x' + scaleConfig.defaultIconCode + '</i>';
            },
            getDuration: function () {
                return scaleService.calculateDuration(this.longest_queued, moment.utc().toISOString());
            }
        };

        // static methods, assigned to class
        QueueStatus.build = function (data) {
            if (data) {
                return new QueueStatus(
                    data.count,
                    data.longest_queued,
                    data.job_type_name,
                    data.job_type_version,
                    data.highest_priority,
                    data.is_job_type_paused
                );
            }
            return new QueueStatus();
        };

        QueueStatus.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(QueueStatus.build)
                    .filter(Boolean);
            }
            return QueueStatus.build(data);
        };

        return QueueStatus;
    });
})();
