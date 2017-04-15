(function () {
    'use strict';

    angular.module('scaleApp').factory('Scan', function (scaleConfig, Job, ScanConfiguration) {
        var Scan = function (id, name, title, description, file_count, job, dry_run_job, created, last_modified, configuration) {
            this.id = id;
            this.name = name;
            this.title = title;
            this.description = description;
            this.file_count = file_count;
            this.job = Job.transformer(job);
            this.dry_run_job = Job.transformer(dry_run_job);
            this.created = created;
            this.created_formatted = moment.utc(created).format(scaleConfig.dateFormats.day_second_utc);
            this.last_modified = last_modified;
            this.last_modified_formatted = moment.utc(last_modified).format(scaleConfig.dateFormats.day_second_utc);
            this.configuration = ScanConfiguration.transformer(configuration);
        };

        Scan.prototype = {

        };

        // static methods, assigned to class
        Scan.build = function (data) {
            if (data) {
                return new Scan(
                    data.id,
                    data.name,
                    data.title,
                    data.description,
                    data.file_count,
                    data.job,
                    data.dry_run_job,
                    data.created,
                    data.last_modified,
                    data.configuration
                );
            }
            return new Scan();
        };

        Scan.transformer = function (data) {
            if (angular.isArray(data)) {
                return data.map(Scan.build);
            }
            return Scan.build(data);
        };

        return Scan;
    });
})();
