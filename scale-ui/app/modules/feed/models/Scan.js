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
            clean: function () {
                var returnObj = {
                    name: this.name,
                    title: this.title,
                    description: this.description,
                    configuration: this.configuration
                };
                if (returnObj.configuration && returnObj.configuration.scanner.type === 's3') {
                    delete returnObj.configuration.scanner.transfer_suffix;
                }
                if (returnObj.configuration.files_to_ingest) {
                    _.forEach(returnObj.configuration.files_to_ingest, function (f) {
                        delete f.$$hashKey;
                    });
                }
                // remove empty/null/undefined values from returnObj
                return _.pick(returnObj, _.identity);
            }
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
