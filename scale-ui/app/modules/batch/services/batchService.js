(function () {
    'use strict';

    angular.module('scaleApp').service('batchService', function($http, $q, $resource, scaleConfig, poller, pollerFactory) {

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
            getBatchesOnce: function (params) {
                params = params || getBatchesParams();
                var d = $q.defer();
                var url = scaleConfig.getUrlPrefix() + 'batches/';
                $http({
                    url: url,
                    method: 'GET',
                    params: params
                }).success(function (data) {
                    //data.results = Job.transformer(data.results);
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });

                return d.promise;
            }
        };
    });
})();
