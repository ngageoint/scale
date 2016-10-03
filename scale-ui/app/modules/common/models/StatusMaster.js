(function () {
    'use strict';
    
    angular.module('scaleApp').factory('StatusMaster', function () {
        var StatusMaster = function (is_online, hostname, port) {
            this.is_online = is_online;
            this.hostname = hostname;
            this.port = port;
        };

        // public methods
        StatusMaster.prototype = {

        };

        // static methods, assigned to class
        StatusMaster.build = function (data) {
            if (data) {
                return new StatusMaster(
                    data.is_online,
                    data.hostname,
                    data.port
                );
            }
            return new StatusMaster();
        };

        StatusMaster.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(StatusMaster.build)
                    .filter(Boolean);
            }
            return StatusMaster.build(data);
        };

        return StatusMaster;
    });
})();