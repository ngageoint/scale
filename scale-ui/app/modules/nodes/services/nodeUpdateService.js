(function () {
    'use strict';

    angular.module('scaleApp').service('nodeUpdateService', function ($http, $q, scaleConfig, Node) {
        var getNodeUpdateData = function (pause_reason, is_paused, is_active) {
            return {
                pause_reason: pause_reason,
                is_paused: is_paused,
                is_active: is_active
            };
        };

        return {
            updateNode: function (id, data) {
                data = data || getNodeUpdateData();
                var d = $q.defer();

                $http({
                    url: scaleConfig.getUrlPrefix('nodes') + 'nodes/' + id + '/',
                    method: 'PATCH',
                    data: data
                }).success(function (result) {
                    d.resolve(Node.transformer(result));
                }).error(function (error) {
                    d.reject(error);
                });

                return d.promise;
            }
        };
    })
})();
