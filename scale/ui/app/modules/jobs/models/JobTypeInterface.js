(function () {
    'use strict';

    angular.module('scaleApp').factory('JobTypeInterface', function (scaleConfig, JobTypeInputData, JobTypeOutputData) {
        var JobTypeInterface = function (version, command, command_arguments, input_data, output_data) {
            this.version = version;
            this.command = command;
            this.command_arguments = command_arguments;
            this.input_data = JobTypeInputData.transformer(input_data);
            this.output_data = JobTypeOutputData.transformer(output_data);
        };

        // public methods
        JobTypeInterface.prototype = {
            getIcon: function () {
                return this.iconCode ? '<i class="fa">&#x' + this.iconCode + '</i>' : '<i class="fa">&#x' + scaleConfig.defaultIconCode + '</i>';
            }
        };

        // static methods, assigned to class
        JobTypeInterface.build = function (data) {
            if (data) {
                return new JobTypeInterface(
                    data.version,
                    data.command,
                    data.command_arguments,
                    data.input_data,
                    data.output_data
                );
            }
            return new JobTypeInterface();
        };

        JobTypeInterface.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(JobTypeInterface.build)
                    .filter(Boolean);
            }
            return JobTypeInterface.build(data);
        };

        return JobTypeInterface;
    });
})();
