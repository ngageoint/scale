(function () {
    'use strict';
    angular.module('scaleApp').service('dataService', function ($location, $timeout, $q, $http, scaleConfig, Ingest) {

        var getSourceParams = function (page, page_size, started, ended, time_field, order, is_parsed, file_name) {
            return {
                page: page,
                page_size: page_size ? page_size : 1000,
                started: started,
                ended: ended,
                time_field: time_field,
                order: order ? order : '-last_modified',
                is_parsed: is_parsed,
                file_name: file_name
            };
        };

        return {
            getSources: function (params) {
                params = params || getSourceParams();
                var d = $q.defer();
                $http({
                    url: scaleConfig.getUrlPrefix('data') + 'sources/',
                    method: 'GET',
                    params: params
                }).success(function (data) {
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getSourceDetails: function (id) {
                var d = $q.defer();
                $http({
                    url: scaleConfig.getUrlPrefix('data') + 'sources/' + id + '/',
                    method: 'GET'
                }).success(function (data) {
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getSourceDescendants: function (id, type, params) {
                params = params || {};
                var d = $q.defer();
                $http({
                    url: scaleConfig.getUrlPrefix('data') + 'sources/' + id + '/' + type + '/',
                    method: 'GET',
                    params: params
                }).success(function (data) {
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            }
        };
    });
})();
