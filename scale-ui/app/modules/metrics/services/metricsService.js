(function () {
    'use strict';

    angular.module('scaleApp').service('metricsService', function ($http, $q, $resource, scaleConfig) {
        var getPlotDataParams = function (page, page_size, started, ended, choice_id, column, group, dataType) {
            console.log(choice_id);
            return {
                page: page,
                page_size: page_size,
                started: started,
                ended: ended,
                choice_id: choice_id,
                column: column,
                group: group,
                dataType: dataType
            };
        };

        return {
            getDataTypes: function () {
                var d = $q.defer();
                $http.get(scaleConfig.urls.getMetricsDataTypes()).success(function (data) {
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getDataTypeMetrics: function (id) {
                var d = $q.defer();
                $http.get(scaleConfig.urls.getMetricsDataTypeOptions(id)).success(function (data) {
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getDataTypeOptions: function (name) {
                var d = $q.defer();
                var url = scaleConfig.urls.getMetricsDataTypeOptions(name);
                $http.get(url).success(function (data) {
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getPlotData: function (params) {
                var params = params || getPlotDataParams(),
                    d = $q.defer();

                $http({
                    method: 'GET',
                    url: scaleConfig.urls.getMetricsPlotData(params.dataType),
                    params: params
                }).success(function (data) {
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });

                return d.promise;
            },
            getGeneratedPlotData: function (obj) {
                var d = $q.defer();

                var returnObj = {
                    count: 28,
                    next: null,
                    previous: null,
                    results: []
                };

                var numDays = moment.utc(obj.params.ended).diff(moment.utc(obj.params.started), 'd') + 1;

                _.forEach(obj.query.selectedMetrics, function (metric) {
                    var returnResult = {
                        column: metric,
                        min_x: moment.utc(obj.params.started).format('YYYY-MM-DD'),
                        max_x: moment.utc(obj.params.ended).format('YYYY-MM-DD'),
                        min_y: 1,
                        max_y: 100,
                        values: []
                    };

                    for (var i = 0; i < numDays; i++) {
                        if (obj.query.filtersApplied.length > 1) {
                            _.forEach(obj.query.filtersApplied, function (filter) {
                                returnResult.values.push({
                                    date: moment.utc(obj.params.started).add(i, 'd').format('YYYY-MM-DD'),
                                    value: Math.floor(Math.random() * (1000 - 1 + 1)) + 1,
                                    id: filter.id
                                });
                            });
                        } else {
                            returnResult.values.push({
                                date: moment.utc(obj.params.started).add(i, 'd').format('YYYY-MM-DD'),
                                value: Math.floor(Math.random() * (1000 - 1 + 1)) + 1
                            });
                        }
                    }
                    returnObj.results.push(returnResult);
                });

                d.resolve(returnObj);

                return d.promise;
            }
        };
    });
})();
