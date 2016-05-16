(function () {
    'use strict';
    
    angular.module('scaleApp').controller('jobTypesPerformanceController', function (scaleConfig, subnavService, jobTypeService, metricsService, toastr, moment) {
        var vm = this;

        vm.loading = true;
        vm.moment = moment;
        vm._ = _;
        vm.started = moment.utc().subtract(3, 'd').toISOString();
        vm.ended = moment.utc().toISOString();
        vm.jobTypes = [];
        vm.performanceData = [];
        vm.subnavLinks = scaleConfig.subnavLinks.jobs;
        subnavService.setCurrentPath('jobs/performance');

        var combineData = function (total, failed, id) {
            var valueArr = [],
                currDate = '',
                currTotal = 0,
                currFailed = 0,
                numDays = moment.utc(vm.ended).diff(moment.utc(vm.started), 'd');

            for (var i = 0; i <= numDays; i++) {
                currDate = moment.utc(vm.started).add(i, 'd').format('YYYY-MM-DD');
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
                vm.jobTypes = jobTypesData.results;

                var metricsParams = {
                    page: null,
                    page_size: null,
                    started: vm.started,
                    ended: vm.ended,
                    choice_id: _.map(vm.jobTypes, 'id'),
                    column: ['failed_count', 'total_count'],
                    group: null,
                    dataType: 'job-types'
                };

                metricsService.getPlotData(metricsParams).then(function (data) {
                    var failed = _.find(data.results, { column: { title: 'Failed Count'}});
                    var total = _.find(data.results, { column: { title: 'Total Count'}});

                    _.forEach(vm.jobTypes, function (jobType) {
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