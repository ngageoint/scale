(function () {
    'use strict';
    
    angular.module('scaleApp').controller('jobTypesPerformanceController', function (scaleConfig, subnavService, metricsService, toastr, moment) {
        var vm = this,
            started = moment.utc().subtract(3, 'd').toISOString(),
            ended = moment.utc().toISOString(),
            numDays = moment.utc(ended).diff(moment.utc(started), 'd'),
            errorTypes = [1, 2, 3];

        vm.loading = true;
        vm.performanceData = [];
        vm.dates = [];
        vm.subnavLinks = scaleConfig.subnavLinks.jobs;
        subnavService.setCurrentPath('jobs/performance');

        var formatData = function (data, id) {
            var valueArr = [],
                currDate = '',
                currValue = 0;

            for (var i = 0; i <= numDays; i++) {
                currDate = moment.utc(started).add(i, 'd').format('YYYY-MM-DD');
                if (vm.dates.length <= numDays) {
                    vm.dates.push(currDate);
                }
                currValue = _.find(data.values, { date: currDate, id: id });
                valueArr.push({
                    date: currDate,
                    value: currValue ? currValue.value : 0
                });
            }

            return valueArr;
        };

        var initialize = function () {
            var metricsParams = {
                page: null,
                page_size: null,
                started: started,
                ended: ended,
                choice_id: errorTypes,
                column: ['total_count'],
                group: null,
                dataType: 'error-types'
            };

            metricsService.getPlotData(metricsParams).then(function (data) {
                if (data.results.length > 0) {
                    _.forEach(metricsParams.choice_id, function (id) {
                        vm.performanceData.push({
                            id: id,
                            values: formatData(data.results[0], id)
                        });
                    });
                }

                vm.loading = false;
            }).catch(function (error) {
                vm.loading = false;
                console.log(error);
                toastr['error'](error);
            });
        };
        
        initialize();
    });
})();