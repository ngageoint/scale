(function () {
    'use strict';

    angular.module('scaleApp').factory('Ingest', function (scaleConfig, scaleService) {
        var Ingest = function (id, file_name, strike, status, bytes_transferred, transfer_started, transfer_ended, media_type, file_size, data_type, ingest_started, ingest_ended, source_file, created, last_modified) {
            this.id = id;
            this.file_name = file_name;
            this.strike = strike;
            this.status = status;
            this.bytes_transferred = bytes_transferred;
            this.transfer_started = transfer_started;
            this.transfer_started_formatted = moment.utc(transfer_started).format(scaleConfig.dateFormats.day_second_utc_nolabel);
            this.transfer_ended = transfer_ended;
            this.transfer_ended_formatted = moment.utc(transfer_ended).format(scaleConfig.dateFormats.day_second_utc_nolabel);
            this.media_type = media_type;
            this.file_size = file_size;
            this.file_size_formatted = scaleService.calculateFileSizeFromBytes(file_size);
            this.data_type = data_type;
            this.ingest_started = ingest_started;
            this.ingest_started_formatted = moment.utc(ingest_started).format(scaleConfig.dateFormats.day_second_utc_nolabel);
            this.ingest_ended = ingest_ended;
            this.ingest_ended_formatted = moment.utc(ingest_ended).format(scaleConfig.dateFormats.day_second_utc_nolabel);
            this.source_file = source_file;
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
                    data.strike,
                    data.status,
                    data.bytes_transferred,
                    data.transfer_started,
                    data.transfer_ended,
                    data.media_type,
                    data.file_size,
                    data.data_type,
                    data.ingest_started,
                    data.ingest_ended,
                    data.source_file,
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
