(function () {
    'use strict';
    
    angular.module('scaleApp').controller('jobTypesPerformanceController', function (scaleConfig, subnavService, jobTypeService, metricsService, toastr, moment) {
        var vm = this,
            started = moment.utc().subtract(3, 'd').toISOString(),
            ended = moment.utc().toISOString(),
            numDays = moment.utc(ended).diff(moment.utc(started), 'd'),
            jobTypes = [];

        vm.loading = true;
        vm.performanceData = [];
        vm.dates = [];
        vm.subnavLinks = scaleConfig.subnavLinks.jobs;
        subnavService.setCurrentPath('jobs/performance');

        var combineData = function (total, failed, id) {
            var valueArr = [],
                currDate = '',
                currTotal = 0,
                currFailed = 0;

            for (var i = 0; i <= numDays; i++) {
                currDate = moment.utc(started).add(i, 'd').format('YYYY-MM-DD');
                if (vm.dates.length <= numDays) {
                    vm.dates.push(currDate);
                }
                currTotal = _.find(total.values, { date: currDate, id: id });
                currFailed = _.find(failed.values, { date: currDate, id: id });
                valueArr.push({
                    date: currDate,
                    total: currTotal ? currTotal.value : 0,
                    failed: currFailed ? currFailed.value : 0
                });
            }

            return valueArr;
        };

        var initialize = function () {
            jobTypeService.getJobTypesOnce().then(function (jobTypesData) {
                jobTypes = jobTypesData.results;

                var metricsParams = {
                    page: null,
                    page_size: null,
                    started: started,
                    ended: ended,
                    choice_id: _.map(jobTypes, 'id'),
                    column: ['failed_count', 'total_count'],
                    group: null,
                    dataType: 'job-types'
                };

                metricsService.getPlotData(metricsParams).then(function (data) {
                    var failed = _.find(data.results, { column: { title: 'Failed Count'}});
                    var total = _.find(data.results, { column: { title: 'Total Count'}});

                    _.forEach(jobTypes, function (jobType) {
                        vm.performanceData.push({
                            id: jobType.id,
                            name: jobType.name,
                            title: jobType.title,
                            version: jobType.version,
                            icon_code: jobType.icon_code,
                            values: combineData(total, failed, jobType.id)
                        });
                    });

                    vm.loading = false;
                }).catch(function (error) {
                    vm.loading = false;
                    console.log(error);
                    toastr['error'](error);
                });
            });
        };
        
        initialize();
    });
})();