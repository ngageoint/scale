(function () {
    'use strict';

    angular.module('scaleApp').factory('JobType', function (scaleConfig, JobTypeInterface) {
        var JobType = function (id, name, title, version, description, is_system, is_long_running, is_active, is_operational, is_paused, uses_docker, docker_privileged, docker_image, priority, timeout, max_tries, cpus_required, mem_required, disk_out_const_required, disk_out_mult_required, icon_code, created, archived, paused, last_modified, job_type_interface) {
            this.id = id;
            this.name = name;
            this.title = title;
            this.version = version;
            this.description = description;
            this.is_system = is_system;
            this.is_long_running = is_long_running;
            this.is_active = is_active;
            this.is_operational = is_operational;
            this.is_paused = is_paused;
            this.uses_docker = uses_docker;
            this.docker_privileged = docker_privileged;
            this.docker_image = docker_image;
            this.priority = priority;
            this.timeout = timeout;
            this.max_tries = max_tries;
            this.cpus_required = cpus_required;
            this.mem_required = mem_required;
            this.disk_out_const_required = disk_out_const_required;
            this.disk_out_mult_required = disk_out_mult_required;
            this.icon_code = icon_code;
            this.created = created;
            this.archived = archived;
            this.paused = paused;
            this.last_modified = last_modified;
            this.job_type_interface = JobTypeInterface.transformer(job_type_interface);
        };

        // public methods
        JobType.prototype = {
            toString: function () {
                return 'JobType';
            },
            getIcon: function () {
                return this.icon_code ? '<i class="fa fa-fw">&#x' + this.icon_code + '</i>' : '<i class="fa fa-fw">&#x' + scaleConfig.defaultIconCode + '</i>';
            },
            getCellText: function () {
                return this.icon_code ? '&#x' + this.icon_code + ';' : '&#x' + scaleConfig.defaultIconCode + ';';
            },
            getCellTitle: function () {
                return this.title;
            }
        };

        // static methods, assigned to class
        JobType.build = function (data) {
            if (data) {
                return new JobType(
                    data.id,
                    data.name,
                    data.title,
                    data.version,
                    data.description,
                    data.is_system,
                    data.is_long_running,
                    data.is_active,
                    data.is_operational,
                    data.is_paused,
                    data.uses_docker,
                    data.docker_privileged,
                    data.docker_image,
                    data.priority,
                    data.timeout,
                    data.max_tries,
                    data.cpus_required,
                    data.mem_required,
                    data.disk_out_const_required,
                    data.disk_out_mult_required,
                    data.icon_code,
                    data.created,
                    data.archived,
                    data.paused,
                    data.last_modified,
                    data.interface
                );
            }
            return new JobType();
        };

        JobType.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(JobType.build)
                    .filter(Boolean);
            }
            return JobType.build(data);
        };

        return JobType;
    });
})();