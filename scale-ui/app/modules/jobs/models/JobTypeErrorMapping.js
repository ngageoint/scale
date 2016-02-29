(function () {
    'use strict';
    
    angular.module('scaleApp').factory('JobTypeErrorMapping', function () {
        var JobTypeErrorMapping = function (version, exit_codes) {
            this.version = version;
            this.exit_codes = exit_codes;
        };

        // public methods
        JobTypeErrorMapping.prototype = {

        };

        // static methods, assigned to class
        JobTypeErrorMapping.build = function (data) {
            if (data) {
                return new JobTypeErrorMapping(
                    data.version,
                    data.exit_codes
                );
            }
            return new JobTypeErrorMapping();
        };

        JobTypeErrorMapping.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(JobTypeErrorMapping.build)
                    .filter(Boolean);
            }
            return JobTypeErrorMapping.build(data);
        };

        return JobTypeErrorMapping;
    })
})();