(function () {
    'use strict';

    angular.module('scaleApp').service('strikeService', function ($http, $q, $resource, scaleConfig) {
        return {
            getStrikes: function () {
                var d = $q.defer();
                var url = scaleConfig.urls.apiPrefix + 'strikes/';

                $http({
                    url: url,
                    method: 'GET',
                    params: { order: '-title' }
                }).success(function (data) {
                    d.resolve(data.results);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getStrikeDetails: function (id) {
                var d = $q.defer();
                var url = scaleConfig.urls.apiPrefix + 'strikes/' + id + '/';

                $http({
                    url: url,
                    method: 'GET'
                }).success(function (data) {
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;

            },
            validateStrike: function (workspace) {
                var d = $q.defer();
                var cleanStrike = strike.clean();

                $http.post(scaleConfig.urls.apiPrefix + 'strikes/validation/', cleanStrike).success(function (result) {
                    d.resolve(result);
                }).error(function(error){
                    d.reject(error);
                });

                return d.promise;
            },
            saveStrike: function (strike) {
                var d = $q.defer();

                if (!strike.id) {
                    $http.post(scaleConfig.urls.apiPrefix + 'strikes/', strike.clean()).success(function (result) {
                        d.resolve(result);
                    }).error(function (error) {
                        d.reject(error);
                    });
                } else {
                    $http.patch(scaleConfig.urls.apiPrefix + 'strikes/' + strike.id + '/', strike.clean()).success(function (result) {
                        strike = result;
                        d.resolve(strike);
                    }).error(function (error) {
                        d.reject(error);
                    });
                }

                return d.promise;
            }
        };
    });
})();
