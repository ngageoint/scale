(function () {
    'use strict';

    angular.module('scaleApp').factory('JobDetailInputData', function () {
        var JobDetailInputData = function (name, value, file_id, file_ids, files) {
            this.name = name;
            this.value = value;
            this.file_id = file_id;
            this.file_ids = file_ids;
            this.files = files;
        };

        // public methods
        JobDetailInputData.prototype = {
            getValue: function () {
                if (this.value)
                    return this.value;
                if (this.file_id)
                    return this.file_id;
                if (this.file_ids)
                    return this.file_ids;
            }
        };

        // static methods, assigned to class
        JobDetailInputData.build = function (data) {
            if (data) {
                return new JobDetailInputData(
                    data.name,
                    data.value,
                    data.file_id,
                    data.file_ids,
                    data.files
                );
            }
            return new JobDetailInputData();
        };

        JobDetailInputData.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(JobDetailInputData.build)
                    .filter(Boolean);
            }
            return JobDetailInputData.build(data);
        };

        return JobDetailInputData;
    });
})();
