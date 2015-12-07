(function () {
    'use strict';

    angular.module('scaleApp').factory('JobTypeOutputData', function () {
        var JobTypeOutputData = function (name, type, required, media_type) {
            this.name = name;
            this.type = type;
            this.required = required;
            this.media_type = media_type;
        };

        // public methods
        JobTypeOutputData.prototype = {

        };

        // static methods, assigned to class
        JobTypeOutputData.build = function (data) {
            if (data) {
                return new JobTypeOutputData(
                    data.name,
                    data.type,
                    data.required,
                    data.media_type
                );
            }
            return new JobTypeOutputData();
        };

        JobTypeOutputData.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(JobTypeOutputData.build)
                    .filter(Boolean);
            }
            return JobTypeOutputData.build(data);
        };

        return JobTypeOutputData;
    });
})();