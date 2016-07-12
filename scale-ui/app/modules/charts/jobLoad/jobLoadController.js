(function () {
    'use strict';

    angular.module('scaleApp').controller('aisJobLoadController', function ($scope, scaleConfig, scaleService, loadService) {
        var vm = this,
            chart = null,
            colArr = [],
            xArr = [];

        vm.filterValue = 1;
        vm.filterDuration = 'w';
        vm.filterDurations = ['M', 'w', 'd'];
        vm.zoomEnabled = false;
        vm.zoomClass = 'btn-default';
        vm.zoomText = 'Enable Zoom';
        vm.jobLoadData = {};
        vm.loadingJobLoad = true;
        vm.jobLoadError = null;
        vm.jobLoadErrorStatus = null;
        vm.total = 0;
        vm.chartStyle = '';

        var jobLoadParams = {
            started: moment.utc().subtract(vm.filterValue, vm.filterDuration).startOf('d').toDate(), ended: moment.utc().endOf('d').toDate(), job_type_id: null, job_type_name: null, job_type_category: null, url: null
        };

        vm.toggleZoom = function () {
            vm.zoomEnabled = !vm.zoomEnabled;
            chart.zoom.enable(vm.zoomEnabled);
            if (vm.zoomEnabled) {
                vm.zoomClass = 'btn-primary';
                vm.zoomText = 'Disable Zoom';
            } else {
                vm.zoomClass = 'btn-default';
                vm.zoomText = 'Enable Zoom';
            }
        };

        var initChart = function () {
            xArr = [];
            
            xArr = _.pluck(vm.jobLoadData.results, 'time');
            _.forEach(xArr, function (d, i) {
                xArr[i] = moment.utc(d).toDate();
            });
            xArr.unshift('x');

            var pendingArr = _.pluck(vm.jobLoadData.results, 'pending_count'),
                queuedArr = _.pluck(vm.jobLoadData.results, 'queued_count'),
                runningArr = _.pluck(vm.jobLoadData.results, 'running_count');

            pendingArr.unshift('Pending');
            queuedArr.unshift('Queued');
            runningArr.unshift('Running');

            // add to colArr
            colArr = [xArr, pendingArr, queuedArr, runningArr];

            var types = {},
                type = {},
                groups = [];

            _.forEach(colArr, function(col){
                type = {};
                if (col[0] !== 'x') {
                    type[col[0]] = 'area';
                    groups.push(col[0]);
                }
                angular.extend(types, type);
            });

            if (chart) {
                chart.flush();
            }
            // chart config
            chart = c3.generate({
                bindto: '#job-load',
                data: {
                    x: 'x',
                    columns: colArr,
                    types: types,
                    groups: [groups],
                    colors: {
                        Pending: scaleConfig.colors.chart_pink,
                        Queued: scaleConfig.colors.chart_purple,
                        Running: scaleConfig.colors.chart_blue
                    }
                },
                transition: {
                    duration: 700
                },
                tooltip: {
                    format: {
                        title: function (x) {
                            return moment.utc(x).startOf('h').format(scaleConfig.dateFormats.day_second);
                        }
                    }
                },
                axis: {
                    x: {
                        type: 'timeseries',
                        tick: {
                            format: function (d) {
                                return moment.utc(d).format(scaleConfig.dateFormats.day);
                            }
                        }
                    }
                }
            });
            vm.loadingJobLoad = false;
        };

        var getJobLoad = function (showPageLoad) {
            if (showPageLoad) {
                $scope.$parent.loading = true;
            } else {
                vm.loadingJobLoad = true;
            }
            jobLoadParams.started = moment.utc().subtract(vm.filterValue, vm.filterDuration).startOf('d').toDate();
            jobLoadParams.ended = moment.utc(jobLoadParams.started).add(1, vm.filterDuration).endOf('d').toDate();
            jobLoadParams.page_size = 1000;

            loadService.getJobLoad(jobLoadParams).then(null, null, function (result) {
                if (result.$resolved) {
                    vm.jobLoadData = result;
                    initChart();
                } else {
                    if (result.statusText && result.statusText !== '') {
                        vm.jobLoadErrorStatus = result.statusText;
                    }
                    vm.jobLoadError = 'Unable to retrieve job load.';
                }
                if (showPageLoad) {
                    $scope.$parent.loading = false;
                } else {
                    vm.loadingJobLoad = false;
                }
            });
        };

        vm.updateJobLoadRange = function (action) {
            if (action === 'older') {
                vm.filterValue++;
            } else if (action === 'newer') {
                if (vm.filterValue > 1) {
                    vm.filterValue--;
                }
            } else if (action === 'today') {
                vm.filterValue = 1;
            }
            getJobLoad(true);
        };

        $scope.$watch('vm.filterValue', function (value) {
            var $jobLoadNewer = $('.job-load-newer'),
                $jobLoadToday = $('.job-load-today');

            if (value > 1) {
                $jobLoadNewer.removeAttr('disabled');
                $jobLoadToday.removeAttr('disabled');
            } else {
                $jobLoadNewer.attr('disabled', 'disabled');
                $jobLoadToday.attr('disabled', 'disabled');
            }
        });


        if ($scope.autoHeight) {
            // set chart height
            angular.element(document).ready(function () {
                // set container heights equal to available page height
                var viewport = scaleService.getViewportSize(),
                    offset = scaleConfig.headerOffset,
                    headerOffset = $('.job-load-header').height(),
                    legendOffset = $('.job-load-legend-label').height(),
                    filterOffset = $('.job-load-filter').outerHeight(true),
                    chartMaxHeight = viewport.height - offset - headerOffset - legendOffset - filterOffset - 5;

                vm.chartStyle = 'height: ' + chartMaxHeight + 'px; max-height: ' + chartMaxHeight + 'px;';
                getJobLoad();
            });
        } else {
            getJobLoad();
        }
    });
})();
