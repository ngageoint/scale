(function () {
    'use strict';

    angular.module('scaleApp').controller('metricsController', function ($scope, $location, scaleConfig, scaleService, navService, metricsService, moment) {
        var vm = this,
            chart = null,
            colArr = [],
            colNames = {},
            xArr = [],
            removeIds = [],
            yUnits = [];

        vm._ = _;
        vm.moment = moment;
        vm.loadingMetrics = false;
        vm.chartArr = [];
        vm.chartData = [];
        vm.chartStyle = '';
        vm.selectedDataType = {};
        vm.inputStartDate = moment.utc().subtract(1, 'M').toDate();
        vm.inputEndDate = moment.utc().toDate();
        vm.openInputStart = function ($event) {
            $event.stopPropagation();
            vm.inputStartOpened = true;
        };
        vm.inputStartOpened = false;
        vm.openInputEnd = function ($event) {
            $event.stopPropagation();
            vm.inputEndOpened = true;
        };
        vm.inputEndOpened = false;
        vm.dateModelOptions = {
            timezone: '+000'
        };
        vm.dataTypeFilterText = '';
        vm.filtersApplied = [];
        vm.filteredChoices = [];
        vm.filteredChoicesOptions = [];
        vm.selectedMetrics = [];
        vm.columnGroupsOptions = [];
        vm.columns = [];
        vm.groups = [];
        vm.chartTitle = '';
        vm.chartDisplay = 'stacked';
        vm.stackedClass = 'btn-primary';
        vm.groupedClass = 'btn-default';
        vm.subchartClass = 'btn-primary';
        vm.subchartEnabled = false;
        vm.chartType = 'bar';
        vm.chartTypeDisplay = 'Bar';
        vm.barClass = 'btn-primary';
        vm.areaClass = 'btn-default';
        vm.lineClass = 'btn-default';
        vm.splineClass = 'btn-default';
        vm.scatterClass = 'btn-default';
        vm.metricsTotal = null;

        vm.getPlotDataParams = function (obj) {
            return {
                page: null,
                page_size: null,
                started: obj.started,
                ended: obj.ended,
                choice_id: obj.choice_id,
                column: obj.column,
                group: obj.group,
                dataType: obj.dataType.name
            };
        };

        vm.resetSelections = function () {
            vm.inputStartDate = moment.utc().subtract(1, 'M').toDate();
            vm.inputEndDate = moment.utc().toDate();
            vm.selectedDataType = {};
            vm.changeDataTypeSelection();
        };

        vm.updateChart = function () {
            vm.chartData = [];
            if (vm.chartArr.length === 0) {
                // nothing to show on chart
                chart.destroy();
                chart = null;
            } else {
                var callInit = _.after(vm.chartArr.length, function () {
                    // only initChart after this function has been called for all datasets in chartArr
                    vm.loadingMetrics = false;
                    vm.initChart();
                });

                _.forEach(vm.chartArr, function (obj) {
                    var params = vm.getPlotDataParams(obj);
                    metricsService.getPlotData(params).then(function (data) {
                    //metricsService.getGeneratedPlotData({query: obj, params: params}).then(function (data) {
                        vm.chartData.push({
                            query: obj,
                            results: data.results
                        });
                        callInit();
                    }).catch(function (error) {
                        vm.loadingMetrics = false;
                        console.log(error);
                        toastr['error'](error);
                    });
                });
            }
        };

        vm.addToChart = function () {
            vm.chartArr = []; // comment this out if allowing multiple adds
            vm.loadingMetrics = true;
            var filteredChoices = [],
                selectedColumns = [];
            // find the filter object associated with the chosen filter IDs
            _.forEach(vm.filtersApplied, function (id) {
                filteredChoices.push(_.find(vm.filteredChoices, { id: parseInt(id) }));
            });
            if (angular.isArray(vm.selectedMetrics)) {
                _.forEach(vm.selectedMetrics, function (metric) {
                    selectedColumns.push(_.find(vm.columns, { name: metric }));
                });
            } else {
                selectedColumns.push(_.find(vm.columns, { name: vm.selectedMetrics }));
            }
            vm.chartArr.push({
                started: vm.inputStartDate.toISOString(),
                ended: vm.inputEndDate.toISOString(),
                choice_id: vm.filtersApplied,
                column: _.pluck(selectedColumns, 'name'),
                group: null,
                dataType: vm.selectedDataType,
                filtersApplied: filteredChoices,
                selectedMetrics: selectedColumns
            });
            vm.updateChart();
            //vm.resetSelections();
        };

        vm.deleteFromChart = function (objToDelete) {
            _.remove(vm.chartArr, function (obj) {
                return JSON.stringify(obj) === JSON.stringify(objToDelete);
            });
            vm.updateChart();
        };

        vm.getFilterOptions = function (param) {
            return _.uniq(_.pluck(vm.filteredChoices, param));
        };

        vm.changeDataTypeSelection = function () {
            // reset options
            vm.filtersApplied = [];
            vm.selectedDataTypeOptions = [];
            vm.dataTypeFilterText = '';
            vm.selectedMetrics = [];
            vm.columns = [];

            if (!vm.selectedDataType.name || vm.selectedDataType.name === '') {
                vm.selectedDataType = {};
                vm.getDataTypes();
            } else {
                vm.getDataTypeOptions(vm.selectedDataType);
            }
        };

        vm.areFiltersApplied = function () {
            return vm.filtersApplied.length > 0;
        };

        vm.updateChartDisplay = function (display) {
            vm.chartDisplay = display;
            vm.stackedClass = display === 'stacked' ? 'btn-primary' : 'btn-default';
            vm.groupedClass = display === 'grouped' ? 'btn-primary' : 'btn-default';
            vm.initChart();
        };

        vm.updateChartType = function (type) {
            vm.chartType = type;
            vm.chartTypeDisplay = _.capitalize(type);
            vm.barClass = type === 'bar' ? 'btn-primary' : 'btn-default';
            vm.areaClass = type === 'area' ? 'btn-primary' : 'btn-default';
            vm.lineClass = type === 'line' ? 'btn-primary' : 'btn-default';
            vm.splineClass = type === 'spline' ? 'btn-primary' : 'btn-default';
            vm.scatterClass = type === 'scatter' ? 'btn-primary' : 'btn-default';
            vm.initChart();
        };

        vm.toggleSubchart = function () {
            vm.subchartEnabled = !vm.subchartEnabled;
            if (vm.subchartEnabled) {
                vm.subchartClass = 'btn-primary';
            } else {
                vm.subchartClass = 'btn-default';
            }
        };

        vm.initialize = function () {
            navService.updateLocation('metrics');
            vm.getDataTypes();
        };

        vm.getDataTypes = function () {
            metricsService.getDataTypes().then(function (result) {
                vm.availableDataTypes = result.results;
            }).catch(function (error) {
                console.log(error);
                toastr['error'](error);
            });
        };

        vm.getDataType = function (id) {
            metricsService.getDataTypeMetrics(id).then(function (result) {
                vm.selectedDataTypeAvailableMetrics = result.metrics;
            }).catch(function (error) {
                console.log(error);
            });
        };

        vm.getDataTypeOptions = function (dataType) {
            metricsService.getDataTypeOptions(dataType.name).then(function (result) {
                vm.selectedDataTypeOptions = result;
                _.forEach(result.filters, function (filter) {
                    vm.dataTypeFilterText = vm.dataTypeFilterText.length === 0 ? _.capitalize(filter.param) : vm.dataTypeFilterText + ', ' + _.capitalize(filter.param);
                });
                vm.filteredChoices = _.sortByOrder(result.choices, ['title','version'], ['asc','asc']);
                // format filteredChoices for use with multiselect directive
                var filteredChoicesOptions = [];
                _.forEach(vm.filteredChoices, function (choice) {
                    filteredChoicesOptions.push({
                        label: choice.version ? choice.title + ' ' + choice.version : choice.title,
                        title: choice.version ? choice.title + ' ' + choice.version : choice.title,
                        value: choice.id
                    });
                });
                vm.filteredChoicesOptions = filteredChoicesOptions;
                vm.columns = _.sortByOrder(result.columns, ['title'], ['asc']);
                vm.groups = result.groups;

                // create an array of objects containing grouped columns
                var columnGroupsOptions = [],
                    columnGroups = _.pairs(_.groupBy(result.columns, 'group'));
                _.forEach(columnGroups, function (group) {
                    var option = {
                        label: _.find(vm.groups, { name: group[0] }).title,
                        children: []
                    };
                    _.forEach(group[1], function (column) {
                        var child = {
                            label: column.title,
                            title: column.title,
                            value: column.name
                        };
                        option.children.push(child);
                    });
                    columnGroupsOptions.push(option);
                });
                columnGroupsOptions.unshift({
                    label: 'None Selected',
                    title: 'None Selected',
                    value: ''
                });
                vm.columnGroupsOptions = columnGroupsOptions;
            }).catch(function (error){
                console.log(error);
                toastr['error'](error);
            });
        };

        vm.initialize();

        $scope.$watch('vm.inputEndDate', function (value) {
            console.log(value)
        });

        var formatYValues = function (data, noPadding) {
            noPadding = noPadding || false;
            if (yUnits[0] === 'seconds') {
                return scaleService.calculateDuration(moment.utc().startOf('d'), moment.utc().startOf('d').add(data, 's'), noPadding);
            } else if (yUnits[0] === 'bytes') {
                return scaleService.calculateFileSizeFromBytes(data, 1);
            }
            return data;
        };

        // set up chart
        vm.initChart = function () {
            // mark any existing data for removal
            // compare currCols (columns currently in the chart) with displayCols (columns to display)
            removeIds = [];
            vm.metricsTotal = null;
            var currCols = [],
                displayCols = [];
            _.forEach(colArr, function (col, idx) {
                if (idx > 0) {
                    currCols.push(col[0]);
                }
            });
            _.forEach(vm.chartData, function (d) {
                displayCols = displayCols.concat(_.pluck(d.query.filtersApplied, 'name'));
                // increase metrics total if selected metric produces a sum
                // for now it is only possible to select one metric at a time
                // so just check the first element from selectedMetrics
                if (d.query.selectedMetrics[0].aggregate === 'sum') {
                    vm.metricsTotal = vm.metricsTotal + _.sum(d.results[0].values, 'value');
                }
            });
            // determine the exact differences between currCols and displayCols
            // if none are found, then removeIds stays empty
            _.forEach(currCols, function (currCol) {
                var displayCol = _.find(displayCols, function (dCol) {
                    return dCol === currCol;
                });
                if (!displayCol) {
                    removeIds.push(currCol);
                }
            });

            // init with new data
            colArr = [];
            xArr = [];
            colNames = {};

            // create xArr
            var numDays = moment.utc(vm.inputEndDate).endOf('d').diff(moment.utc(vm.inputStartDate.toISOString()).startOf('d'), 'd') + 1; // add 1 to include starting day in count
            for (var i = 0; i < numDays; i++) {
                xArr.push(moment.utc(vm.inputStartDate.toISOString()).startOf('d').add(i, 'd').toDate());
            }

            // iterate over datatypes and add values to colArr
            _.forEach(vm.chartData, function (data) {
                var valueArr = [],
                    query = data.query,
                    queryFilter = {},
                    queryDates = [];

                yUnits = _.pluck(query.selectedMetrics, 'units');

                if (query.filtersApplied.length > 0) {
                    // filters were applied, so build data source accordingly
                    _.forEach(data.results, function (result) {
                        if (result.values.length > 0) {
                            // values for all filters are returned in one array of arrays,
                            // so group results by id to isolate filter values
                            var groupedResult = _.groupBy(result.values, 'id'),
                                resultObj = {},
                                filterIds = _.pluck(query.filtersApplied, 'id');
                            // try to get each filter id from groupedResult.
                            // if it's undefined, an empty array will be returned
                            // this allows a zeroed array to appear in the chart,
                            // since we want to include all filters selected by the user
                            // regardless of value
                            if (filterIds.length > 1) {
                                // when more than one filter is requested, then an id
                                // value is present within data.results
                                _.forEach(filterIds, function (id) {
                                    resultObj[id] = _.get(groupedResult, id, []);
                                });
                            } else {
                                // when one filter is requested, no id value is included
                                // in data.results, so build resultObj with the other
                                // info we have
                                resultObj[query.choice_id[0]] = _.pairs(groupedResult)[0][1];
                            }
                            _.forEach(_.pairs(resultObj), function (d) {
                                valueArr = [];
                                // d[0] will be choice id, d[1] will be values
                                // if only one filter was selected, d[0] will return as string 'undefined' since no id is included in this case
                                queryFilter = d[0] === 'undefined' ? query.filtersApplied[0] : _.find(query.filtersApplied, {id: parseInt(d[0])});
                                queryDates = d[1];

                                // add result values to valueArr
                                _.forEach(xArr, function (xDate) {
                                    var valueObj = _.find(queryDates, function (qDate) {
                                        return moment.utc(qDate.date).isSame(xDate, 'day');
                                    });
                                    // push 0 if data for xDate is not present in queryDates
                                    valueArr.push(valueObj ? valueObj.value : 0);
                                });

                                // prepend valueArr with filter title, and push onto colArr
                                valueArr.unshift(queryFilter.name + queryFilter.id);
                                colNames[queryFilter.name + queryFilter.id] = queryFilter.version ? queryFilter.title + ' ' + queryFilter.version : queryFilter.title;
                                colArr.push(valueArr);
                            });
                        }
                    });
                } else {
                    // no filters were applied, so show aggregate statistics
                    _.forEach(data.results, function (result) {
                        // add result values to valueArr
                        _.forEach(xArr, function (xDate) {
                            var valueObj = _.find(result.values, function (qDate) {
                                return moment.utc(qDate.date).isSame(xDate, 'day');
                            });
                            // push 0 if data for xDate is not present in result.values
                            valueArr.push(valueObj ? valueObj.value : 0);
                        });

                        // prepend valueArr with filter title, and push onto colArr
                        var columnLabel = result.column.title + ' for all ' + query.dataType.title;
                        valueArr.unshift(columnLabel);
                        colNames['aggregate'] = columnLabel;
                        colArr.push(valueArr);
                    });
                }
            });

            // inform the user if the metrics they selected are empty
            if (_.sum(_.flatten(colArr)) === 0) {
                toastr['info']('There is no data to display.');
            }

            // prepend xArr with an 'x' label and add to colArr
            xArr.unshift('x');
            colArr.unshift(xArr);

            var types = {},
                type = {},
                groups = [];

            _.forEach(colArr, function (col) {
                type = {};
                if (col[0] !== 'x') {
                    type[col[0]] = vm.chartType;
                    if (vm.chartDisplay === 'stacked') {
                        groups.push(col[0]);
                    }
                }
                angular.extend(types, type);
            });

            if (chart) {
                // chart already exists, so update values
                chart.groups([groups]);
                chart.data.names(colNames);
                chart.axis.labels({
                    y: _.capitalize(yUnits[0])
                });
                chart.load({
                    columns: colArr,
                    types: types,
                    unload: removeIds
                });
            } else {
                // no chart yet, so set it up
                chart = c3.generate({
                    bindto: '#metrics',
                    data: {
                        x: 'x',
                        columns: colArr,
                        types: types,
                        groups: [groups],
                        names: colNames
                    },
                    subchart: {
                        show: vm.subchartEnabled
                    },
                    transition: {
                        duration: 700
                    },
                    color: {
                        pattern: scaleConfig.colors.patternD320
                    },
                    axis: {
                        type: 'timeseries',
                        x: {
                            tick: {
                                format: function (d) {
                                    return moment.utc(d).toISOString();
                                }
                            },
                            label: {
                                text: 'Dates',
                                position: 'outer-center'
                            }
                        },
                        y: {
                            tick: {
                                format: function (d) {
                                    return formatYValues(d);
                                }
                            },
                            label: {
                                text: _.capitalize(yUnits[0]),
                                position: 'outer-middle'
                            }
                        }
                    }
                });
            }

            if (vm.metricsTotal) {
                vm.metricsTotal = formatYValues(vm.metricsTotal, true);
                vm.chartTitle = '<div class="label label-success">' + vm.metricsTotal.toLocaleString() + '</div> ' + vm.chartData[0].query.selectedMetrics[0].title + ' for ' + moment.utc(vm.inputStartDate).format('DD MMM YYYY') + ' - ' + moment.utc(vm.inputEndDate).format('DD MMM YYYY');
            } else {
                vm.chartTitle = vm.chartData[0].query.selectedMetrics[0].title + ' ' + moment.utc(vm.inputStartDate).format('DD MMM YYYY') + ' - ' + moment.utc(vm.inputEndDate).format('DD MMM YYYY');
            }
        };

        // set chart height
        angular.element(document).ready(function () {
            // set container heights equal to available page height
            var viewport = scaleService.getViewportSize(),
                offset = scaleConfig.headerOffset,
                chartMaxHeight = viewport.height - offset;

            vm.chartStyle = 'height: ' + chartMaxHeight + 'px; max-height: ' + chartMaxHeight + 'px;';
        });
    });
})();
