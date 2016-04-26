(function () {
    'use strict';

    angular.module('scaleApp').service('stateService', function () {
        var version = '';

        return {
            getVersion: function () {
                return version;
            },
            setVersion: function (v) {
                version = v;
            }
        };
    });
})();
