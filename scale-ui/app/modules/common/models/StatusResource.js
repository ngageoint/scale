(function () {
    'use strict';

    angular.module('scaleApp').factory('StatusResource', function () {
        var StatusResource = function (cpus, mem, disk) {
            this.cpus = cpus;
            this.mem = mem;
            this.disk = disk;
        };

        // public methods
        StatusResource.prototype = {

        };

        // static methods, assigned to class
        StatusResource.build = function (data) {
            if (data) {
                return new StatusResource(
                    data.cpus,
                    data.mem,
                    data.disk
                );
            }
            return new StatusResource();
        };

        StatusResource.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(StatusResource.build)
                    .filter(Boolean);
            }
            return StatusResource.build(data);
        };

        return StatusResource;
    });
})();