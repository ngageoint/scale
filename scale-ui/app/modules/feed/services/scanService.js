(function () {
    'use strict';

    angular.module('scaleApp').service('scanService', function ($http, $q, $resource, scaleConfig) {
        return {
            getScans: function (params) {
                var d = $q.defer();
                var url = scaleConfig.urls.apiPrefix + 'scans/';

                $http({
                    url: url,
                    method: 'GET',
                    params: params
                }).success(function (data) {
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getScanDetails: function (id) {
                var d = $q.defer();
                var url = scaleConfig.urls.apiPrefix + 'scans/' + id + '/';

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
            validateScan: function (scan) {
                var d = $q.defer();

                $http.post(scaleConfig.urls.apiPrefix + 'scans/validation/', scan.configuration).success(function (result) {
                    d.resolve(result);
                }).error(function(error){
                    d.reject(error);
                });

                return d.promise;
            },
            saveScan: function (scan) {
                var d = $q.defer();

                if (!scan.id) {
                    $http.post(scaleConfig.urls.apiPrefix + 'scans/', scan).success(function (result) {
                        d.resolve(result);
                    }).error(function (error) {
                        d.reject(error);
                    });
                } else {
                    $http.patch(scaleConfig.urls.apiPrefix + 'scans/' + scan.id + '/', scan).success(function (result) {
                        scan = result;
                        d.resolve(scan);
                    }).error(function (error) {
                        d.reject(error);
                    });
                }

                return d.promise;
            }
        };
    });
})();
