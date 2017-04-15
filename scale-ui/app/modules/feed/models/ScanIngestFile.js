(function () {
    'use strict';

    angular.module('scaleApp').factory('ScanIngestFile', function () {
        var ScanIngestFile = function (filename_regex, data_types, new_workspace, new_file_path) {
            this.filename_regex = filename_regex;
            this.data_types = data_types || [];
            this.new_workspace = new_workspace || '';
            this.new_file_path = new_file_path || '';
        };

        ScanIngestFile.prototype = {

        };

        // static methods, assigned to class
        ScanIngestFile.build = function (data) {
            if (data) {
                var returnObj = new ScanIngestFile(
                    data.filename_regex,
                    data.data_types,
                    data.new_workspace,
                    data.new_file_path
                );
                if (data.data_types && data.data_types.length === 0) {
                    delete returnObj.data_types;
                }
                // remove empty/null/undefined values from returnObj
                return _.pick(returnObj, _.identity);
            }
            return new ScanIngestFile();
        };

        ScanIngestFile.transformer = function (data) {
            if (angular.isArray(data)) {
                return data.map(ScanIngestFile.build);
            }
            return ScanIngestFile.build(data);
        };

        return ScanIngestFile;
    });
})();
