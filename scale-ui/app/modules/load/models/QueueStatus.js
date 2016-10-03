(function () {
    'use strict';

    angular.module('scaleApp').factory('QueueStatus', function (scaleConfig, scaleService, JobType) {
        var QueueStatus = function (job_type, count, longest_queued, highest_priority) {
            this.job_type = JobType.transformer(job_type);
            this.count = count;
            this.longest_queued = longest_queued;
            this.highest_priority = highest_priority;
        };

        // public methods
        QueueStatus.prototype = {
            getIcon: function () {
                return this.job_type.icon_code ? '<i class="fa">&#x' + this.job_type.icon_code + '</i>' : '<i class="fa">&#x' + scaleConfig.defaultIconCode + '</i>';
            },
            getDuration: function () {
                return scaleService.calculateDuration(this.longest_queued, moment.utc().toISOString());
            }
        };

        // static methods, assigned to class
        QueueStatus.build = function (data) {
            if (data) {
                return new QueueStatus(
                    data.job_type,
                    data.count,
                    data.longest_queued,
                    data.highest_priority
                );
            }
            return new QueueStatus();
        };

        QueueStatus.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(QueueStatus.build);
            }
            return QueueStatus.build(data);
        };

        return QueueStatus;
    });
})();
