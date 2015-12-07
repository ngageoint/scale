(function () {
    'use strict';

    angular.module('scaleApp').factory('JobTypeError', function (moment, scaleConfig) {
        var JobTypeError = function (id, name, title, description, category, created, last_modified) {
            this.id = id;
            this.name = name;
            this.title = title;
            this.description = description;
            this.category = category;
            this.created = created;
            this.created_formatted = created ? moment.utc(created).toISOString() : created;
            this.last_modified = last_modified;
            this.last_modified_formatted = last_modified ? moment.utc(last_modified).toISOString() : last_modified;
        };

        // public methods
        JobTypeError.prototype = {

        };

        // static methods, assigned to class
        JobTypeError.build = function (data) {
            if (data) {
                return new JobTypeError(
                    data.id,
                    data.name,
                    data.title,
                    data.description,
                    data.category,
                    data.created,
                    data.last_modified
                );
            }
            return new JobTypeError();
        };

        JobTypeError.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(JobTypeError.build)
                    .filter(Boolean);
            }
            return JobTypeError.build(data);
        };

        return JobTypeError;
    })
})();
