(function () {
    'use strict';

    angular.module('scaleApp').factory('JobTypeDetails', function (scaleConfig, JobTypeInterface, JobTypeErrorMapping, JobTypeError, scaleService) {
        var JobTypeDetails = function (id, name, version, title, description, category, author_name, author_url, is_system, is_long_running, is_active, is_operational, is_paused, icon_code, uses_docker, docker_privileged, docker_image, revision_num, priority, timeout, max_scheduled, max_tries, cpus_required, mem_required, disk_out_const_required, disk_out_mult_required, created, archived, paused, last_modified, job_type_interface, error_mapping, trigger_rule, errors, job_counts_6h, job_counts_12h, job_counts_24h) {
            this.id = id;
            this.name = name;
            this.version = version;
            this.title = title;
            this.description = description;
            this.category = category;
            this.author_name = author_name;
            this.author_url = author_url;
            this.is_system = is_system;
            this.is_long_running = is_long_running;
            this.is_active = is_active;
            this.is_operational = is_operational;
            this.is_paused = is_paused;
            this.icon_code = icon_code;
            this.uses_docker = uses_docker;
            this.docker_privileged = docker_privileged;
            this.docker_image = docker_image;
            this.revision_num = revision_num;
            this.priority = priority;
            this.timeout = timeout;
            this.max_scheduled = max_scheduled;
            this.max_tries = max_tries;
            this.cpus_required = cpus_required;
            this.mem_required = mem_required;
            this.mem_required_formatted = scaleService.calculateFileSizeFromMib(mem_required);
            this.disk_out_const_required = disk_out_const_required;
            this.disk_out_const_required_formatted = scaleService.calculateFileSizeFromMib(disk_out_const_required);
            this.disk_out_mult_required = disk_out_mult_required;
            this.created = created;
            this.archived = archived;
            this.paused = paused;
            this.last_modified = last_modified;
            this.job_type_interface = job_type_interface;
            this.error_mapping = JobTypeErrorMapping.transformer(error_mapping);
            this.trigger_rule = trigger_rule;
            this.errors = JobTypeError.transformer(errors);
            this.job_counts_6h = job_counts_6h;
            this.job_counts_12h = job_counts_12h;
            this.job_counts_24h = job_counts_24h;
        };

        // public methods
        JobTypeDetails.prototype = {
            getIcon: function () {
                return this.icon_code ? '<i class="fa">&#x' + this.icon_code + '</i>' : '<i class="fa">&#x' + scaleConfig.defaultIconCode + '</i>';
            },
            getPerformance: function () {
                var failed6Arr = _.where(this.job_counts_6h, { 'status': 'FAILED' }),
                    failed12Arr = _.where(this.job_counts_12h, { 'status': 'FAILED' }),
                    failed24Arr = _.where(this.job_counts_24h, { 'status': 'FAILED' });

                var completed6 = _.find(this.job_counts_6h, 'status', 'COMPLETED') || { count: 0 },
                    failed6 = _.sum(failed6Arr, 'count'),
                    total6 = failed6Arr.length > 0 ? failed6 + completed6.count : completed6.count,
                    successRate6 = total6 === 0 ? 0 : 100 - ((failed6 / total6) * 100).toFixed(2),
                    completed12 = _.find(this.job_counts_12h, 'status', 'COMPLETED') || { count: 0 },
                    failed12 = _.sum(failed12Arr, 'count'),
                    total12 = failed12Arr.length > 0 ? failed12 + completed12.count : completed12.count,
                    successRate12 = total12 === 0 ? 0 : 100 - ((failed12 / total12) * 100).toFixed(2),
                    completed24 = _.find(this.job_counts_24h, 'status', 'COMPLETED') || { count: 0 },
                    failed24 = _.sum(failed24Arr, 'count'),
                    total24 = failed24Arr.length > 0 ? failed24 + completed24.count : completed24.count,
                    successRate24 = total24 === 0 ? 0 : 100 - ((failed24 / total24) * 100).toFixed(2);

                return {
                    hour6: {
                        rate: successRate6,
                        failed: failed6,
                        completed: completed6.count,
                        total: total6
                    },
                    hour12: {
                        rate: successRate12,
                        failed: failed12,
                        completed: completed12.count,
                        total: total12
                    },
                    hour24: {
                        rate: successRate24,
                        failed: failed24,
                        completed: completed24.count,
                        total: total24
                    }
                };
            },
            getFailures: function () {
                var failed6 = _.where(this.job_counts_6h, { 'status': 'FAILED' }),
                    failed6Values = _.values(_.groupBy(failed6, 'category')),
                    failed12 = _.where(this.job_counts_12h, { 'status': 'FAILED' }),
                    failed12Values = _.values(_.groupBy(failed12, 'category')),
                    failed24 = _.where(this.job_counts_24h, { 'status': 'FAILED' }),
                    failed24Values = _.values(_.groupBy(failed24, 'category'));

                var getFailureCounts = function (categories) {
                    var returnArr = [];
                    _.forEach(categories, function (category) {
                        _.forEach(category, function (val) {
                            returnArr.push({ status: val.category, count: val.count });
                        });
                    });
                    return returnArr;
                };

                return {
                    hour6: getFailureCounts(failed6Values),
                    hour12: getFailureCounts(failed12Values),
                    hour24: getFailureCounts(failed24Values)
                };
            }
        };

        // static methods, assigned to class
        JobTypeDetails.build = function (data) {
            if (data) {
                // TODO: change property returned by API from "interface" to "job_type_interface" because "interface" is a reserved word in JS
                var jobTypeInterface = data.interface ? data.interface : data.job_type_interface;
                return new JobTypeDetails(
                    data.id,
                    data.name,
                    data.version,
                    data.title,
                    data.description,
                    data.category,
                    data.author_name,
                    data.author_url,
                    data.is_system,
                    data.is_long_running,
                    data.is_active,
                    data.is_operational,
                    data.is_paused,
                    data.icon_code,
                    data.uses_docker,
                    data.docker_privileged,
                    data.docker_image,
                    data.revision_num,
                    data.priority,
                    data.timeout,
                    data.max_scheduled,
                    data.max_tries,
                    data.cpus_required,
                    data.mem_required,
                    data.disk_out_const_required,
                    data.disk_out_mult_required,
                    data.created,
                    data.archived,
                    data.paused,
                    data.last_modified,
                    jobTypeInterface,
                    data.error_mapping,
                    data.trigger_rule,
                    data.errors,
                    data.job_counts_6h,
                    data.job_counts_12h,
                    data.job_counts_24h
                );
            }
            return new JobTypeDetails();
        };

        JobTypeDetails.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(JobTypeDetails.build);
            }
            return JobTypeDetails.build(data);
        };

        return JobTypeDetails;
    });
})();