(function () {
    'use strict';

    angular.module('scaleApp').factory('JobDetailEvent', function (JobDetailEventRule) {
        var JobDetailEvent = function (id, type, rule, occurred) {
            this.id = id;
            this.type = type;
            this.rule = JobDetailEventRule.transformer(rule);
            this.occurred = occurred;
        };

        // public methods
        JobDetailEvent.prototype = {

        };

        // static methods, assigned to class
        JobDetailEvent.build = function (data) {
            if (data) {
                return new JobDetailEvent(
                    data.id,
                    data.type,
                    data.rule,
                    data.occurred
                );
            }
            return new JobDetailEvent();
        };

        JobDetailEvent.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(JobDetailEvent.build)
                    .filter(Boolean);
            }
            return JobDetailEvent.build(data);
        };

        return JobDetailEvent;
    });
})();
