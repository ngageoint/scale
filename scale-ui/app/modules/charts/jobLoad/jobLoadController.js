(function () {
    'use strict';

    angular.module('scaleApp').controller('aisJobLoadController', function ($scope, scaleConfig, scaleService, loadService) {
        var chart = null,
            colArr = [],
            xArr = [],
            pendingArr = [],
            queuedArr = [],
            runningArr = [],
            removeIds = [],
            legendHide = [];

        $scope.filterValue = 1;
        $scope.filterDuration = 'w';
        $scope.filterDurations = ['M', 'w', 'd'];
        $scope.zoomEnabled = false;
        $scope.zoomClass = 'btn-default';
        $scope.zoomText = 'Enable Zoom';
        $scope.jobLoadData = {};
        $scope.loadingJobLoad = true;
        $scope.jobLoadError = null;
        $scope.jobLoadErrorStatus = null;
        $scope.total = 0;
        $scope.chartStyle = '';

        var jobLoadParams = {
            started: moment.utc().subtract($scope.filterValue, $scope.filterDuration).startOf('d').toDate(), ended: moment.utc().endOf('d').toDate(), job_type_id: null, job_type_name: null, job_type_category: null, url: null
        };

        $scope.toggleZoom = function () {
            $scope.zoomEnabled = !$scope.zoomEnabled;
            chart.zoom.enable($scope.zoomEnabled);
            if ($scope.zoomEnabled) {
                $scope.zoomClass = 'btn-primary';
                $scope.zoomText = 'Disable Zoom';
            } else {
                $scope.zoomClass = 'btn-default';
                $scope.zoomText = 'Enable Zoom';
            }
        };

        var initChart = function () {
            colArr = [];
            xArr = [];
            pendingArr = [];
            queuedArr = [];
            runningArr = [];

            /*
            // x axis values
            var numHours = moment.utc(jobLoadParams.ended).diff(moment.utc(jobLoadParams.started), 'h');
            for (var i = 0; i < numHours; i++) {
                xArr.push(moment.utc(jobLoadParams.started).add(i, 'h').startOf('h').toDate());
            }

            // data values
            _.forEach(xArr, function (xDate) {
                var dataObj = _.find($scope.jobLoadData.results, function (d) {
                    return moment.utc(d.time).startOf('h').isSame(xDate, 'hour');
                });
                // push 0 if data for xDate is not present in queryDates
                pendingArr.push(dataObj ? dataObj.pending_count : 0);
                queuedArr.push(dataObj ? dataObj.queued_count : 0);
                runningArr.push(dataObj ? dataObj.running_count : 0);
            });

            xArr.unshift('x');
            pendingArr.unshift('Pending');
            queuedArr.unshift('Queued');
            runningArr.unshift('Running');
            */

            xArr = _.pluck($scope.jobLoadData.results, 'time');
            _.forEach(xArr, function (d, i) {
                xArr[i] = moment.utc(d).toDate();
            });
            xArr.unshift('x');

            var pendingArr = _.pluck($scope.jobLoadData.results, 'pending_count'),
                queuedArr = _.pluck($scope.jobLoadData.results, 'queued_count'),
                runningArr = _.pluck($scope.jobLoadData.results, 'running_count');

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

            //if (chart) {
                /*
                chart.groups([groups]);
                chart.load({
                    columns: colArr,
                    types: types,
                });
                */
                /*
                chart.flow({
                    columns: colArr
                });
                */
            //} else {
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
            //}
            $scope.loadingJobLoad = false;
        };

        var getJobLoad = function (showPageLoad) {
            if (showPageLoad) {
                $scope.$parent.loading = true;
            } else {
                $scope.loadingJobLoad = true;
            }
            jobLoadParams.started = moment.utc().subtract($scope.filterValue, $scope.filterDuration).startOf('d').toDate();
            jobLoadParams.ended = moment.utc(jobLoadParams.started).add(1, $scope.filterDuration).endOf('d').toDate();
            jobLoadParams.page_size = 1000;

            loadService.getJobLoad(jobLoadParams).then(null, null, function (result) {
                if (result.$resolved) {
                    $scope.jobLoadData = result;
                    initChart();
                } else {
                    if (result.statusText && result.statusText !== '') {
                        $scope.jobLoadErrorStatus = result.statusText;
                    }
                    $scope.jobLoadError = 'Unable to retrieve job load.';
                }
                if (showPageLoad) {
                    $scope.$parent.loading = false;
                } else {
                    $scope.loadingJobLoad = false;
                }
            });
        };

        $scope.updateJobLoadRange = function (action) {
            if (action === 'older') {
                $scope.filterValue++;
            } else if (action === 'newer') {
                if ($scope.filterValue > 1) {
                    $scope.filterValue--;
                }
            } else if (action === 'today') {
                $scope.filterValue = 1;
            }
            getJobLoad(true);
        };

        $scope.$watch('filterValue', function (value) {
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

                $scope.chartStyle = 'height: ' + chartMaxHeight + 'px; max-height: ' + chartMaxHeight + 'px;';
                getJobLoad();
            });
        } else {
            getJobLoad();
        }
    });
})();
