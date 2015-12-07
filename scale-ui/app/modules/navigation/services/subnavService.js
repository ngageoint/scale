(function () {
    'use strict';

    angular.module('scaleApp').service('subnavService', function ($http, scaleConfig) {
        var currentPath = '';

        this.setCurrentPath = function (path) {
            currentPath = path;
        };

        this.getCurrentPath = function () {
            return currentPath;
        };
    });
})();