(function () {
    'use strict';

    angular.module('scaleApp').factory('Ingest', function (scaleConfig, scaleService, Job) {
        var Ingest = function (id, file_name, scan, strike, status, bytes_transferred, transfer_started, transfer_ended, media_type, file_size, data_type, file_path, workspace, new_file_path, new_workspace, job, ingest_started, ingest_ended, source_file, data_started, data_ended, created, last_modified) {
            this.id = id;
            this.file_name = file_name;
            this.scan = scan;
            this.strike = strike;
            this.status = status;
            this.bytes_transferred = bytes_transferred;
            this.bytes_transferred_formatted = scaleService.calculateFileSizeFromBytes(bytes_transferred);
            this.transfer_started = transfer_started;
            this.transfer_started_formatted = moment.utc(transfer_started).format(scaleConfig.dateFormats.day_second_utc_nolabel);
            this.transfer_ended = transfer_ended;
            this.transfer_ended_formatted = transfer_ended ? moment.utc(transfer_ended).format(scaleConfig.dateFormats.day_second_utc_nolabel) : '';
            this.media_type = media_type;
            this.file_size = file_size;
            this.file_size_formatted = scaleService.calculateFileSizeFromBytes(file_size);
            this.data_type = data_type;
            this.file_path = file_path;
            this.workspace = workspace;
            this.new_file_path = new_file_path;
            this.new_workspace = new_workspace;
            this.job = Job.transformer(job);
            this.ingest_started = ingest_started;
            this.ingest_started_formatted = ingest_started ? moment.utc(ingest_started).format(scaleConfig.dateFormats.day_second_utc_nolabel) : '';
            this.ingest_ended = ingest_ended;
            this.ingest_ended_formatted = ingest_ended ? moment.utc(ingest_ended).format(scaleConfig.dateFormats.day_second_utc_nolabel) : '';
            this.source_file = source_file;
            this.data_started = data_started;
            this.data_ended = data_ended;
            this.created = created;
            this.created_formatted = moment.utc(created).format(scaleConfig.dateFormats.day_second_utc_nolabel);
            this.last_modified = last_modified;
            this.last_modified_formatted = moment.utc(last_modified).format(scaleConfig.dateFormats.day_second_utc_nolabel);
        };

        // public methods
        Ingest.prototype = {

        };

        // static methods, assigned to class
        Ingest.build = function (data) {
            if (data) {
                return new Ingest(
                    data.id,
                    data.file_name,
                    data.scan,
                    data.strike,
                    data.status,
                    data.bytes_transferred,
                    data.transfer_started,
                    data.transfer_ended,
                    data.media_type,
                    data.file_size,
                    data.data_type,
                    data.file_path,
                    data.workspace,
                    data.new_file_path,
                    data.new_workspace,
                    data.job,
                    data.ingest_started,
                    data.ingest_ended,
                    data.source_file,
                    data.data_started,
                    data.data_ended,
                    data.created,
                    data.last_modified
                );
            }
            return new Ingest();
        };

        Ingest.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(Ingest.build);
            }
            return Ingest.build(data);
        };

        return Ingest;
    });
})();
