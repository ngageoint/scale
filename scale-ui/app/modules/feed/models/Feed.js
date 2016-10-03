(function () {
    'use strict';

    angular.module('scaleApp').factory('Feed', function (scaleConfig) {
        var Feed = function (value, status) {
            this.value = value;
            this.status = status;
        };

        // public methods
        Feed.prototype = {
            toString: function () {
                return 'Feed';
            },
            getCellText: function () {
                return this.value;
            },
            getCellTitle: function () {
                return '';
            }
        };

        // static methods, assigned to class
        Feed.build = function (data) {
            if (data) {
                return new Feed(
                    data.value,
                    data.status
                );
            }
            return new Feed();
        };

        Feed.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(Feed.build)
                    .filter(Boolean);
            }
            return Feed.build(data);
        };

        return Feed;
    });
})();
