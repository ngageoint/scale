(function () {
    'use strict';

    angular.module('scaleApp').factory('Status', function () {
        var Status = function ($resolved, timestamp, scheduler, system, num_offers, resources, job_types, nodes) {
            this.$resolved = $resolved;
            this.timestamp = timestamp;
            this.scheduler = scheduler;
            this.system = system;
            this.num_offers = num_offers;
            this.resources = resources;
            this.job_types = job_types;
            this.nodes = nodes;
        };

        // public methods
        Status.prototype = {
            getUsage: function (metric) {
                if (metric) {
                    var adjustedTotal = metric.total - metric.unavailable;
                    if (adjustedTotal > 0 && metric.running > 0) {
                        return +((metric.running / adjustedTotal) * 100).toFixed(2);
                    }
                    return 0.00;
                }
                return 0.00;
            }
        };

        // static methods, assigned to class
        Status.build = function (data) {
            if (data) {
                return new Status(
                    data.$resolved,
                    data.timestamp,
                    data.scheduler,
                    data.system,
                    data.num_offers,
                    data.resources,
                    data.job_types,
                    data.nodes
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
