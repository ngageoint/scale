(function () {
    'use strict';

    angular.module('scaleApp').factory('Job', function (scaleConfig, JobType, scaleService) {
        var Job = function (id, job_type, job_type_rev, event, error, status, priority, num_exes, timeout, max_tries, cpus_required, mem_required, disk_in_required, disk_out_required, created, queued, started, ended, last_status_change, last_modified) {
            this.id = id;
            this.job_type = JobType.transformer(job_type);
            this.job_type_rev = job_type_rev;
            this.event = event;
            this.error = error;
            this.status = status;
            this.priority = priority;
            this.num_exes = num_exes;
            this.timeout = timeout;
            this.max_tries = max_tries;
            this.cpus_required = cpus_required;
            this.mem_required = mem_required;
            this.disk_in_required = disk_in_required;
            this.disk_out_required = disk_out_required;
            this.created = created;
            this.created_formatted = moment.utc(created).format(scaleConfig.dateFormats.day_second_utc_nolabel);
            this.queued = queued;
            this.started = started;
            this.ended = ended;
            this.last_status_change = last_status_change;
            this.last_modified = last_modified;
            this.last_modified_formatted = moment.utc(last_modified).format(scaleConfig.dateFormats.day_second_utc_nolabel);
        };

        // public methods
        Job.prototype = {
            getDuration: function () {
                var start = this.started,
                    end = this.ended ? this.ended : moment.utc().toISOString();
                return scaleService.calculateDuration(start, end);
            }
        };

        // static methods, assigned to class
        Job.build = function (data) {
            if (data) {
                return new Job(
                    data.id,
                    data.job_type,
                    data.job_type_rev,
                    data.event,
                    data.error,
                    data.status,
                    data.priority,
                    data.num_exes,
                    data.timeout,
                    data.max_tries,
                    data.cpus_required,
                    data.mem_required,
                    data.disk_in_required,
                    data.disk_out_required,
                    data.created,
                    data.queued,
                    data.started,
                    data.ended,
                    data.last_status_change,
                    data.last_modified
                );
            }
            return new Job();
        };

        Job.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(Job.build)
                    .filter(Boolean);
            }
            return Job.build(data);
        };

        return Job;
    });
})();
