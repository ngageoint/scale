(function () {
    'use strict';

    angular.module('scaleApp').factory('JobExecutionLog', function (scaleConfig, Job, Node) {
        var JobExecutionLog = function (id, status, command_arguments, timeout, exit_code, created, queued, scheduled, pre_started, pre_completed, job_started, job_completed, post_started, post_completed, ended, last_modified, job, node, error, is_finished, stdout, stderr) {
            this.id = id;
            this.status = status;
            this.command_arguments = command_arguments;
            this.timeout = timeout;
            this.exit_code = exit_code;
            this.created = created;
            this.queued = queued;
            this.scheduled = scheduled;
            this.pre_started = pre_started;
            this.pre_completed = pre_completed;
            this.job_started = job_started;
            this.job_completed = job_completed;
            this.post_started = post_started;
            this.post_completed = post_completed;
            this.ended = ended;
            this.last_modified = last_modified;
            this.job = Job.transformer(job);
            this.node = Node.transformer(node);
            this.error = error;
            this.is_finished = is_finished;
            this.stdout = stdout;
            this.stdoutHtml = stdout ? stdout.replace(new RegExp('\r?\n','g'), '<br />') : '';
            this.stderr = stderr;
        };

        // public methods
        JobExecutionLog.prototype = {
            toHtml: function(instr){
                return instr
            }

        };

        // static methods, assigned to class
        JobExecutionLog.build = function (data) {
            if (data) {
                return new JobExecutionLog(
                    data.id,
                    data.status,
                    data.command_arguments,
                    data.timeout,
                    data.exit_code,
                    data.created,
                    data.queued,
                    data.scheduled,
                    data.pre_started,
                    data.pre_completed,
                    data.job_started,
                    data.job_completed,
                    data.post_started,
                    data.post_completed,
                    data.ended,
                    data.last_modified,
                    data.job,
                    data.node,
                    data.error,
                    data.is_finished,
                    data.stdout,
                    data.stderr
                );
            }
            return new JobExecutionLog();
        };

        JobExecutionLog.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(JobExecutionLog.build)
                    .filter(Boolean);
            }
            return JobExecutionLog.build(data);
        };

        return JobExecutionLog;
    });
})();
