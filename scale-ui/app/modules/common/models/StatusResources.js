(function () {
    'use strict';

    angular.module('scaleApp').factory('StatusResources', function (StatusResource) {
        var StatusResources = function (total, scheduled, used) {
            this.total = StatusResource.transformer(total);
            this.scheduled = StatusResource.transformer(scheduled);
            this.used = StatusResource.transformer(used);
        };

        // public methods
        StatusResources.prototype = {

        };

        // static methods, assigned to class
        StatusResources.build = function (data) {
            if (data) {
                return new StatusResources(
                    data.total,
                    data.scheduled,
                    data.used
                );
            }
            return new StatusResources();
        };

        StatusResources.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(StatusResources.build)
                    .filter(Boolean);
            }
            return StatusResources.build(data);
        };

        return StatusResources;
    });
})();