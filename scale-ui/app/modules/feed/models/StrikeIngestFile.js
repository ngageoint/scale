(function () {
    'use strict';

    angular.module('scaleApp').factory('StrikeIngestFile', function () {
        var StrikeIngestFile = function (filename_regex, data_types, new_workspace, new_file_path) {
            this.filename_regex = filename_regex;
            this.data_types = data_types || [];
            this.new_workspace = new_workspace || '';
            this.new_file_path = new_file_path || '';
        };

        StrikeIngestFile.prototype = {

        };

        // static methods, assigned to class
        StrikeIngestFile.build = function (data) {
            if (data) {
                var returnObj = new StrikeIngestFile(
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
            return new StrikeIngestFile();
        };

        StrikeIngestFile.transformer = function (data) {
            if (angular.isArray(data)) {
                return data.map(StrikeIngestFile.build);
            }
            return StrikeIngestFile.build(data);
        };

        return StrikeIngestFile;
    });
})();
