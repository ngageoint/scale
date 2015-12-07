(function () {
    'use strict';

    angular.module('scaleApp').factory('Status', function (StatusMaster, StatusScheduler, StatusResources) {
        var Status = function ($resolved, master, scheduler, queue_depth, resources) {
            this.$resolved = $resolved;
            this.master = StatusMaster.transformer(master);
            this.scheduler = StatusScheduler.transformer(scheduler);
            this.queue_depth = queue_depth;
            this.resources = StatusResources.transformer(resources);
        };

        // public methods
        Status.prototype = {
            getCpuUsage: function () {
                if (this.resources.scheduled.cpus && this.resources.total.cpus) {
                    if (this.resources.total.cpus > 0) {
                        return ((this.resources.scheduled.cpus / this.resources.total.cpus) * 100).toFixed(2);
                    }
                }
                return 0.00;
            },
            getMemUsage: function () {
                if (this.resources.scheduled.mem && this.resources.total.mem) {
                    if (this.resources.total.mem > 0) {
                        return ((this.resources.scheduled.mem / this.resources.total.mem) * 100).toFixed(2);
                    }
                }
                return 0.00;
            },
            getDiskUsage: function () {
                if (this.resources.scheduled.disk && this.resources.total.disk) {
                    if (this.resources.total.disk > 0) {
                        return ((this.resources.scheduled.disk / this.resources.total.disk) * 100).toFixed(2);
                    }
                }
                return 0.00;
            }
        };

        // static methods, assigned to class
        Status.build = function (data) {
            if (data) {
                return new Status(
                    data.$resolved,
                    data.master,
                    data.scheduler,
                    data.queue_depth,
                    data.resources
                );
            }
            return new Status();
        };

        Status.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(Status.build)
                    .filter(Boolean);
            }
            return Status.build(data);
        };

        return Status;
    });
})();