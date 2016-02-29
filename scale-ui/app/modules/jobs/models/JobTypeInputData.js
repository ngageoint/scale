(function () {
    'use strict';

    angular.module('scaleApp').factory('JobTypeInputData', function (scaleConfig) {
        var JobTypeInputData = function (media_types, required, type, name) {
            this.media_types = media_types;
            this.required = required;
            this.type = type;
            this.name = name;
        };

        // public methods
        JobTypeInputData.prototype = {

        };

        // static methods, assigned to class
        JobTypeInputData.build = function (data) {
            if (data) {
                return new JobTypeInputData(
                    data.media_types,
                    data.required,
                    data.type,
                    data.name
                );
            }
            return new JobTypeInputData();
        };

        JobTypeInputData.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(JobTypeInputData.build);
            }
            return JobTypeInputData.build(data);
        };

        return JobTypeInputData;
    });
})();