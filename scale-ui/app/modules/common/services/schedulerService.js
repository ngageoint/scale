(function () {
    'use strict';

    angular.module('scaleApp').service('schedulerService', function ($http, $q, scaleConfig) {
        var getUpdateSchedulerData = function (is_paused) {
            return {
                is_paused: is_paused
            };
        };

        return {
            updateScheduler: function (data) {
                data = data || getUpdateSchedulerData();
                var d = $q.defer();

                $http({
                    url: scaleConfig.urls.apiPrefix + 'scheduler/',
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
