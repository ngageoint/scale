(function () {
    'use strict';

    angular.module('scaleApp').service('batchService', function($http, $q, $resource, scaleConfig) {

        var getBatchesParams = function (page, page_size, started, ended, order, status) {
            return {
                page: page,
                page_size: page_size,
                started: started,
                ended: ended,
                order: order,
                status: status
            };
        };

        return {
            getBatches: function (params) {
                params = params || getBatchesParams();
                var d = $q.defer();
                var url = scaleConfig.getUrlPrefix() + 'batches/';
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
            getBatchById: function (id) {
                var d = $q.defer();

                $http({
                    url: scaleConfig.getUrlPrefix() + 'batches/' + id + '/',
                    method: 'GET'
                }).success(function (data) {
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });

                return d.promise;
            },
            validateBatch: function (batch) {
                var d = $q.defer();

                $http.post(scaleConfig.urls.apiPrefix + 'batches/validation/', batch.clean()).success(function (result) {
                    d.resolve(result);
                }).error(function(error){
                    d.reject(error);
                });

                return d.promise;
            },
            saveBatch: function (batch) {
                var d = $q.defer();

                $http.post(scaleConfig.urls.apiPrefix + 'batches/', batch.clean()).success(function (result) {
                    d.resolve(result);
                }).error(function (error) {
                    d.reject(error);
                });

                return d.promise;
            }
        };
    });
})();
