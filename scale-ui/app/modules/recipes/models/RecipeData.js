(function () {
    'use strict';

    angular.module('scaleApp').factory('RecipeData', function () {
        var RecipeData = function (input_data, version, workspace_id) {
            this.input_data = input_data;
            this.version = version;
            this.workspace_id = workspace_id;
        };

        // static methods, assigned to class
        RecipeData.build = function (data) {
            if (data) {
                return new RecipeData(
                    data.input_data,
                    data.version,
                    data.workspace_id
                );
            }
            return new RecipeData();
        };

        RecipeData.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(RecipeData.build)
                    .filter(Boolean);
            }
            return RecipeData.build(data);
        };

        return RecipeData;
    });
})();