(function () {
    'use strict';
    angular.module('scaleApp').service('feedService', function ($location, $timeout, $q, $http, scaleConfig, scaleService, Feed, FeedStatus) {

        var getFeedParams = function(params){
            if(!params){ params = {}; }
            var p = {};
            p.page_size = 1000;
            p.started = params.started ? params.started : moment.utc().add(-7,'days').startOf('d').toDate();
            p.ended = params.ended ? params.ended : moment.utc().toDate();
            p.use_ingest_time = params.use_ingest_time ? params.use_ingest_time : null;
            return p;
        };

        var getIngestsParams = function(params){
            return params;
        };

        return {
            getFeed: function(params){
                var d = $q.defer();
                var params = getFeedParams(params);
                $http({
                    url: scaleConfig.urls.getDataFeed(),
                    method: 'GET',
                    params: params
                }).success(function (data) {
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getIngestsOnce: function(params) {
                var d = $q.defer();
                var params = getIngestsParams(params);
                $http({
                    url: scaleConfig.urls.getIngests(),
                    method: 'GET',
                    params: params
                }).success(function (data) {
                    _.forEach(data.results, function(d){
                        d.file_size_formatted = scaleService.calculateFileSizeFromBytes(d.file_size);
                    });
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            }
        };
    });
})();
