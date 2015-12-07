(function () {
    'use strict';

    angular.module('scaleApp').factory('JobExecution', function (scaleConfig, Job, Node, moment) {
        var JobExecution = function (id, status, command_arguments, timeout, pre_started, pre_completed, pre_exit_code, job_started, job_completed, job_exit_code, post_started, post_completed, post_exit_code, created, queued, started, ended, last_modified, job, node, error, environment, cpus_scheduled, mem_scheduled, disk_in_scheduled, disk_out_scheduled, disk_total_scheduled, results, current_stdout_url, current_stderr_url, results_manifest) {
            this.id = id;
            this.status = status;
            this.command_arguments = command_arguments;
            this.timeout = timeout;
            this.pre_started = pre_started;
            this.pre_completed = pre_completed;
            this.pre_exit_code = pre_exit_code;
            this.job_started = job_started;
            this.job_completed = job_completed;
            this.job_exit_code = job_exit_code;
            this.post_started = post_started;
            this.post_completed = post_completed;
            this.post_exit_code = post_exit_code;
            this.created = created;
            this.created_formatted = created ? moment.utc(created).toISOString() : created;
            this.queued = queued;
            this.queued_formatted = queued ? moment.utc(queued).toISOString() : queued;
            this.started = started;
            this.started_formatted = started ? moment.utc(started).toISOString() : started;
            this.ended = ended;
            this.ended_formatted = ended ? moment.utc(ended).toISOString() : ended;
            this.last_modified = last_modified;
            this.last_modified_formatted = last_modified ? moment.utc(last_modified).toISOString() : last_modified;
            this.job = Job.transformer(job);
            this.node = Node.transformer(node);
            this.error = error;
            this.environment = environment;
            this.cpus_scheduled = cpus_scheduled;
            this.mem_scheduled = mem_scheduled;
            this.disk_in_scheduled = disk_in_scheduled;
            this.disk_out_scheduled = disk_out_scheduled;
            this.disk_total_scheduled = disk_total_scheduled;
            this.results = results;
            this.current_stdout_url = current_stdout_url;
            this.current_stderr_url = current_stderr_url;
            this.results_manifest = results_manifest;
        };

        // public methods
        JobExecution.prototype = {
            getDuration: function () {
                return moment.utc(this.job_completed).diff(moment.utc(this.job_started));
            },
            getIcon: function () {
                return this.job.jobType.iconCode ? '<i class="fa">&#x' + this.job.jobType.iconCode + '</i>' : '<i class="fa">&#x' + scaleConfig.defaultIconCode + '</i>';
            }
        };

        // static methods, assigned to class
        JobExecution.build = function (data) {
            if (data) {
                return new JobExecution(
                    data.id,
                    data.status,
                    data.command_arguments,
                    data.timeout,
                    data.pre_started,
                    data.pre_completed,
                    data.pre_exit_code,
                    data.job_started,
                    data.job_completed,
                    data.job_exit_code,
                    data.post_started,
                    data.post_completed,
                    data.post_exit_code,
                    data.created,
                    data.queued,
                    data.started,
                    data.ended,
                    data.last_modified,
                    data.job,
                    data.node,
                    data.error,
                    data.environment,
                    data.cpus_scheduled,
                    data.mem_scheduled,
                    data.disk_in_scheduled,
                    data.disk_out_scheduled,
                    data.disk_total_scheduled,
                    data.results,
                    data.current_stdout_url,
                    data.current_stderr_url,
                    data.results_manifest
                );
            }
            return new JobExecution();
        };

        JobExecution.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(JobExecution.build)
                    .filter(Boolean);
            }
            return JobExecution.build(data);
        };

        return JobExecution;
    });
})();
