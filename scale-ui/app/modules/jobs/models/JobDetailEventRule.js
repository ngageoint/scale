(function () {
    'use strict';

    angular.module('scaleApp').factory('JobDetailEventRule', function () {
        var JobDetailEventRule = function (id, type, is_active, created, archived, last_modified) {
            this.id = id;
            this.type = type;
            this.is_active = is_active;
            this.created = created;
            this.archived = archived;
            this.last_modified = last_modified;
        };

        // public methods
        JobDetailEventRule.prototype = {

        };

        // static methods, assigned to class
        JobDetailEventRule.build = function (data) {
            if (data) {
                return new JobDetailEventRule(
                    data.id,
                    data.type,
                    data.is_active,
                    data.created,
                    data.archived,
                    data.last_modified
                );
            }
            return new JobDetailEventRule();
        };

        JobDetailEventRule.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(JobDetailEventRule.build)
                    .filter(Boolean);
            }
            return JobDetailEventRule.build(data);
        };

        return JobDetailEventRule;
    });
})();
