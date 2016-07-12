(function () {
    'use strict';

    angular.module('scaleApp').factory('Strike', function (scaleConfig, Job, StrikeConfiguration) {
        var Strike = function (id, name, title, description, job, created, last_modified, configuration) {
            this.id = id;
            this.name = name;
            this.title = title;
            this.description = description;
            this.job = Job.transformer(job);
            this.created = created;
            this.last_modified = last_modified;
            this.configuration = StrikeConfiguration.transformer(configuration);
        };

        Strike.prototype = {
            clean: function () {
                return {
                    name: this.name,
                    title: this.title,
                    description: this.description,
                    configuration: this.configuration
                };
            }
        };

        // static methods, assigned to class
        Strike.build = function (data) {
            if (data) {
                return new Strike(
                    data.id,
                    data.name,
                    data.title,
                    data.description,
                    data.job,
                    data.created,
                    data.last_modified,
                    data.configuration
                );
            }
            return new Strike();
        };

        Strike.transformer = function (data) {
            if (angular.isArray(data)) {
                return data.map(Strike.build);
            }
            return Strike.build(data);
        };

        return Strike;
    });
})();
