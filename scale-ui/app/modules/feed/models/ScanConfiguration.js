(function () {
    'use strict';

    angular.module('scaleApp').factory('ScanConfiguration', function (scaleConfig, ScanIngestFile) {
        var ScanConfiguration = function (version, workspace, scanner, files_to_ingest) {
            this.version = scaleConfig.scanConfigurationVersion;
            this.workspace = workspace;
            this.scanner = scanner ? scanner : {
                type: '',
                transfer_suffix: ''
            };
            this.files_to_ingest = files_to_ingest ? ScanIngestFile.transformer(files_to_ingest) : [];
        };

        ScanConfiguration.prototype = {

        };

        // static methods, assigned to class
        ScanConfiguration.build = function (data) {
            if (data) {
                var returnObj = new ScanConfiguration(
                    data.version,
                    data.workspace,
                    data.scanner,
                    data.files_to_ingest
                );
                // remove empty/null/undefined values from returnObj
                return _.pick(returnObj, _.identity);
            }
            return new ScanConfiguration();
        };

        ScanConfiguration.transformer = function (data) {
            if (angular.isArray(data)) {
                return data.map(ScanConfiguration.build);
            }
            return ScanConfiguration.build(data);
        };

        return ScanConfiguration;
    });
})();
