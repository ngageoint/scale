(function () {
    'use strict';

    angular.module('scaleApp').factory('JobDetailOutputData', function () {
        var JobDetailOutputData = function (name, workspace_id, files) {
            this.name = name;
            this.workspace_id = workspace_id;
            this.files = files;
        };

        // public methods
        JobDetailOutputData.prototype = {

        };

        // static methods, assigned to class
        JobDetailOutputData.build = function (data) {
            if (data) {
                return new JobDetailOutputData(
                    data.name,
                    data.workspace_id,
                    data.files
                );
            }
            return new JobDetailOutputData();
        };

        JobDetailOutputData.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(JobDetailOutputData.build)
                    .filter(Boolean);
            }
            return JobDetailOutputData.build(data);
        };

        return JobDetailOutputData;
    });
})();
