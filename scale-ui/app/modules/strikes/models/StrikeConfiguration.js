(function () {
    'use strict';

    angular.module('scaleApp').factory('StrikeConfiguration', function (StrikeIngestFile) {
        var StrikeConfiguration = function (version, workspace, monitor, files_to_ingest) {
            this.version = version;
            this.workspace = workspace;
            this.monitor = monitor;
            this.files_to_ingest = files_to_ingest ? StrikeIngestFile.transformer(files_to_ingest) : [];
        };

        StrikeConfiguration.prototype = {

        };

        // static methods, assigned to class
        StrikeConfiguration.build = function (data) {
            if (data) {
                return new StrikeConfiguration(
                    data.version,
                    data.workspace,
                    data.monitor,
                    data.files_to_ingest
                );
            }
            return new StrikeConfiguration();
        };

        StrikeConfiguration.transformer = function (data) {
            if (angular.isArray(data)) {
                return data.map(StrikeConfiguration.build);
            }
            return StrikeConfiguration.build(data);
        };

        return StrikeConfiguration;
    });
})();
