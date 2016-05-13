(function () {
    'use strict';
    
    angular.module('scaleApp').controller('jobTypesPerformanceController', function (scaleConfig, subnavService, jobTypeService, metricsService, toastr, moment) {
        var vm = this;

        vm.loading = true;
        vm.moment = moment;
        vm.started = moment.utc().subtract(72, 'h').toISOString();
        vm.ended = moment.utc().toISOString();
        vm.jobTypes = [];
        vm.performanceData = [];
        vm.subnavLinks = scaleConfig.subnavLinks.jobs;
        subnavService.setCurrentPath('jobs/performance');

        vm.getJobType = function (id) {
            return _.find(jobTypes, { id: id });
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

                    _.forEach(jobTypes, function (jobType) {
                        vm.performanceData.push({
                            id: jobType.id,
                            name: jobType.name,
                            title: jobType.title,
                            version: jobType.version,
                            icon_code: jobType.icon_code,
                            values: []
                        });

                        _.forEach(failed.values, function (value) {
                            vm.performance[value.id].values.push({
                                
                            })
                        })
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