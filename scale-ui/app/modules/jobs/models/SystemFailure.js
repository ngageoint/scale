(function () {
    'use strict';

    angular.module('scaleApp').factory('SystemFailure', function (scaleConfig, scaleService) {
        var SystemFailure = function (count, job_type_name, job_type_version, error_name, first_error, last_error) {
            this.count = count;
            this.job_type_name = job_type_name;
            this.job_type_version = job_type_version;
            this.error_name = error_name;
            this.first_error = first_error;
            this.last_error = last_error;
        };

        // public methods
        SystemFailure.prototype = {
            getDuration: function () {
                return scaleService.calculateDuration(this.first_error, this.last_error);
            },
            getIcon: function () {
                var configJobType = _.find(scaleConfig.jobTypes, 'title', this.job_type_name);
                if (configJobType) {
                    return configJobType.icon;
                }
                return scaleConfig.defaultIcon;
            }
        };

        // static methods, assigned to class
        SystemFailure.build = function (data) {
            if (data) {
                return new SystemFailure(
                    data.count,
                    data.job_type_name,
                    data.job_type_version,
                    data.error_name,
                    data.first_error,
                    data.last_error
                );
            }
            return new SystemFailure();
        };

        SystemFailure.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(SystemFailure.build)
                    .filter(Boolean);
            }
            return SystemFailure.build(data);
        };

        return SystemFailure;
    });
})();
