(function () {
    'use strict';

    angular.module('scaleApp').service('schedulerService', function ($http, $q, scaleConfig) {
        var getUpdateSchedulerData = function (is_paused, resource_level) {
            return {
                is_paused: is_paused || false,
                resource_level: resource_level || 'GOOD'
            };
        };

        return {
            getScheduler: function () {
                var d = $q.defer();

                $http({
                    url: scaleConfig.getUrlPrefix('scheduler') + 'scheduler/',
                    method: 'GET'
                }).success(function (result) {
                    d.resolve(result);
                }).error(function (error) {
                    d.reject(error);
                });

                return d.promise;
            },
            updateScheduler: function (data) {
                data = data || getUpdateSchedulerData();
                var d = $q.defer();

                $http({
                    url: scaleConfig.getUrlPrefix('scheduler') + 'scheduler/',
                    method: 'PATCH',
                    data: data
                }).success(function (result) {
                    d.resolve(result);
                }).error(function (error) {
                    d.reject(error);
                });

                return d.promise;
            }
        }
    });
})();
