(function () {
    'use strict';

    angular.module('scaleApp').factory('FeedStatus', function (scaleConfig) {
        var FeedStatus = function (status) {
            this.status = status;
        };

        // public methods
        FeedStatus.prototype = {
            toString: function () {
                return 'FeedStatus';
            },
            getCellFill: function () {
                return scaleConfig.colors.chart_green;
            },
            getCellActivity: function () {
                return '';
            },
            getCellActivityTotal: function () {
                return '';
            },
            getCellError: function () {
                return '';
            },
            getCellTotal: function () {
                return '';
            }
        };

        // static methods, assigned to class
        FeedStatus.build = function (data) {
            if (data) {
                return new FeedStatus(
                    data.status
                );
            }
            return new FeedStatus();
        };

        FeedStatus.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(FeedStatus.build)
                    .filter(Boolean);
            }
            return FeedStatus.build(data);
        };

        return FeedStatus;
    });
})();
