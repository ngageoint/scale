(function () {
    'use strict';

    angular.module('scaleApp').controller('metricsController', function ($scope, $location, scaleConfig, scaleService, navService, metricsService, moment) {
        var chart = null,
            colArr = [],
            colNames = {},
            xArr = [],
            removeIds = [],
            yUnits = [],
            locationParams = {
                chart: null
            },
            self = this;

        $scope._ = _;
        $scope.moment = moment;
        $scope.loadingMetrics = false;
        $scope.chartArr = [];
        $scope.chartData = [];
        $scope.chartStyle = '';
        $scope.selectedDataType = {};
        $scope.inputStartDate = moment.utc().subtract(1, 'M').toISOString();
        $scope.inputEndDate = moment.utc().toISOString();
        $scope.openInputStart = function ($event) {
            $event.stopPropagation();
            $scope.inputStartOpened = true;
        };
        $scope.inputStartOpened = false;
        $scope.openInputEnd = function ($event) {
            $event.stopPropagation();
            $scope.inputEndOpened = true;
        };
        $scope.inputEndOpened = false;
        $scope.dataTypeFilterText = '';
        $scope.filtersApplied = [];
        $scope.filteredChoices = [];
        $scope.filteredChoicesOptions = [];
        $scope.selectedMetrics = [];
        $scope.columnGroupsOptions = [];
        $scope.columns = [];
        $scope.groups = [];
        $scope.chartTitle = '';
        $scope.chartDisplay = 'stacked';
        $scope.stackedClass = 'btn-primary';
        $scope.groupedClass = 'btn-default';
        $scope.subchartClass = 'btn-primary';
        $scope.subchartEnabled = false;
        $scope.chartType = 'bar';
        $scope.chartTypeDisplay = 'Bar';
        $scope.barClass = 'btn-primary';
        $scope.areaClass = 'btn-default';
        $scope.lineClass = 'btn-default';
        $scope.splineClass = 'btn-default';
        $scope.scatterClass = 'btn-default';

        /*
        // check for locationParams in query string, and update as necessary
        _.forEach(_.pairs(locationParams), function (param) {
            var value = _.at($location.search(), param[0]);
            if (value.length > 0) {
                locationParams[param[0]] = value.length > 1 ? value : value[0];
            }
        });

        if (locationParams.chart) {
            try {
                $scope.chartArr = JSON.parse(atob(locationParams.chart));
            } catch (e) {
                toastr['error']('Unable to parse JSON');
            }
        }
        */

        self.getPlotDataParams = function (obj) {
            return {
                page: null,
                page_size: null,
                started: obj.started,
                ended: obj.ended,
                'choice-id': obj.choice_id,
                column: obj.column,
                group: obj.group,
                dataType: obj.dataType.name
            };
        };

        self.resetSelections = function () {
            $scope.inputStartDate = moment.utc().subtract(1, 'M').toISOString();
            $scope.inputEndDate = moment.utc().toISOString();
            $scope.selectedDataType = {};
            $scope.changeDataTypeSelection();
        };

        self.updateChart = function () {
            $scope.chartData = [];
            if ($scope.chartArr.length === 0) {
                // nothing to show on chart
                chart.destroy();
                chart = null;
            } else {
                var callInit = _.after($scope.chartArr.length, function () {
                    // only initChart after this function has been called for all datasets in chartArr
                    $scope.loadingMetrics = false;
                    self.initChart();
                });

                _.forEach($scope.chartArr, function (obj) {
                    var params = self.getPlotDataParams(obj);
                    metricsService.getPlotData(params).then(function (data) {
                    //metricsService.getGeneratedPlotData({query: obj, params: params}).then(function (data) {
                        $scope.chartData.push({
                            query: obj,
                            results: data.results
                        });
                        callInit();
                    }).catch(function (error) {
                        $scope.loadingMetrics = false;
                        console.log(error);
                        toastr['error'](error);
                    });
                });
                /*
                locationParams.chart = btoa(JSON.stringify($scope.chartArr));
                $location.search('chart', locationParams.chart).replace();
                */
            }
        };

        $scope.addToChart = function () {
            $scope.chartArr = []; // comment this out if allowing multiple adds
            $scope.loadingMetrics = true;
            var filteredChoices = [],
                selectedColumns = [];
            // find the filter object associated with the chosen filter IDs
            _.forEach($scope.filtersApplied, function (id) {
                filteredChoices.push(_.find($scope.filteredChoices, { id: parseInt(id) }));
            });
            if (angular.isArray($scope.selectedMetrics)) {
                _.forEach($scope.selectedMetrics, function (metric) {
                    selectedColumns.push(_.find($scope.columns, { name: metric }));
                });
            } else {
                selectedColumns.push(_.find($scope.columns, { name: $scope.selectedMetrics }));
            }
            $scope.chartArr.push({
                started: $scope.inputStartDate,
                ended: $scope.inputEndDate,
                choice_id: $scope.filtersApplied,
                column: _.pluck(selectedColumns, 'name'),
                group: null,
                dataType: $scope.selectedDataType,
                filtersApplied: filteredChoices,
                selectedMetrics: selectedColumns
            });
            self.updateChart();
            //self.resetSelections();
        };

        $scope.deleteFromChart = function (objToDelete) {
            _.remove($scope.chartArr, function (obj) {
                return JSON.stringify(obj) === JSON.stringify(objToDelete);
            });
            self.updateChart();
        };

        $scope.getFilterOptions = function (param) {
            return _.uniq(_.pluck($scope.filteredChoices, param));
        };

        $scope.changeDataTypeSelection = function () {
            // reset options
            $scope.filtersApplied = [];
            //$scope.filteredChoices = [];
            $scope.selectedDataTypeOptions = [];
            $scope.dataTypeFilterText = '';
            $scope.selectedMetrics = [];
            //$scope.columnGroups = [];
            $scope.columns = [];

            if (!$scope.selectedDataType.name || $scope.selectedDataType.name === '') {
                $scope.selectedDataType = {};
                self.getDataTypes();
            } else {
                self.getDataTypeOptions($scope.selectedDataType);
            }
        };

        /*$scope.changeFilterSelection = function (name) {
            console.log(name + ': ' + $scope.filtersApplied[name]);
            // remove filter if value is null or empty
            if (!$scope.filtersApplied[name] || $scope.filtersApplied[name] === '') {
                delete $scope.filtersApplied[name];
            }
            // update filtered choices
            applyFiltersToChoices();
        };*/

        $scope.areFiltersApplied = function () {
            return $scope.filtersApplied.length > 0;
        };

        /*$scope.removeFilter = function (name) {
            // set value = null
            $scope.filtersApplied[name] = '';
            // trigger filter selection change
            $scope.changeFilterSelection(name);
        };*/

        $scope.updateChartDisplay = function (display) {
            $scope.chartDisplay = display;
            $scope.stackedClass = display === 'stacked' ? 'btn-primary' : 'btn-default';
            $scope.groupedClass = display === 'grouped' ? 'btn-primary' : 'btn-default';
            self.initChart();
        };

        $scope.updateChartType = function (type) {
            $scope.chartType = type;
            $scope.chartTypeDisplay = _.capitalize(type);
            $scope.barClass = type === 'bar' ? 'btn-primary' : 'btn-default';
            $scope.areaClass = type === 'area' ? 'btn-primary' : 'btn-default';
            $scope.lineClass = type === 'line' ? 'btn-primary' : 'btn-default';
            $scope.splineClass = type === 'spline' ? 'btn-primary' : 'btn-default';
            $scope.scatterClass = type === 'scatter' ? 'btn-primary' : 'btn-default';
            self.initChart();
        };

        $scope.toggleSubchart = function () {
            $scope.subchartEnabled = !$scope.subchartEnabled;
            if ($scope.subchartEnabled) {
                $scope.subchartClass = 'btn-primary';
            } else {
                $scope.subchartClass = 'btn-default';
            }
        };

        self.initialize = function () {
            navService.updateLocation('metrics');
            self.getDataTypes();
            /*
            if ($scope.chartArr.length > 0) {
                self.updateChart();
            }
            */
        };

        /*var applyFiltersToChoices = function () {
            var choices = $scope.selectedDataTypeOptions ? $scope.selectedDataTypeOptions.choices : [];
            var filteredChoices = _.where(choices,$scope.filtersApplied);
            $scope.filteredChoices = filteredChoices;
        };*/

        self.getDataTypes = function () {
            metricsService.getDataTypes().then(function (result) {
                $scope.availableDataTypes = result.results;
            }).catch(function (error) {
                console.log(error);
                toastr['error'](error);
            });
        };

        self.getDataType = function (id) {
            metricsService.getDataTypeMetrics(id).then(function (result) {
                $scope.selectedDataTypeAvailableMetrics = result.metrics;
            }).catch(function (error) {
                console.log(error);
            });
        };

        self.getDataTypeOptions = function (dataType) {
            metricsService.getDataTypeOptions(dataType.name).then(function (result) {
                $scope.selectedDataTypeOptions = result;
                _.forEach(result.filters, function (filter) {
                    $scope.dataTypeFilterText = $scope.dataTypeFilterText.length === 0 ? _.capitalize(filter.param) : $scope.dataTypeFilterText + ', ' + _.capitalize(filter.param);
                });
                $scope.filteredChoices = _.sortByOrder(result.choices, ['title','version'], ['asc','asc']);
                // format filteredChoices for use with multiselect directive
                var filteredChoicesOptions = [];
                _.forEach($scope.filteredChoices, function (choice) {
                    filteredChoicesOptions.push({
                        label: choice.version ? choice.title + ' ' + choice.version : choice.title,
                        title: choice.version ? choice.title + ' ' + choice.version : choice.title,
                        value: choice.id
                    });
                });
                $scope.filteredChoicesOptions = filteredChoicesOptions;
                $scope.columns = _.sortByOrder(result.columns, ['title'], ['asc']);
                $scope.groups = result.groups;

                // create an array of objects containing grouped columns
                var columnGroupsOptions = [],
                    columnGroups = _.pairs(_.groupBy(result.columns, 'group'));
                _.forEach(columnGroups, function (group) {
                    var option = {
                        label: _.find($scope.groups, { name: group[0] }).title,
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
                $scope.columnGroupsOptions = columnGroupsOptions;
            }).catch(function (error){
                console.log(error);
                toastr['error'](error);
            });
        };

        self.initialize();

        $scope.$watch('inputEndDate', function (value) {
            console.log(value)
        });

        // set up chart
        self.initChart = function () {
            // mark any existing data for removal
            // compare currCols (columns currently in the chart) with displayCols (columns to display)
            removeIds = [];
            var currCols = [],
                displayCols = [];
            _.forEach(colArr, function (col, idx) {
                if (idx > 0) {
                    currCols.push(col[0]);
                }
            });
            _.forEach($scope.chartData, function (d) {
                displayCols = displayCols.concat(_.pluck(d.query.filtersApplied, 'name'));
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
            var numDays = moment.utc($scope.inputEndDate).endOf('d').diff(moment.utc($scope.inputStartDate).startOf('d'), 'd') + 1; // add 1 to include starting day in count
            for (var i = 0; i < numDays; i++) {
                xArr.push(moment.utc($scope.inputStartDate).startOf('d').add(i, 'd').toDate());
            }

            // iterate over datatypes and add values to colArr
            _.forEach($scope.chartData, function (data) {
                var valueArr = [],
                    query = data.query,
                    queryFilter = {},
                    queryDates = [];

                yUnits = _.pluck(query.selectedMetrics, 'units');

                if (query.filtersApplied.length > 0) {
                    // filters were applied, so build data source accordingly
                    _.forEach(data.results, function (result) {
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
                            queryFilter = d[0] === 'undefined' ? query.filtersApplied[0] : _.find(query.filtersApplied, { id: parseInt(d[0]) });
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
                    type[col[0]] = $scope.chartType;
                    if ($scope.chartDisplay === 'stacked') {
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
                        show: $scope.subchartEnabled
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
                            label: {
                                text: _.capitalize(yUnits[0]),
                                position: 'outer-middle'
                            }
                        }
                    }
                });
            }
        };

        // set chart height
        angular.element(document).ready(function () {
            // set container heights equal to available page height
            var viewport = scaleService.getViewportSize(),
                offset = scaleConfig.headerOffset,
                chartMaxHeight = viewport.height - offset;

            $scope.chartStyle = 'height: ' + chartMaxHeight + 'px; max-height: ' + chartMaxHeight + 'px;';
        });
    });
})();
