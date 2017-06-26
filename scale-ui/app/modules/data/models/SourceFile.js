(function () {
    'use strict';

    angular.module('scaleApp').factory('SourceFile', function (scaleConfig, scaleService) {
        var SourceFile = function (id, workspace, file_name, media_type, file_size, data_type, is_deleted, uuid, url, created, deleted, data_started, data_ended, geometry, center_point, meta_data, countries, last_modified, is_parsed, parsed) {
            this.id = id;
            this.workspace = workspace;
            this.file_name = file_name;
            this.media_type = media_type;
            this.file_size = file_size;
            this.file_size_formatted = file_size ? scaleService.calculateFileSizeFromBytes(file_size) : null;
            this.data_type = data_type;
            this.is_deleted = is_deleted;
            this.uuid = uuid;
            this.url = url;
            this.created = created;
            this.created_formatted = created ? moment.utc(created).format(scaleConfig.dateFormats.day_second_utc_nolabel) : null;
            this.deleted = deleted;
            this.deleted_formatted = deleted ? moment.utc(deleted).format(scaleConfig.dateFormats.day_second_utc_nolabel) : null;
            this.data_started = data_started;
            this.data_started_formatted = data_started ? moment.utc(data_started).format(scaleConfig.dateFormats.day_second_utc_nolabel) : null;
            this.data_ended = data_ended;
            this.data_ended_formatted = data_ended ? moment.utc(data_ended).format(scaleConfig.dateFormats.day_second_utc_nolabel) : null;
            this.geometry = geometry;
            this.center_point = center_point;
            this.meta_data = meta_data;
            this.countries = countries;
            this.last_modified = last_modified;
            this.last_modified_formatted = last_modified ? moment.utc(last_modified).format(scaleConfig.dateFormats.day_second_utc_nolabel) : null;
            this.is_parsed = is_parsed;
            this.parsed = parsed;
            this.parsed_formatted = parsed ? moment.utc(parsed).format(scaleConfig.dateFormats.day_second_utc_nolabel) : null;
        };

        // public methods
        SourceFile.prototype = {

        };

        // static methods, assigned to class
        SourceFile.build = function (data) {
            if (data) {
                return new SourceFile(
                    data.id,
                    data.workspace,
                    data.file_name,
                    data.media_type,
                    data.file_size,
                    data.data_type,
                    data.is_deleted,
                    data.uuid,
                    data.url,
                    data.created,
                    data.deleted,
                    data.data_started,
                    data.data_ended,
                    data.geometry,
                    data.center_point,
                    data.meta_data,
                    data.countries,
                    data.last_modified,
                    data.is_parsed,
                    data.parsed
                );
            }
            return new SourceFile();
        };

        SourceFile.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(SourceFile.build);
            }
            return SourceFile.build(data);
        };

        return SourceFile;
    });
})();
