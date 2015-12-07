(function () {
    'use strict';

    angular.module('scaleApp').factory('StatusScheduler', function () {
        var StatusScheduler = function (is_online, is_paused, hostname) {
            this.is_online = is_online;
            this.is_paused = is_paused;
            this.hostname = hostname;
        };

        // public methods
        StatusScheduler.prototype = {

        };

        // static methods, assigned to class
        StatusScheduler.build = function (data) {
            if (data) {
                return new StatusScheduler(
                    data.is_online,
                    data.is_paused,
                    data.hostname
                );
            }
            return new StatusScheduler();
        };

        StatusScheduler.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(StatusScheduler.build)
                    .filter(Boolean);
            }
            return StatusScheduler.build(data);
        };

        return StatusScheduler;
    });
})();