(function () {
    'use strict';

    var app = angular.module('scaleApp', [
        'ngCookies',
        'ngResource',
        'ngSanitize',
        'ngRoute',
        'emguo.poller',
        'ui.bootstrap',
        'ui.grid',
        'ui.grid.selection',
        'ui.grid.pagination',
        'ui.grid.resizeColumns',
        'cfp.hotkeys'
    ]);

    app.config(function($routeProvider, $resourceProvider, pollerConfig) {
        // stop pollers when route changes
        pollerConfig.stopOnRouteChange = true;
        pollerConfig.smart = true;

        // preserve trailing slashes
        $resourceProvider.defaults.stripTrailingSlashes = false;

        //routing
        $routeProvider
            .when('/', {
                controller: 'ovController',
                templateUrl: 'modules/overview/partials/ovTemplate.html'
            })
            .when('/admin/login',{
                controller: 'adminLoginController',
                templateUrl: 'modules/admin/partials/adminLoginTemplate.html'
            })
            .when('/admin/logout',{
                controller: 'logoutController',
                templateUrl: 'modules/admin/partials/adminLoginTemplate.html'
            })
            .when('/about', {
                controller: 'aboutController',
                templateUrl: 'modules/about/partials/aboutTemplate.html'
            })
            .when('/feed', {
                controller: 'feedDetailsController',
                templateUrl: 'modules/feed/partials/feedDetailsTemplate.html',
                reloadOnSearch: false
            })
            .when('/feed/ingests', {
                controller: 'ingestRecordsController',
                templateUrl: 'modules/feed/partials/ingestRecordsTemplate.html',
                reloadOnSearch: false
            })
            .when('/metrics', {
                controller: 'metricsController',
                templateUrl: 'modules/metrics/partials/metricsTemplate.html',
                reloadOnSearch: false
            })
            .when('/nodes', {
                controller: 'nodesController',
                templateUrl: 'modules/nodes/partials/nodesTemplate.html'
            })
            .when('/nodes/:id', {
                controller: 'nodeDetailsController',
                templateUrl: 'modules/nodes/partials/nodeDetailsTemplate.html'
            })
            .when('/queue', {
                controller: 'queueController',
                templateUrl: 'modules/queue/partials/queueTemplate.html'
            })
            .when('/queue/running', {
                controller: 'queueRunningController',
                templateUrl: 'modules/queue/partials/queueRunningTemplate.html'
            })
            .when('/queue/depth', {
                controller: 'queueDepthDetailController',
                templateUrl: 'modules/queue/partials/queueDepthDetailTemplate.html'
            })
            .when('/recipes', {
                controller: 'recipesController',
                templateUrl: 'modules/recipes/partials/recipesTemplate.html'
            })
            .when('/recipes/recipe/:id', {
                controller: 'recipeDetailsController',
                templateUrl: 'modules/recipes/partials/recipeDetailsTemplate.html'
            })
            .when('/recipes/types/:id?', {
                controller: 'recipeTypesController',
                templateUrl: 'modules/recipes/partials/recipeTypesTemplate.html'
            })
            .when('/recipes/builder', {
                controller: 'recipeEditorController',
                templateUrl: 'modules/recipes/partials/recipeEditorTemplate.html'
            })
            .when('/recipes/builder/:id', {
                controller: 'recipeEditorController',
                templateUrl: 'modules/recipes/partials/recipeEditorTemplate.html'
            })
            .when('/jobs', {
                controller: 'jobsController',
                templateUrl: 'modules/jobs/partials/jobsTemplate.html'
            })
            .when('/jobs/job/:id', {
                controller: 'jobDetailController',
                templateUrl: 'modules/jobs/partials/jobDetailTemplate.html'
            })
            .when('/jobs/types/:id?', {
                controller: 'jobTypesController',
                templateUrl: 'modules/jobs/partials/jobTypesTemplate.html'
            })
            .when('/jobs/executions', {
                controller: 'jobExecutionsController',
                templateUrl: 'modules/jobs/partials/jobExecutionsTemplate.html'
            })
            .when('/jobs/executions/:id', {
                controller: 'jobExecutionDetailController',
                templateUrl: 'modules/jobs/partials/jobExecutionDetailTemplate.html'
            })
            .otherwise({
                redirectTo: '/'
            });
    })
    .value('moment', window.moment)
    .value('localStorage', window.localStorage);
})();

(function () {
    'use strict';

    angular.module('scaleApp').factory('pollerFactory', function (poller) {
        return {
            newPoller: function (resource, interval) {
                return poller.get(resource, {
                    delay: interval,
                    catchError: true
                });
            }
        }
    });
})();
(function () {
    'use strict';

    angular.module('scaleApp').controller('aboutController', function($scope, $location, $window, navService) {
        var initialize = function() {
            navService.updateLocation('about');
        };
        initialize();
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').controller('adminLoginController', function ($timeout, $rootScope, $location, userService) {

        var initialize = function () {
            $rootScope.user = userService.getUserCreds();
            if(!$rootScope.user){
                $rootScope.user = userService.login('admin');
            }

            console.log($rootScope.user);

            $timeout(function(){
                // Any code in here will automatically have an $scope.apply() run afterwards
                $location.path("/");
            });
        };

        initialize();
    });
})();
(function () {
    'use strict';

    angular.module('scaleApp').controller('logoutController', function ($timeout, $rootScope, $location, userService) {

        var initialize = function () {
            userService.logout();
            $timeout(function(){
                // Any code in here will automatically have an $scope.apply() run afterwards
                $location.path("/");
            });
        };

        initialize();
    });
})();
(function () {
    'use strict';

    angular.module('scaleApp').controller('aisDonutController', function($scope, $element, scaleConfig) {
        var chart = null;

        var genChart = function () {
            if (chart) {
                //chart.data()
                //$scope.colData
                var oldData = [],
                    removeIds = [];

                // reassemble currently displayed data to match $scope.colData
                _.forEach(chart.data(), function (d) {
                    oldData.push([d.values[0].id, d.values[0].value]);
                });

                // determine which elements to remove
                _.forEach(oldData, function (od) {
                    var keep = _.find($scope.colData, function (cd) {
                        return cd[0] === od[0];
                    });
                    if (!keep) {
                        removeIds.push(od[0]);
                    }
                });

                // update chart
                //console.log(JSON.stringify($scope.colData));
                //console.log(JSON.stringify(removeIds));
                chart.load({
                    columns: $scope.colData,
                    unload: removeIds
                });
            } else {
                chart = c3.generate({
                    bindto: $element[0],
                    data: {
                        columns: $scope.colData,
                        type: $scope.type,
                        colors: {
                            down: scaleConfig.colors.chart_red,
                            warning: scaleConfig.colors.chart_yellow,
                            up: scaleConfig.colors.chart_green,
                            Completed: scaleConfig.colors.chart_green,
                            Done: '#3681bf',
                            Queue: scaleConfig.colors.chart_yellow,
                            Failed: scaleConfig.colors.chart_red,
                            Algorithm: '#444',
                            Data: '#888',
                            System: '#ccc',
                            Offline: scaleConfig.colors.chart_red,
                            'High Failure Rate': scaleConfig.colors.chart_orange,
                            Paused: scaleConfig.colors.chart_yellow
                        }
                    },
                    transition: {
                        duration: 700
                    },
                    pie: {
                        label: {
                            format: d3.format(',')
                        }
                    },
                    donut: {
                        label: {
                            format: $scope.showLabel ? d3.format(',') : function () {
                                return '';
                            }
                        },
                        width: $scope.width,
                        title: $scope.name
                    },
                    tooltip: {
                        format: {
                            value: d3.format(',')
                        }
                    },
                    size: {
                        height: $scope.size || 320
                    }
                });
            }
            $element[0].style.position = 'static';
        };

        var initColumnData = function(){
            $scope.colData = [];
            $scope.data.forEach(function(obj){
                $scope.colData.push([obj.status,obj.count]);
            });
        };

        var initialize = function() {
            initColumnData();
            genChart();
        };

        $scope.$watch('data', function (data) {
            if (data) {
                if (data.length > 0) {
                    initialize();
                } else {
                    $($element[0]).empty();
                }
            }
        });
    });
})();
(function () {
    'use strict';

    angular.module('scaleApp').directive('aisDonut', function () {
        /**
         * Usage: <ais-donut data="nodeCounts" />
         */
        return {
            controller: 'aisDonutController',
            restrict: 'E',
            scope: {
                data: '=',
                type: '=',
                size: '=',
                showLabel: '=',
                width: '=',
                name: '='
            }
        };
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').controller('aisGaugeController', function($scope, $element, scaleConfig) {
        var showLabel = $scope.showLabel || true;
        var chart = null;
        var genChart = function () {
            if (chart) {
                chart.load({
                    columns: $scope.data
                });
            } else {
                chart = c3.generate({
                    bindto: $element[0],
                    data: {
                        columns: $scope.data,
                        type: 'gauge'
                    },
                    transition: {
                        duration: 700
                    },
                    gauge: {
                        width: $scope.width || 25,
                        label: {
                            format: function (ratio, value) {
                                return showLabel ? (value * 100).toFixed(2) + '%' : '';
                            }
                        }
                    },
                    color: {
                        pattern: [scaleConfig.colors.chart_red, scaleConfig.colors.chart_orange, scaleConfig.colors.chart_yellow, scaleConfig.colors.chart_green],
                        threshold: {
                            values: [30, 60, 90, 100]
                        }
                    },
                    interaction: {
                        enabled: false
                    }
                });
            }
        };

        var initialize = function() {
            genChart();
            $('.c3-gauge-value').attr('dy', '-1.6em');
        };

        $scope.$watch('data', function (data) {
            if (data) {
                if (data.length > 0) {
                    initialize();
                }
            }
        });
    });
})();
(function () {
    'use strict';

    angular.module('scaleApp').directive('aisGauge', function () {
        /**
         * Usage: <ais-gauge data="nodeCounts" />
         */
        return {
            controller: 'aisGaugeController',
            restrict: 'E',
            scope: {
                data: '=',
                width: '=',
                showLabel: '='
            }
        };
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').directive('aisHealth', function () {
        /**
         * Usage: <ais-health data="nodeCounts" />
         */
        return {
            controller: 'aisHealthController',
            templateUrl: 'modules/charts/healthTemplate.html',
            restrict: 'E',
            scope: {
                name: '=',
                data: '=',
                scale: '=',
                errorLabel: '=',
                type: '='
            }
        };
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').controller('aisHealthController', function ($scope, gaugeFactory) {
        var gauge = null,
            initialized = false;

        var initialize = function () {
            initialized = true;
            var scale = $scope.scale || 1;
            //$scope.gaugeSize = 150 * scale;
            //$scope.gaugeWidth = 25 * scale;
            $scope.donutSize = 275 * scale;
            $scope.donutWidth = 25 * scale;
            //gauge = gaugeFactory.createGauge($scope.type, 'Failure Rate')
        };

        /*var redrawGauge = function () {
            if (gauge) {
                gauge.redraw($scope.data.gaugeData);
            }
        };*/

        $scope.$watch('data', function (data) {
            if (data) {
                if (_.keys(data).length > 0) {
                    if (!initialized) {
                        initialize();
                    }
                    //redrawGauge();
                }
            }
        });
    });
})();
'use strict';

angular.module('scaleApp').controller('aisRadialPercentageController', function($scope, $element, scaleConfig) {
    var isInitialized = false,
        foreground = '',
        text = '',
        arcTween = '',
        textTween = '';

    var getForeground = function () {
        var value = parseFloat($scope.percentage);
        if (value >= 75) {
            return scaleConfig.colors.chart_green;
        } else if (value < 75 && value >= 50) {
            return scaleConfig.colors.chart_yellow;
        } else {
            return scaleConfig.colors.chart_red;
        }
    };

    var initialize = function() {
        // handle input either .83 or 83
        var percentage = $scope.percentage || 0;
        if (percentage > 1) {
            percentage /= 100;
        }

        // size the chart to the parent container. It's square, so take the
        // smaller of width/height
        var size = $element[0].parentNode.clientWidth;
        if ($element[0].parentNode.clientHeight < size) {
            size = $element[0].parentNode.clientHeight;
        }


        var duration = 1000;
        var formatPercent = d3.format('.0%');

        var arc = d3.svg.arc()
            .startAngle(0)
            .outerRadius(size * 0.95 / 2)
            .innerRadius(size * 0.80 / 2);

        var svg = d3.select($element[0]).append('svg').attr({
            width: size,
            height: size
        }).append('g').attr({
            'transform': 'translate(' + size / 2 + ',' + size / 2 + ')',
            'class': 'aisRadial'
        });

        var meter = svg.append('g').attr({
            'transform': 'rotate(180)'
        });
        meter.append('path')
            .datum({
                endAngle: (2 * Math.PI),
            })
            .attr('class', 'background')
            .attr('d', arc);

        foreground = meter.append('path')
            .datum({
                endAngle: 0
            })
            .attr({
                'd': arc
            })
            .style('fill', function () {
                return getForeground();
            });

        text = svg.append('text')
            .datum({
                percentage: 0
            })
            .attr('text-anchor', 'middle')
            .attr('dy', '.35em');


        textTween = function(transition, newPercentage) {
            transition.attrTween('text', function(d) {
                if (typeof d === 'undefined') {
                    d = 0;
                }
                var i = d3.interpolate(d.percentage, newPercentage);
                return function(t) {
                    d.percentage = i(t);
                    text.text(formatPercent(i(t)));
                    return t;
                }
            });
        };
        arcTween = function(transition, newAngle) {
            transition.attrTween('d', function(d) {
                var i = d3.interpolate(d.endAngle, newAngle);
                return function(t) {
                    d.endAngle = i(t);
                    return arc(d);
                };
            });
        };

        isInitialized = true;

        redraw(percentage);

        // get progress...

        //foreground.attr('d', arc.endAngle((Math.PI * 2) * 0.83));
        //text.text(formatPercent(percentage));
    };

    var redraw = function (value) {
        if (isInitialized) {
            var percentage = value;
            if (percentage > 1) {
                percentage /= 100;
            }
            //console.log('Setting percentage to: ' + percentage);

            //foreground.transition().duration(5000).attr('d', arc);
            foreground.transition().duration(1000)
                .style('fill', function () {
                    return getForeground();
                })
                .call(arcTween, (Math.PI * 2) * percentage);
            //text.text(formatPercent(percentage));
            text.transition().duration(1000).call(textTween, percentage);
        }
    };

    $scope.$watch('percentage', function(value) {
        if (value && !isInitialized) {
            initialize();
        } else {
            redraw(value);
        }
    })
});

'use strict';

angular.module('scaleApp').directive('aisRadialPercentage', function () {

    /**
     * Usage: <ais-radial-percentage percentage="83"></ais-radial-percentage>
     */
    return {
        controller: 'aisRadialPercentageController',
        restrict: 'E',
        scope: {
            percentage: '@'
        }
    };

});

/**
 * System Overview Chart for Scale
 * Shows a large chart containing information on several system
 * components (nodes, feed, jobs, queue). Chart components configured
 * with the $scope.components variable.
 */
angular.module('scaleApp').controller('aisScaleOverviewController', function($scope, $element, $interval, $q) {

    'use strict';

    $scope.components = [{
        'id': 'feed',
        'name': 'Feed Status',
        'type': 'timeline',
        'url': 'modules/charts/asoc.data.feed.json',
        'height': 50
    }, {
        'id': 'nodes',
        'name': 'Node Health',
        'type': 'bar',
        'url': 'modules/charts/asoc.data.nodes2.json',
        'height': 50
    }, {
        'id': 'jobs',
        'name': 'Job Status',
        'type': 'bar',
        'url': 'modules/charts/asoc.data.jobs.json',
        'height': 50
    }, {
        'id': 'queues',
        'name': 'Queue Size',
        'type': 'line',
        'url': 'modules/charts/asoc.data.queues.json',
        'height': 175
    }];

    $scope.chart = {
        'width': 0,
        'height': 0
    };

    var asoc_insertTextBackground = function(textEl, layer) {
      var bbox = textEl.node().getBBox();
      var padding = 3;

      var rect = layer.insert('rect', 'text')
          .attr('x', bbox.x - padding)
          .attr('y', bbox.y - padding)
          .attr('width', bbox.width + (padding*2))
          .attr('height', bbox.height + (padding*2))
          .style('fill', 'gray')
          .style('fill-opacity', 0.5);
    };

    var asoc_initBackground = function() {
        // add startHeight to each component so we know where to draw
        // the axis lines (and where to draw the rects for the data later).
        var numComponents = $scope.components.length;
        var currentHeight = 1; // should set to .aisScaleOverview.background.stroke-width
        var i, height;
        for (i = 0; i < numComponents; i++) {
            height = $scope.chart.height - currentHeight;
            $scope.components[i].startHeight = height;
            currentHeight += $scope.components[i].height;
        }

        // Initialize the timelines
        $scope.timelines = [
            {'time': '12am'},
            {'time': '3am'},
            {'time': '6am'},
            {'time': '9am'},
            {'time': '12pm'},
            {'time': '3pm'},
            {'time': '6pm'},
            {'time': '9pm'},
            {'time': '12am'}
        ];
        var currentWidth = 0;
        var width;
        var numTimelines = $scope.timelines.length;
        for (i = 0; i < numTimelines; i++) {
            width = currentWidth;
            if (i === 0) {
                width += 1;
            } else if (i === (numTimelines - 1)) {
                width -= 1;
            }
            $scope.timelines[i].linePos = width;
            $scope.timelines[i].txtPos = width + 5;
            if (i === (numTimelines - 1)) {
                // Flip the last 12am to the left side of the line
                $scope.timelines[i].txtPos = width - 40;
            }
            currentWidth += ($scope.chart.width / (numTimelines - 1));
        }
    };

    var asoc_drawTimeline = function(data, opts) {
        var svg = d3.select($element[0]).select('svg');
        var lyr = svg.select(opts.layerSelector);

        var minTime = moment('00:00', 'HH:mm').unix();
        var maxTime = moment('24:00', 'HH:mm').unix();

        var scale = d3.scale.linear()
            .domain([minTime, maxTime])
            .range([0, $scope.chart.width]);

            lyr.selectAll('rect')
                .data(data.events)
                .enter().append('rect')
                .attr('class', function(d, i) {
                    return 'statusbar ' + d.status;
                })
                .attr('x', function(d, i) {
                    return scale(moment(d.start, 'HH:mm').unix());
                })
                .attr('y', opts.y - opts.lineheight)
                .attr('width', function(d, i) {
                    // subtract the start from the end since we aren't
                    // starting from zero
                    var e = moment(d.end, 'HH:mm').unix();
                    var s = moment(d.start, 'HH:mm').unix();
                    return scale(e) - scale(s);
                })
                .attr('height', opts.lineheight)
                .on('mouseover', function(d, i) {
                    console.log('Status: ' + d.status);
                });

            var txt = lyr.append('text')
                  .text(opts.name)
                  .attr({
                      'x': 5,
                      'y': opts.y - 3
                  });

            asoc_insertTextBackground(txt, lyr);

    };

    var asoc_drawBar = function(data, opts) {
        var svg = d3.select($element[0]).select('svg');
        var lyr = svg.select(opts.layerSelector);

        var minTime = moment('00:00', 'HH:mm');
        var maxTime = moment('24:00', 'HH:mm');

        var xscale = d3.scale.linear()
            .domain([minTime.unix(), maxTime.unix()])
            .range([0, $scope.chart.width]);

        var first = data.events[0];
        var yscale = d3.scale.linear()
            .domain([0, first.up + first.down + first.warning])
            .range([0, opts.lineheight]);

        var w = $scope.chart.width / data.events.length;

        // See http://stackoverflow.com/questions/21098230/adding-multiple-rect-per-data-element-in-d3
        // for an explaination... needed a way to draw multiple rect elements
        // per data element.
        lyr.selectAll('g')
            .data(data.events)
            .enter().append('g')
            .selectAll('rect')
            .data(function(d) {
                //console.log('Data on ' + JSON.stringify(d));
                return [{
                    'status': 'up',
                    'count': d.up,
                    'time': d.time
                }, {
                    'status': 'warning',
                    'count': d.warning,
                    'time': d.time
                }, {
                    'status': 'down',
                    'count': d.down,
                    'time': d.time
                }];
            })
            .enter().append('rect')
            .attr('class', function(d, i) {
                return 'statusbar ' + d.status;
            })
            .attr('x', function(d, i) {
                return xscale(moment(d.time, 'HH:mm').unix());
            })
            .attr('y', function(d, i) {
                if (d.status === 'down') {
                    // go from the bottom
                    return opts.y - yscale(d.count);
                }
                else if (d.status === 'warning') {
                    // shit, have to lookup where to start the rect
                    var down = this.parentElement.__data__.down;
                    return opts.y - yscale(down) - yscale(d.count);
                }
                // go from the top
                return opts.y - opts.lineheight;
            })
            .attr('width', w)
            .attr('height', function(d, i) {
                var h = yscale(d.count);
                return h;
            })
            .on('mouseover', function(d, i) {
                console.log('Status: ' + JSON.stringify(d));
            });

        var txt = lyr.append('text')
            .text(opts.name)
            .attr({
                'x': 5,
                'y': opts.y - 3
            });
        asoc_insertTextBackground(txt, lyr);
    };

    var asoc_drawline = function(data, opts) {
        console.log('Drawing line chart with options: ' + JSON.stringify(opts));

        var svg = d3.select($element[0]).select('svg');
        var lyr = svg.select(opts.layerSelector);

        var minTime = moment('00:00', 'HH:mm');
        var maxTime = moment('24:00', 'HH:mm');

        var xscale = d3.scale.linear()
            .domain([minTime.unix(), maxTime.unix()])
            .range([0, $scope.chart.width]);

        var yscale = d3.scale.linear()
            .domain([0, d3.max(data.events, function(d) {
                //return d3.max([d.up, d.down, d.warning]);
                return d.up;
            })])
            .range([0, opts.lineheight]);

        console.log('yscale domain: ' + JSON.stringify(yscale.domain()));

        // done
        lyr.append('path')
            .datum(data.events)
            .attr('class', 'area up')
            .attr('d', d3.svg.area()
                .x(function(d) {
                    return xscale(moment(d.time, 'HH:mm').unix());
                })
                .y0(opts.y)
                .y1(function(d) {
                    return opts.y - yscale(d.up);
                })
            );

        // warning
        lyr.append('path')
            .datum(data.events)
            .attr('class', 'area warning')
            .attr('d', d3.svg.area()
                .x(function(d) {
                    return xscale(moment(d.time, 'HH:mm').unix());
                })
                .y0(opts.y)
                .y1(function(d) {
                    return opts.y - yscale(d.warning);
                })
            );

        // error
        lyr.append('path')
            .datum(data.events)
            .attr('class', 'area down')
            .attr('d', d3.svg.area()
                .x(function(d) {
                    return xscale(moment(d.time, 'HH:mm').unix());
                })
                .y0(opts.y)
                .y1(function(d) {
                    return opts.y - yscale(d.down);
                })
            );
        var txt = lyr.append('text')
            .text(opts.name)
            .attr({
                'x': 5,
                'y': opts.y - 3
            });
        asoc_insertTextBackground(txt, lyr);
    };

    var asoc_loadData = function(url) {
        var deferred = $q.defer();
        d3.json(url, function(data) {
            deferred.resolve(data);
        });
        return deferred.promise;
    };

    var asoc_drawComponent = function(component, ypos) {
        console.log('Drawing component ' + component.id);
        asoc_loadData(component.url).then(function(data) {
            console.log('Drawing ' + component.id + ' at ' + ypos);
            if (component.type === 'bar') {
                asoc_drawBar(data, {
                    'name': component.name,
                    'y': ypos,
                    'lineheight': component.height - 10,
                    'layerSelector': '.lyr-' + component.id
                });
            }
            else if (component.type === 'line') {
                asoc_drawline(data, {
                    'name': component.name,
                    'y': ypos,
                    'lineheight': component.height,
                    'layerSelector': '.lyr-' + component.id
                });
            }
            else {
                asoc_drawTimeline(data, {
                    'name': component.name,
                    'y': ypos,
                    'lineheight': component.height - 10,
                    'layerSelector': '.lyr-' + component.id
                });
            }
        });
    };


    var asoc_generatedata = function() {
        var startTime = moment('00:00', 'HH:mm');
        var stopTime = moment('24:00', 'HH:mm');
        var curTime = startTime;
        var numNodes = 3000;
        var data = [];
        var r1, r2, r3 = 0;
        while (curTime.isBefore(stopTime)) {
            console.log('Generating Data for time: ' + curTime.toISOString());
            r1 = Math.floor(Math.random() * 10);
            r2 = Math.floor(Math.random() * 50);
            r3 = Math.floor(Math.random() * 200) + 50;
            data.push({
                'time': curTime.toISOString(),
                'up': r3,
                'warning': r2,
                'down': r1
            });

            curTime.add('5', 'minutes');
        }

        console.log('Generated data: ' + JSON.stringify(data));
        return data;
    };

    var asoc_drawNowMarker = function() {
        var svg = d3.select($element[0]).select('svg');
        var lyr = svg.select('.layer-now');

        var minTime = moment('00:00', scaleConfig.dateFormats.hour_minute);
        var maxTime = moment('24:00', scaleConfig.dateFormats.hour_minute);

        var xscale = d3.scale.linear()
            .domain([minTime.unix(), maxTime.unix()])
            .range([0, $scope.chart.width]);

        $scope.now = {
            'x': xscale($scope.currentTime.unix()),
            'label': $scope.currentTime.toISOString(),
        };

        var tt = d3.select($element[0]).select('.tooltip');
        tt.style({
            'top': '30px',
            'left': (xscale($scope.currentTime.unix()) + 14) + 'px',
            'opacity': 1
        });
    };

    var asoc_setupTime = function() {
        $scope.currentTime = moment();
        var timeUpdater = $interval(function() {
            $scope.currentTime = moment();
        }, 10 * 1000); // update every 10 seconds

        // Stop updating percentage when user leaves the stats page
        $scope.$on('$destroy', function() {
            if (angular.isDefined(timeUpdater)) {
                $interval.cancel(timeUpdater);
                timeUpdater = undefined;
            }
        });

        $scope.$watch('currentTime', function() {
            asoc_drawNowMarker();
        });
    };

    var initialize = function() {
        // size the chart to the parent container.
        var width = $element[0].parentNode.clientWidth;
        var height = $element[0].parentNode.clientHeight;

        $scope.chart = {
            'width': width,
            'height': height
        };

        asoc_initBackground();

        var len = $scope.components.length;
        var i, ypos;
        var currentHeight = 0;
        for (i = 0; i < len; i++) {
            ypos = height - (currentHeight + 1);
            asoc_drawComponent($scope.components[i], ypos);
            currentHeight = currentHeight + $scope.components[i].height;
        }

        asoc_setupTime();
        //asoc_drawNowMarker();
        //asoc_generatedata();

    };
    initialize();

});

/**
 * <ais-scale-overview />
 */
angular.module('scaleApp').directive('aisScaleOverview', function () {

    'use strict';

    /**
     * Usage: <ais-scale-overview data="dater" />
     */
    return {
        controller: 'aisScaleOverviewController',
        templateUrl: 'modules/charts/scaleOverviewTemplate.html',
        restrict: 'E',
        scope: {
            data: '='
        }
    };

});

(function () {
    'use strict';

    angular.module('scaleApp').controller('aisDataFeedController', function ($scope, scaleConfig, queueService, scaleService) {
        $scope.days = [];
        $scope.hours = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23];
        $scope.values = {};
        var processNewFeed = function(){
            var currentDay = moment.utc();
            $scope.days = [];
            var day = '';
            if($scope.feed){
                _.forEach($scope.feed.values, function(val){
                    var valday = moment.utc(val.time).format(scaleConfig.dateFormats.day)
                    var valhour = moment.utc(val.time).hour();
                    var id = valday + '_' + valhour;
                    $scope.values[id] = val;
                    if(valday !== day){
                        day = valday;
                        $scope.days.push(valday);
                    }
                });
                buildTable();
            }
        };

        var buildTable = function () {
            var currDay = moment().utc().format(scaleConfig.dateFormats.day);
            var currHour = moment().utc().hour();

            var table_html = '<div class="table-responsive"><table>';
            table_html += '<tr><th>Hour (UTC)</th>';
            for(day in $scope.days){
                table_html += '<td class="day-label" title="' + $scope.days[day] + '"><div class="day-of-week">' + scaleService.getDayString(moment($scope.days[day]).day()) + '</div>' + moment($scope.days[day]).format('MM/DD') + '</td>';
            }
            table_html += '</tr>';
            for(var hour in $scope.hours){
                hour = 23-hour;
                table_html += '<tr>';
                table_html += '<th title="' + $scope.hours[hour] + ':00">' + $scope.hours[hour] + '</th>';

                for(var day in $scope.days){
                    var key =  $scope.days[day] + '_' + $scope.hours[hour];
                    var files = $scope.values[key].files;
                    var size = $scope.values[key].size;
                    var cls = 'good';
                    if($scope.days[day] === currDay){
                        if($scope.hours[hour] === currHour){
                            cls = 'current';
                        }
                        else if($scope.hours[hour] > currHour) {
                            cls = 'future';
                        }
                    }
                    if(files === 0 && size === 0 && cls !== 'current' && cls !== 'future'){
                        cls = 'unknown';
                    }
                    //console.log(key);
                    table_html += '<td id="' + key + '" title="' + $scope.days[day] + ' ' + $scope.hours[hour] + ':00">';
                    if(cls === 'future'){
                        //table_html += '<span class="' + cls + '" id="span_' + $scope.days[day] + '_' + $scope.hours[hour] + '" style="display: block;"><div class="file-count">&nbsp;</div><div class="file-size">&nbsp;</div></span></td>';
                        table_html += '<span class="' + cls + '" id="span_' + $scope.days[day] + '_' + $scope.hours[hour] + '" style="display: block;">&nbsp;</span></td>';
                    }
                    else{
                        //table_html += '<span class="' + cls + '" id="span_' + $scope.days[day] + '_' + $scope.hours[hour] + '" style="display: block;"><div class="file-count">' + files + '</div><div class="file-size">' + scaleService.calculateFileSizeFromBytes(size,1) + '</div></span></td>';
                        //table_html += '<span class="' + cls + '" id="span_' + $scope.days[day] + '_' + $scope.hours[hour] + '" style="display: block;"><span class="file-count">' + files + '</span> / <span class="file-size">' + scaleService.calculateFileSizeFromBytes(size,1) + '</span></span></td>';
                        table_html += '<span class="' + cls + '" id="span_' + $scope.days[day] + '_' + $scope.hours[hour] + '" style="display: block;">' + scaleService.calculateFileSizeFromBytes(size,1) + ' / ' + files + '</span></td>';
                    }

                }
                table_html += '</tr>';
            }
            table_html += '</table></div>';
            $('#history').html(table_html);
        };

        var initialize = function(){

            $scope.$watch('feed', function (value) {
                if($scope.feed){
                    processNewFeed();
                }
            });
        };

        initialize();
    }).directive('aisDataFeed', function () {
        /**
         * Usage: <ais-queue-depth data="dater" ticks="10" />
         */
        return {
            controller: 'aisDataFeedController',
            templateUrl: 'modules/charts/dataFeed/dataFeedTemplate.html',
            restrict: 'E',
            scope: {
                feed: '=' // Feed data
            }
        };

    });
})();

/**
 * <ais-scale-recipe-viewer />
 */
(function () {
    angular.module('scaleApp').controller('aisTimelineDirectiveController', function ($scope, $element, scaleConfig) {

        var gantt = null;

        $element[0].onresize = function(){
            console.log('element resize');
        };

        var initialize = function() {
            $scope.$watch('tasks', function (value) {
                drawTimeline();
            });
        };

        var drawTimeline = function(){
            if($scope.tasks && $scope.tasks.length > 0){
                $scope.tasks.sort(function(a, b) {
                    return a[$scope.ended] - b[$scope.ended];
                });

                $scope.taskNames = _($scope.tasks).pluck('taskName').uniq().value();
                var height = $scope.taskNames.length * 30 + 20;

                var width = $element[0].clientWidth;
                if (!width || width === 0) { width = 600; }


                $scope.tasks.sort(function(a, b) {
                    return a[$scope.started] - b[$scope.started];
                });
                var minDate = $scope.tasks[0][$scope.started];
                var maxDate = $scope.tasks[$scope.tasks.length - 1][$scope.ended];
                var daysDiff = moment.utc(maxDate).diff(moment.utc(minDate),'days');
                var format = '%H:%M:%S.%m';
                if(daysDiff > 0){
                    format = "%m/%d/%y %H:%M";
                }

                gantt = d3.gantt().renderTo("#ais-timeline").taskTypes($scope.taskNames).taskStatus(scaleConfig.taskStatusStyles).tickFormat(format).begin($scope.started).ended($scope.ended).height(height).width(width);

                gantt.timeDomainMode("fit");

                gantt($scope.tasks);

            }
        };

        function getend() {
            var lastend = Date.now();
            if ($scope.tasks.length > 0) {
                lastend = $scope.tasks[$scope.tasks.length - 1][$scope.ended];
            }

            return lastend;
        };

        $scope.formatDate = function(date){
            if(date){
                return moment.utc(date).toISOString();
            }
            else {
                return date;
            }
        };
        initialize();

    }).directive('aisTimeline', function () {
        'use strict';
        /**
         * Usage: <ais-timeline />
         */
        return {
            controller: 'aisTimelineDirectiveController',
            templateUrl: 'modules/charts/timeline/timelineDirectiveTemplate.html',
            restrict: 'E',
            scope: {
                tasks: '=',
                started: '=',
                ended: '='
            }
        };

    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').directive('aisJobLoad', function () {
        /**
         * Usage: <ais-queue-depth data="dater" ticks="10" />
         */
        return {
            controller: 'aisJobLoadController',
            templateUrl: 'modules/charts/jobLoad/jobLoadTemplate.html',
            restrict: 'E',
            scope: {
                showFilter: '=', // show time range filter UI
                cullLegend: '=', // only show job types in legend whose value is > 0
                hideTitle: '=',
                autoHeight: '='
            }
        };

    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').controller('aisJobLoadController', function ($scope, scaleConfig, scaleService, queueService) {
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

            queueService.getJobLoad(jobLoadParams).then(null, null, function (result) {
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

        getJobLoad();

        if ($scope.autoHeight) {
            // set chart height
            angular.element(document).ready(function () {
                // set container heights equal to available page height
                var viewport = scaleService.getViewportSize(),
                    offset = scaleConfig.headerOffset,
                    headerOffset = $('.job-load-header').height(),
                    legendOffset = $('.job-load-legend-label').height(),
                    filterOffset = $('.job-load-filter').height(),
                    chartMaxHeight = viewport.height - offset - headerOffset - legendOffset - filterOffset - 5;

                $scope.chartStyle = 'height: ' + chartMaxHeight + 'px; max-height: ' + chartMaxHeight + 'px;';
            });
        }
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').controller('aisHeaderController', function($scope, $element, subnavService) {
        $scope.date = new Date();
        $scope.currentPath = subnavService.getCurrentPath();
    })
    .directive('aisHeader', function () {
        /**
         * Usage: <ais-header name={name}></ais-header>
         */
        return {
            controller: 'aisHeaderController',
            restrict: 'E',
            templateUrl: 'modules/header/headerTemplate.html',
            scope: {
                name: '=',
                hideTitle: '=',
                loading: '=', // optional - will overlay a loading spinner on the page based on the passed-in value
                showSubnav: '=',
                subnavLinks: '='
            }
        };

    });
})();

angular.module('scaleApp').controller('aisHostSummaryController', function($scope, $element, $modal, nodeService, scaleConfig) {
    'use strict';

    $scope.chart = {};

    // Calculates the status of the host given the number of errors and
    // duration since last checkin time.
    $scope.getStatus = function(h) {
        var status = h.checkin_style === 'error' ? 'btn-danger' : 'btn-' + h.checkin_style;
        // if (h.checkin_style > 5) {
        //     status = 'hs-error';
        // }
        // if (h.errors > 0) {
        //     status = 'hs-warning';
        // }
        // if (h.etcheckin > '00:03:00') {
        //     status = 'hs-error';
        // }
        //status += ' hs-hostname';
        return status;
    };

    $scope.modalContent = function (host) {
        console.log(host);
        var margin = {top: 20, right: 20, bottom: 30, left: 50},
            width = $('#' + $scope.name + '-chart-health').width() - margin.left - margin.right,
            height = 200 - margin.top - margin.bottom;

        var x = d3.time.scale.utc()
            .range([0, width]);

        var y = d3.scale.linear()
            .range([height, 0]);

        var xAxis = d3.svg.axis()
            .scale(x)
            .orient('bottom')
            .ticks(9);

        var yAxis = d3.svg.axis()
            .scale(y)
            .orient('left')
            .ticks(5);

        var line = d3.svg.line()
            .x(function(d) { return x(d.date); })
            .y(function(d) { return y(d.successRate); });

        var svg = d3.select('#' + $scope.name + '-chart-health').append('svg')
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom)
            .append('g')
            .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

        nodeService.getNode(host.id).then(function (node) {
            if (node) {
                var data = _.sortBy(node.nodeHistory, 'date'),
                    yMin = Math.floor(d3.min(_.pluck(data, 'successRate')));

                x.domain(d3.extent(data, function(d) { return d.date; }));
                y.domain([yMin > 2 ? yMin - 2 : yMin,100]);

                svg.append('g')
                    .attr('class', 'x axis')
                    .attr('transform', 'translate(0,' + height + ')')
                    .call(xAxis);

                svg.append('g')
                    .attr('class', 'y axis')
                    .call(yAxis)
                    .append('text')
                    .attr('transform', 'rotate(-90)')
                    .attr('y', 6)
                    .attr('dy', '.71em')
                    .style('text-anchor', 'end')
                    .text('Success Rate (%)');

                svg.append('path')
                    .datum(data)
                    .attr('class', 'line')
                    .attr('d', line);
            }
        }).fail(function (error) {
            $scope.status = 'Unable to load node data: ' + error.message;
            console.error($scope.status);
        });
    };

    $scope.showModal = function(host, name){
        var modalInstance = $modal.open({
            animation: $scope.animationsEnabled,
            templateUrl: 'modalContentHosts.html',
            size: 'lg',
            controller: function dialogController($scope, $modalInstance) {
                $scope.host = host;
                $scope.name = name;
            }
        });

        modalInstance.opened.then(function (selectedItem) {
            setTimeout(function () {
                $scope.modalContent($scope.host);
            }, 200);

        });
    };
})
.directive('aisHostSummary', function () {
    'use strict';
    /**
     * Usage: <ais-host-summary host={host}></ais-host-summary>
     */
    return {
        controller: 'aisHostSummaryController',
        restrict: 'E',
        templateUrl: 'modules/hostsummary/hostsummaryTemplate.html',
        scope: {
            host: '=',
            name: '=',
            data: '='
        }
    };

});

(function () {
    'use strict';

    angular.module('scaleApp').controller('navController', function($scope, $location, $window, scaleConfig, navService) {

        $scope.activePage = 'overview';
        $scope.docsUrl = scaleConfig.urls.documentation;

        $scope.goto = function(loc) {
            $location.search('');
            $location.path(loc);
        };

        var locationUpdated = function() {
            $scope.activePage = navService.location;
        };

        var initialize = function() {
            navService.registerObserver(locationUpdated);
        };
        initialize();

    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').directive('scaleNavigation', function () {
        return {
            restrict: 'E',
            templateUrl: 'modules/navigation/partials/navTemplate.html',
            controller: 'navController'
        };
    });
})();

(function () {
    'use strict';
    /**
     * See: http://stackoverflow.com/questions/12576798/angularjs-how-to-watch-service-variables/17558885#17558885
     * Doing things this way so that ssNavbarController can get notified
     * when the location changes. Then, our controllers just need to call into
     * this service to updateLocation.
     *
     * The only thing I don't like about this is that the individual
     * controllers have to call in and tell the ssNavigationService what
     * page they are showing.
     */
    angular.module('scaleApp').service('navService', function ($location) {

        this.location = 'overview'; // where the app starts

        var observers = [];

        this.registerObserver = function(callback) {
            observers.push(callback);
        };

        this.notifyObservers = function() {
            angular.forEach(observers, function(observer) {
                observer();
            });
        };

        this.updateLocation = function(locationIn) {
            this.location = locationIn;
            this.notifyObservers();
        };

    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').service('subnavService', function ($http, scaleConfig) {
        var currentPath = '';

        this.setCurrentPath = function (path) {
            currentPath = path;
        };

        this.getCurrentPath = function () {
            return currentPath;
        };
    });
})();
(function () {
    'use strict';

    angular.module('scaleApp').controller('ovController', function($rootScope, $scope, navService, nodeService, jobService, jobTypeService, statusService, gaugeFactory, scaleConfig, scaleService, schedulerService, userService) {
        $scope.date = new Date();
        $scope.jobError = null;
        $scope.jobErrorStatus = null;
        $scope.loadingJobs = true;
        $scope.jobTypes = [];
        $scope.hourValue = 3;
        $scope.jobData = {
            data: null,
            status: null
        };
        $scope.jobErrorBreakdown = [];
        $scope.status = null;
        $scope.loadingStatus = true;
        $scope.statusError = null;
        $scope.statusErrorStatus = null;
        $scope.masterStatus = '';
        $scope.masterStatusClass = 'alert-success';
        $scope.schedulerStatus = '';
        $scope.schedulerStatusClass = 'alert-success';
        $scope.memCalc = '';
        $scope.diskCalc = '';
        $scope.schedulerIsPaused = false;
        $scope.user = userService.getUserCreds();
        $scope.schedulerContainerClass = $scope.user ? $scope.user.is_admin ? 'col-xs-8 col-lg-10' : 'col-xs-12' : 'col-xs-12';
        $scope.schedulerBtnClass = 'fa-pause';

        $scope.toggleScheduler = function () {
            $scope.schedulerIsPaused = !$scope.schedulerIsPaused;
            var schedulerData = {
                is_paused: $scope.schedulerIsPaused
            };
            schedulerService.updateScheduler(schedulerData).then(function (data) {
                $scope.schedulerStatus = data.is_paused ? 'Paused' : 'Running';
                $scope.schedulerStatusClass = data.is_paused ? 'alert-warning' : 'alert-success';
                $scope.schedulerBtnClass = data.is_paused ? 'fa-play' : 'fa-pause';
            }).catch(function (error) {
                console.log(error);
            });
        };

        var redrawGrid = function () {
            $scope.$broadcast('redrawGrid', $scope.jobData);
        };

        var getJobTypes = function () {
            jobTypeService.getJobTypes().then(null, null, function (data) {
                if (data.$resolved) {
                    $scope.jobError = null;
                    $scope.jobData.data = data.results;
                    redrawGrid();
                } else {
                    if (data.statusText && data.statusText !== '') {
                        $scope.jobErrorStatus = data.statusText;
                    }
                    $scope.jobError = 'Unable to retrieve job types.'
                }
                $scope.loadingJobs = false
            });
        };

        var getStatus = function () {
            var cpuGauge = gaugeFactory.createGauge('cpu', 'CPU', 0, 100, 180),
                memGauge = gaugeFactory.createGauge('memory', 'Memory', 0, 100, 180),
                diskGauge = gaugeFactory.createGauge('disk', 'Disk', 0, 100, 180);

            statusService.getStatus().then(null, null, function (result) {
                if (result.$resolved) {
                    $scope.statusError = null;
                    $scope.status = result;
                    cpuGauge.redraw(result.getCpuUsage());
                    memGauge.redraw(result.getMemUsage());
                    diskGauge.redraw(result.getDiskUsage());
                    $scope.masterStatus = result.master.is_online ? 'Online' : 'Offline';
                    $scope.masterStatusClass = result.master.is_online ? 'alert-success' : 'alert-danger';
                    if (result.scheduler.is_online) {
                        $scope.schedulerStatus = result.scheduler.is_paused ? 'Paused' : 'Running';
                        $scope.schedulerStatusClass = result.scheduler.is_paused ? 'alert-warning' : 'alert-success';
                        $scope.schedulerIsPaused = result.scheduler.is_paused;
                        $scope.schedulerBtnClass = result.scheduler.is_paused ? 'fa-play' : 'fa-pause';
                    } else {
                        $scope.schedulerStatus = result.scheduler.is_paused ? 'Offline; Paused' : 'Offline';
                        $scope.schedulerStatusClass = 'alert-danger';
                        $scope.schedulerIsPaused = result.scheduler.is_paused;
                        $scope.schedulerBtnClass = result.scheduler.is_paused ? 'fa-play' : 'fa-pause';
                    }
                    if (result.resources.scheduled.mem && result.resources.total.mem) {
                        $scope.memCalc = scaleService.calculateFileSizeFromMib(result.resources.scheduled.mem) + ' / ' + scaleService.calculateFileSizeFromMib(result.resources.total.mem);
                    }
                    if (result.resources.scheduled.disk && result.resources.total.disk) {
                        $scope.diskCalc = scaleService.calculateFileSizeFromMib(result.resources.scheduled.disk) + ' / ' + scaleService.calculateFileSizeFromMib(result.resources.total.disk);
                    }
                } else {
                    if (result.statusText && result.statusText !== '') {
                        $scope.statusErrorStatus = result.statusText;
                    }
                    $scope.statusError = 'Unable to retrieve cluster status.';
                }
                $scope.loadingStatus = false;
            });
        };

        $rootScope.$on('jobTypeStatus', function (event, data) {
            $scope.jobData.status = data;
            redrawGrid();
        });

        var initialize = function () {
            getJobTypes();
            getStatus();
            navService.updateLocation('overview');
        };

        initialize();
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').factory('gridFactory', function (uiGridConstants) {

        var getSortConfig = function(orderParam){
            if(orderParam){
                var sortField = orderParam
                var sortDirection = 'asc';
                if(_.startsWith(orderParam, '-')){
                    sortDirection = 'desc';
                    sortField = sortField[0].length === 1 ? sortField.substring(1) : sortField[0].substring(1);
                }
                return {
                    direction: sortDirection,
                    field: sortField
                };
            }
            return {};
        };

        return {
            defaultGridOptions: function () {
                return {
                    enableRowSelection: true,
                    enableRowHeaderSelection: false,
                    enableHorizontalScrollbar: uiGridConstants.scrollbars.NEVER,
                    multiSelect: false,
                    enableFiltering: true,
                    useExternalSorting: true,
                    useExternalFiltering: true,
                    enableSorting: true,
                    minRowsToShow: 17,
                    paginationPageSizes: [25, 50, 75, 100],
                    paginationPageSize: 25,
                    useExternalPagination: true
                }
            },
            applySortConfig: function(columnDefs, gridParams){
                var sortConfig = getSortConfig(gridParams.order);
                if(sortConfig.field){
                    var colDef = _.find(columnDefs, {field: sortConfig.field});
                    if(colDef){
                        colDef.sort = {
                            direction: sortConfig.direction,
                            priority: 1
                        }
                    }
                }
                return columnDefs;
            }
        }
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').directive('aisMultiselect', function () {
        return {
            scope: {
                multiselectDataProvider: '=',
                enableFiltering: '=',
                maxHeight: '=',
                numberDisplayed: '=',
                includeSelectAllOption: '=',
                nonSelectedText: '='
            },
            link: function(scope, element, attributes) {
                element.multiselect({
                    enableFiltering: scope.enableFiltering,
                    enableCaseInsensitiveFiltering: true,
                    maxHeight: scope.maxHeight || 300,
                    numberDisplayed: scope.numberDisplayed || 3,
                    includeSelectAllOption: scope.includeSelectAllOption,
                    nonSelectedText: scope.nonSelectedText || 'None Selected'
                });

                scope.$watchCollection('multiselectDataProvider', function (newValue) {
                    if (newValue) {
                        element.multiselect('dataprovider', newValue);
                    }
                });

                /*
                // Watch for any changes to the length of our select element
                scope.$watch(function () {
                    return element[0];
                }, function (newValue) {
                    debugger;
                    //element.multiselect('setOptions', element[0]);
                    //element.multiselect('rebuild');
                }, true);

                // Watch for any changes from outside the directive and refresh
                scope.$watch(attributes.ngModel, function () {
                    element.multiselect('refresh');
                });
                */
            }
        };
    })
})();

(function () {
    'use strict';

    angular.module('scaleApp').factory('Status', function (StatusMaster, StatusScheduler, StatusResources) {
        var Status = function ($resolved, master, scheduler, queue_depth, resources) {
            this.$resolved = $resolved;
            this.master = StatusMaster.transformer(master);
            this.scheduler = StatusScheduler.transformer(scheduler);
            this.queue_depth = queue_depth;
            this.resources = StatusResources.transformer(resources);
        };

        // public methods
        Status.prototype = {
            getCpuUsage: function () {
                if (this.resources.scheduled.cpus && this.resources.total.cpus) {
                    if (this.resources.total.cpus > 0) {
                        return ((this.resources.scheduled.cpus / this.resources.total.cpus) * 100).toFixed(2);
                    }
                }
                return 0.00;
            },
            getMemUsage: function () {
                if (this.resources.scheduled.mem && this.resources.total.mem) {
                    if (this.resources.total.mem > 0) {
                        return ((this.resources.scheduled.mem / this.resources.total.mem) * 100).toFixed(2);
                    }
                }
                return 0.00;
            },
            getDiskUsage: function () {
                if (this.resources.scheduled.disk && this.resources.total.disk) {
                    if (this.resources.total.disk > 0) {
                        return ((this.resources.scheduled.disk / this.resources.total.disk) * 100).toFixed(2);
                    }
                }
                return 0.00;
            }
        };

        // static methods, assigned to class
        Status.build = function (data) {
            if (data) {
                return new Status(
                    data.$resolved,
                    data.master,
                    data.scheduler,
                    data.queue_depth,
                    data.resources
                );
            }
            return new Status();
        };

        Status.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(Status.build)
                    .filter(Boolean);
            }
            return Status.build(data);
        };

        return Status;
    });
})();
(function () {
    'use strict';
    
    angular.module('scaleApp').factory('StatusMaster', function () {
        var StatusMaster = function (is_online, hostname, port) {
            this.is_online = is_online;
            this.hostname = hostname;
            this.port = port;
        };

        // public methods
        StatusMaster.prototype = {

        };

        // static methods, assigned to class
        StatusMaster.build = function (data) {
            if (data) {
                return new StatusMaster(
                    data.is_online,
                    data.hostname,
                    data.port
                );
            }
            return new StatusMaster();
        };

        StatusMaster.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(StatusMaster.build)
                    .filter(Boolean);
            }
            return StatusMaster.build(data);
        };

        return StatusMaster;
    });
})();
(function () {
    'use strict';

    angular.module('scaleApp').factory('StatusResource', function () {
        var StatusResource = function (cpus, mem, disk) {
            this.cpus = cpus;
            this.mem = mem;
            this.disk = disk;
        };

        // public methods
        StatusResource.prototype = {

        };

        // static methods, assigned to class
        StatusResource.build = function (data) {
            if (data) {
                return new StatusResource(
                    data.cpus,
                    data.mem,
                    data.disk
                );
            }
            return new StatusResource();
        };

        StatusResource.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(StatusResource.build)
                    .filter(Boolean);
            }
            return StatusResource.build(data);
        };

        return StatusResource;
    });
})();
(function () {
    'use strict';

    angular.module('scaleApp').factory('StatusResources', function (StatusResource) {
        var StatusResources = function (total, scheduled, used) {
            this.total = StatusResource.transformer(total);
            this.scheduled = StatusResource.transformer(scheduled);
            this.used = StatusResource.transformer(used);
        };

        // public methods
        StatusResources.prototype = {

        };

        // static methods, assigned to class
        StatusResources.build = function (data) {
            if (data) {
                return new StatusResources(
                    data.total,
                    data.scheduled,
                    data.used
                );
            }
            return new StatusResources();
        };

        StatusResources.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(StatusResources.build)
                    .filter(Boolean);
            }
            return StatusResources.build(data);
        };

        return StatusResources;
    });
})();
(function () {
    'use strict';

    angular.module('scaleApp').factory('StatusScheduler', function () {
        var StatusScheduler = function (is_online, is_paused, hostname) {
            this.is_online = is_online;
            this.is_paused = is_paused;
            this.hostname = hostname;
        };

        // public methods
        StatusScheduler.prototype = {

        };

        // static methods, assigned to class
        StatusScheduler.build = function (data) {
            if (data) {
                return new StatusScheduler(
                    data.is_online,
                    data.is_paused,
                    data.hostname
                );
            }
            return new StatusScheduler();
        };

        StatusScheduler.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(StatusScheduler.build)
                    .filter(Boolean);
            }
            return StatusScheduler.build(data);
        };

        return StatusScheduler;
    });
})();
(function () {
    'use strict';

    angular.module('scaleApp').service('statusService', function ($resource, scaleConfig, poller, pollerFactory, Status) {
        return {
            getStatus: function () {
                var statusResource = $resource(scaleConfig.urls.getStatus()),
                    statusPoller = pollerFactory.newPoller(statusResource, scaleConfig.pollIntervals.status);

                return statusPoller.promise.then(null, null, function (result) {
                    if (result.$resolved) {
                        result = Status.transformer(result);
                        //result = angular.extend(result, returnResult);
                    } else {
                        statusPoller.stop();
                    }
                    return result;
                });
            }
        }
    });
})();
(function () {
    'use strict';

    angular.module('scaleApp').service('scaleService', function (scaleConfig) {
        return {
            calculateFileSizeFromMib: function(num){
                if (num > 0) {
                    if (num < 1024) {
                        return num.toFixed(2) + ' MB';
                    }
                    if (num >= 1024 && num < 1024*1024) {
                        return (num/1024).toFixed(2) + ' GB';
                    }
                    return (num/1024/1024).toFixed(2) + ' TB';
                }
                return num;
            },
            calculateFileSizeFromBytes: function(num,decimals){
                // if(precision){
                //     // round num to specified precision
                //     num = Math.round(num/precision);
                // }
                if (num > 0) {
                    if (num < 1024) {
                        return num.toFixed(decimals) + ' Bytes';
                    }
                    if (num >= 1024 && num < 1024*1024) {
                        return (num/1024).toFixed(decimals) + ' KB';
                    }
                    if (num >= 1024*1024 && num < 1024*1024*1024) {
                        return (num/1024/1024).toFixed(decimals) + ' MB';
                    }
                    if (num >= 1024*1024*1024 && num < 1024*1024*1024*1024) {
                        return (num/1024/1024/1024).toFixed(decimals) + ' GB';
                    }
                    return (num/1024/1024/1024/1024).toFixed(decimals) + ' TB';
                }
                return num;
            },
            getViewportSize: function () {
                var w = window,
                    d = document,
                    e = d.documentElement,
                    g = document.body,
                    x = w.innerWidth || e.clientWidth || g.clientWidth,
                    y = w.innerHeight || e.clientHeight || g.clientHeight;

                return {
                    width: x,
                    height: y
                };
            },
            calculateDuration: function (start, stop, formatStr) {
                var to = moment.utc(stop),
                    from = moment.utc(start),
                    diff = to.diff(from);

                formatStr = formatStr || 'D[d], H[h], M[m], ss';

                return moment.duration(diff, 'milliseconds').format();
            },
            getDayString: function(dayNumber){
                var dayArr = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
                return dayArr[dayNumber];
            }
        }
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').service('userService', function ($rootScope) {
        return {
            getUserCreds: function(){
                var creds = localStorage.getItem('userCreds');
                try {
                    return JSON.parse(creds);
                } catch (e) {
                    console.log('Error parsing user credentials');
                    return creds;
                }
            },
            setUserCreds: function(user){
                if (user !== null) {
                    localStorage.setItem('userCreds', JSON.stringify(user));
                } else {
                    $rootScope.user = null;
                    localStorage.removeItem('userCreds');
                }

            },
            login: function (username) {
                var user = {
                    username: username,
                    is_admin: true
                };
                this.setUserCreds(user);
                return user;
            },
            logout: function() {
                this.setUserCreds(null);
            }
        }
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').service('schedulerService', function ($http, $q, scaleConfig) {
        var getUpdateSchedulerData = function (is_paused) {
            return {
                is_paused: is_paused
            };
        };

        return {
            updateScheduler: function (data) {
                data = data || getUpdateSchedulerData();
                var d = $q.defer();

                $http({
                    url: scaleConfig.urls.updateScheduler(),
                    method: 'PATCH',
                    data: data
                }).success(function (result) {
                    d.resolve(result);
                }).error(function (error) {
                    d.reject(error);
                });

                return d.promise;
            }
        }
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').factory('gaugeFactory', function (scaleConfig) {
        var Gauge = function (placeholderName, configuration)
        {
            this.placeholderName = placeholderName;

            var self = this; // for internal d3 functions

            this.configure = function(configuration)
            {
                this.config = configuration;

                this.config.size = this.config.size * 0.9;

                this.config.radius = this.config.size * 0.97 / 2;
                this.config.cx = this.config.size / 2;
                this.config.cy = this.config.size / 2;

                this.config.min = undefined != configuration.min ? configuration.min : 0;
                this.config.max = undefined != configuration.max ? configuration.max : 100;
                this.config.range = this.config.max - this.config.min;

                this.config.majorTicks = configuration.majorTicks || 5;
                this.config.minorTicks = configuration.minorTicks || 2;

                this.config.greenColor 	= configuration.greenColor || '#8fca0e';
                this.config.yellowColor = configuration.yellowColor || '#ffc317';
                this.config.redColor 	= configuration.redColor || '#f54d36';

                this.config.transitionDuration = configuration.transitionDuration || 500;
            };

            this.render = function()
            {
                this.body = d3.select('#' + this.placeholderName)
                    .append('svg:svg')
                    .attr('class', 'gauge')
                    .attr('width', this.config.size)
                    .attr('height', this.config.size);

                this.body.append('svg:circle')
                    .attr('class', 'outer-circle')
                    .attr('cx', this.config.cx)
                    .attr('cy', this.config.cy)
                    .attr('r', this.config.radius)
                    .style('fill', '#ccc');
                /*.style('stroke', '#000')
                 .style('stroke-width', '0.5px');*/

                this.body.append('svg:circle')
                    .attr('cx', this.config.cx)
                    .attr('cy', this.config.cy)
                    .attr('r', 0.9 * this.config.radius)
                    .style('fill', '#fff')
                    .style('stroke', '#e0e0e0')
                    .style('stroke-width', '2px');

                for (var greenIdx in this.config.greenZones)
                {
                    this.drawBand(this.config.greenZones[greenIdx].from, this.config.greenZones[greenIdx].to, self.config.greenColor);
                }

                for (var yellowIdx in this.config.yellowZones)
                {
                    this.drawBand(this.config.yellowZones[yellowIdx].from, this.config.yellowZones[yellowIdx].to, self.config.yellowColor);
                }

                for (var redIdx in this.config.redZones)
                {
                    this.drawBand(this.config.redZones[redIdx].from, this.config.redZones[redIdx].to, self.config.redColor);
                }

                var fontSize = 0;

                if (undefined != this.config.label)
                {
                    fontSize = Math.round(this.config.size / 9);
                    this.body.append('svg:text')
                        .attr('x', this.config.cx)
                        .attr('y', this.config.cy / 2 + fontSize / 2)
                        .attr('dy', fontSize / 2)
                        .attr('text-anchor', 'middle')
                        .text(this.config.label)
                        .style('font-size', fontSize + 'px')
                        .style('fill', '#333')
                        .style('stroke-width', '0px');
                }

                fontSize = Math.round(this.config.size / 16);
                var majorDelta = this.config.range / (this.config.majorTicks - 1);
                for (var major = this.config.min; major <= this.config.max; major += majorDelta)
                {
                    var minorDelta = majorDelta / this.config.minorTicks,
                        point1 = 0,
                        point2 = 0;
                    for (var minor = major + minorDelta; minor < Math.min(major + majorDelta, this.config.max); minor += minorDelta)
                    {
                        point1 = this.valueToPoint(minor, 0.75);
                        point2 = this.valueToPoint(minor, 0.85);

                        this.body.append('svg:line')
                            .attr('x1', point1.x)
                            .attr('y1', point1.y)
                            .attr('x2', point2.x)
                            .attr('y2', point2.y)
                            .style('stroke', '#666')
                            .style('stroke-width', '1px');
                    }

                    point1 = this.valueToPoint(major, 0.7);
                    point2 = this.valueToPoint(major, 0.85);

                    this.body.append('svg:line')
                        .attr('x1', point1.x)
                        .attr('y1', point1.y)
                        .attr('x2', point2.x)
                        .attr('y2', point2.y)
                        .style('stroke', '#333')
                        .style('stroke-width', '2px');

                    if (major == this.config.min || major == this.config.max)
                    {
                        var point = this.valueToPoint(major, 0.63);

                        this.body.append('svg:text')
                            .attr('x', point.x)
                            .attr('y', point.y)
                            .attr('dy', fontSize / 3)
                            .attr('text-anchor', major == this.config.min ? 'start' : 'end')
                            .text(major)
                            .style('font-size', fontSize + 'px')
                            .style('fill', '#333')
                            .style('stroke-width', '0px');
                    }
                }

                var pointerContainer = this.body.append('svg:g').attr('class', 'pointerContainer');

                var midValue = (this.config.min + this.config.max) / 2;

                var pointerPath = this.buildPointerPath(midValue);

                var pointerLine = d3.svg.line()
                    .x(function(d) { return d.x })
                    .y(function(d) { return d.y })
                    .interpolate('basis');

                pointerContainer.selectAll('path')
                    .data([pointerPath])
                    .enter()
                    .append('svg:path')
                    .attr('d', pointerLine)
                    .style('fill', '#888');

                pointerContainer.append('svg:circle')
                    .attr('cx', this.config.cx)
                    .attr('cy', this.config.cy)
                    .attr('r', 0.07 * this.config.radius)
                    .style('fill', '#888');

                fontSize = Math.round(this.config.size / 10);
                pointerContainer.selectAll('text')
                    .data([midValue])
                    .enter()
                    .append('svg:text')
                    .attr('x', this.config.cx)
                    .attr('y', this.config.size - this.config.cy / 4 - fontSize)
                    .attr('dy', fontSize / 2)
                    .attr('text-anchor', 'middle')
                    .style('font-size', fontSize + 'px')
                    .style('fill', '#000')
                    .style('stroke-width', '0px');

                this.redraw(this.config.min, 0);
            };

            this.buildPointerPath = function(value)
            {
                var delta = this.config.range / 13;

                var head = valueToPoint(value, 0.85);
                var head1 = valueToPoint(value - delta, 0.12);
                var head2 = valueToPoint(value + delta, 0.12);

                var tailValue = value - (this.config.range * (1/(270/360)) / 2);
                var tail = valueToPoint(tailValue, 0.28);
                var tail1 = valueToPoint(tailValue - delta, 0.12);
                var tail2 = valueToPoint(tailValue + delta, 0.12);

                return [head, head1, tail2, tail, tail1, head2, head];

                function valueToPoint(value, factor)
                {
                    var point = self.valueToPoint(value, factor);
                    point.x -= self.config.cx;
                    point.y -= self.config.cy;
                    return point;
                }
            };

            this.drawBand = function(start, end, color)
            {
                if (0 >= end - start) return;

                this.body.append('svg:path')
                    .style('fill', color)
                    .attr('d', d3.svg.arc()
                        .startAngle(this.valueToRadians(start))
                        .endAngle(this.valueToRadians(end))
                        .innerRadius(0.65 * this.config.radius)
                        .outerRadius(0.85 * this.config.radius))
                    .attr('transform', function() { return 'translate(' + self.config.cx + ', ' + self.config.cy + ') rotate(270)' });
            };

            this.redraw = function(value, transitionDuration)
            {
                var pointerContainer = this.body.select('.pointerContainer');

                pointerContainer.selectAll('text').text(parseFloat(value).toFixed(2) + '%');

                var pointer = pointerContainer.selectAll('path');
                pointer.transition()
                    .duration(undefined != transitionDuration ? transitionDuration : this.config.transitionDuration)
                    //.delay(0)
                    //.ease('linear')
                    //.attr('transform', function(d)
                    .attrTween('transform', function()
                    {
                        var pointerValue = value;
                        if (value > self.config.max) pointerValue = self.config.max + 0.02*self.config.range;
                        else if (value < self.config.min) pointerValue = self.config.min - 0.02*self.config.range;
                        var targetRotation = (self.valueToDegrees(pointerValue) - 90);
                        var currentRotation = self._currentRotation || targetRotation;
                        self._currentRotation = targetRotation;

                        return function(step)
                        {
                            var rotation = currentRotation + (targetRotation-currentRotation)*step;
                            return 'translate(' + self.config.cx + ', ' + self.config.cy + ') rotate(' + rotation + ')';
                        }
                    });

                var outerCircle = this.body.select('.outer-circle')
                    .transition()
                    .duration(750)
                    .style('fill', function () {
                        var i = parseInt(value);
                        if (i >= 0 && i < 75) {
                            return self.config.greenColor;
                        } else if (i >= 75 && i < 90) {
                            return self.config.yellowColor;
                        } else {
                            return self.config.redColor;
                        }
                    });
            };

            this.valueToDegrees = function(value)
            {
                // thanks @closealert
                //return value / this.config.range * 270 - 45;
                return value / this.config.range * 270 - (this.config.min / this.config.range * 270 + 45);
            };

            this.valueToRadians = function(value)
            {
                return this.valueToDegrees(value) * Math.PI / 180;
            };

            this.valueToPoint = function(value, factor)
            {
                return { 	x: this.config.cx - this.config.radius * factor * Math.cos(this.valueToRadians(value)),
                    y: this.config.cy - this.config.radius * factor * Math.sin(this.valueToRadians(value)) 		};
            };

            // initialization
            this.configure(configuration);
        };

        return {
            createGauge: function (name, label, min, max, size) {
                var config = {
                    size: size || scaleConfig.defaultGaugeWidth,
                    label: label,
                    min: min || 0,
                    max: max || 100,
                    minorTicks: 5
                };

                var range = config.max - config.min;
                config.yellowZones = [{ from: config.min + range*0.75, to: config.min + range*0.9 }];
                config.redZones = [{ from: config.min + range*0.9, to: config.max }];

                var gauge = new Gauge(name + 'GaugeContainer', config);
                gauge.render();
                return gauge;
            }
        }
    });
})();
(function () {
    'use strict';

    angular.module('scaleApp').controller('feedDetailsController', function($scope, $location, scaleConfig, navService, subnavService, feedService) {
        $scope.loading = true;
        $scope.feedData = {};
        $scope.subnavLinks = scaleConfig.subnavLinks.feed;
        $scope.useIngestTime = 'false';

        $scope.changeFeedSelection = function(){
            setFeedUrl();
            //getFeed();
        }

        $scope.changeIngestTimeSelection = function(){
            setFeedUrl();
            getFeed();
        }

        var getFeedParams = function(){
            var params = {};
            var strikeId = $scope.selectedFeed ? $scope.selectedFeed.strike.id : null;
            if(strikeId != $location.search().strike_id){
                params.strike_id = strikeId;
            }
            else if($location.search().strike_id){
                params.strike_id = $location.search().strike_id;
            }
            var useIngestTime = $scope.useIngestTime ? $scope.useIngestTime : null;
            if(useIngestTime != $location.search().use_ingest_time){

               params.use_ingest_time = useIngestTime;
            }
            else if($location.search().use_ingest_time){
               console.log('getFeedParams use_ingest_time: ' + $location.search().use_ingest_time);
               params.use_ingest_time = $location.search().use_ingest_time;
            }
            return params;
        }

        var getFeed = function () {
            $scope.loading = true;
            if($location.search().use_ingest_time){
              $scope.useIngestTime = $location.search().use_ingest_time;
            }
            var feedParams = getFeedParams();
            feedService.getFeed(feedParams).then(function (data) {
                $scope.allFeeds = _.sortByOrder(data.results, ['strike.name'], ['asc']);
                var strikeId = $location.search().strike_id;
                if(strikeId){
                    // set selectedFeed = new feed
                    var feed = _.find($scope.allFeeds, function(feed){
                        return feed.strike.id == strikeId;
                    });
                    $scope.selectedFeed = feed ? feed : null;
                } else {
                    $scope.selectedFeed = $scope.allFeeds[0];
                    setFeedUrl();
                }
            }).finally(function(){
                $scope.loading = false;
            });
        };

        var setFeedUrl = function(){
            // set param in URL
            var params = getFeedParams();
            $location.search(params);
        };

        var initialize = function () {
            navService.updateLocation('feed');
            subnavService.setCurrentPath('feed');
            getFeed();
        };

        initialize();
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').controller('ingestRecordsController', function($scope, $rootScope, $location, scaleConfig, scaleService, gridFactory, navService, subnavService, feedService) {
        $scope.subnavLinks = scaleConfig.subnavLinks.feed;

        var gridParams = {
            page: 1, page_size: 25, started: null, ended: null, order: '-transfer_started', status: null
        };

        // check for gridParams in query string, and update as necessary
        _.forEach(_.pairs(gridParams), function (param) {
            var value = _.at($location.search(), param[0]);
            if (value.length > 0 && value[0]) {
                gridParams[param[0]] = value.length > 1 ? value : value[0];
            }
            else {
                $location.search()[param[0]] = param[1];
            }
        });

        var filteredByStatus = gridParams.status ? true : false;
        var filteredByOrder = gridParams.order ? true : false;

        $scope.statusValues = scaleConfig.ingestStatus;
        $scope.selectedStatus = gridParams.status || $scope.statusValues[0];
        $scope.$watch('selectedStatus', function (value) {
            if ($scope.loading) {
                if (filteredByStatus) {
                    updateStatus(value);
                }
            } else {
                filteredByStatus = value !== 'VIEW ALL';
                updateStatus(value);
            }
        });

        var updateStatus = function (value) {
            if (value != gridParams.status) {
                gridParams.page = 1;
            }
            gridParams.status = value === 'VIEW ALL' ? null : value;
            gridParams.page_size = $scope.gridOptions.paginationPageSize;
            if (!$scope.loading) {
                $scope.filterResults();
            }
        };

        var defaultColumnDefs = [
            { field: 'file_name', displayName: 'File Name', enableFiltering: false },
            {
                field: 'file_size',
                displayName: 'File Size',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.file_size_formatted }}</div>',
            },
            { field: 'strike.title', displayName: 'Strike Process', enableFiltering: false },
            {
                field: 'status',
                filterHeaderTemplate: '<div class="ui-grid-filter-container"><select class="form-control input-sm" ng-model="grid.appScope.selectedStatus"><option ng-selected="{{ grid.appScope.statusValues[$index] == grid.appScope.selectedStatus }}" value="{{ grid.appScope.statusValues[$index] }}" ng-repeat="status in grid.appScope.statusValues track by $index">{{ status.toUpperCase() }}</option></select></div>'
            },
            {
                field: 'transfer_started',
                enableFiltering: false
            },
            { field: 'transfer_ended', enableFiltering: false },
            {
                field: 'ingest_started',
                enableFiltering: false
            },
            { field: 'ingest_ended', enableFiltering: false }
        ];

        $scope.gridOptions = gridFactory.defaultGridOptions();
        $scope.gridOptions.paginationCurrentPage = parseInt(gridParams.page || 1);
        $scope.gridOptions.paginationPageSize = parseInt(gridParams.page_size) || $scope.gridOptions.paginationPageSize;
        $scope.gridOptions.columnDefs = gridFactory.applySortConfig(defaultColumnDefs, gridParams);
        $scope.gridOptions.data = [];
        $scope.gridOptions.onRegisterApi = function (gridApi) {
                //set gridApi on scope
                $scope.gridApi = gridApi;
                // $scope.gridApi.selection.on.rowSelectionChanged($scope, function (row) {
                //     if ($scope.actionClicked) {
                //         $scope.actionClicked = false;
                //     } else {
                //         $scope.$apply(function(){
                //             $location.path('/feed/ingests/' + row.entity.id);
                //         });
                //     }
                //
                // });
                $scope.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                    gridParams.page = currentPage;
                    gridParams.page_size = pageSize;
                    console.log('gridApi.paginationChanged');
                    $scope.filterResults();
                });
                $scope.gridApi.core.on.sortChanged($scope, function (grid, sortColumns) {
                    $rootScope.colDefs = null;
                    _.forEach($scope.gridApi.grid.columns, function (col) {
                        col.colDef.sort = col.sort;
                    });
                    $rootScope.colDefs = $scope.gridApi.grid.options.columnDefs;
                    var sortArr = [];
                    _.forEach(sortColumns, function (col) {
                        sortArr.push(col.sort.direction === 'desc' ? '-' + col.field : col.field);
                    });
                    updateOrder(sortArr);
                });
            };

        $scope.filterResults = function () {
            _.forEach(_.pairs(gridParams), function (param) {
                $location.search(param[0], param[1]);
            });
            getIngests();
        };

        var updateOrder = function (sortArr) {
            gridParams.order = sortArr.length > 0 ? sortArr : null;
            filteredByOrder = sortArr.length > 0;
            $scope.filterResults();
        };

        var getIngests = function () {
            $scope.loading = true;
            feedService.getIngestsOnce(gridParams).then(function (data) {
                $scope.ingests = data.results;
                $scope.gridOptions.totalItems = data.count;
                $scope.gridOptions.data = $scope.ingests;
                $scope.loading = false;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                $scope.loading = false;
            });
        };


        var initialize = function () {
            navService.updateLocation('feed');
            subnavService.setCurrentPath('feed/ingests');
            getIngests();
        };

        initialize();

        angular.element(document).ready(function () {
            // set container heights equal to available page height
            var viewport = scaleService.getViewportSize(),
                offset = scaleConfig.headerOffset,
                gridMaxHeight = viewport.height - offset;

            $scope.gridStyle = 'height: ' + gridMaxHeight + 'px; max-height: ' + gridMaxHeight + 'px; overflow-y: auto;';
        });
    });
})();

(function () {
    'use strict';
    angular.module('scaleApp').service('feedService', function ($location, $timeout, $q, $http, scaleConfig, scaleService, Feed, FeedStatus) {

        var getFeedParams = function(params){
            if(!params){ params = {}; }
            var p = {};
            p.page_size = 1000;
            p.started = params.started ? params.started : moment.utc().add(-7,'days').startOf('d').toDate();
            p.ended = params.stopped ? params.stopped : moment.utc().toDate();
            p.use_ingest_time = params.use_ingest_time ? params.use_ingest_time : null;
            return p;
        };

        var getIngestsParams = function(params){
            return params;
        };

        return {
            getFeed: function(params){
                var d = $q.defer();
                var params = getFeedParams(params);
                $http({
                    url: scaleConfig.urls.getDataFeed(),
                    method: 'GET',
                    params: params
                }).success(function (data) {
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getIngestsOnce: function(params) {
                var d = $q.defer();
                var params = getIngestsParams(params);
                $http({
                    url: scaleConfig.urls.getIngests(),
                    method: 'GET',
                    params: params
                }).success(function (data) {
                    _.forEach(data.results, function(d){
                        d.file_size_formatted = scaleService.calculateFileSizeFromBytes(d.file_size);
                    });
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            }
        };
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').factory('Feed', function (scaleConfig) {
        var Feed = function (value, status) {
            this.value = value;
            this.status = status;
        };

        // public methods
        Feed.prototype = {
            toString: function () {
                return 'Feed';
            },
            getCellText: function () {
                return this.value;
            },
            getCellTitle: function () {
                return '';
            }
        };

        // static methods, assigned to class
        Feed.build = function (data) {
            if (data) {
                return new Feed(
                    data.value,
                    data.status
                );
            }
            return new Feed();
        };

        Feed.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(Feed.build)
                    .filter(Boolean);
            }
            return Feed.build(data);
        };

        return Feed;
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').factory('FeedStatus', function (scaleConfig) {
        var FeedStatus = function (status) {
            this.status = status;
        };

        // public methods
        FeedStatus.prototype = {
            toString: function () {
                return 'FeedStatus';
            },
            getCellFill: function () {
                return scaleConfig.colors.chart_green;
            },
            getCellActivity: function () {
                return '';
            },
            getCellActivityTotal: function () {
                return '';
            },
            getCellError: function () {
                return '';
            },
            getCellTotal: function () {
                return '';
            }
        };

        // static methods, assigned to class
        FeedStatus.build = function (data) {
            if (data) {
                return new FeedStatus(
                    data.status
                );
            }
            return new FeedStatus();
        };

        FeedStatus.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(FeedStatus.build)
                    .filter(Boolean);
            }
            return FeedStatus.build(data);
        };

        return FeedStatus;
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').controller('statsController', function($scope, $interval, navService) {
        $scope.percentage = 0.83;
        $scope.date = new Date();

        var initialize = function() {
            navService.updateLocation('stats');

            var percentageUpdater = $interval(function() {
                $scope.percentage = Math.random();
            }, 2000);

            // Stop updating percentage when user leaves the stats page
            $scope.$on('$destroy', function() {
                if (angular.isDefined(percentageUpdater)) {
                    $interval.cancel(percentageUpdater);
                    percentageUpdater = undefined;
                }
            });
        };

        initialize();
    });
})();
(function () {
    'use strict';

    angular.module('scaleApp').service('statsService', function ($http, $q, scaleConfig) {
        this.getDetails = function (hour) {
            hour = hour || 3;
            var d = $q.defer();

            $http.get(scaleConfig.urls.getDetails(hour)).success(function (data) {
                d.resolve(data);
            });

            return d.promise;

            /*var d = $.Deferred(),
                details = {
                    job_types_details: {},
                    hosts_details: {},
                    node_sleep: '1',
                    running: true,
                    hosts: [],
                    job_types: []
                },
                jobTotal = Math.floor(Math.random() * scaleConfig.jobTypes.length) + 1,
                hostTotal = Math.floor(Math.random() * 25) + 1;

            for (var j = 0; j < jobTotal; j++) {
                var job = scaleConfig.jobTypes[j],
                    jobTitleNice = job.title,
                    jDone = Math.floor(Math.random() * 15) + 5,
                    jError = Math.floor(Math.random() * 3),
                    jActive = Math.floor(Math.random() * 5),
                    jTotal = jDone + jError + jActive;

                details.job_types_details[job.title] = {
                    active_title: [],
                    execution_style: scaleConfig.executions[jError],
                    done: jDone + jError,
                    error: jError,
                    active: jActive,
                    total_duration: 10.00000000000001,
                    total: jTotal,
                    percent: ((jError / (jDone + jActive))*100).toFixed(2).toString(),
                    nice: jobTitleNice
                };

                details.job_types.push(job.title);
            }

            for (var h = 0; h < hostTotal; h++) {
                var hostTitle = h < 10 ? 'host0' + h : 'host' + h,
                    hActive = Math.floor(Math.random() * 2),
                    hTotal = Math.floor(Math.random() * 15) + 5,
                    hError = Math.floor(Math.random() * 3);

                details.hosts_details[hostTitle] = {
                    id: h,
                    active_duration: '',
                    checkin: '',
                    stop: false,
                    sleep: 0,
                    active: hActive > 0,
                    lockfile: false,
                    active_id: null,
                    active_title: '',
                    checkin_style: scaleConfig.executions[hError],
                    total: hTotal,
                    percent: ((hError / hTotal) * 100).toFixed(2).toString(),
                    time_since: '0:06:12',
                    error: hError,
                    execution_style: scaleConfig.executions[Math.floor(Math.random() * 3)]
                };

                details.hosts.push(hostTitle);
            }

            d.resolve(details);

            return d.promise();*/
        };
    });
})();

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
            };

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

        var getPlotDataParams = function (obj) {
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

        var resetSelections = function () {
            $scope.inputStartDate = moment.utc().subtract(1, 'M').toISOString();
            $scope.inputEndDate = moment.utc().toISOString();
            $scope.selectedDataType = {};
            $scope.changeDataTypeSelection();
        };

        var updateChart = function () {
            $scope.chartData = [];
            if ($scope.chartArr.length === 0) {
                // nothing to show on chart
                chart.destroy();
                chart = null;
            } else {
                var callInit = _.after($scope.chartArr.length, function () {
                    // only initChart after this function has been called for all datasets in chartArr
                    $scope.loadingMetrics = false;
                    initChart();
                });

                _.forEach($scope.chartArr, function (obj) {
                    var params = getPlotDataParams(obj);
                    //metricsService.getPlotData(params).then(function (data) {
                    metricsService.getGeneratedPlotData({query: obj, params: params}).then(function (data) {
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
            updateChart();
            //resetSelections();
        };

        $scope.deleteFromChart = function (objToDelete) {
            _.remove($scope.chartArr, function (obj) {
                return JSON.stringify(obj) === JSON.stringify(objToDelete);
            });
            updateChart();
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
                getDataTypes();
            } else {
                getDataTypeOptions($scope.selectedDataType);
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
            initChart();
        };

        $scope.updateChartType = function (type) {
            $scope.chartType = type;
            $scope.chartTypeDisplay = _.capitalize(type);
            $scope.barClass = type === 'bar' ? 'btn-primary' : 'btn-default';
            $scope.areaClass = type === 'area' ? 'btn-primary' : 'btn-default';
            $scope.lineClass = type === 'line' ? 'btn-primary' : 'btn-default';
            $scope.splineClass = type === 'spline' ? 'btn-primary' : 'btn-default';
            $scope.scatterClass = type === 'scatter' ? 'btn-primary' : 'btn-default';
            initChart();
        };

        $scope.toggleSubchart = function () {
            $scope.subchartEnabled = !$scope.subchartEnabled;
            if ($scope.subchartEnabled) {
                $scope.subchartClass = 'btn-primary';
            } else {
                $scope.subchartClass = 'btn-default';
            }
        };

        var initialize = function () {
            navService.updateLocation('metrics');
            getDataTypes();
            /*
            if ($scope.chartArr.length > 0) {
                updateChart();
            }
            */
        };

        /*var applyFiltersToChoices = function () {
            var choices = $scope.selectedDataTypeOptions ? $scope.selectedDataTypeOptions.choices : [];
            var filteredChoices = _.where(choices,$scope.filtersApplied);
            $scope.filteredChoices = filteredChoices;
        };*/

        var getDataTypes = function () {
            metricsService.getDataTypes().then(function (result) {
                $scope.availableDataTypes = result.results;
            }).catch(function (error) {
                console.log(error);
                toastr['error'](error);
            });
        };

        var getDataType = function (id) {
            metricsService.getDataTypeMetrics(id).then(function (result) {
                $scope.selectedDataTypeAvailableMetrics = result.metrics;
            }).catch(function (error) {
                console.log(error);
            });
        };

        var getDataTypeOptions = function (dataType) {
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

        initialize();

        $scope.$watch('inputEndDate', function (value) {
            console.log(value)
        });

        // set up chart
        var initChart = function () {
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
            var numDays = moment.utc($scope.inputEndDate).diff(moment.utc($scope.inputStartDate), 'd');
            for (var i = 0; i < numDays; i++) {
                xArr.push(moment.utc($scope.inputStartDate).add(i, 'd').startOf('d').toDate());
            }

            // iterate over datatypes and add values to colArr
            _.forEach($scope.chartData, function (data) {
                var valueArr = [],
                    query = data.query,
                    queryFilter = {},
                    queryDates = [];

                yUnits = _.pluck(query.selectedMetrics, 'units');

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

(function () {
    'use strict';

    angular.module('scaleApp').service('metricsService', function ($http, $q, $resource, scaleConfig, QueueDepth) {
        var getPlotDataParams = function (page, page_size, started, ended, choice_id, column, group, dataType) {
            return {
                page: page,
                page_size: page_size,
                started: started,
                ended: ended,
                'choice-id': choice_id,
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

                var numDays = moment.utc(obj.params.ended).diff(moment.utc(obj.params.started), 'd');

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

(function () {
    'use strict';

    angular.module('scaleApp').controller('nodesController', function($scope, $location, $timeout, navService, nodeService) {
        $scope.nodeCounts = [];
        $scope.loading = true;
        $scope.hourValue = 3;
        $scope.nodesError = null;
        $scope.nodesErrorStatus = null;
        $scope.nodeStatusError = null;
        $scope.nodeStatusErrorStatus = null;
        $scope.nodeData = {
            data: null,
            status: null
        };

        var debounceTimer = {};

        var debounceBroadcast = function (message, args) {
            if (debounceTimer[message]) {
                $timeout.cancel(debounceTimer[message]);
            }
            debounceTimer[message] = $timeout(function () {
                $scope.$broadcast(message, args);
            }, 500);
        };

        $scope.redrawGrid = function () {
            debounceBroadcast('redrawGrid', $scope.nodeData);
        };

        var getNodes = function () {
            nodeService.getNodes().then(null, null, function (data) {
                if (data.$resolved) {
                    $scope.nodesError = null;
                    $scope.nodeData.data = data.results;
                    $scope.redrawGrid();
                } else {
                    if (data.statusText && data.statusText !== '') {
                        $scope.nodesErrorStatus = data.statusText;
                    }
                    $scope.nodesError = 'Unable to retrieve nodes.';
                }
            });
        };

        var getNodeStatus = function () {
            nodeService.getNodeStatus(null, null, 'PT' + $scope.hourValue + 'H', null).then(null, null, function (data) {
                if (data.$resolved) {
                    $scope.nodeStatusError = null;
                    $scope.nodeData.status = data.results;
                    $scope.redrawGrid();
                } else {
                    if (data.statusText && data.statusText !== '') {
                        $scope.nodeStatusErrorStatus = data.statusText;
                    }
                    $scope.nodeStatusError = 'Unable to retrieve node status.';
                }
            });
        };

        var initialize = function() {
            getNodes();
            getNodeStatus();
            _.defer(function () {
                $scope.loading = false;
            });
            navService.updateLocation('nodes');
        };

        initialize();
    });
})();
(function () {
    'use strict';

    angular.module('scaleApp').controller('nodeDetailsController', function($scope, $location, $routeParams, $timeout, navService, nodeService) {
        $scope.nodeId = $routeParams.id;

        var getNodeDetails = function (nodeId) {
            nodeService.getNode(nodeId).then( function (data) {
                $scope.node = data;
            });
        };

        var initialize = function() {
            navService.updateLocation('nodes');

            getNodeDetails($scope.nodeId);
            _.defer(function () {
                $scope.loading = false;
            });
        };

        initialize();

        /*$scope.$watch('nodeData', function (val) {
            $scope.redrawGrid();
        }, true);*/
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').service('nodeService', function ($http, $q, $resource, scaleConfig, Node, NodeStatus, poller, pollerFactory) {
        /*var totalNodes = 5;

        var getTotalNodes = function () {
            return totalNodes;
        };

        var setTotalNodes = function () {
            totalNodes = Math.floor(Math.random() * (20 - 1 + 1)) + 1;
        };

        setInterval(function () {
            setTotalNodes();
        }, 3100);*/

        var getNodeStatusParams = function (page, page_size, started, ended) {
            var params = {};

            if(page) { params.page = page; }
            if(page_size) { params.page_size = page_size; }
            if(started) { params.started = started; }
            if(ended) { params.ended = ended; }

            return params;
        };

        return {
            getNodes: function () {
                var nodesResource = $resource(scaleConfig.urls.getNodes()),
                    nodesPoller = pollerFactory.newPoller(nodesResource, scaleConfig.pollIntervals.nodes);

                return nodesPoller.promise.then(null, null, function (data) {
                    if (data.$resolved) {
                        /*var returnResult = {
                            $resolved: true,
                            nodes: []
                        };
                        var newData = {};
                        for (var i = 0; i < getTotalNodes(); i++) {
                            newData = {
                                "id": i,
                                "hostname": "node" + i + ".local",
                                "port": 5051,
                                "slave_id": "20150616-103050-1800454536-5050-6193-S2",
                                "total_cpus": 2.0,
                                "total_mem": 6793.0,
                                "total_disk": 94639.0,
                                "is_paused": false,
                                "created": "2015-06-15T17:18:52.414Z",
                                "last_modified": "2015-06-15T17:18:52.414Z"
                            };
                            returnResult.nodes.push(newData);
                        }
                        result = returnResult;*/

                        data.results = Node.transformer(data.results);
                    } else {
                        nodesPoller.stop();
                    }
                    return data;
                });
            },
            getNodesOnce: function () {
                var d = $q.defer();
                $http.get(scaleConfig.urls.getNodes()).success(function (data) {
                    var returnData = Node.transformer(data.nodes);
                    d.resolve(returnData);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getNode: function (slaveId) {
                var d = $q.defer();
                $http.get(scaleConfig.urls.getNode(slaveId)).success(function (data) {
                    var returnData = Node.transformer(data);
                    d.resolve(returnData);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getNodeStatus: function (page, page_size, started, ended) {
                var params = getNodeStatusParams(page, page_size, started, ended);

                var nodeStatusResource = $resource(scaleConfig.urls.getNodeStatus(), params),
                    nodeStatusPoller = pollerFactory.newPoller(nodeStatusResource, scaleConfig.pollIntervals.nodeStatus);

                return nodeStatusPoller.promise.then(null, null, function (data) {
                    if (data.$resolved) {
                        /*var returnResult = {
                            $resolved: true,
                            node_stats: []
                        };
                        var newData = {};
                        for (var i = 0; i < getTotalNodes(); i++) {
                            newData = {
                                "hostname": "node" + i + ".local",
                                "jobs_completed": Math.floor(Math.random() * (100 - 20 + 1)) + 20,
                                "system_failures": Math.floor(Math.random() * (20 - 0 + 1)) + 0,
                                "id": i
                            };
                            returnResult.node_stats.push(newData);
                        }
                        result = returnResult;*/

                        data.results = NodeStatus.transformer(data.results);
                    } else {
                        nodeStatusPoller.stop();
                    }
                    return data;
                });
            },
            getNodeStatusOnce: function (page, page_size, started, ended) {
                var d = $q.defer();
                var params = getNodeStatusParams(page, page_size, started, ended);
                $http({
                    url: scaleConfig.urls.getNodeStatus(),
                    method: 'GET',
                    params: params
                }).success(function (data) {
                    data.results = NodeStatus.transformer(data.results);
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getNodeData: function (slaveId, since) {
                var data = {},
                    self = this;

                since = since || 'PT3H';

                return self.getNodes().then(function (nodes) {
                    data.nodes = nodes;
                    return self.getNodeStatus(since).then(function (stats) {
                        data.stats = stats;
                        return data;
                    });
                });
            }
        };

    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').service('nodeUpdateService', function ($http, $q, scaleConfig, Node) {
        var getNodeUpdateData = function (hostname, port, pause_reason, is_paused) {
            return {
                hostname: hostname,
                port: port,
                pause_reason: pause_reason,
                is_paused: is_paused
            };
        };

        return {
            updateNode: function (id, data) {
                data = data || getNodeUpdateData();
                var d = $q.defer();

                $http({
                    url: scaleConfig.urls.updateNode(id),
                    method: 'PATCH',
                    data: data
                }).success(function (result) {
                    d.resolve(Node.transformer(result));
                }).error(function (error) {
                    d.reject(error);
                });

                return d.promise;
            }
        };
    })
})();

(function(){
    'use strict';

    angular.module('scaleApp').factory('Node', function (NodeResources, scaleService) {
        var Node = function (id, hostname, port, slave_id, pause_reason, is_paused, is_paused_errors, is_active, archived, created, last_offer, last_modified, resources) {
            this.id = id;
            this.hostname = hostname;
            this.port = port;
            this.slave_id = slave_id;
            this.pause_reason = pause_reason;
            this.is_paused = is_paused;
            this.is_paused_errors = is_paused_errors;
            this.is_active = is_active;
            this.archived = archived;
            this.created = created;
            this.last_offer = last_offer;
            this.last_modified = last_modified;
            this.resources = NodeResources.transformer(resources);
        };

        //public methods
        Node.prototype = {
            toString: function () {
                return 'Node';
            },
            getDuration: function () {
                return scaleService.calculateDuration(this.created, this.last_modified);
            },
            getCellText: function () {
                return this.hostname;
            },
            getCellTitle: function () {
                return this.hostname.split('.')[0];
            }
        };

        // static methods, assigned to class
        Node.build = function (data) {
            if (data) {
                return new Node(
                    data.id,
                    data.hostname,
                    data.port,
                    data.slave_id,
                    data.pause_reason,
                    data.is_paused,
                    data.is_paused_errors,
                    data.is_active,
                    data.archived,
                    data.created,
                    data.last_offer,
                    data.last_modified,
                    data.resources
                );
            }
            return new Node();
        };

        Node.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(Node.build);
            }
            return Node.build(data);
        };

        return Node;
    });
})();

(function(){
    'use strict';

    angular.module('scaleApp').factory('NodeResources', function(){
        var NodeResources = function (cpus, mem, disk) {
            this.cpus = cpus;
            this.mem = mem;
            this.disk = disk;
        };

        //public methods
        NodeResources.prototype = {
            // getDuration: function() {
                //return scaleService.calculateDuration(this.created, this.last_modified);
            // }
        };

        // static methods, assigned to class
        NodeResources.build = function (data) {
            if (data) {
                return new NodeResources(
                    data.cpus,
                    data.mem,
                    data.disk
                );
            }
            return new NodeResources();
        };

        NodeResources.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(NodeResources.build)
                    .filter(Boolean);
            }
            return NodeResources.build(data);
        };

        return NodeResources;
    });
})();

(function() {
    'use strict';

    angular.module('scaleApp').factory('NodeStatus', function (scaleConfig, nodeUpdateService, Node, JobExecution) {
        var NodeStatus = function (node, is_online, job_exe_counts, job_exes_running) {
            this.node = Node.transformer(node);
            this.is_online = is_online;
            this.job_exe_counts = job_exe_counts;
            this.job_exes_running = JobExecution.transformer(job_exes_running);
        };

        //public methods
        NodeStatus.prototype = {
            toString: function () {
                return 'NodeStatus';
            },
            getCompleted: function () {
                var completed = _.find(this.job_exe_counts, 'status', 'COMPLETED');
                return completed ? completed.count : 0;
            },
            getFailed: function () {
                var failed = _.find(this.job_exe_counts, 'status', 'FAILED');
                return failed ? failed.count : 0;
            },
            getCellFill: function () {
                var color = '';
                if (this.is_online) {
                    if (this.node.is_paused_errors) {
                        color = scaleConfig.colors.chart_orange;
                    } else if (this.node.is_paused) {
                        color = scaleConfig.colors.chart_yellow;
                    } else {
                        color = scaleConfig.colors.chart_green;
                    }
                } else {
                    color = scaleConfig.colors.chart_red;
                }
                return color;
            },
            getCellActivity: function () {
                return '';
            },
            getCellError: function () {
                return 'Failed: ' + this.getFailed();
            },
            getCellTotal: function () {
                return 'Completed: ' + this.getCompleted();
            },
            getCellStatus: function () {
                if (this.is_online) {
                    if (this.node.is_paused_errors) {
                        return 'High Failure Rate';
                    } else if (this.node.is_paused) {
                        return 'Paused';
                    } else {
                        return 'Online';
                    }
                } else {
                    return 'Offline';
                }
            },
            getCellJobs: function () {
                var text = '';
                _.forEach(this.job_exes_running, function (jobExecution) {
                    text = jobExecution.job.job_type.icon_code ?
                    text + ' ' + '&#x' + jobExecution.job.job_type.icon_code :
                    text + ' ' + '&#x' + scaleConfig.defaultIconCode;
                });
                return text;
            },
            getCellPauseResume: function () {
                return this.node.is_paused ? '&#xf04b' : '&#xf04c';
            },
            pauseResumeCell: function (pause_reason) {
                var updateData = {
                    hostname: this.node.hostname,
                    port: this.node.port,
                    pause_reason: pause_reason || '',
                    is_paused: !this.node.is_paused
                };
                return nodeUpdateService.updateNode(this.node.id, updateData).then(function (result) {
                    return Node.transformer(result);
                }).catch(function (error) {
                    console.log(error);
                });
            }
        };

        // static methods, assigned to class
        NodeStatus.build = function (data) {
            if (data) {
                return new NodeStatus(
                    data.node,
                    data.is_online,
                    data.job_exe_counts,
                    data.job_exes_running
                );
            }
            return new NodeStatus();
        };

        NodeStatus.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(NodeStatus.build);
            }
            return NodeStatus.build(data);
        };

        return NodeStatus;
    });
})();

(function (){
    'use strict';

    angular.module('scaleApp').controller('aisNodeHealthController', function ($rootScope, $scope, nodeService) {
        $scope.loadingNodeHealth = true;
        $scope.nodeHealthError = null;
        $scope.nodeHealthErrorStatus = null;
        $scope.nodeHealth = {};
        $scope.nodesOffline = 0;
        $scope.nodesPausedErrors = 0;
        $scope.nodesPaused = 0;
        $scope.healthyNodes = 0;
        $scope.totalNodes = 0;

        var getNodeStatus = function () {
            $scope.loadingNodeHealth = true;
            nodeService.getNodeStatus(null, null, $scope.duration, null).then(null, null, function (data) {
                if (data.$resolved) {
                    $scope.totalNodes = data.results.length;
                    $scope.nodesOffline = _.where(data.results, { 'is_online': false }).length;
                    $scope.nodesPausedErrors = _.where(data.results, { node: { 'is_paused_errors': true }}).length;
                    $scope.nodesPaused = _.where(data.results, { node: { 'is_paused': true }}).length;
                    $scope.healthyNodes = $scope.totalNodes - $scope.nodesOffline - $scope.nodesPausedErrors - $scope.nodesPaused;

                    var donutData = [];

                    // determine percentage of healthy nodes, and breakdown of why nodes are unhealthy
                    var gaugeData = $scope.totalNodes > 0 ? (($scope.healthyNodes / $scope.totalNodes) * 100).toFixed(2) : 0.00;

                    if ($scope.nodesOffline > 0) {
                        donutData.push({
                            status: 'Offline',
                            count: $scope.nodesOffline
                        });
                    }

                    if ($scope.nodesPausedErrors > 0) {
                        donutData.push({
                            status: 'High Failure Rate',
                            count: $scope.nodesPausedErrors
                        });
                    }

                    if ($scope.nodesPaused > 0) {
                        donutData.push({
                            status: 'Paused',
                            count: $scope.nodesPaused
                        });
                    }

                    $scope.nodeHealth = {
                        gaugeData: gaugeData,
                        donutData: donutData
                    };
                } else {
                    if (data.statusText && data.statusText !== '') {
                        $scope.nodeHealthErrorStatus = data.statusText;
                    }
                    $scope.nodeHealthError = 'Unable to retrieve node health.';
                }
                $scope.loadingNodeHealth = false;
            });
        };

        getNodeStatus();

        $rootScope.$on('updateNodeHealth', function () {
            getNodeStatus();
        });
    }).directive('aisNodeHealth', function(){
        /**
         * Usage: <ais-node-health />
         **/
         return {
             controller: 'aisNodeHealthController',
             templateUrl: 'modules/nodes/directives/nodeHealthTemplate.html',
             restrict: 'E',
             scope: {
                 duration: '=',
                 showDescription: '='
             }
         };
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').controller('queueController', function($scope, $location, scaleService, navService, queueService, uiGridConstants, scaleConfig, subnavService, QueueStatus, gridFactory) {
        $scope.loading = true;
        $scope.queueStatusError = null;
        $scope.queueStatusErrorStatus = null;
        $scope.totalQueued = 0;
        $scope.gridStyle = '';
        $scope.subnavLinks = scaleConfig.subnavLinks.queue;
        subnavService.setCurrentPath('queue');

        $scope.getPage = function (pageNumber, pageSize) {
            $scope.loading = true;
            queueService.getQueue(pageNumber - 1, pageSize).then(function (data) {
                var newData = [];
                for (var i = 0; i < $scope.gridOptions.paginationPageSize; i++) {
                    newData.push(data.jobs[i]);
                }
                $scope.gridOptions.data = newData;
            }).catch(function (error) {
                $scope.status = 'Unable to load queue status: ' + error.message;
                console.error($scope.status);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        var initialize = function() {
            $scope.gridOptions = gridFactory.defaultGridOptions();
            $scope.gridOptions.enableSorting = false;
            $scope.gridOptions.columnDefs = [
                    {
                        field: 'job_type_name',
                        displayName: 'Job Type',
                        enableFiltering: false,
                        cellTemplate: '<div class="ui-grid-cell-contents"><span ng-bind-html="row.entity.getIcon()"></span> {{ row.entity.job_type_name }}</div>'
                    },
                    { field: 'job_type_version', enableFiltering: false },
                    { field: 'highest_priority', enableFiltering: false },
                    {
                        field: 'longestQueued',
                        displayName: 'Duration of Longest Queued Job',
                        enableFiltering: false,
                        cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.getDuration() }}</div>'
                    },
                    { field: 'count', enableFiltering: false },
                    { field: 'is_job_type_paused', enableFiltering: false }
                ];
            $scope.gridOptions.data = [];
            $scope.gridOptions.onRegisterApi = function (gridApi) {
                    //set gridApi on scope
                    $scope.gridApi = gridApi;
                    gridApi.selection.on.rowSelectionChanged($scope, function (row) {
                        console.log(row);
                        //$location.path('/jobs').search({job_type_id: row.entity.job_type_id, status: 'RUNNING'});
                    });
                    $scope.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                        $scope.getPage(currentPage, pageSize);
                    });
                };


            queueService.getQueueStatus(0, $scope.gridOptions.paginationPageSize).then(null, null, function (result) {
                if (result.$resolved) {
                    $scope.gridOptions.data = result.queue_status;
                    $scope.gridOptions.totalItems = result.queue_status.length;
                    $scope.totalQueued = _.sum(result.queue_status, 'count');
                    console.log('queue status updated');
                } else {
                    if (result.statusText && result.statusText !== '') {
                        $scope.queueStatusErrorStatus = result.statusText;
                    }
                    $scope.queueStatusError = 'Unable to retrieve queue status.';
                }
                $scope.loading = false
            });

            navService.updateLocation('queue');
        };
        initialize();

        angular.element(document).ready(function () {
            // set container heights equal to available page height
            var viewport = scaleService.getViewportSize(),
                offset = scaleConfig.headerOffset,
                gridMaxHeight = viewport.height - offset;

            $scope.gridStyle = 'height: ' + gridMaxHeight + 'px; max-height: ' + gridMaxHeight + 'px; overflow-y: auto;';
        });
    });
})();

(function(){
    'use strict';

    angular.module('scaleApp').controller('queueRunningController', function($scope, $location, scaleService, navService, jobService, gridFactory, uiGridConstants, scaleConfig, subnavService) {
        $scope.loading = true;
        $scope.runningJobsError = null;
        $scope.runningJobsErrorStatus = null;
        $scope.totalRunning = 0;
        $scope.gridStyle = '';
        $scope.subnavLinks = scaleConfig.subnavLinks.queue;
        subnavService.setCurrentPath('queue/running');

        $scope.getPage = function (pageNumber, pageSize){
            $scope.loading = true;
            jobService.getRunningJobsOnce(pageNumber - 1, pageSize).then(function (data) {
                var newData = [];
                for(var i = 0; i < $scope.gridOptions.paginationPageSize; i++){
                    newData.push(data.results[i]);
                }
                $scope.gridOptions.data = newData;
            }).catch(function(error){
                $scope.status = 'Unable to load queue running status: ' + error.message;
                console.error($scope.status);
            }).finally(function(){
                $scope.loading = false;
            });
        };

        var initialize = function() {
            $scope.gridOptions = gridFactory.defaultGridOptions();
            $scope.gridOptions.enableSorting = false;
            $scope.gridOptions.columnDefs = [
                {
                    field: 'title',
                    displayName: 'Job Type',
                    enableFiltering: false,
                    cellTemplate: '<div class="ui-grid-cell-contents"><i class="fa fa-{{ row.entity.getIcon() }}"></i> {{ row.entity.job_type.title }}</div>'
                },
                {field: 'job_type.version', enableFiltering: false},
                {field: 'count', displayName: 'Number of Jobs', enableFiltering: false},
                {
                    field: 'longestRunning',
                    displayName: 'Duration of Longest Running Job',
                    enableFiltering: false,
                    cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.getDuration() }}</div>'
                }
            ];
            $scope.gridOptions.data = [];
            $scope.gridOptions.onRegisterApi = function (gridApi) {
                // set gridApi on scope
                $scope.gridApi = gridApi;
                gridApi.selection.on.rowSelectionChanged($scope, function (row) {
                    $scope.$apply(function(){
                        $location.path('/jobs').search({job_type_id: row.entity.job_type.id, status: 'RUNNING'});
                    });
                });
                $scope.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                    $scope.getPage(currentPage, pageSize);
                });
            };

            jobService.getRunningJobs(0, $scope.gridOptions.paginationPageSize).then(null, null, function (data) {
                if (data.$resolved) {
                    $scope.gridOptions.data = data.results;
                    $scope.gridOptions.totalItems = data.results.length;
                    $scope.totalRunning = _.sum(data.results, 'count');
                    console.log('running jobs updated');
                } else {
                    if (data.statusText && data.statusText !== '') {
                        $scope.runningJobsErrorStatus = data.statusText;
                    }
                    $scope.runningJobsError = 'Unable to retrieve running jobs.';
                }
                $scope.loading = false;
            });
            navService.updateLocation('queue');
        };
        initialize();

        angular.element(document).ready(function () {
            // set container heights equal to available page height
            var viewport = scaleService.getViewportSize(),
                offset = scaleConfig.headerOffset,
                gridMaxHeight = viewport.height - offset;

            $scope.gridStyle = 'height: ' + gridMaxHeight + 'px; max-height: ' + gridMaxHeight + 'px; overflow-y: auto;';
        });
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').controller('queueDepthDetailController', function ($scope, $location, navService, queueDepthService, scaleConfig, subnavService) {
        $scope.subnavLinks = scaleConfig.subnavLinks.queue;
        subnavService.setCurrentPath('queue/depth');

        $scope.loading = false;

        var initialize = function () {
            navService.updateLocation('queue');
        };

        initialize();
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').factory('QueueStatus', function (scaleConfig, scaleService) {
        var QueueStatus = function (count, longest_queued, job_type_name, job_type_version, highest_priority, is_job_type_paused) {
            this.count = count;
            this.longest_queued = longest_queued;
            this.job_type_name = job_type_name;
            this.job_type_version = job_type_version;
            this.highest_priority = highest_priority;
            this.is_job_type_paused = is_job_type_paused;
        };

        // public methods
        QueueStatus.prototype = {
            getIcon: function () {
                var configJobType = _.find(scaleConfig.jobTypes, 'title', this.job_type_name);
                return configJobType ? '<i class="fa">&#x' + configJobType.code + '</i>' : '<i class="fa">&#x' + scaleConfig.defaultIconCode + '</i>';
            },
            getDuration: function () {
                return scaleService.calculateDuration(this.longest_queued, moment.utc().toISOString());
            }
        };

        // static methods, assigned to class
        QueueStatus.build = function (data) {
            if (data) {
                return new QueueStatus(
                    data.count,
                    data.longest_queued,
                    data.job_type_name,
                    data.job_type_version,
                    data.highest_priority,
                    data.is_job_type_paused
                );
            }
            return new QueueStatus();
        };

        QueueStatus.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(QueueStatus.build)
                    .filter(Boolean);
            }
            return QueueStatus.build(data);
        };

        return QueueStatus;
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').factory('QueueDepth', function () {
        var QueueDepth = function (time, depth_per_job_type, depth_per_priority, total_count) {
            this.time = time;
            this.depth_per_job_type = depth_per_job_type;
            this.depth_per_priority = depth_per_priority;
            this.total_count = total_count;
        };

        // public methods
        QueueDepth.prototype = {
            
        };

        // static methods, assigned to class
        QueueDepth.build = function (data) {
            if (data) {
                return new QueueDepth(
                    data.time,
                    data.depth_per_job_type,
                    data.depth_per_priority,
                    data.total_count
                );
            }
            return new QueueDepth();
        };

        QueueDepth.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(QueueDepth.build)
                    .filter(Boolean);
            }
            return QueueDepth.build(data);
        };

        return QueueDepth;
    });
})();
(function () {
    'use strict';

    angular.module('scaleApp').service('queueService', function($http, $q, $resource, scaleConfig, poller, pollerFactory, QueueStatus) {
        var getJobLoadParams = function (page, page_size, started, ended, order, status, job_type_id, job_type_name, job_type_category, url) {
            return {
                started: started,
                ended: ended,
                job_type_id: job_type_id,
                job_type_name: job_type_name,
                job_type_category: job_type_category,
                page_size: 1000,
                url: url
            };
        };

        return {
            getQueue: function (pageNumber, pageSize) {
                var d = $q.defer();

                $http.get(scaleConfig.urls.getQueue(pageNumber, pageSize)).success(function (data) {
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });

                return d.promise;
            },
            getQueueStatus: function () {
                var queueStatusResource = $resource(scaleConfig.urls.getQueueStatus()),
                    queueStatusPoller = pollerFactory.newPoller(queueStatusResource, scaleConfig.pollIntervals.queueStatus);

                return queueStatusPoller.promise.then(null, null, function (result) {
                    if (result.$resolved) {
                        result.queue_status = QueueStatus.transformer(result.queue_status);
                    } else {
                        queueStatusPoller.stop();
                    }
                    return result;
                });
            },
            getQueueStatusOnce: function () {
                var d = $q.defer();

                $http.get(scaleConfig.urls.getQueueStatus()).success(function (data) {
                    var returnData = QueueStatus.transformer(data.queue_status);
                    d.resolve(returnData);
                }).error(function (error) {
                    d.reject(error);
                });

                return d.promise;
            },
            requeueJob: function(jobId){
                var d = $q.defer();
                var payload = { job_id: jobId };
                var url = scaleConfig.urls.requeueJob();
                $http.post(url,payload).success(function(result){
                    d.resolve(result);
                }).error(function(error){
                    d.reject(error);
                })

                return d.promise;
            },
            getJobLoad: function (params) {
                params = params || getJobLoadParams();
                params.url = params.url ? params.url : scaleConfig.urls.getJobLoad();

                var jobLoadResource = $resource(params.url, params),
                    jobLoadPoller = pollerFactory.newPoller(jobLoadResource, scaleConfig.pollIntervals.jobLoad);

                return jobLoadPoller.promise.then(null, null, function (data) {
                    if (!data.$resolved) {
                        jobLoadPoller.stop();
                    }
                    return data;
                });
            },
            getJobLoadOnce: function (params) {
                params = params || getJobLoadParams();
                var d = $q.defer();

                $http({
                    url: params.url ? params.url : scaleConfig.urls.getJobLoad(),
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

(function () {
    'use strict';

    angular.module('scaleApp').service('queueDepthService', function ($http, $q, $resource, poller, pollerFactory, scaleConfig, QueueDepth, JobType) {
        return {
            getQueueDepth: function (started, ended) {
                started = started || moment.utc().subtract(30, 'd').toISOString();
                ended = ended || moment.utc().toISOString();

                var queueDepthResource = $resource(scaleConfig.urls.getQueueDepth(started, ended)),
                    queueDepthPoller = pollerFactory.newPoller(queueDepthResource, scaleConfig.pollIntervals.queueDepth);

                return queueDepthPoller.promise.then(null, null, function (result) {
                    if (result.$resolved) {
                        /*var returnData = QueueDepth.transformer(data);
                         _.forEach(returnData.queueDepths, function (depth) {
                         var p1 = Math.floor(Math.random() * (100 - 20 + 1)) + 20,
                         p2 = Math.floor(Math.random() * (100 - 20 + 1)) + 20,
                         p3 = Math.floor(Math.random() * (100 - 20 + 1)) + 20,
                         p4 = Math.floor(Math.random() * (100 - 20 + 1)) + 20;
                         depth.depthPerPriority = [p1,p2,p3,p4];
                         depth.totalCount = p1 + p2 + p3 + p4;
                         });
                         return returnData;*/
                        result.job_types = JobType.transformer(result.job_types);
                        result.queue_depths = QueueDepth.transformer(result.queue_depths);
                    } else {
                        queueDepthPoller.stop();
                    }
                    return result;
                });
            },
            getQueueDepthOnce: function (started, ended) {
                started = started || moment.utc().subtract(30, 'd').toISOString();
                ended = ended || moment.utc().toISOString();

                var d = $q.defer();

                $http.get(scaleConfig.urls.getQueueDepth(started, ended)).success(function (data) {
                    var returnData = QueueDepth.transformer(data);
                    d.resolve(returnData);
                }).error(function (error) {
                    d.reject(error);
                });

                return d.promise;
            }
        }
    });
})();
(function () {
    'use strict';

    angular.module('scaleApp').controller('recipeTypesController', function ($rootScope, $scope, $routeParams, $location, $modal, hotkeys, scaleService, navService, recipeService, subnavService, jobTypeService, scaleConfig, RecipeType, userService) {
        $scope.loading = true;
        $scope.masterContainerStyle = '';
        $scope.detailContainerStyle = '';
        $scope.masterMaxHeight = 0;
        $scope.detailMaxHeight = 0;
        $scope.recipeTypes = [];
        $scope.recipeTypeIds = [];
        $scope.requestedRecipeTypeId = parseInt($routeParams.id);
        $scope.activeRecipeType = null;
        $scope.percentage = 73;
        $scope.date = new Date();
        $scope.recipes = null;
        $scope.mode = 'view'; // valid values are add, view, and edit
        $scope.addBtnText = 'New Recipe';
        $scope.addBtnClass = 'btn-primary';
        $scope.addBtnIcon = 'fa-plus-circle';
        $scope.editBtnText = 'Edit';
        $scope.editBtnClass = 'btn-success';
        $scope.editBtnIcon = 'fa-edit';
        $scope.jobTypeValues = [];
        $scope.isRecipeModified = false;
        $scope.saveBtnClass = 'btn-default';
        $scope.masterClass = 'col-xs-3';
        $scope.detailClass = 'col-xs-9';
        $scope.minimizeMaster = false;
        $scope.newBtnContainerClass = 'hidden';
        $scope.minimizeBtnContainerClass = 'hidden';
        $scope.minimizeBtnClass = 'fa fa-chevron-left';
        $scope.user = $rootScope.user;

        $scope.subnavLinks = scaleConfig.subnavLinks.recipes;
        subnavService.setCurrentPath('recipes/types');

        var initialize = function () {
            navService.updateLocation('recipes');
            $rootScope.user = userService.getUserCreds();
            getRecipeTypes();
            //getJobTypes();
        };
        
        var getRecipeTypes = function () {
            recipeService.getRecipeTypes().then(function (data) {
                $scope.recipeTypes = data;
                $scope.recipeTypeIds = _.pluck(data, 'id');
                $scope.viewRecipeTypeDetail($scope.requestedRecipeTypeId);
                hotkeys.bindTo($scope)
                    .add({
                        combo: 'ctrl+up',
                        description: 'Previous Recipe Type',
                        callback: function () {
                            if ($scope.activeRecipeType) {
                                var idx = _.indexOf($scope.recipeTypeIds, $scope.activeRecipeType.id);
                                if (idx > 0) {
                                    $scope.loadRecipeType($scope.recipeTypeIds[idx - 1]);
                                }
                            }
                        }
                    }).add({
                        combo: 'ctrl+down',
                        description: 'Next Recipe Type',
                        callback: function () {
                            if ($scope.activeRecipeType) {
                                var idx = _.indexOf($scope.recipeTypeIds, $scope.activeRecipeType.id);
                                if (idx < ($scope.recipeTypeIds.length - 1)) {
                                    $scope.loadRecipeType($scope.recipeTypeIds[idx + 1]);
                                }
                            }
                        }
                    });
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                if ($scope.loading) {
                    $scope.loading = false;
                }
            })
        };

        $scope.newRecipeType = function(){
            $location.path('/recipes/types/0');
        };

        $scope.viewRecipeTypeDetail = function(recipeTypeId){
            if (recipeTypeId > 0) {
                recipeService.getRecipeTypeDetail(recipeTypeId).then(function (data){
                    $scope.activeRecipeType = data;
                });
            } else if( recipeTypeId === 0) {
                $scope.activeRecipeType = new RecipeType();
            }
        };

        $scope.loadRecipeType = function (id) {
            if($scope.activeRecipeType && $scope.activeRecipeType.modified){
                confirmChangeRecipe().then(function () {
                    // OK
                    $location.path('/recipes/types/' + id);
                }, function () {
                    // Cancel

                });
            } else {
                $location.path('/recipes/types/' + id);
            }
        };

        var confirmChangeRecipe = function () {
            var modalInstance = $modal.open({
                animation: $scope.animationsEnabled,
                templateUrl: 'confirmDialog.html',
                scope: $scope,
                size: 'sm'
            });

            return modalInstance.result;
        };

        $scope.toggleMaster = function (minimizeMaster) {
            if (typeof minimizeMaster !== 'undefined') {
                $scope.minimizeMaster = minimizeMaster;
            } else {
                $scope.minimizeMaster = !$scope.minimizeMaster;
            }
            $scope.masterClass = $scope.minimizeMaster ? 'col-xs-1' : 'col-xs-3';
            $scope.detailClass = $scope.minimizeMaster ? 'col-xs-11' : 'col-xs-9';
            $scope.minimizeBtnContainerClass = $scope.minimizeMaster ? 'col-xs-12' : $rootScope.user ? 'col-xs-6 text-right' : 'col-xs-12 text-right';
            $scope.minimizeBtnClass = $scope.minimizeMaster ? 'fa fa-chevron-right' : 'fa fa-chevron-left';
            $scope.newBtnContainerClass = $scope.minimizeMaster ? 'hidden' : 'col-xs-6';
        };

        $rootScope.$on('toggleEdit', function (event, data) {
            $scope.toggleMaster(data === 'edit');
        });

        initialize();

        $rootScope.$on('recipeModified', function () {
            $scope.isRecipeModified = true;
            $scope.saveBtnClass = 'btn-success';
        });

        angular.element(document).ready(function () {
            $scope.newBtnContainerClass = $rootScope.user ? 'col-xs-6' : 'hidden';
            $scope.minimizeBtnContainerClass = $rootScope.user ? 'col-xs-6 text-right' : 'col-xs-12 text-right';
            // set container heights equal to available page height
            var viewport = scaleService.getViewportSize(),
                masterOffset = scaleConfig.headerOffset + document.getElementsByClassName('master-controls')[0].scrollHeight,
                detailOffset = scaleConfig.headerOffset;

            $scope.masterMaxHeight = viewport.height - masterOffset;
            $scope.detailMaxHeight = viewport.height - detailOffset;

            $scope.masterContainerStyle = 'height: ' + $scope.masterMaxHeight + 'px; max-height: ' + $scope.masterMaxHeight + 'px; overflow-y: auto;';
            $scope.detailContainerStyle = 'height: ' + $scope.detailMaxHeight + 'px; max-height: ' + $scope.detailMaxHeight + 'px';
        });
    });
})();
(function(){
    'use strict';

    angular.module('scaleApp').controller('recipeEditorController', function($scope, $log, $location, $routeParams, $modal, navService, recipeService, RecipeType, subnavService, jobTypeService, scaleConfig) {

        $scope.date = new Date();
        $scope.recipes = null;
        $scope.recipeTypeId = parseInt($routeParams.id);

        $scope.jobTypeValues = [];

        $scope.subnavLinks = scaleConfig.subnavLinks.recipes;
        subnavService.setCurrentPath('recipes/builder');

        $scope.items = ['item1', 'item2', 'item3'];
        $scope.animationsEnabled = true;
        $scope.selected = null;

        var getJobTypes = function () {
            jobTypeService.getJobTypesOnce().then(function (data) {
                $scope.jobTypeValues = data;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        $scope.openAddJob = function (size) {
           var modalInstance = $modal.open({
             animation: $scope.animationsEnabled,
             templateUrl: 'addJobContent.html',
             scope: $scope,
             size: 'sm'
           });

           modalInstance.result.then(function () {
             $scope.addJobType($scope.selectedItem);
           }, function () {

           });
         };

         $scope.addJobType = function(selectedJobType){
             $scope.recipeType.definition.addJobType(selectedJobType);
             $scope.redrawGraph();
         };

         $scope.selectItem = function(item){
             $scope.selectedItem = item;
         };

        $scope.initialize = function() {
            getJobTypes();
            navService.updateLocation('recipes');
            if($scope.recipeTypeId){
                $scope.getRecipeTypeDetail($scope.recipeTypeId);
            }
            else{
                $scope.recipeType = RecipeType.new();
            }

        };

        $scope.getRecipeTypeDetail = function (id) {
            recipeService.getRecipeTypeDetail(id).then(function (data) {
                $scope.recipeType = data;
                if ($scope.redrawGraph) {
                    $scope.redrawGraph();
                }
            });
        };

        $scope.saveRecipeType = function(){
                console.log($scope.recipeType.name);
        };

        $scope.initialize();
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').controller('recipesController', function ($rootScope, $scope, $location, scaleService, navService, gridFactory, uiGridConstants, scaleConfig, subnavService, recipeService) {

        var recipesParams = {
            page: null, page_size: null, started: null, ended: null, order: $rootScope.recipesControllerOrder || null, type_id: null, type_name: null, url: null
        };

        // check for recipesParams in query string, and update as necessary
        _.forEach(_.pairs(recipesParams), function (param) {
            var value = _.at($location.search(), param[0]);
            if (value.length > 0) {
                recipesParams[param[0]] = value.length > 1 ? value : value[0];
            }
        });

        var gridPageNumber = recipesParams.page || 1,
            filteredByRecipeType = recipesParams.type_id ? true : false,
            filteredByOrder = recipesParams.order ? true : false;

        // this file will be similar to jobsController
        $scope.recipesData = {};
        $scope.loading = true;
        $scope.recipeTypeValues = [];
        $scope.selectedRecipeType = recipesParams.type_id || 0;
        $scope.subnavLinks = scaleConfig.subnavLinks.recipes;
        $scope.gridStyle = '';

        subnavService.setCurrentPath('recipes');

        var defaultColumnDefs = [
            {
                field: 'recipe_type',
                displayName: 'Recipe Type',
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.recipe_type.title }} {{ row.entity.recipe_type.version }}</div>',
                filterHeaderTemplate: '<div class="ui-grid-filter-container"><select class="form-control input-sm" ng-model="grid.appScope.selectedRecipeType"><option ng-selected="{{ grid.appScope.recipeTypeValues[$index].id == grid.appScope.selectedRecipeType }}" value="{{ grid.appScope.recipeTypeValues[$index].id }}" ng-repeat="recipeType in grid.appScope.recipeTypeValues track by $index">{{ grid.appScope.recipeTypeValues[$index].title }} {{ grid.appScope.recipeTypeValues[$index].version }}</option></select>'
            },
            //{ field: 'created', enableFiltering: false, cellFilter: 'date:\'yyyy-MM-dd HH:mm:ss\''},
            { field: 'created', enableFiltering: false},
            {
                field: 'last_modified',
                enableFiltering: false,
                //cellFilter: 'date:\'yyyy-MM-dd HH:mm:ss\'',                
            },
            { field: 'duration', enableFiltering: false, enableSorting: false, cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.getDuration() }}</div>' }
        ];

        $scope.gridOptions = gridFactory.defaultGridOptions();
        $scope.gridOptions.paginationCurrentPage = parseInt(recipesParams.page || 1);
        $scope.gridOptions.paginationPageSize = parseInt(recipesParams.page_size) || $scope.gridOptions.paginationPageSize;
        var colDefs = $rootScope.recipeColDefs ? $rootScope.recipeColDefs : defaultColumnDefs;
        $scope.gridOptions.columnDefs = gridFactory.applySortConfig(colDefs, recipesParams);
        $scope.gridOptions.data = [];
        $scope.gridOptions.onRegisterApi = function (gridApi) {
            //set gridApi on scope
            $scope.gridApi = gridApi;
            $scope.gridApi.selection.on.rowSelectionChanged($scope, function (row) {
                $scope.$apply(function(){
                    $location.path('/recipes/recipe/' + row.entity.id);
                });

            });
            $scope.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                recipesParams.page = currentPage;
                recipesParams.page_size = pageSize;
                console.log('gridApi');
                $scope.filterResults();
            });
            $scope.gridApi.core.on.sortChanged($scope, function (grid, sortColumns) {
                $rootScope.recipeColDefs = null;
                _.forEach($scope.gridApi.grid.columns, function (col) {
                    col.colDef.sort = col.sort;
                });
                $rootScope.recipeColDefs = $scope.gridApi.grid.options.columnDefs;
                var sortArr = [];
                _.forEach(sortColumns, function (col) {
                    sortArr.push(col.sort.direction === 'desc' ? '-' + col.field : col.field);
                });
                updateRecipeOrder(sortArr);
            });
        };

        $scope.getPage = function (filter, pageNumber, pageSize, url) {
            $scope.loading = true;
            recipeService.getRecipes(filter, pageNumber, pageSize, url).then(function (data) {
                var newData = [];
                for (var i = 0; i < $scope.gridOptions.paginationPageSize; i++) {
                    if (data.results[i]) {
                        newData.push(data.results[i]);
                    }
                }
                $scope.gridOptions.data = newData;
                $scope.gridOptions.totalItems = data.count;
                $scope.jobsData = data;
                gridPageNumber = pageNumber;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        $scope.filterResults = function () {
            _.forEach(_.pairs(recipesParams), function (param) {
                $location.search(param[0], param[1]);
            });
        };

        var getRecipes = function () {
            recipeService.getRecipes(recipesParams).then(function (data) {
                $scope.recipesData = data;
                $scope.gridOptions.totalItems = data.count;
                $scope.gridOptions.data = data.results;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        var getRecipeTypes = function () {
            recipeService.getRecipeTypes().then(function (data) {
                $scope.recipeTypeValues = data;
                $scope.recipeTypeValues.unshift({ name: 'VIEW ALL', title: 'VIEW ALL', version: '', id: 0 });
                getRecipes();
            }).catch(function (error) {
                $scope.loading = false;
                console.log(error);
            });
        };

        var updateRecipeOrder = function (sortArr) {
            recipesParams.order = sortArr.length > 0 ? sortArr : null;
            filteredByOrder = sortArr.length > 0;
            $scope.filterResults();
        };

        var updateRecipeType = function (value) {
            if (value != recipesParams.type_id) {
                recipesParams.page = 1;
            }
            recipesParams.type_id = value == 0 ? null : value;
            recipesParams.page_size = $scope.gridOptions.paginationPageSize;
            console.log('selectedRecipeType');
            if (!$scope.loading) {
                $scope.filterResults();
            }
        };

        $scope.$watch('selectedRecipeType', function (value) {
            if ($scope.loading) {
                if (filteredByRecipeType) {
                    updateRecipeType(value);
                }
            } else {
                filteredByRecipeType = value != 0;
                updateRecipeType(value);
            }
        });

        var initialize = function () {
            if (typeof $rootScope.recipeColDefs === 'undefined') {
                // root column defs have not been altered by user, so set up defaults
                if (!recipesParams.order) {
                    recipesParams.order = '-last_modified';
                    $location.search('order', recipesParams.order).replace();
                }
                if (!recipesParams.page_size) {
                    recipesParams.page_size = $scope.gridOptions.paginationPageSize;
                    $location.search('page_size', recipesParams.page_size).replace();
                }
            }
            getRecipeTypes();
            navService.updateLocation('recipes');
        };

        initialize();

        angular.element(document).ready(function(){
           // set container height equal to available page height
            var viewport = scaleService.getViewportSize();
            var offset = scaleConfig.headerOffset;
            var gridMaxHeight = viewport.height - offset;
            $scope.gridStyle = 'height: ' + gridMaxHeight + 'px; max-height: ' + gridMaxHeight + 'px;';
        });
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').controller('recipeDetailsController', function ($rootScope, $scope, $location, $routeParams, navService, recipeService, scaleConfig, subnavService, userService) {
        $scope.recipe = {};
        $scope.recipeId = $routeParams.id;
        $scope.subnavLinks = scaleConfig.subnavLinks.recipes;
        subnavService.setCurrentPath('recipes');
        $scope.loadingRecipeDetail = true;
        $scope.activeTab = 'status';
        $scope.lastStatusChange = '';

        var getRecipeDetail = function (recipeId) {
            $scope.loadingRecipeDetail = true;
            recipeService.getRecipeDetails(recipeId).then(function (data) {
                $scope.recipe = data;
                recipeService.getRecipeTypeDetail(data.recipe_type.id).then(function(recipeType){
                    $scope.recipeType = recipeType;
                }).catch(function(error){
                   console.log(error);
                });
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                $scope.loadingRecipeDetail = false;
            });
        };

        var initialize = function () {
            navService.updateLocation('recipes');
            $rootScope.user = userService.getUserCreds();

            getRecipeDetail($scope.recipeId);
        };



        $scope.switchTab = function (tab) {
            $('#' + $scope.activeTab).hide();
            $scope.activeTab = tab;
            $('#' + $scope.activeTab).show();
        };

        initialize();
    });
})();

/**
 * <ais-scale-recipe-viewer />
 */
(function () {
    angular.module('scaleApp').controller('aisScaleRecipeGraphViewerController', function ($rootScope, $scope, $location, $modal, jobTypeService, recipeService) {
        $scope.vertices = [];
        $scope.edges = [];
        $scope.isUpdate = false;
        $scope.selectedJob = null;
        $scope.selectedInputProvider = null;
        $scope.mode = null;
        $scope.editMode = null;
        $scope.dependencyBtnClass = 'fa-plus';
        $scope.addBtnText = 'New Recipe';
        $scope.addBtnClass = 'btn-primary';
        $scope.addBtnIcon = 'fa-plus-circle';
        $scope.editBtnText = 'Edit';
        $scope.editBtnClass = 'btn-success';
        $scope.editBtnIcon = 'fa-edit';
        $scope.jobTypeValues = [];
        $scope.saveBtnClass = 'btn-default';
        $scope.savingRecipe = false;
        $scope.warnings = [];
        $scope.readonly = true;
        $scope.detailMaxHeight = 0;
        $scope.detailContainerStyle = '';
        $scope.containerClass = $scope.hasContainer ? '' : 'detail-container no-tabs';
        $scope.lastStatusChange = '';
        $scope.recipeInputTypes = [
            {
                name: 'property',
                title: 'Property',
                fields: []
            },
            {
                name: 'file',
                title: 'File',
                fields: [
                    {
                        name: 'media_types',
                        title: 'Media Types',
                        value: []
                    }
                ]
            },
            {
                name: 'files',
                title: 'Files',
                fields: [
                    {
                        name: 'media_types',
                        title: 'Media Types',
                        value: []
                    }
                ]
            }
        ];
        $scope.selectedRecipeInputType = {};
        $scope.recipeInput = {
            name: '',
            required: true,
            type: ''
        };

        var startJob = null;

        // Dagre variables
        var svg = null;
        var inner = null;
        var graph = null;
        var zoom = null;
        var render = null;


        var resetEditBtn = function () {
            $scope.editBtnText = $scope.mode === 'edit' ? 'Cancel Edit' : 'Edit';
            $scope.editBtnClass = $scope.mode === 'edit' ? 'btn-warning' : 'btn-success';
            $scope.editBtnIcon = $scope.mode === 'edit' ? 'fa-close' : 'fa-edit';
        };

        var resetAddBtn = function () {
            $scope.addBtnText = $scope.mode === 'add' ? 'Cancel' : 'New Recipe';
            $scope.addBtnClass = $scope.mode === 'add' ? 'btn-warning' : 'btn-primary';
            $scope.addBtnIcon = $scope.mode === 'add' ? 'fa-close' : 'fa-plus-circle';
        };

        var toggleAddRecipe = function () {
            $scope.mode = $scope.mode === 'add' ? 'view' : 'add';
            resetAddBtn();
        };

        var toggleEditRecipe = function () {
            if($scope.mode === 'edit'){
                $scope.mode = 'view';
                $scope.reloadRecipeTypeDetail($scope.recipeType.id);
            } else {
                $scope.mode = 'edit';
            }
            $scope.editMode = '';
            resetEditBtn();
        };

        var enableSaveRecipe = function () {
            $scope.recipeType.modified = true;
            $scope.saveBtnClass = 'btn-success';
        };

        var disableSaveRecipe = function () {
            $scope.recipeType.modified = false;
            $scope.saveBtnClass = 'btn-default;'
        };

        var confirmChangeRecipe = function () {
            var modalInstance = $modal.open({
                animation: $scope.animationsEnabled,
                templateUrl: 'confirmDialog.html',
                scope: $scope,
                size: 'sm'
            });

            return modalInstance.result;
        };

        var getRecipeTypeJobClassName = function(job){
            // default to 'nostatus'
            var className = 'nostatus';
            // find the associated job in the recipe.jobs
            if($scope.recipe){
                var recipejob = _.find($scope.recipe.jobs,{job_name: job.name});
                if(recipejob){
                    className = recipejob.job.status.toLowerCase();
                }
            }
            return className;
        };

        var getJobTypes = function () {
            jobTypeService.getJobTypesOnce().then(function (data) {
                $scope.jobTypeValues = data.results;
                $scope.$watch('recipeType', function(newValue,oldValue){
                    if($scope.recipeType){
                        if(!$scope.recipeType.id || $scope.recipeType.id === 0){
                            $scope.mode = 'add';
                        }
                        _.forEach($scope.recipeType.definition.jobs, function(job, idx){
                            jobTypeService.getJobTypeDetails(job.job_type_id).then(function(data){
                                $scope.recipeType.definition.jobs[idx].job_type = data;
                                initGraph();
                                getIoMappings();
                                drawGraph($scope.isUpdate);
                            });
                        })

                    }
                });
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                if ($scope.loading) {
                    $scope.loading = false;
                }
            });
        };

        $scope.reloadRecipeTypeDetail = function (id) {
            var getRecipeDetail = function () {
                recipeService.getRecipeTypeDetail(id).then(function (data) {
                    $scope.recipeType = data;
                });
            };

            if ($scope.recipeType.modified) {
                confirmChangeRecipe().then(function () {
                    // OK
                    disableSaveRecipe();
                    resetAddBtn();
                    if ($scope.mode === 'edit') {
                        toggleEditRecipe();
                    }
                    getRecipeDetail();
                }, function () {
                    // Cancel

                });
            } else {
                if ($scope.mode === 'edit') {
                    toggleEditRecipe();
                }
                resetAddBtn();
                getRecipeDetail();
            }
        };

        $scope.redraw = function () {
            initialize();
            //$rootScope.$broadcast('recipeModified');
        };

        $scope.nodeClick = function (name) {
            // Remove selection class
            $('div').removeClass('selected-node');
            $('div').removeClass('selected-node-dependency');
            $('div').removeClass('job-active');

            // find the job in the recipe definition
            var job = _.find($scope.recipeType.definition.jobs,{name: name});

            if(name === 'start'){
                job = startJob;
            }
            var $name = $('#' + name);
            var pos = $name.position();

            // click node different from selectedJob
            if (!$scope.selectedJob || job.name !== $scope.selectedJob.name) {
                if ($scope.editMode === 'addDependency') {
                    addDependency(name);
                    enableSaveRecipe();
                    $scope.redraw();

                } else if ($scope.editMode === 'addInput') {
                    $scope.selectedInputProvider = job;
                    $('.recipeNode:not(".selected-node")').removeClass('selected-node-selectable');
                    $('#' + name).addClass('selected-node-dependency');
                    $('#output-selector').css({top: pos.top, left: pos.left, position: 'absolute'});
                    console.log('toggle input selector');
                } else if ($scope.editMode === 'addOutput'){
                    $scope.selectedOutputReceiver = job;
                    // set position of output-selector
                    $('#input-selector').css({top: pos.top, left: pos.left, position: 'absolute'});
                    //$scope.mode = 'addInputActive';
                    $('.recipeNode:not(".selected-node")').removeClass('selected-node-selectable');
                    $('#' + name).addClass('selected-node-dependency');
                    console.log('toggle output selector');
                } else {
                    // update the selected job
                    $scope.selectedJob = job;
                    if($scope.recipe){
                        $scope.selectedRecipeJob = _.find($scope.recipe.jobs, { job_name: job.name });
                    }
                    // apply the selected-node class
                    $name.addClass('selected-node');
                }
            }
            else { // click selected node
                $('div').removeClass('selected-node');
                $scope.selectedJob = null;
                $scope.selectedRecipeJob = null;
                $scope.selectedOutputReceiver = null;
                $scope.selectedInputProvider = null;
                $scope.editMode = '';
                $scope.dependencyBtnClass = 'fa-plus';

                $('.recipeNode:not(".selected-node")').removeClass('selected-node-selectable');
            }
            if($scope.selectedJob){
                $('#' + $scope.selectedJob.name).addClass('selected-node');
            }
        };
        $scope.toggleEditMode = function () {
            if ($scope.mode === 'edit') {
                $scope.reloadRecipeTypeDetail($scope.recipeType.id);
            } else {
                toggleEditRecipe();
                resetAddBtn();
            }
            $rootScope.$broadcast('toggleEdit', $scope.mode);
        };

        $scope.openAddJob = function (size) {
            var modalInstance = $modal.open({
                animation: $scope.animationsEnabled,
                templateUrl: 'addJobContent.html',
                scope: $scope,
                size: 'sm'
            });

            modalInstance.result.then(function () {
                jobTypeService.getJobTypeDetails($scope.selectedItem.id).then(function(data){
                    $scope.addJobType(data);
                    enableSaveRecipe();
                });
            }, function () {

            });
        };

        $scope.openAddInput = function(){
            var modalInstance = $modal.open({
                animation: $scope.animationsEnabled,
                templateUrl: 'addInput.html',
                scope: $scope
            });

            modalInstance.result.then(function(){
                // check for fields and add as necessary
                if( $scope.selectedRecipeInputType.fields.length > 0){
                    var fieldArr = [];
                    _.forEach($scope.selectedRecipeInputType.fields, function(field){
                        _.forEach(field.value.split(','), function(value){
                            fieldArr.push(value);
                        });
                        $scope.recipeInput[field.name] = fieldArr;
                    });
                }

                // add input to recipe type definition
                $scope.recipeType.definition.input_data.push($scope.recipeInput);
                _.forEach($scope.recipeType.definition.jobs, function(job){
                    if(job.recipe_inputs.length === 0){
                        job.recipe_inputs.push({
                            job_input: $scope.recipeInput.name,
                            recipe_input: $scope.recipeInput.name
                        });
                    }
                });
                getIoMappings();

                // reset form fields
                $scope.recipeInput = {
                    name: '',
                    required: true,
                    type: ''
                };
                $scope.selectedRecipeInputType = {};
            });
        };

        $scope.changeInputType = function(){
            $scope.selectedRecipeInputType = _.find($scope.recipeInputTypes, {'name': $scope.recipeInput.type});
        };

        var getWarningsHtml = function (warnings) {
            var warningsHtml = '';
            _.forEach(warnings, function (warning) {
                warningsHtml += '<b>' + warning.id + ':</b> ' + warning.details + '<br /><br />';
            });
            warningsHtml += '<button type="button" class="btn btn-default btn-xs clear">Hide</button>';
            return warningsHtml;
        };

        $scope.validateRecipeType = function () {
            recipeService.validateRecipeType($scope.recipeType).then(function(validationResult){
                if(validationResult.warnings && validationResult.warnings.length > 0){
                    // display the warnings
                    var warningsHtml = getWarningsHtml(validationResult.warnings);
                    toastr["error"](warningsHtml);
                } else {
                    toastr["success"]('Recipe is valid.');
                }
            }).catch(function(error){
                if(error.detail){
                    toastr["error"](error.detail);
                } else {
                    toastr["error"](error);
                }
            });

        };


        $scope.saveRecipeType = function () {
            $scope.savingRecipe = true;
            console.log('save recipe: ' + $scope.recipeType.name);
            recipeService.validateRecipeType($scope.recipeType).then(function(validationResult){
                if(validationResult.warnings && validationResult.warnings.length > 0){
                    // display the warnings
                    var warningsHtml = getWarningsHtml(validationResult.warnings);
                    toastr["error"](warningsHtml);
                    $scope.savingRecipe = false;
                } else {
                    recipeService.saveRecipeType($scope.recipeType).then(function(saveResult){
                        $location.path('/recipes/types/' + saveResult.id);
                    });
                }
            }).catch(function(error){
                if(error.detail){
                    toastr['error'](error.detail);
                } else {
                    toastr['error'](error);
                }
                $scope.savingRecipe = false;
            });

            disableSaveRecipe();
        };

        $scope.addJobType = function (selectedJobType) {
            $scope.recipeType.definition.addJob(selectedJobType);
            $scope.$broadcast('redrawRecipes');
        };

        $scope.mapInput = function (providerName, providerOutput) {
            console.log('map selected job input to ' + providerName + '.' + providerOutput);
            var dependency = _.find($scope.selectedJob.dependencies, {name: providerName});

            if(dependency && dependency.connections && dependency.connections.length > 0){
                var conn = _.find(dependency.connections, { output: providerOutput, input: $scope.selectedJobInput.name });
                if(!conn){
                    dependency.connections.push({ output: providerOutput, input: $scope.selectedJobInput.name });
                }
            }
            else if(!dependency){
                dependency = {name: providerName, connections: [{ output: providerOutput, input: $scope.selectedJobInput.name }]};
                $scope.selectedJob.dependencies.push(dependency);
            }
            else {
                dependency.connections = [{ output: providerOutput, input: $scope.selectedJobInput.name }];
            }
            $scope.selectedJob.depStart = false;
            $scope.editMode = '';
            $scope.selectedJobInput = null;
            $scope.selectedInputProvider = null;
            enableSaveRecipe();
            $scope.redraw();
        };

        $scope.mapOutput = function (receiverName, receiverInput) {
            var dependency = _.find($scope.selectedOutputReceiver.dependencies, {name: $scope.selectedJob.name});

            if(dependency && dependency.connections && dependency.connections.length > 0){
                var conn = _.find(dependency.connections, { output: $scope.selectedJobOutput.name, input: receiverInput });
                if(!conn){
                    dependency.connections.push({output: $scope.selectedJobOutput.name, input: receiverInput});
                }
            }
            else if(!dependency){
                dependency = {name: $scope.selectedJob.name, connections: [{output: $scope.selectedJobOutput.name, input: receiverInput}]};
                $scope.selectedOutputReceiver.dependencies.push(dependency);
            }
            else {
                dependency.connections = [{output: $scope.selectedJobOutput.name, input: receiverInput}];
            }
            $scope.selectedOutputReceiver.depStart = false;
            $scope.editMode = '';
            $scope.selectedJobOutput = null;
            $scope.selectedOutputReceiver = null;
            enableSaveRecipe();
            $scope.redraw();
        };

        $scope.toggleAddDependency = function () {
            if ($scope.editMode === 'addDependency') {
                $scope.editMode = '';
                $scope.dependencyBtnClass = 'fa-plus';
                $('.recipeNode:not(".selected-node")').removeClass('selected-node-selectable');
            } else {
                console.log('toggle addDependency mode');
                $scope.editMode = 'addDependency';
                $scope.dependencyBtnClass = 'fa-minus';
                $('.recipeNode:not(".selected-node")').addClass('selected-node-selectable');
            }
        };

        $scope.toggleAddInput = function (jobinput) {
            if ($scope.editMode === 'addInput') {
                $scope.editMode = '';
                $('.recipeNode:not(".selected-node")').removeClass('selected-node-selectable');
            } else {
                $scope.selectedJobInput = jobinput;
                console.log('toggle addInput mode');
                $scope.editMode = 'addInput';
                $('.recipeNode:not(".selected-node")').addClass('selected-node-selectable');
            }
        };

        $scope.toggleAddOutput = function (joboutput) {
            if ($scope.editMode === 'addOutput') {
                $scope.editMode = '';
                $('.recipeNode:not(".selected-node")').removeClass('selected-node-selectable');
            } else {
                $scope.selectedJobOutput = joboutput;
                console.log('toggle addOutput mode');
                $scope.editMode = 'addOutput';
                $('.recipeNode:not(".selected-node")').addClass('selected-node-selectable');
            }
        };

        $scope.removeDependency = function (depName) {
            var removedDeps = _.remove($scope.selectedJob.dependencies, function (dep) {
                return dep.name === depName;
            });
            console.log('removed ' + removedDeps.length + ' dependencies.');
            enableSaveRecipe();
            $scope.redraw();
        };

        $scope.removeInputMapping = function (depName, depOutput) {
            var dep = _.find($scope.selectedJob.dependencies, {name: depName});
            if (dep && dep.connections) {
                var removedCon = _.remove(dep.connections, function (conn) {
                    return conn.output === depOutput;
                });
                console.log('removed ' + removedCon.length + ' input connections.');
                enableSaveRecipe();
                $scope.redraw();
            }
        };

        $scope.removeOutputMapping = function (jobName, depOutput) {
            // we have to remove output mapping from the job where the dependency is defined
            var receiver = _.find($scope.recipeType.definition.jobs,{name: jobName});
            var dep = _.find(receiver.dependencies, {name: $scope.selectedJob.name});
            if (dep && dep.connections) {
                var removedCon = _.remove(dep.connections, function (conn) {
                    return conn.output === depOutput;
                });
                console.log('removed ' + removedCon.length + ' output connections.');
                enableSaveRecipe();
                $scope.redraw();
            }
        };

        $scope.selectItem = function(item){
            $scope.selectedItem = item;
        };

        $scope.$on('redrawRecipes', function () {
            $scope.redraw();
        });

        var addDependency = function(jobName){
            console.log($scope.selectedJob.name + '->' + jobName);
            if (!$scope.selectedJob.dependencies) {
                $scope.selectedJob.dependencies = [];
            }
            var existingDependency = _.find($scope.selectedJob.dependencies, {name: jobName});

            if(!existingDependency){ $scope.selectedJob.dependencies.push({name: jobName}); }
            $scope.selectedJob.depStart = false;
            $scope.editMode = '';
            $scope.dependencyBtnClass = 'fa-plus';

        };

        var getIoMappings = function () {
            if($scope.recipeType.definition){
                _.forEach($scope.recipeType.definition.jobs, function (job) {
                    // populate the current jobType
                    /*var thisJobType = _.find($scope.recipeType.job_types,{id: job.job_type_id});
                    job.job_type = thisJobType;*/

                    // find dependents
                    if (job.job_type && job.job_type.job_type_interface) {
                        _.forEach(job.job_type.job_type_interface.output_data, function (jobOutput, key) {
                            if (jobOutput) {
                                var deps = getDependents(job.name,jobOutput.name);
                                jobOutput.dependents = deps;
                            }
                        });
                        // add dependency mappings
                        _.forEach(job.job_type.job_type_interface.input_data, function (jobInput, key) {
                            if (jobInput) {
                                var inputMappings = [];
                                _.forEach(job.dependencies, function (dependency,key) {
                                    _.forEach(dependency.connections, function (conn,key) {
                                        if (conn.input === jobInput.name) {
                                            inputMappings.push({
                                                name: dependency.name,
                                                output: conn.output,
                                                input: conn.input
                                            });
                                        }
                                    });
                                });
                                _.forEach(job.recipe_inputs, function(recipeInput, key){
                                    if(recipeInput.job_input === jobInput.name){
                                        inputMappings.push({
                                            name: 'recipe',
                                            output: recipeInput.recipe_input,
                                            input: recipeInput.job_input
                                        });
                                    }
                                });
                                jobInput.dependencies = inputMappings;
                            }
                        });

                    }
                });
            }

        };

        var initialize = function () {
            getJobTypes();

            if($rootScope.user){
                $scope.readonly = false;
            }
        };

        var initGraph = function () {
            // ******
            // setup D3 container and Graph
            // ******
            //$scope.selectedJob = null;
            function clicked() {
                var d = d3.event;
                var x = d3.event.x;
                var y = d3.event.y;
                var width = parseInt(svg.style("width").replace(/px/, ""));
                var height = parseInt(svg.style("height").replace(/px/, ""));

                inner.attr("transform", "translate(" + width / 2 + "," + height / 2 + ")scale(2)translate(" + -x + "," + -y + ")");

                //inner.attr("transform", "translate(50px, 50px)scale(2,3)");

                console.log(d);
            }

            svg = d3.select("svg");
            inner = svg.select("g"); //.on("click", clicked);
            // Set up zoom support
            zoom = d3.behavior.zoom().on("zoom", function () {
                inner.attr("transform", "translate(" + d3.event.translate + ")" +
                    "scale(" + d3.event.scale + ")");
            });
            svg.call(zoom);

            render = new dagreD3.render();

            // Left-to-right layout
            graph = new dagreD3.graphlib.Graph();
            graph.setGraph({
                nodesep: 70,
                ranksep: 50,
                rankdir: "TB",
                marginx: 20,
                marginy: 20
            });
        };

        drawGraph = function (isUpdate) {
            $scope.isUpdate = true;
            if($scope.recipe){
                $scope.lastStatusChange = $scope.recipe.last_modified ? moment.duration(moment.utc($scope.recipe.last_modified).diff(moment.utc())).humanize(true) : '';
            }

            var jobs = [];
            if ($scope.recipeType.definition) {
                jobs = $scope.recipeType.definition.jobs;
            }
            var childCounts = [];
            // create graph objects
            for (var idx in jobs) {
                var job = jobs[idx];
                var jobType = _.find($scope.jobTypeValues, 'id', job.job_type_id);
                if ( job.dependencies === undefined || job.dependencies.length < 1) {
                    job.depStart = true;
                }
                var className = getRecipeTypeJobClassName(job);
                if (job.count > 10000) {
                    className += ' warn';
                }
                var html = '<div>';
                //var html = "<div onclick=\"console.log('" + job.job_type.name + "')\">";
                html += '<span class="status"></span>';
                //   html += "<span class=consumers>"+worker.consumers+"</span>";
                html += '<span class="name">';
                if (jobType) {
                    //console.log(job.jobType);
                    html += '<div id="' + job.name + '" class="recipeNode" onclick="nodeClick(\'' + job.name + '\')"><span class="name">' + jobType.getIcon() + ' ' + job.name + '</span></div>';
                    //if(jobType.name){
                    //    html += '<div id="' + job.name + '" class="recipeNode" onclick="nodeClick(\'' + job.name + '\')"><span class="name">' + jobType.getIcon() + ' ' + jobType.title + '</span></div>';
                    //} else {
                    //    html += '<div id="' + job.name + '" class="recipeNode" onclick="nodeClick(\'' + job.name + '\')"><span class="name">' + jobType.getIcon() + ' ' + job.name + '</span></div>';
                    //}

                }
                html += '</span>';
                //   html += "<span class=queue><span class=counter>"+worker.count+"</span></span>";
                html += '</div>';
                graph.setNode(job.name, {
                    labelType: 'html',
                    label: html,
                    rx: 5,
                    ry: 5,
                    padding: 0,
                    class: className
                });
                // setup edges
                for (var d in job.dependencies) {
                    var dep = job.dependencies[d];

                    if (dep.name) {
                        graph.setEdge(dep.name, job.name, {
                            //labelType: 'html',
                            //label: dep.name + '-->' + job.name,
                            width: 20

                        });
                        if (childCounts[dep.name]) {
                            childCounts[dep.name] += 1;
                        } else {
                            childCounts[dep.name] = 1;
                        }
                    }
                }
            }

            // set start node and edges
            graph.setNode('start', {
                labelType: 'html',
                label: '<div id="Start" class="recipeNode" onclick="nodeClick(\'start\')"><span class=name>Start</span></div>',
                rx: 5,
                ry: 5,
                padding: 0
            });
            startJob = {
                name: 'Start',
                job_type: {
                    title: 'Start'
                }
            };
            var noDeps = _.filter(jobs, 'depStart', true);
            for (var n in noDeps) {
                graph.setEdge('start', noDeps[n].name, {
                    width: 20
                });
            }

            // set end node and edges
            graph.setNode('end', {
                labelType: 'html',
                label: '<div><span class=name>End</span></div>',
                rx: 5,
                ry: 5,
                padding: 0
            });
            var noChildren =_.filter(jobs, function (job) {
                return !childCounts[job.name];
            });
            for (var o in noChildren) {
                graph.setEdge(noChildren[o].name, 'end', {
                    width: 20
                });
            }

            // wait for current call stack to clear
            _.defer(function () {
                inner.call(render, graph);

                // Zoom and scale to fit
                var zoomScale = zoom.scale();
                var graphWidth = graph.graph().width + 40;
                var graphHeight = graph.graph().height + 40;
                var width = parseInt(svg.style("width").replace(/px/, ""));
                var height = parseInt(svg.style("height").replace(/px/, ""));
                //zoomScale = Math.min(width / graphWidth, height / graphHeight);
                //if(zoomScale<0.80){
                //  zoomScale = 0.80;
                // }
                zoomScale = 0.75;
                if(zoomScale < 1){
                    //console.log('zoomScale: ' + zoomScale);
                    var translate = [0,0];// [(width*zoomScale)-(graphWidth*zoomScale), 0];
                    zoom.translate(translate);
                    zoom.scale(zoomScale);
                    zoom.event(isUpdate ? svg.transition().duration(500) : d3.select("svg"));
                }

                // add selected class to appropriate node
                if($scope.selectedJob){
                    $('#' + $scope.selectedJob.name).addClass('selected-node');
                }
            });
        };

        var getDependents = function (name,outputName) {
            var results = [];

            _.forEach($scope.recipeType.definition.jobs, function (job, key) {
                if (job.name !== name) {
                    _.forEach(job.dependencies, function (dependency, key) {
                        if (dependency.name === name) {
                            _.forEach(dependency.connections, function (conn, key) {
                                if (conn.output === outputName) {
                                    results.push({
                                        name: job.name,
                                        output: conn.output,
                                        input: conn.input
                                    });
                                }
                            });
                        }
                    });
                }
            });
            return results;
        };

        initialize();

    }).directive('aisScaleRecipeGraphViewer', function () {
        'use strict';
        /**
         * Usage: <ais-scale-recipe-viewer recipe="recipe" />
         */
        return {
            controller: 'aisScaleRecipeGraphViewerController',
            templateUrl: 'modules/recipes/partials/recipeGraphViewerTemplate.html',
            restrict: 'E',
            scope: {
                recipeType: '=',
                recipe: '=',
                isModified: '=modified',
                allowEdit: '=',
                hasContainer: '='
            },
            link: function (scope) {
                angular.element(document).ready(function () {
                    var elHeight = document.getElementsByClassName('recipe-viewer-title')[0].scrollHeight;
                    scope.detailMaxHeight = scope.$parent.detailMaxHeight ? scope.$parent.detailMaxHeight - elHeight : 700;
                    scope.detailContainerStyle = 'height: ' + scope.detailMaxHeight + 'px; max-height: ' + scope.detailMaxHeight + 'px; overflow-y: auto;';
                });
            }
        };

    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').factory('RecipeType', function (scaleConfig, RecipeTypeDefinition) {
        var RecipeType = function (id, name, version, title, description, is_active, definition, created,  last_modified, archived) {
            this.id = id;
            this.name = name || 'new-recipe';
            this.version = version || '1.0';
            this.title = title || 'New Recipe';
            this.description = description || 'New Recipe';
            this.is_active = is_active;
            this.definition = definition ? RecipeTypeDefinition.transformer(definition) : new RecipeTypeDefinition();
            this.created = created;
            this.last_modified = last_modified;
            this.archived = archived;
            this.modified = false;
        };

        // static methods, assigned to class
        RecipeType.build = function (data) {
            if(data){
                return new RecipeType(
                    data.id,
                    data.name,
                    data.version,
                    data.title,
                    data.description,
                    data.is_active,
                    data.definition,
                    data.created,
                    data.last_modified,
                    data.archived
                );
            }
            return new RecipeType();
        };

        RecipeType.transformer = function (data) {
            if (angular.isArray(data)) {
                return data.map(RecipeType.build);
            }
            return RecipeType.build(data);
        };

        return RecipeType;
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').factory('RecipeTypeDefinition', function (scaleConfig, RecipeTypeDefinitionJob, JobTypeInputData) {

        var self = this;
        // private methods
        var RecipeTypeDefinition = function (input_data, version, jobs) {
            this.input_data = input_data ? JobTypeInputData.transformer(input_data) : [];
            this.version = version || '1.0';
            this.jobs = jobs ? RecipeTypeDefinitionJob.transformer(jobs) : [];
        };

        // public methods
        RecipeTypeDefinition.prototype = {
            addJob: function (jobType) {
                var job = {
                    recipe_inputs: [],
                    name: jobType.name,
                    job_type_id: jobType.id,
                    job_type: jobType
                };
                this.jobs.push(job);
            }
        };

        // static methods, assigned to class
        RecipeTypeDefinition.build = function (data) {
            if(data){
                return new RecipeTypeDefinition(
                    data.input_data,
                    data.version,
                    data.jobs
                );
            }
            return new RecipeTypeDefinition();
        };

        RecipeTypeDefinition.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(RecipeTypeDefinition.build);
            }
            return RecipeTypeDefinition.build(data);
        };

        return RecipeTypeDefinition;
    });
})();

(function(){
    'use strict';

    angular.module('scaleApp').factory('RecipeTypeDefinitionJob', function (scaleConfig, JobTypeDetails) {
        // private methods
        var RecipeTypeDefinitionJob = function (recipe_inputs, name, job_type_id, dependencies) {
            this.recipe_inputs = recipe_inputs;
            this.name = name;
            this.job_type_id = job_type_id;
            this.dependencies = dependencies || [];
        };

        // static methods, assigned to class
        RecipeTypeDefinitionJob.build = function (data) {
            if (data) {
                return new RecipeTypeDefinitionJob(
                    data.recipe_inputs,
                    data.name,
                    data.job_type_id,
                    data.dependencies
                );
            }
            return new RecipeTypeDefinitionJob();
        };

        RecipeTypeDefinitionJob.new = function () {
            return this.build({
                recipe_inputs: null,
                job_type_id: null,
                name: null,
                dependencies: null
            });
        };

        RecipeTypeDefinitionJob.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(RecipeTypeDefinitionJob.build)
                    .filter(Boolean);
            }
            return RecipeTypeDefinitionJob.build(data);
        };


        return RecipeTypeDefinitionJob;

    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').factory('RecipeTypeDetail', function (scaleConfig, RecipeTypeDefinition, JobTypeDetails) {
        var RecipeTypeDetail = function (id, name, version, title, description, is_active, definition, created, last_modified, archived, job_types) {
            this.id = id;
            this.name = name;
            this.version = version;
            this.title = title;
            this.description = description;
            this.is_active = is_active;
            this.definition = RecipeTypeDefinition.transformer(definition);
            this.created = created;
            this.last_modified = last_modified;
            this.archived = archived;
            this.job_types = JobTypeDetails.transformer(job_types);
            this.modified = false;
        };

        // static methods, assigned to class
        RecipeTypeDetail.build = function (data) {
            if (data) {
                return new RecipeTypeDetail(
                    data.id,
                    data.name,
                    data.version,
                    data.title,
                    data.description,
                    data.is_active,
                    data.definition,
                    data.created,
                    data.last_modified,
                    data.archived,
                    data.job_types
                );
            }
            return new RecipeTypeDetail();
        };

        RecipeTypeDetail.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(RecipeTypeDetail.build);
            }
            return RecipeTypeDetail.build(data);
        };

        return RecipeTypeDetail;
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').factory('RecipeTypeValidation', function (RecipeTypeDefinition) {
        var RecipeTypeValidation = function (name, version, title, description, definition) {
            this.name = name;
            this.version = version;
            this.title = title;
            this.description = description;
            this.definition = RecipeTypeDefinition.transformer(definition);
        };

        // static methods, assigned to class
        RecipeTypeValidation.build = function (data) {
            if (data) {
                return new RecipeTypeValidation(
                    data.name,
                    data.version,
                    data.title,
                    data.description,
                    data.definition
                );
            }
            return new RecipeTypeValidation();
        };

        RecipeTypeValidation.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(RecipeTypeValidation.build);
            }
            return RecipeTypeValidation.build(data);
        };

        return RecipeTypeValidation;
    });
})();
(function () {
    'use strict';

    angular.module('scaleApp').factory('Recipe', function (RecipeType, scaleService) {
        var Recipe = function (id, created, completed, last_modified, recipe_type) {
            this.id = id;
            this.created = created;
            this.completed = completed;
            this.last_modified = last_modified;
            this.recipe_type = RecipeType.transformer(recipe_type);
        };

        // public methods
        Recipe.prototype = {
            getDuration: function () {
                return scaleService.calculateDuration(this.created, this.last_modified);
            }
        };

        // static methods, assigned to class
        Recipe.build = function (data) {
            if (data) {
                return new Recipe(
                    data.id,
                    data.created,
                    data.completed,
                    data.last_modified,
                    data.recipe_type
                );
            }
            return new Recipe();
        };

        Recipe.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(Recipe.build)
                    .filter(Boolean);
            }
            return Recipe.build(data);
        };

        return Recipe;
    });
})();
(function () {
    'use strict';

    angular.module('scaleApp').factory('RecipeDetails', function (RecipeData, RecipeTypeDefinition, RecipeType, RecipeJobContainer, scaleConfig) {
        var RecipeDetails = function (id, created, completed, last_modified, data, recipe_type, jobs) {
            this.id = id;
            this.created = created;
            this.completed = completed;
            this.completed_formatted = this.completed ? moment.utc(this.completed).toISOString() : this.completed;
            this.last_modified = last_modified;
            this.data = RecipeData.transformer(data);
            this.recipe_type = RecipeType.transformer(recipe_type);
            this.jobs = RecipeJobContainer.transformer(jobs);
        };

        // static methods, assigned to class
        RecipeDetails.build = function (data) {
            if (data) {
                return new RecipeDetails(
                    data.id,
                    data.created,
                    data.completed,
                    data.last_modified,
                    data.data,
                    data.recipe_type,
                    data.jobs
                );
            }
            return new RecipeDetails();
        };

        RecipeDetails.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(RecipeDetails.build)
                    .filter(Boolean);
            }
            return RecipeDetails.build(data);
        };

        return RecipeDetails;
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').factory('RecipeJob', function (JobType) {
        var RecipeJob = function (id, status, job_type) {
            this.id = id;
            this.status = status;
            this.job_type = JobType.transformer(job_type);
        };

        // static methods, assigned to class
        RecipeJob.build = function (data) {
            if (data) {
                return new RecipeJob(
                    data.id,
                    data.status,
                    data.job_type
                );
            }
            return new RecipeJob();
        };

        RecipeJob.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(RecipeJob.build)
                    .filter(Boolean);
            }
            return RecipeJob.build(data);
        };

        return RecipeJob;
    });
})();
(function () {
    'use strict';

    angular.module('scaleApp').factory('RecipeJobContainer', function (RecipeJob) {
        var RecipeJobContainer = function (job_name, job) {
            this.job_name = job_name;
            this.job = RecipeJob.transformer(job);
        };

        // static methods, assigned to class
        RecipeJobContainer.build = function (data) {
            if (data) {
                return new RecipeJobContainer(
                    data.job_name,
                    data.job
                );
            }
            return new RecipeJobContainer();
        };

        RecipeJobContainer.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(RecipeJobContainer.build)
                    .filter(Boolean);
            }
            return RecipeJobContainer.build(data);
        };

        return RecipeJobContainer;
    });
})();
(function () {
    'use strict';

    angular.module('scaleApp').factory('RecipeData', function () {
        var RecipeData = function (input_data, version, workspace_id) {
            this.input_data = input_data;
            this.version = version;
            this.workspace_id = workspace_id;
        };

        // static methods, assigned to class
        RecipeData.build = function (data) {
            if (data) {
                return new RecipeData(
                    data.input_data,
                    data.version,
                    data.workspace_id
                );
            }
            return new RecipeData();
        };

        RecipeData.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(RecipeData.build)
                    .filter(Boolean);
            }
            return RecipeData.build(data);
        };

        return RecipeData;
    });
})();
(function () {
    'use strict';
    /**
     *
     */
    angular.module('scaleApp').service('recipeService', function ($http, $q, $timeout, scaleConfig, RecipeType, RecipeTypeDetail, Recipe, RecipeDetails, RecipeTypeValidation) {
        var getRecipesParams = function (page, page_size, started, ended, order, completed, recipe_type_id, recipe_type_name, url) {
            return {
                page: page,
                page_size: page_size,
                started: started,
                ended: ended,
                order: order,
                completed: completed,
                recipe_type_id: recipe_type_id,
                recipe_type_name: recipe_type_name,
                url: url
            };
        };

        return {
            getRecipeTypes: function () {
                var d = $q.defer();
                $http.get(scaleConfig.urls.getRecipeTypes()).success(function (data) {
                    d.resolve(RecipeType.transformer(data.results));
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },

            getRecipeTypeDetail: function (id) {
              var d = $q.defer();

              $http.get(scaleConfig.urls.getRecipeTypeDetail(id)).success(function (data) {
                var returnData = RecipeTypeDetail.transformer(data);
                d.resolve(returnData);
              });
              return d.promise;
            },

            getRecipes: function (params) {
                params = params || getRecipesParams();
                var d = $q.defer();

                $http({
                    url: params.url ? params.url : scaleConfig.urls.getRecipes(),
                    method: 'GET',
                    params: params
                }).success(function (data) {
                    data.results = Recipe.transformer(data.results);
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });

                return d.promise;
            },

            getRecipeDetails: function (id) {
                var d = $q.defer();
                $http.get(scaleConfig.urls.getRecipeDetails(id)).success(function (data) {
                    var result = RecipeDetails.transformer(data);
                    d.resolve(result);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },

            saveRecipeType: function(recipeType) {
                var d = $q.defer();
                var cleanRecipeType = RecipeTypeValidation.transformer(recipeType);

                $http.post(scaleConfig.urls.saveRecipeType(),cleanRecipeType).success(function(result){
                    recipeType.id = result;
                    d.resolve(recipeType);
                }).error(function(error){
                    d.reject(error);
                });

                return d.promise;
            },

            validateRecipeType: function(recipeType) {
                var d = $q.defer();
                var cleanRecipeType = RecipeTypeValidation.transformer(recipeType);

                $http.post(scaleConfig.urls.validateRecipeType(),cleanRecipeType).success(function(result){
                    d.resolve(result);
                }).error(function(error){
                    d.reject(error);
                })

                return d.promise;
            }
        };
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').controller('jobsController', function($rootScope, $scope, $location, $modal, navService, jobService, jobTypeService, jobExecutionService, statsService, uiGridConstants, scaleConfig, subnavService, gridFactory, queueService, scaleService, userService) {

        var jobsParams = {
            page: null, page_size: null, started: null, ended: null, order: $rootScope.jobsControllerOrder || '-last_modified', status: null, job_type_id: null, job_type_name: null, job_type_category: null, url: null
        };

        // check for jobsParams in query string, and update as necessary
        _.forEach(_.pairs(jobsParams), function (param) {
            var value = _.at($location.search(), param[0]);
            if (value.length > 0) {
                jobsParams[param[0]] = value.length > 1 ? value : value[0];
            }
        });

        var gridPageNumber = jobsParams.page || 1,
            filteredByJobType = jobsParams.job_type_id ? true : false,
            filteredByJobStatus = jobsParams.status ? true : false,
            filteredByOrder = jobsParams.order ? true : false;

        $scope.jobsData = {};
        $scope.loading = true;
        $scope.jobTypeValues = [];
        $scope.selectedJobType = jobsParams.job_type_id || 0;
        $scope.jobStatusValues = scaleConfig.jobStatus;
        $scope.selectedJobStatus = jobsParams.status || $scope.jobStatusValues[0];
        $scope.subnavLinks = scaleConfig.subnavLinks.jobs;
        $scope.actionClicked = false;
        $scope.gridStyle = '';
        $scope.readonly = true;

        subnavService.setCurrentPath('jobs');

        var defaultColumnDefs = [
            {
                field: 'job_type',
                displayName: 'Job Type',
                cellTemplate: '<div class="ui-grid-cell-contents"><span ng-bind-html="row.entity.job_type.getIcon()"></span> {{ row.entity.job_type.title }} {{ row.entity.job_type.version }}</div>',
                filterHeaderTemplate: '<div class="ui-grid-filter-container"><select class="form-control input-sm" ng-model="grid.appScope.selectedJobType"><option ng-if="grid.appScope.jobTypeValues[$index]" ng-selected="{{ grid.appScope.jobTypeValues[$index].id == grid.appScope.selectedJobType }}" value="{{ grid.appScope.jobTypeValues[$index].id }}" ng-repeat="jobType in grid.appScope.jobTypeValues track by $index">{{ grid.appScope.jobTypeValues[$index].title }} {{ grid.appScope.jobTypeValues[$index].version }}</option></select>'
            },
            {
                field: 'created',
                displayName: 'Created',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.created_formatted }}</div>'
            },
            {
                field: 'last_modified',
                displayName: 'Last Modified',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.last_modified_formatted }}</div>'
                //cellFilter: 'date:\'' + scaleConfig.dateFormats.day_minute_utc + '\'',
            },
            { field: 'duration', enableFiltering: false, enableSorting: false, cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.getDuration() }}</div>' },
            {
                field: 'status',
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.status }} <button ng-show="((!grid.appScope.readonly) && (row.entity.status === \'FAILED\' || row.entity.status === \'CANCELED\'))" ng-click="grid.appScope.requeueJob(row.entity)" class="btn btn-xs btn-default" title="Requeue Job"><i class="fa fa-repeat"></i></button> <button ng-show="!grid.appScope.readonly && row.entity.status !== \'COMPLETED\' && row.entity.status !== \'CANCELED\'" ng-click="grid.appScope.cancelJob(row.entity)" class="btn btn-xs btn-default" title="Cancel Job"><i class="fa fa-ban"></i></button></div>',
                filterHeaderTemplate: '<div class="ui-grid-filter-container"><select class="form-control input-sm" ng-model="grid.appScope.selectedJobStatus"><option ng-selected="{{ grid.appScope.jobStatusValues[$index] == grid.appScope.selectedJobStatus }}" value="{{ grid.appScope.jobStatusValues[$index] }}" ng-repeat="status in grid.appScope.jobStatusValues track by $index">{{ status.toUpperCase() }}</option></select></div>'
            },
            {
                field: 'id',
                displayName: 'Log',
                enableFiltering: false,
                sortable: false,
                width: 60,
                cellTemplate: '<div class="ui-grid-cell-contents text-center"><button ng-click="grid.appScope.showLog(row.entity.id)" class="btn btn-xs btn-default"><i class="fa fa-file-text"></i></button></div>'
            }
        ];

        $scope.gridOptions = gridFactory.defaultGridOptions();
        $scope.gridOptions.paginationCurrentPage = parseInt(jobsParams.page || 1);
        $scope.gridOptions.paginationPageSize = parseInt(jobsParams.page_size) || $scope.gridOptions.paginationPageSize;
        var colDefs = $rootScope.colDefs ? $rootScope.colDefs : defaultColumnDefs;
        $scope.gridOptions.columnDefs = gridFactory.applySortConfig(colDefs, jobsParams);
        $scope.gridOptions.data = [];
        $scope.gridOptions.onRegisterApi = function (gridApi) {
                //set gridApi on scope
                $scope.gridApi = gridApi;
                $scope.gridApi.selection.on.rowSelectionChanged($scope, function (row) {
                    if ($scope.actionClicked) {
                        $scope.actionClicked = false;
                    } else {
                        $scope.$apply(function(){
                            $location.path('/jobs/job/' + row.entity.id);
                        });
                    }

                });
                $scope.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                    jobsParams.page = currentPage;
                    jobsParams.page_size = pageSize;
                    console.log('gridApi');
                    $scope.filterResults();
                });
                $scope.gridApi.core.on.sortChanged($scope, function (grid, sortColumns) {
                    $rootScope.colDefs = null;
                    _.forEach($scope.gridApi.grid.columns, function (col) {
                        col.colDef.sort = col.sort;
                    });
                    $rootScope.colDefs = $scope.gridApi.grid.options.columnDefs;
                    var sortArr = [];
                    _.forEach(sortColumns, function (col) {
                        sortArr.push(col.sort.direction === 'desc' ? '-' + col.field : col.field);
                    });
                    updateJobOrder(sortArr);
                });
            };


        $scope.showStatus = function (status) {
            return _.includes($scope.jobStatusValues, status);
        };

        var updateJobType = function (value) {
            if (value != jobsParams.job_type_id) {
                jobsParams.page = 1;
            }
            jobsParams.job_type_id = value == 0 ? null : value;
            jobsParams.page_size = $scope.gridOptions.paginationPageSize;
            console.log('selectedJobType');
            if (!$scope.loading) {
                $scope.filterResults();
            }
        };

        $scope.$watch('selectedJobType', function (value) {
            if ($scope.loading) {
                if (filteredByJobType) {
                    updateJobType(value);
                }
            } else {
                filteredByJobType = value != 0;
                updateJobType(value);
            }
        });

        var updateJobStatus = function (value) {
            if (value != jobsParams.status) {
                jobsParams.page = 1;
            }
            jobsParams.status = value === 'VIEW ALL' ? null : value;
            jobsParams.page_size = $scope.gridOptions.paginationPageSize;
            console.log('selectedJobStatus');
            if (!$scope.loading) {
                $scope.filterResults();
            }
        };

        $scope.$watch('selectedJobStatus', function (value) {
            if ($scope.loading) {
                if (filteredByJobStatus) {
                    updateJobStatus(value);
                }
            } else {
                filteredByJobStatus = value !== 'VIEW ALL';
                updateJobStatus(value);
            }
        });

        var updateJobOrder = function (sortArr) {
            jobsParams.order = sortArr.length > 0 ? sortArr : null;
            filteredByOrder = sortArr.length > 0;
            $scope.filterResults();
        };

        /*$scope.$watch('gridApi', function (gridApi) {
            if (filteredByOrder) {
                gridApi.core.raise.sortChanged();
            }
        });*/

        $scope.showLog = function (jobId) {
            // show log modal
            $scope.actionClicked = true;
            console.log('show log modal');
            jobService.getJobDetail(jobId).then(function (data) {
                $scope.selectedJob = data.job_type.title + ' ' + data.job_type.version;
                $scope.jobExecution = data.getLatestExecution();
                var modalInstance = $modal.open({
                    animation: true,
                    templateUrl: 'showLog.html',
                    scope: $scope,
                    size: 'lg'
                });
            });
        };

        $scope.filterResults = function () {
            _.forEach(_.pairs(jobsParams), function (param) {
                $location.search(param[0], param[1]);
            });
        };

        $scope.requeueJob = function (job) {
            $scope.actionClicked = true;
            $scope.loading = true;
            job.status = 'REQUEUE';
            queueService.requeueJob(job.id).then(function (data) {
                toastr['success']('Requeued Job');
                job.status = 'QUEUED';
            }).catch(function (error) {
                toastr['error'](error);
                console.log(error);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        $scope.cancelJob = function (job) {
            $scope.actionClicked = true;
            $scope.loading = true;
            var originalStatus = job.status;
            job.status = 'CANCEL';
            jobService.updateJob(job.id, { status: 'CANCELED' }).then(function (data) {
                toastr['success']('Job Canceled');
                job.status = 'CANCELED';
            }).catch(function (error) {
                toastr['error'](error);
                console.log(error);
                job.status = originalStatus;
            }).finally(function () {
                $scope.loading = false;
            });
        };

        var getJobs = function () {
            jobService.getJobsOnce(jobsParams).then(function (data) {
                $scope.jobsData = data.results;
                $scope.gridOptions.totalItems = data.count;
                $scope.gridOptions.data = data.results;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        var getJobTypes = function () {
            jobTypeService.getJobTypesOnce().then(function (data) {
                $scope.jobTypeValues = data.results;
                $scope.jobTypeValues.unshift({ name: 'VIEW ALL', title: 'VIEW ALL', version: '', id: 0 });
                /*if (!filteredByJobType && !filteredByJobStatus && !filteredByOrder) {
                    getJobs();
                } else {
                    if (filteredByOrder) {
                        updateJobOrder(jobsParams.order);
                    }
                }*/
                getJobs(jobsParams);
            }).catch(function (error) {
                $scope.loading = false;
                console.log(error);
            });
        };

        var initialize = function () {
            if (typeof $rootScope.colDefs === 'undefined') {
                // root column defs have not been altered by user, so set up defaults
                if (!jobsParams.order) {
                    jobsParams.order = '-last_modified';
                    $location.search('order', jobsParams.order).replace();
                }
                if (!jobsParams.page_size) {
                    jobsParams.page_size = $scope.gridOptions.paginationPageSize;
                    $location.search('page_size', jobsParams.page_size).replace();
                }
            }
            getJobTypes();
            $rootScope.user = userService.getUserCreds();

            if($rootScope.user){
                $scope.readonly = false;
            }
            navService.updateLocation('jobs');
        };

        initialize();

        angular.element(document).ready(function () {
            // set container heights equal to available page height
            var viewport = scaleService.getViewportSize(),
                offset = scaleConfig.headerOffset,
                gridMaxHeight = viewport.height - offset;

            $scope.gridStyle = 'height: ' + gridMaxHeight + 'px; max-height: ' + gridMaxHeight + 'px; overflow-y: auto;';
        });
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').controller('jobDetailController', function ($scope, $rootScope, $location, $routeParams, $modal, navService, jobService, jobExecutionService, nodeService, queueService, scaleConfig, subnavService, userService) {
        $scope.job = {};
        $scope.jobId = $routeParams.id;
        $scope.subnavLinks = scaleConfig.subnavLinks.jobs;
        subnavService.setCurrentPath('jobs');
        $scope.loadingJobDetail = false;
        $scope.latestExecution = null;
        $scope.executionLog = null;
        $scope.executionDetails = null;
        $scope.selectedExectuionDetailValues = null;
        $scope.timeline = [];
        $scope.readonly = true;
        $scope.jobErrorCreated = '';
        $scope.jobErrorLastModified = '';
        $scope.lastStatusChange = '';
        $scope.triggerOccurred = '';

        $scope.showLog = function (execution) {
            $scope.selectedExecutionLog = execution;
            var modalInstance = $modal.open({
                animation: true,
                templateUrl: 'showLog.html',
                scope: $scope,
                //size: 'lg',
                windowClass: 'log-modal-window'
            });
        };

        $scope.showExecutionDetails = function (executionId) {
            jobExecutionService.getJobExecutionDetails(executionId).then(function (data) {
                $scope.selectedExecutionDetails = data;
                $scope.selectedExecutionDetailValues = _.pairs(data);
                var modalInstance = $modal.open({
                    animation: true,
                    templateUrl: 'showExecutionDetails.html',
                    scope: $scope,
                    size: 'lg'
                });
            });
        };

        $scope.mediaTypeClass = function (mediaType) {
            var mediaTypeCfg = _.find(scaleConfig.mediaTypes, 'mimeType', mediaType);
            if (mediaTypeCfg) {
                return mediaTypeCfg.icon;
            } else {
                return null;
            }
        };

        $scope.requeueJob = function(jobId){
            $scope.jobStatus = 'REQUEUE';
            $scope.loading = true;
            queueService.requeueJob(jobId).then(function (data) {
                toastr['success']('Requeued Job');
                getJobDetail(jobId);
            }).catch(function (error) {
                toaster['error'](error);
                console.log(error);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        var getJobDetail = function (jobId) {
            $scope.loadingJobDetail = true;
            jobService.getJobDetail(jobId).then(function (data) {
                $scope.job = data;
                $scope.timeline = calculateTimeline(data);
                $scope.publishedProducts = _.where(data.products, { 'is_published': true });
                $scope.unpublishedProducts = _.where(data.products, { 'is_published': false });
                $scope.publishedProductsGrouped = _.pairs(_.groupBy($scope.publishedProducts, 'job_exe.id'));
                $scope.latestExecution = data.getLatestExecution();
                $scope.jobErrorCreated = data.error ? moment.utc(data.error.created).toISOString() : '';
                $scope.lastStatusChange = data.last_status_change ? moment.duration(moment.utc(data.last_status_change).diff(moment.utc())).humanize(true) : '';
                $scope.triggerOccurred = data.event.occurred ? moment.duration(moment.utc(data.event.occurred).diff(moment.utc())).humanize(true) : '';
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                $scope.loadingJobDetail = false;
            });
        };

        var calculateTimeline = function (job) {
            var tl = [];
            tl.push({ taskName: 'Created', started: job.created ? moment.utc(job.created).toDate() : job.created, ended: job.queued ? moment.utc(job.queued).toDate() : job.queued });
            tl.push({ taskName: 'Queued', started: job.queued ? moment.utc(job.queued).toDate() : job.queued, ended: job.started ? moment.utc(job.started).toDate() : job.started });
            tl.push({ taskName: 'Executed', started: job.started ? moment.utc(job.started).toDate() : job.started, ended: job.ended ? moment.utc(job.ended).toDate() : job.ended });

            return tl;
        };

        var initialize = function () {
            navService.updateLocation('jobs');

            $rootScope.user = userService.getUserCreds();
            if($rootScope.user){
                $scope.readonly = false;
            }

            getJobDetail($scope.jobId);
        };

        initialize();
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').controller('jobExecutionDetailController', function ($scope, $location, $routeParams, navService, jobExecutionService, nodeService, scaleConfig, subnavService) {
        $scope.jobExecution = {};
        $scope.jobExecutionId = $routeParams.id;
        $scope.loading = true;
        $scope.subnavLinks = scaleConfig.subnavLinks.jobs;
        subnavService.setCurrentPath('jobs/runs');

        var getJobExecutionDetail = function (jobExecutionId) {
            jobExecutionService.getJobExecutionDetail(id).then(function (data) {
                $scope.jobExecution = data;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        var initialize = function () {
            getJobExecutionDetail($routeParams.id);
            navService.updateLocation('jobs');
        };

        initialize();
    });
})();
(function () {
    'use strict';

    angular.module('scaleApp').controller('jobExecutionsController', function($scope, $location, navService, statsService, jobExecutionService, jobTypeService, uiGridConstants, scaleConfig, subnavService) {

        $scope.jobExecutions = [];
        $scope.loading = true;
        $scope.jobTypeValues = [];
        $scope.selectedJobType = '';
        $scope.jobStatus = scaleConfig.jobStatus;
        $scope.selectedJobStatus = '';
        $scope.subnavLinks = scaleConfig.subnavLinks.jobs;
        subnavService.setCurrentPath('jobs/executions');

        var gridFilter = {},
            gridPageNumber = 1;

        $scope.gridOptions = {
            enableRowSelection: true,
            enableRowHeaderSelection: false,
            enableHorizontalScrollbar: uiGridConstants.scrollbars.NEVER,
            multiSelect: false,
            enableFiltering: true,
            useExternalFiltering: true,
            enableSorting: true,
            minRowsToShow: 17,
            paginationPageSizes: [25,50,75],
            paginationPageSize: 25,
            useExternalPagination: true,
            columnDefs: [
                {
                    field: 'jobTypeId',
                    displayName: 'Job Type',
                    cellTemplate: '<div class="ui-grid-cell-contents"><span ng-bind-html="row.entity.getIcon()"></span> {{ row.entity.job.jobType.title }}</div>',
                    filterHeaderTemplate: '<div class="ui-grid-filter-container"><select class="form-control input-sm" ng-model="grid.appScope.selectedJobType"><option value="{{ grid.appScope.jobTypeValues[$index].id }}" ng-repeat="jobType in grid.appScope.jobTypeValues track by $index">{{ grid.appScope.jobTypeValues[$index].name }} {{ grid.appScope.jobTypeValues[$index].version }}</option></select>'
                },
                { field: 'created', enableFiltering: false, cellFilter: 'date:\'yyyy-MM-dd HH:mm:ss\'' },
                { field: 'lastModified', enableFiltering: false, cellFilter: 'date:\'yyyy-MM-dd HH:mm:ss\'' },
                {
                    field: 'status',
                    filterHeaderTemplate: '<div class="ui-grid-filter-container"><select class="form-control input-sm" ng-model="grid.appScope.selectedJobStatus"><option ng-repeat="status in grid.appScope.jobStatus track by $index">{{ status.toUpperCase() }}</option></select>'
                },
                { field: 'id', displayName: 'ID', enableFiltering: false }
            ],
            data: [],
            onRegisterApi: function (gridApi) {
                //set gridApi on scope
                $scope.gridApi = gridApi;
                $scope.gridApi.selection.on.rowSelectionChanged($scope, function (row) {
                    $scope.$apply(function () {
                        //$location.path('/jobexecutions/' + row.entity.id);
                        console.log(row);
                    });
                });
                $scope.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                    $scope.getPage(currentPage, pageSize);
                });
            }
        };

        $scope.$watch('selectedJobType', function (value) {
            if (!$scope.loading) {
                gridFilter.jobTypeId = value;
                $scope.getPage(gridPageNumber, $scope.gridOptions.paginationPageSize, gridFilter);
            }
        });

        $scope.$watch('selectedJobStatus', function (value) {
            if (!$scope.loading) {
                gridFilter.jobStatus = value;
                $scope.getPage(gridPageNumber, $scope.gridOptions.paginationPageSize, gridFilter);
            }
        });

        $scope.getPage = function (pageNumber, pageSize) {
            $scope.loading = true;
            gridPageNumber = pageNumber;
            jobExecutionService.getJobExecutions(pageNumber, pageSize, gridFilter).then(function (data) {
                var newData = [];
                for (var i = 0; i < $scope.gridOptions.paginationPageSize; i++) {
                    if (data.executions[i]) {
                        newData.push(data.executions[i]);
                    }
                }
                $scope.gridOptions.data = newData;
                $scope.gridOptions.totalItems = data.count;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        var getJobExecutions = function () {
            jobExecutionService.getJobExecutions(gridPageNumber, $scope.gridOptions.paginationPageSize, gridFilter).then(function (data) {
                window.localStorage['scale-jobexecutions-time'] = moment.utc().toISOString();
                window.localStorage['scale-jobexecutions'] = JSON.stringify(data);
                $scope.gridOptions.totalItems = data.count;
                $scope.gridOptions.data = data.executions;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                getJobTypes();
            });
        };

        var getJobTypes = function () {
            jobTypeService.getJobTypesOnce().then(function (data) {
                $scope.jobTypeValues = data.results;
                $scope.jobTypeValues.unshift({ name: '', version: '', id: null });
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        var initialize = function() {
            getJobExecutions();
            navService.updateLocation('jobs');
        };
        initialize();
    });
})();
(function () {
    'use strict';

    angular.module('scaleApp').controller('jobTypesController', function ($rootScope, $scope, $routeParams, $location, hotkeys, scaleService, navService, jobTypeService, scaleConfig, subnavService, nodeService, localStorage, userService) {
        $scope.requestedJobTypeId = parseInt($routeParams.id);
        $scope.masterContainerStyle = '';
        $scope.detailContainerStyle = '';
        $scope.jobTypes = [];
        $scope.jobTypeIds = [];
        $scope.jobTypeCount = 0;
        $scope.activeJobTypeDetails = {};
        $scope.activeJobTypeInterfaceValues = [];
        $scope.activeJobTypeErrors = [];
        $scope.activeJobTypeStats = {};
        $scope.showJobTypeErrors = false;
        $scope.loading = true;
        $scope.activeJobType = null;
        $scope.healthData6 = {};
        $scope.healthData12 = {};
        $scope.healthData24 = {};
        $scope.activityIcon = '<i class="fa fa-pulse">&#x' + scaleConfig.activityIconCode + '</i>';
        $scope.selectJobClass = 'visible';
        $scope.jobDetailsClass = 'invisible';
        $scope.pauseBtnClass = 'fa-pause';
        $scope.user = userService.getUserCreds();
        $scope.subnavLinks = scaleConfig.subnavLinks.jobs;
        subnavService.setCurrentPath('jobs/types');

        var jobTypeStats = {};

        $scope.viewDetails = function (id) {
            $scope.activeJobType = _.find($scope.jobTypes, 'id', id);
            $scope.activeJobType.created = formatDateTime($scope.activeJobType.created);
            $scope.activeJobType.lastModified = formatDateTime($scope.activeJobType.lastModified);

            $location.path('jobs/types/' + id);

            getJobTypeDetails($scope.activeJobType.id);

            //formatJobTypeStats();

            $scope.jobDetailsClass = 'visible';
            $scope.selectJobClass = 'invisible';
        };

        $scope.togglePause = function () {
            $scope.activeJobType.is_paused = !$scope.activeJobType.is_paused;
            $scope.activeJobTypeDetails.is_paused = $scope.activeJobType.is_paused;
            $scope.loading = true;
            jobTypeService.updateJobType($scope.activeJobTypeDetails).then(function(data){
                $scope.activeJobTypeDetails = data;
                $scope.pauseBtnClass = $scope.getPauseButtonClass($scope.activeJobTypeDetails.is_paused);
                $scope.loading = false;
            }).catch(function (error) {
                console.log(error);
                toastr['error'](error);
                $scope.loading = false;
            });
        };

        $scope.getPauseButtonClass = function(is_paused){
            return is_paused ? 'fa-play' : 'fa-pause';
        }

        $scope.getJobTypeListItemClass = function(jobType){
            return jobType.is_paused ? 'paused' : '';
        }

        var formatDateTime = function (dt) {
            return moment.utc(dt).toISOString();
        };

        var getJobTypes = function () {
            jobTypeService.getJobTypesOnce().then(function (data) {
                $scope.jobTypes = data.results;
                $scope.jobTypeIds = _.pluck(data.results, 'id');
                $scope.jobTypeCount = data.count;
                if ($scope.requestedJobTypeId) {
                    $scope.viewDetails($scope.requestedJobTypeId);
                } else {
                    $scope.loading = false;
                }
                hotkeys.bindTo($scope)
                    .add({
                        combo: 'ctrl+up',
                        description: 'Previous Job Type',
                        callback: function () {
                            if ($scope.activeJobType) {
                                var idx = _.indexOf($scope.jobTypeIds, $scope.activeJobType.id);
                                if (idx > 0) {
                                    $scope.viewDetails($scope.jobTypeIds[idx - 1]);
                                }
                            }
                        }
                    }).add({
                        combo: 'ctrl+down',
                        description: 'Next Job Type',
                        callback: function () {
                            if ($scope.activeJobType) {
                                var idx = _.indexOf($scope.jobTypeIds, $scope.activeJobType.id);
                                if (idx < ($scope.jobTypeIds.length - 1)) {
                                    $scope.viewDetails($scope.jobTypeIds[idx + 1]);
                                }
                            }
                        }
                    });
            }).catch(function (error) {
                console.log(error);
                $scope.loading = false;
            });
        };

        var getJobTypeDetails = function (id) {
            $scope.loading = true;
            jobTypeService.getJobTypeDetails(id).then(function (data) {
                $scope.activeJobTypeDetails = data;
                $scope.activeJobTypeInterfaceValues = _.pairs(data.job_type_interface);
                $scope.pauseBtnClass = $scope.getPauseButtonClass($scope.activeJobTypeDetails.is_paused);
                // format error mapping
                $scope.activeJobTypeErrors = [];
                $scope.showJobTypeErrors = _.keys(data.error_mapping.exit_codes).length > 0;
                if ($scope.showJobTypeErrors) {
                    _.forEach(data.error_mapping.exit_codes, function (error_name) {
                        var error = _.find(data.errors, 'name', error_name),
                            exitCode = _.invert(data.error_mapping.exit_codes)[error_name];
                        $scope.activeJobTypeErrors.push({code: exitCode, data: error});
                    });
                }

                // format job type stats
                var performance = data.getPerformance(),
                    failures = data.getFailures();

                $scope.activeJobTypeStats = performance;

                $scope.healthData6 = {
                    gaugeData: performance.hour6.rate,
                    donutData: failures.hour6
                };
                $scope.healthData12 = {
                    gaugeData: performance.hour12.rate,
                    donutData: failures.hour12
                };
                $scope.healthData24 = {
                    gaugeData: performance.hour24.rate,
                    donutData: failures.hour24
                };
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        var initialize = function () {
            getJobTypes();
            navService.updateLocation('jobs');
        };

        angular.element(document).ready(function () {
            // set container heights equal to available page height
            var viewport = scaleService.getViewportSize(),
                masterOffset = scaleConfig.headerOffset,
                detailOffset = scaleConfig.headerOffset + document.getElementsByClassName('nav-tabs')[0].scrollHeight,
                masterMaxHeight = viewport.height - masterOffset,
                detailMaxHeight = viewport.height - detailOffset;

            $scope.masterContainerStyle = 'height: ' + masterMaxHeight + 'px; max-height: ' + masterMaxHeight + 'px; overflow-y: auto;';
            $scope.detailContainerStyle = 'height: ' + detailMaxHeight + 'px; max-height: ' + detailMaxHeight + 'px; overflow-y: auto;';
        });

        initialize();
    });
})();

(function(){
    angular.module('scaleApp').controller('jobExecutionLogController', function($scope, $location, $element, $timeout, jobExecutionService, scaleConfig) {
        'use strict';
        var initialize = function(){

            $scope.forceScroll = true;

            $scope.jobLogError = null;

            $scope.$watch('execution', function (newValue, oldValue) {
                if ($scope.execution) {
                    jobExecutionService.getLog($scope.execution.id).then(null, null, function(result){
                        // get difference of max scroll length and current scroll length.
                        var logResult = result.execution_log;
                        if(result.$resolved){
                            var div = $($element[0]).find('.bash');
                            $scope.scrollDiff = (div.scrollTop() + div.prop('offsetHeight')) - div.prop('scrollHeight');
                            if($scope.scrollDiff >= 0){ $scope.forceScroll = true; }
                            $scope.execLog = logResult;
                        } else {
                            if (result.statusText && result.statusText !== '') {
                                $scope.jobLogErrorStatus = result.statusText;
                            }
                            $scope.jobLogError = 'Unable to retrieve job logs.';
                        }
                    });
                }
            });
            $scope.$watch('execLog', function (newValue, oldValue) {
                if ($scope.execLog) {
                    if($scope.forceScroll || $scope.scrollDiff >= 0){
                        $timeout(function(){
                            $scope.forceScroll = false;
                            var scrlHeight = $($element[0]).find('.bash').prop("scrollHeight");
                            $($element[0]).find('.bash').scrollTop(scrlHeight);
                        }, 50);
                    }
                }
            });
        };

        $scope.scrollitem = function(item){
                console.log(item);
        };

        $scope.stdoutChanged = function(){
            console.log('stdout changed.');
        };

        initialize();

    }).directive('jobExecutionLog', function () {
        return {
            controller: 'jobExecutionLogController',
            templateUrl: 'modules/jobs/directives/jobExecutionLogTemplate.html',
            restrict: 'E',
            scope: {
                execution: '='
            }
        };
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').controller('aisJobHealthController', function ($rootScope, $scope, jobTypeService) {
        $scope.loadingJobHealth = true;
        $scope.jobHealthError = null;
        $scope.jobHealthErrorStatus = null;
        $scope.jobHealth = {};

        var getJobTypeStatus = function () {
            jobTypeService.getJobTypeStatus(null, null, $scope.duration, null).then(null, null, function (data) {
                if (data.$resolved) {
                    $scope.jobHealthError = null;
                    $scope.jobTypeStatus = data.results;
                    $scope.total = 0;
                    $scope.failed = 0;

                    var performance = {},
                        failures = [];

                    _.forEach(data.results, function (status) {
                        performance = status.getPerformance();
                        $scope.total = $scope.total + performance.total;
                        $scope.failed = $scope.failed + performance.failed;
                        failures.push(status.getFailures());
                    });

                    var failureData = [],
                        systemFailures = 0,
                        dataFailures = 0,
                        algorithmFailures = 0;

                    _.forEach(failures, function (f) {
                        _.forEach(f, function (type) {
                            if (type.status === 'SYSTEM') {
                                systemFailures = systemFailures + type.count;
                            } else if (type.status === 'DATA') {
                                dataFailures = dataFailures + type.count;
                            } else if (type.status === 'ALGORITHM') {
                                algorithmFailures = algorithmFailures + type.count;
                            }
                        });
                    });

                    if (systemFailures > 0 || dataFailures > 0 || algorithmFailures > 0) {
                        if (systemFailures > 0) {
                            failureData.push({
                                status: 'SYSTEM',
                                count: systemFailures
                            });
                        }
                        if (dataFailures > 0) {
                            failureData.push({
                                status: 'DATA',
                                count: dataFailures
                            });
                        }
                        if (algorithmFailures > 0) {
                            failureData.push({
                                status: 'ALGORITHM',
                                count: algorithmFailures
                            });
                        }
                    }

                    $scope.jobHealth = {
                        gaugeData: $scope.total === 0 ? 0 : 100 - (($scope.failed / $scope.total) * 100).toFixed(2),
                        donutData: failureData
                    };

                    if ($scope.broadcastData) {
                        $rootScope.$broadcast('jobTypeStatus', $scope.jobTypeStatus);
                    }
                } else {
                    if (data.statusText && data.statusText !== '') {
                        $scope.jobHealthErrorStatus = data.statusText;
                    }
                    $scope.jobHealthError = 'Unable to retrieve job statistics.';
                }
                $scope.loadingJobHealth = false;
            });
        };

        getJobTypeStatus();
    }).directive('aisJobHealth', function(){
        /**
         * Usage: <ais-job-health />
         **/
        return {
            controller: 'aisJobHealthController',
            templateUrl: 'modules/jobs/directives/jobHealthTemplate.html',
            restrict: 'E',
            scope: {
                duration: '=',
                broadcastData: '=', // set to true when using another widget in the same view that also calls getJobTypeStatus
                showDescription: '='
            }
        };
    });
})();
(function () {
    'use strict';

    angular.module('scaleApp').controller('jobTypeInterfaceDirectiveController', function ($rootScope, $scope, jobTypeService) {

    }).directive('aisJobTypeInterface', function(){
        /**
         * Usage: <ais-job-health />
         **/
        return {
            controller: 'jobTypeInterfaceDirectiveController',
            templateUrl: 'modules/jobs/directives/jobTypeInterfaceTemplate.html',
            restrict: 'E',
            scope: {
                jobTypeInterface: '='
            }
        };
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').factory('Job', function (scaleConfig, JobType, scaleService) {
        var Job = function (id, job_type, event, error, status, priority, num_exes, timeout, max_tries, cpus_required, mem_required, disk_in_required, disk_out_required, created, queued, started, ended, last_status_change, last_modified) {
            this.id = id;
            this.job_type = JobType.transformer(job_type);
            this.event = event;
            this.error = error;
            this.status = status;
            this.priority = priority;
            this.num_exes = num_exes;
            this.timeout = timeout;
            this.max_tries = max_tries;
            this.cpus_required = cpus_required;
            this.mem_required = mem_required;
            this.disk_in_required = disk_in_required;
            this.disk_out_required = disk_out_required;
            this.created = created;
            this.created_formatted = moment.utc(created).toISOString();
            this.queued = queued;
            this.started = started;
            this.ended = ended;
            this.last_status_change = last_status_change;
            this.last_modified = last_modified;
            this.last_modified_formatted = moment.utc(last_modified).toISOString();
        };

        // public methods
        Job.prototype = {
            getDuration: function () {
                var start = this.started,
                    end = this.ended ? this.ended : moment.utc().toISOString();
                return scaleService.calculateDuration(start, end);
            }
        };

        // static methods, assigned to class
        Job.build = function (data) {
            if (data) {
                return new Job(
                    data.id,
                    data.job_type,
                    data.event,
                    data.error,
                    data.status,
                    data.priority,
                    data.num_exes,
                    data.timeout,
                    data.max_tries,
                    data.cpus_required,
                    data.mem_required,
                    data.disk_in_required,
                    data.disk_out_required,
                    data.created,
                    data.queued,
                    data.started,
                    data.ended,
                    data.last_status_change,
                    data.last_modified
                );
            }
            return new Job();
        };

        Job.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(Job.build)
                    .filter(Boolean);
            }
            return Job.build(data);
        };

        return Job;
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').factory('JobDetails', function (scaleConfig, JobType, JobExecution, Product, JobDetailInputData, JobDetailOutputData, Recipe, JobDetailEvent, scaleService) {
        var JobDetails = function (cpus_required, created, queued, started, ended, data, disk_in_required, disk_out_required, error, event, id, job_exes, job_type, last_modified, last_status_change, max_tries, mem_required, num_exes, priority, products, recipes, results, input_files, status, timeout ) {
            // decorate inputs and outputs to support data binding in details view
            data.input_data = decorateInputData(data.input_data, input_files);
            data.output_data = decorateOutputData(data.output_data, results, products);
            this.cpus_required = cpus_required;
            this.created = created;
            this.created_formatted = moment.utc(created).toISOString();
            this.queued = queued;
            this.queued_formatted = moment.utc(queued).toISOString();
            this.started = started;
            this.started_formatted = moment.utc(started).toISOString();
            this.ended = ended;
            this.ended_formatted = moment.utc(ended).toISOString();
            this.data = {
                input_data: JobDetailInputData.transformer(data.input_data),
                version: data.version,
                output_data: JobDetailOutputData.transformer(data.output_data)
            };
            this.disk_in_required = disk_in_required;
            this.disk_out_required = disk_out_required;
            this.error = error;
            this.event = JobDetailEvent.transformer(event);
            this.id = id;
            this.job_exes = JobExecution.transformer(job_exes);
            this.job_type = JobType.transformer(job_type);
            this.last_modified = last_modified;
            this.last_status_change = last_status_change;
            this.max_tries = max_tries;
            this.mem_required = mem_required;
            this.num_exes = num_exes;
            this.priority = priority;
            this.products = Product.transformer(products);
            this.recipes = Recipe.transformer(recipes);
            this.results = {
                output_data: JobDetailOutputData.transformer(results.output_data),
                version: results.version
            };
            this.input_files = input_files;
            this.status = status;
            this.timeout = timeout;
        };

        // private methods
        var decorateInputData = function(input_data, input_files){
            _.forEach(input_data, function(val){
                var file_ids = [];
                if(!val.files){ val.files = []; }

                if(val.file_id && val.file_id > 0){
                    file_ids = [val.file_id];
                }
                else if(val.file_ids && val.file_ids.length > 0){
                    // multiple files
                    file_ids = val.file_ids;
                }
                _.forEach(file_ids, function(file_id){
                    var infile = _.find(input_files, {id: file_id});
                    if(infile){
                        val.files.push(
                            {
                                file_name: infile.file_name,
                                url: infile.url,
                                created: infile.created,
                                last_modified: infile.last_modified,
                                file_size_formatted: scaleService.calculateFileSizeFromBytes(infile.file_size)
                            }
                        );
                    }
                });
            });
            return input_data;
        };

        var decorateOutputData = function(output_data, results, products){
            _.forEach(output_data, function(val){
                var file_ids = [];
                var result = _.find(results.output_data, { name: val.name });
                if(!val.files){ val.files = []; }

                if( result && result.file_id && result.file_id > 0 ){
                    // single file
                    file_ids = [result.file_id];
                }
                else if(result && result.file_ids && result.file_ids.length > 0){
                    // multiple files
                    file_ids = result.file_ids;
                }
                _.forEach(file_ids, function(file_id){
                    var outfile = _.find(products, {id: file_id});
                    console.log(file_id + ': ' + outfile.id);
                    if(outfile){
                        val.files.push(
                            {
                                file_name: outfile.file_name,
                                url: outfile.url,
                                created: outfile.created,
                                last_modified: outfile.last_modified,
                                file_size_formatted: scaleService.calculateFileSizeFromBytes(outfile.file_size)
                            }
                        );
                    }
                });
            });
            return output_data;
        };

        // public methods
        JobDetails.prototype = {
            getDuration: function () {
                return scaleService.calculateDuration(this.created, this.last_modified);
            },
            getLatestExecution: function(){
                if (this.num_exes > 0 ) {
                    return this.job_exes[0];
                }
                return null;
            },
            getStatusClass: function(){
                // if(this.status === 'COMPLETED'){
                //     return 'label-success';
                // }
                // else if( this.status === 'FAILED'){
                //     return 'label-default';//    return 'label-danger';
                // }
                // else{
                //     return 'label-default';
                // }
                return this.status.toLowerCase();
            }
        };

        // static methods, assigned to class
        JobDetails.build = function (data) {
            if (data) {
                return new JobDetails(
                    data.cpus_required,
                    data.created,
                    data.queued,
                    data.started,
                    data.ended,
                    data.data,
                    data.disk_in_required,
                    data.disk_out_required,
                    data.error,
                    data.event,
                    data.id,
                    data.job_exes,
                    data.job_type,
                    data.last_modified,
                    data.last_status_change,
                    data.max_tries,
                    data.mem_required,
                    data.num_exes,
                    data.priority,
                    data.products,
                    data.recipes,
                    data.results,
                    data.input_files,
                    data.status,
                    data.timeout
                );
            }
            return new JobDetails();
        };

        JobDetails.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(JobDetails.build)
                    .filter(Boolean);
            }
            return JobDetails.build(data);
        };

        return JobDetails;
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').factory('JobExecution', function (scaleConfig, Job, Node, moment) {
        var JobExecution = function (id, status, command_arguments, timeout, pre_started, pre_completed, pre_exit_code, job_started, job_completed, job_exit_code, post_started, post_completed, post_exit_code, created, queued, started, ended, last_modified, job, node, error, environment, cpus_scheduled, mem_scheduled, disk_in_scheduled, disk_out_scheduled, disk_total_scheduled, results, current_stdout_url, current_stderr_url, results_manifest) {
            this.id = id;
            this.status = status;
            this.command_arguments = command_arguments;
            this.timeout = timeout;
            this.pre_started = pre_started;
            this.pre_completed = pre_completed;
            this.pre_exit_code = pre_exit_code;
            this.job_started = job_started;
            this.job_completed = job_completed;
            this.job_exit_code = job_exit_code;
            this.post_started = post_started;
            this.post_completed = post_completed;
            this.post_exit_code = post_exit_code;
            this.created = created;
            this.created_formatted = created ? moment.utc(created).toISOString() : created;
            this.queued = queued;
            this.queued_formatted = queued ? moment.utc(queued).toISOString() : queued;
            this.started = started;
            this.started_formatted = started ? moment.utc(started).toISOString() : started;
            this.ended = ended;
            this.ended_formatted = ended ? moment.utc(ended).toISOString() : ended;
            this.last_modified = last_modified;
            this.last_modified_formatted = last_modified ? moment.utc(last_modified).toISOString() : last_modified;
            this.job = Job.transformer(job);
            this.node = Node.transformer(node);
            this.error = error;
            this.environment = environment;
            this.cpus_scheduled = cpus_scheduled;
            this.mem_scheduled = mem_scheduled;
            this.disk_in_scheduled = disk_in_scheduled;
            this.disk_out_scheduled = disk_out_scheduled;
            this.disk_total_scheduled = disk_total_scheduled;
            this.results = results;
            this.current_stdout_url = current_stdout_url;
            this.current_stderr_url = current_stderr_url;
            this.results_manifest = results_manifest;
        };

        // public methods
        JobExecution.prototype = {
            getDuration: function () {
                return moment.utc(this.job_completed).diff(moment.utc(this.job_started));
            },
            getIcon: function () {
                return this.job.jobType.iconCode ? '<i class="fa">&#x' + this.job.jobType.iconCode + '</i>' : '<i class="fa">&#x' + scaleConfig.defaultIconCode + '</i>';
            }
        };

        // static methods, assigned to class
        JobExecution.build = function (data) {
            if (data) {
                return new JobExecution(
                    data.id,
                    data.status,
                    data.command_arguments,
                    data.timeout,
                    data.pre_started,
                    data.pre_completed,
                    data.pre_exit_code,
                    data.job_started,
                    data.job_completed,
                    data.job_exit_code,
                    data.post_started,
                    data.post_completed,
                    data.post_exit_code,
                    data.created,
                    data.queued,
                    data.started,
                    data.ended,
                    data.last_modified,
                    data.job,
                    data.node,
                    data.error,
                    data.environment,
                    data.cpus_scheduled,
                    data.mem_scheduled,
                    data.disk_in_scheduled,
                    data.disk_out_scheduled,
                    data.disk_total_scheduled,
                    data.results,
                    data.current_stdout_url,
                    data.current_stderr_url,
                    data.results_manifest
                );
            }
            return new JobExecution();
        };

        JobExecution.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(JobExecution.build)
                    .filter(Boolean);
            }
            return JobExecution.build(data);
        };

        return JobExecution;
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').factory('JobExecutionLog', function (scaleConfig, Job, Node) {
        var JobExecutionLog = function (id, status, command_arguments, timeout, exit_code, created, queued, scheduled, pre_started, pre_completed, job_started, job_completed, post_started, post_completed, ended, last_modified, job, node, error, is_finished, stdout, stderr) {
            this.id = id;
            this.status = status;
            this.command_arguments = command_arguments;
            this.timeout = timeout;
            this.exit_code = exit_code;
            this.created = created;
            this.queued = queued;
            this.scheduled = scheduled;
            this.pre_started = pre_started;
            this.pre_completed = pre_completed;
            this.job_started = job_started;
            this.job_completed = job_completed;
            this.post_started = post_started;
            this.post_completed = post_completed;
            this.ended = ended;
            this.last_modified = last_modified;
            this.job = Job.transformer(job);
            this.node = Node.transformer(node);
            this.error = error;
            this.is_finished = is_finished;
            this.stdout = stdout;
            this.stdoutHtml = stdout ? stdout.replace(new RegExp('\r?\n','g'), '<br />') : '';
            this.stderr = stderr;
        };

        // public methods
        JobExecutionLog.prototype = {
            toHtml: function(instr){
                return instr
            }

        };

        // static methods, assigned to class
        JobExecutionLog.build = function (data) {
            if (data) {
                return new JobExecutionLog(
                    data.id,
                    data.status,
                    data.command_arguments,
                    data.timeout,
                    data.exit_code,
                    data.created,
                    data.queued,
                    data.scheduled,
                    data.pre_started,
                    data.pre_completed,
                    data.job_started,
                    data.job_completed,
                    data.post_started,
                    data.post_completed,
                    data.ended,
                    data.last_modified,
                    data.job,
                    data.node,
                    data.error,
                    data.is_finished,
                    data.stdout,
                    data.stderr
                );
            }
            return new JobExecutionLog();
        };

        JobExecutionLog.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(JobExecutionLog.build)
                    .filter(Boolean);
            }
            return JobExecutionLog.build(data);
        };

        return JobExecutionLog;
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').factory('JobType', function (scaleConfig, JobTypeInterface) {
        var JobType = function (id, name, title, version, description, is_system, is_long_running, is_active, is_operational, is_paused, uses_docker, docker_privileged, docker_image, priority, timeout, max_tries, cpus_required, mem_required, disk_out_const_required, disk_out_mult_required, icon_code, created, archived, paused, last_modified, job_type_interface) {
            this.id = id;
            this.name = name;
            this.title = title;
            this.version = version;
            this.description = description;
            this.is_system = is_system;
            this.is_long_running = is_long_running;
            this.is_active = is_active;
            this.is_operational = is_operational;
            this.is_paused = is_paused;
            this.uses_docker = uses_docker;
            this.docker_privileged = docker_privileged;
            this.docker_image = docker_image;
            this.priority = priority;
            this.timeout = timeout;
            this.max_tries = max_tries;
            this.cpus_required = cpus_required;
            this.mem_required = mem_required;
            this.disk_out_const_required = disk_out_const_required;
            this.disk_out_mult_required = disk_out_mult_required;
            this.icon_code = icon_code;
            this.created = created;
            this.archived = archived;
            this.paused = paused;
            this.last_modified = last_modified;
            this.job_type_interface = JobTypeInterface.transformer(job_type_interface);
        };

        // public methods
        JobType.prototype = {
            toString: function () {
                return 'JobType';
            },
            getIcon: function () {
                return this.icon_code ? '<i class="fa">&#x' + this.icon_code + '</i>' : '<i class="fa">&#x' + scaleConfig.defaultIconCode + '</i>';
            },
            getCellText: function () {
                return this.icon_code ? '&#x' + this.icon_code + ';' : '&#x' + scaleConfig.defaultIconCode + ';';
            },
            getCellTitle: function () {
                return this.title;
            }
        };

        // static methods, assigned to class
        JobType.build = function (data) {
            if (data) {
                return new JobType(
                    data.id,
                    data.name,
                    data.title,
                    data.version,
                    data.description,
                    data.is_system,
                    data.is_long_running,
                    data.is_active,
                    data.is_operational,
                    data.is_paused,
                    data.uses_docker,
                    data.docker_privileged,
                    data.docker_image,
                    data.priority,
                    data.timeout,
                    data.max_tries,
                    data.cpus_required,
                    data.mem_required,
                    data.disk_out_const_required,
                    data.disk_out_mult_required,
                    data.icon_code,
                    data.created,
                    data.archived,
                    data.paused,
                    data.last_modified,
                    data.interface
                );
            }
            return new JobType();
        };

        JobType.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(JobType.build)
                    .filter(Boolean);
            }
            return JobType.build(data);
        };

        return JobType;
    });
})();
(function () {
    'use strict';

    angular.module('scaleApp').factory('JobTypeDetails', function (scaleConfig, JobTypeInterface, JobTypeErrorMapping, JobTypeError, scaleService) {
        var JobTypeDetails = function (id, name, version, title, description, category, author_name, author_url, is_system, is_long_running, is_active, is_operational, is_paused, icon_code, uses_docker, docker_privileged, docker_image, priority, timeout, max_tries, cpus_required, mem_required, disk_out_const_required, disk_out_mult_required, created, archived, paused, last_modified, job_type_interface, error_mapping, errors, job_counts_6h, job_counts_12h, job_counts_24h) {
            this.id = id;
            this.name = name;
            this.version = version;
            this.title = title;
            this.description = description;
            this.category = category;
            this.author_name = author_name;
            this.author_url = author_url;
            this.is_system = is_system;
            this.is_long_running = is_long_running;
            this.is_active = is_active;
            this.is_operational = is_operational;
            this.is_paused = is_paused;
            this.icon_code = icon_code;
            this.uses_docker = uses_docker;
            this.docker_privileged = docker_privileged;
            this.docker_image = docker_image;
            this.priority = priority;
            this.timeout = timeout;
            this.max_tries = max_tries;
            this.cpus_required = cpus_required;
            this.mem_required = mem_required;
            this.mem_required_formatted = scaleService.calculateFileSizeFromMib(mem_required);
            this.disk_out_const_required = disk_out_const_required;
            this.disk_out_const_required_formatted = scaleService.calculateFileSizeFromMib(disk_out_const_required);
            this.disk_out_mult_required = disk_out_mult_required;
            this.created = created;
            this.archived = archived;
            this.paused = paused;
            this.last_modified = last_modified;
            this.job_type_interface = job_type_interface;
            this.error_mapping = JobTypeErrorMapping.transformer(error_mapping);
            this.errors = JobTypeError.transformer(errors);
            this.job_counts_6h = job_counts_6h;
            this.job_counts_12h = job_counts_12h;
            this.job_counts_24h = job_counts_24h;
        };

        // public methods
        JobTypeDetails.prototype = {
            getIcon: function () {
                return this.icon_code ? '<i class="fa">&#x' + this.icon_code + '</i>' : '<i class="fa">&#x' + scaleConfig.defaultIconCode + '</i>';
            },
            getPerformance: function () {
                var failed6Arr = _.where(this.job_counts_6h, { 'status': 'FAILED' }),
                    failed12Arr = _.where(this.job_counts_12h, { 'status': 'FAILED' }),
                    failed24Arr = _.where(this.job_counts_24h, { 'status': 'FAILED' });

                var completed6 = _.find(this.job_counts_6h, 'status', 'COMPLETED') || { count: 0 },
                    failed6 = _.sum(failed6Arr, 'count'),
                    total6 = failed6Arr.length > 0 ? failed6 + completed6.count : completed6.count,
                    successRate6 = total6 === 0 ? 0 : 100 - ((failed6 / total6) * 100).toFixed(2),
                    completed12 = _.find(this.job_counts_12h, 'status', 'COMPLETED') || { count: 0 },
                    failed12 = _.sum(failed12Arr, 'count'),
                    total12 = failed12Arr.length > 0 ? failed12 + completed12.count : completed12.count,
                    successRate12 = total12 === 0 ? 0 : 100 - ((failed12 / total12) * 100).toFixed(2),
                    completed24 = _.find(this.job_counts_24h, 'status', 'COMPLETED') || { count: 0 },
                    failed24 = _.sum(failed24Arr, 'count'),
                    total24 = failed24Arr.length > 0 ? failed24 + completed24.count : completed24.count,
                    successRate24 = total24 === 0 ? 0 : 100 - ((failed24 / total24) * 100).toFixed(2);

                return {
                    hour6: {
                        rate: successRate6,
                        failed: failed6,
                        completed: completed6.count,
                        total: total6
                    },
                    hour12: {
                        rate: successRate12,
                        failed: failed12,
                        completed: completed12.count,
                        total: total12
                    },
                    hour24: {
                        rate: successRate24,
                        failed: failed24,
                        completed: completed24.count,
                        total: total24
                    }
                };
            },
            getFailures: function () {
                var failed6 = _.where(this.job_counts_6h, { 'status': 'FAILED' }),
                    failed6Values = _.values(_.groupBy(failed6, 'category')),
                    failed12 = _.where(this.job_counts_12h, { 'status': 'FAILED' }),
                    failed12Values = _.values(_.groupBy(failed12, 'category')),
                    failed24 = _.where(this.job_counts_24h, { 'status': 'FAILED' }),
                    failed24Values = _.values(_.groupBy(failed24, 'category'));

                var getFailureCounts = function (categories) {
                    var returnArr = [];
                    _.forEach(categories, function (category) {
                        _.forEach(category, function (val) {
                            returnArr.push({ status: val.category, count: val.count });
                        });
                    });
                    return returnArr;
                };

                return {
                    hour6: getFailureCounts(failed6Values),
                    hour12: getFailureCounts(failed12Values),
                    hour24: getFailureCounts(failed24Values)
                };
            }
        };

        // static methods, assigned to class
        JobTypeDetails.build = function (data) {
            if (data) {
                return new JobTypeDetails(
                    data.id,
                    data.name,
                    data.version,
                    data.title,
                    data.description,
                    data.category,
                    data.author_name,
                    data.author_url,
                    data.is_system,
                    data.is_long_running,
                    data.is_active,
                    data.is_operational,
                    data.is_paused,
                    data.icon_code,
                    data.uses_docker,
                    data.docker_privileged,
                    data.docker_image,
                    data.priority,
                    data.timeout,
                    data.max_tries,
                    data.cpus_required,
                    data.mem_required,
                    data.disk_out_const_required,
                    data.disk_out_mult_required,
                    data.created,
                    data.archived,
                    data.paused,
                    data.last_modified,
                    data.interface,
                    data.error_mapping,
                    data.errors,
                    data.job_counts_6h,
                    data.job_counts_12h,
                    data.job_counts_24h
                );
            }
            return new JobTypeDetails();
        };

        JobTypeDetails.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(JobTypeDetails.build);
            }
            return JobTypeDetails.build(data);
        };

        return JobTypeDetails;
    });
})();
(function () {
    'use strict';

    angular.module('scaleApp').factory('JobTypeInputData', function (scaleConfig) {
        var JobTypeInputData = function (media_types, required, type, name) {
            this.media_types = media_types;
            this.required = required;
            this.type = type;
            this.name = name;
        };

        // public methods
        JobTypeInputData.prototype = {

        };

        // static methods, assigned to class
        JobTypeInputData.build = function (data) {
            if (data) {
                return new JobTypeInputData(
                    data.media_types,
                    data.required,
                    data.type,
                    data.name
                );
            }
            return new JobTypeInputData();
        };

        JobTypeInputData.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(JobTypeInputData.build);
            }
            return JobTypeInputData.build(data);
        };

        return JobTypeInputData;
    });
})();
(function () {
    'use strict';

    angular.module('scaleApp').factory('JobTypeInterface', function (scaleConfig, JobTypeInputData, JobTypeOutputData) {
        var JobTypeInterface = function (version, command, command_arguments, input_data, output_data) {
            this.version = version;
            this.command = command;
            this.command_arguments = command_arguments;
            this.input_data = JobTypeInputData.transformer(input_data);
            this.output_data = JobTypeOutputData.transformer(output_data);
        };

        // public methods
        JobTypeInterface.prototype = {
            getIcon: function () {
                return this.iconCode ? '<i class="fa">&#x' + this.iconCode + '</i>' : '<i class="fa">&#x' + scaleConfig.defaultIconCode + '</i>';
            }
        };

        // static methods, assigned to class
        JobTypeInterface.build = function (data) {
            if (data) {
                return new JobTypeInterface(
                    data.version,
                    data.command,
                    data.command_arguments,
                    data.input_data,
                    data.output_data
                );
            }
            return new JobTypeInterface();
        };

        JobTypeInterface.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(JobTypeInterface.build)
                    .filter(Boolean);
            }
            return JobTypeInterface.build(data);
        };

        return JobTypeInterface;
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').factory('JobTypeOutputData', function () {
        var JobTypeOutputData = function (name, type, required, media_type) {
            this.name = name;
            this.type = type;
            this.required = required;
            this.media_type = media_type;
        };

        // public methods
        JobTypeOutputData.prototype = {

        };

        // static methods, assigned to class
        JobTypeOutputData.build = function (data) {
            if (data) {
                return new JobTypeOutputData(
                    data.name,
                    data.type,
                    data.required,
                    data.media_type
                );
            }
            return new JobTypeOutputData();
        };

        JobTypeOutputData.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(JobTypeOutputData.build)
                    .filter(Boolean);
            }
            return JobTypeOutputData.build(data);
        };

        return JobTypeOutputData;
    });
})();
(function () {
    'use strict';

    angular.module('scaleApp').factory('JobTypeStatus', function (scaleConfig, JobType, JobExecution) {
        var JobTypeStatus = function (job_type, job_counts) {
            this.job_type = JobType.transformer(job_type);
            this.job_counts = job_counts;
            this.has_running = _.find(job_counts, 'status', 'RUNNING');
            this.description = this.getPerformance().rateDescription;
        };

        // public methods
        JobTypeStatus.prototype = {
            toString: function () {
                return 'JobTypeStatus';
            },
            getPerformance: function () {
                var failedArr = _.where(this.job_counts, { 'status': 'FAILED' });

                var completed = _.find(this.job_counts, 'status', 'COMPLETED') || { count: 0 },
                    failed = _.sum(failedArr, 'count'),
                    total = failedArr.length > 0 ? failed + completed.count : completed.count,
                    successRate = total === 0 ? 0 : 100 - ((failed / total) * 100).toFixed(2),
                    successRateDescription = 'success';

                if (successRate <= 30 && total > 0) {
                    successRateDescription = 'error';
                } else if (successRate > 30 && successRate <= 60 && total > 0) {
                    successRateDescription = 'warning';
                } else if (total === 0 && !this.has_running) {
                    successRateDescription = 'z_inactive'; // prepend with 'z_' for ordering purposes
                }

                return {
                    rate: successRate,
                    rateDescription: successRateDescription,
                    failed: failed,
                    completed: completed.count,
                    total: total
                };
            },
            getRunning: function () {
                return _.find(this.job_counts, 'status', 'RUNNING') || { count: 0 };
            },
            getFailures: function () {
                var failed = _.where(this.job_counts, { 'status': 'FAILED' }),
                    failedValues = _.values(_.groupBy(failed, 'category'));

                var getFailureCounts = function (categories) {
                    var returnArr = [];
                    _.forEach(categories, function (category) {
                        _.forEach(category, function (val) {
                            returnArr.push({ status: val.category, count: val.count });
                        });
                    });
                    return returnArr;
                };

                return getFailureCounts(failedValues);
            },
            getCellFill: function () {
                var status = this.getPerformance().rateDescription;
                if (status === 'success') {
                    return scaleConfig.colors.chart_green;
                } else if (status === 'warning') {
                    return scaleConfig.colors.chart_yellow;
                } else if (status === 'error') {
                    return scaleConfig.colors.chart_red;
                } else if (status === 'z_inactive') {
                    return scaleConfig.colors.chart_gray_dark;
                }
            },
            getCellActivity: function () {
                var running = this.getRunning();
                if (running.count > 0) {
                    return '&#x' + scaleConfig.activityIconCode;
                }
                return '';
            },
            getCellActivityTotal: function () {
                return this.getRunning().count > 0 ? this.getRunning().count : '';
            },
            getCellError: function () {
                var performance = this.getPerformance();
                return 'Failed: ' + (performance.failed);
            },
            getCellTotal: function () {
                var performance = this.getPerformance();
                return 'Completed: ' + performance.completed;
            },
            getCellPauseResume: function () {
                return;
            }
        };

        // static methods, assigned to class
        JobTypeStatus.build = function (data) {
            if (data) {
                return new JobTypeStatus(
                    data.job_type,
                    data.job_counts
                );
            }
            return new JobTypeStatus();
        };

        JobTypeStatus.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(JobTypeStatus.build)
                    .filter(Boolean);
            }
            return JobTypeStatus.build(data);
        };

        return JobTypeStatus;
    });
})();

(function () {
    'use strict';
    
    angular.module('scaleApp').factory('JobTypeErrorMapping', function () {
        var JobTypeErrorMapping = function (version, exit_codes) {
            this.version = version;
            this.exit_codes = exit_codes;
        };

        // public methods
        JobTypeErrorMapping.prototype = {

        };

        // static methods, assigned to class
        JobTypeErrorMapping.build = function (data) {
            if (data) {
                return new JobTypeErrorMapping(
                    data.version,
                    data.exit_codes
                );
            }
            return new JobTypeErrorMapping();
        };

        JobTypeErrorMapping.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(JobTypeErrorMapping.build)
                    .filter(Boolean);
            }
            return JobTypeErrorMapping.build(data);
        };

        return JobTypeErrorMapping;
    })
})();
(function () {
    'use strict';

    angular.module('scaleApp').factory('JobTypeError', function (moment, scaleConfig) {
        var JobTypeError = function (id, name, title, description, category, created, last_modified) {
            this.id = id;
            this.name = name;
            this.title = title;
            this.description = description;
            this.category = category;
            this.created = created;
            this.created_formatted = created ? moment.utc(created).toISOString() : created;
            this.last_modified = last_modified;
            this.last_modified_formatted = last_modified ? moment.utc(last_modified).toISOString() : last_modified;
        };

        // public methods
        JobTypeError.prototype = {

        };

        // static methods, assigned to class
        JobTypeError.build = function (data) {
            if (data) {
                return new JobTypeError(
                    data.id,
                    data.name,
                    data.title,
                    data.description,
                    data.category,
                    data.created,
                    data.last_modified
                );
            }
            return new JobTypeError();
        };

        JobTypeError.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(JobTypeError.build)
                    .filter(Boolean);
            }
            return JobTypeError.build(data);
        };

        return JobTypeError;
    })
})();

(function () {
    'use strict';

    angular.module('scaleApp').factory('RunningJob', function (scaleConfig, scaleService, JobType) {
        var RunningJob = function (count, longest_running, job_type) {
            this.count = count;
            this.longest_running = longest_running;
            this.job_type = JobType.transformer(job_type);
        };

        // public methods
        RunningJob.prototype = {
            getDuration: function () {
                return scaleService.calculateDuration(this.longest_running, moment.utc().toISOString());
            },
            getIcon: function () {
                var configJobType = _.find(scaleConfig.jobTypes, 'title', this.job_type.name);
                if (configJobType) {
                    return configJobType.icon;
                }
                return scaleConfig.defaultIcon;
            }
        };

        // static methods, assigned to class
        RunningJob.build = function (data) {
            if (data) {
                return new RunningJob(
                    data.count,
                    data.longest_running,
                    data.job_type
                );
            }
            return new RunningJob();
        };

        RunningJob.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(RunningJob.build)
                    .filter(Boolean);
            }
            return RunningJob.build(data);
        };

        return RunningJob;
    });
})();
(function () {
    'use strict';

    angular.module('scaleApp').factory('SystemFailure', function (scaleConfig, scaleService) {
        var SystemFailure = function (count, job_type_name, job_type_version, error_name, first_error, last_error) {
            this.count = count;
            this.job_type_name = job_type_name;
            this.job_type_version = job_type_version;
            this.error_name = error_name;
            this.first_error = first_error;
            this.last_error = last_error;
        };

        // public methods
        SystemFailure.prototype = {
            getDuration: function () {
                return scaleService.calculateDuration(this.first_error, this.last_error);
            },
            getIcon: function () {
                var configJobType = _.find(scaleConfig.jobTypes, 'title', this.job_type_name);
                if (configJobType) {
                    return configJobType.icon;
                }
                return scaleConfig.defaultIcon;
            }
        };

        // static methods, assigned to class
        SystemFailure.build = function (data) {
            if (data) {
                return new SystemFailure(
                    data.count,
                    data.job_type_name,
                    data.job_type_version,
                    data.error_name,
                    data.first_error,
                    data.last_error
                );
            }
            return new SystemFailure();
        };

        SystemFailure.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(SystemFailure.build)
                    .filter(Boolean);
            }
            return SystemFailure.build(data);
        };

        return SystemFailure;
    });
})();

(function (){
    'use strict';

    angular.module('scaleApp').factory('Product', function (JobType, scaleService, scaleConfig) {
        var Product = function (id, workspace, file_name, media_type, file_size, data_type, is_deleted, uuid, url, created, deleted, data_started, data_ended, geometry, center_point, meta_data, countries, last_modified, is_operational, is_published, published, unpublished, job_type, job, job_exe, update, source_files) {
            this.id = id;
            this.workspace = workspace;
            this.file_name = file_name;
            this.media_type = media_type;
            this.file_size = file_size;
            this.file_size_readable = this.getReadableFileSize();
            this.data_type = data_type;
            this.is_deleted = is_deleted;
            this.uuid = uuid;
            this.url = url;
            this.created = created;
            this.created_formatted = created ? moment.utc(created).toISOString() : created;
            this.deleted = deleted;
            this.data_started = data_started;
            this.data_ended = data_ended;
            this.geometry = geometry;
            this.center_point = center_point;
            this.meta_data = meta_data;
            this.countries = countries;
            this.last_modified = last_modified;
            this.last_modified_formatted = last_modified ? moment.utc(last_modified).toISOString() : last_modified;
            this.is_operational = is_operational;
            this.is_operational_label = is_operational ? 'Operational' : 'R&amp;D';
            this.is_published = is_published;
            this.published = published;
            this.unpublished = unpublished;
            this.job_type = JobType.transformer(job_type);
            this.job = job;
            this.job_exe = job_exe;
            this.update = update;
            this.source_files = source_files;
        };

        // public methods
        Product.prototype = {
            getDuration: function () {
                return moment.utc(this.last_modified).diff(moment.utc(this.created));
            },
            getReadableFileSize: function () {
                return scaleService.calculateFileSizeFromBytes(this.file_size);
            }
        };

        // static methods, assigned to class
        Product.build = function (data) {
            if (data) {
                return new Product(
                    data.id,
                    data.workspace,
                    data.file_name,
                    data.media_type,
                    data.file_size,
                    data.data_type,
                    data.is_deleted,
                    data.uuid,
                    data.url,
                    data.created,
                    data.deleted,
                    data.data_started,
                    data.data_ended,
                    data.geometry,
                    data.center_point,
                    data.meta_data,
                    data.countries,
                    data.last_modified,
                    data.is_operational,
                    data.is_published,
                    data.published,
                    data.unpublished,
                    data.job_type,
                    data.job,
                    data.job_exe,
                    data.update,
                    data.source_files
                );
            }
            return new Product();
        };

        Product.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(Product.build)
                    .filter(Boolean);
            }
            return Product.build(data);
        };

        return Product;
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').factory('JobDetailInputData', function () {
        var JobDetailInputData = function (name, value, file_id, file_ids, files) {
            this.name = name;
            this.value = value;
            this.file_id = file_id;
            this.file_ids = file_ids;
            this.files = files;
        };

        // public methods
        JobDetailInputData.prototype = {
            getValue: function () {
                if (this.value)
                    return this.value;
                if (this.file_id)
                    return this.file_id;
                if (this.file_ids)
                    return this.file_ids;
            }
        };

        // static methods, assigned to class
        JobDetailInputData.build = function (data) {
            if (data) {
                return new JobDetailInputData(
                    data.name,
                    data.value,
                    data.file_id,
                    data.file_ids,
                    data.files
                );
            }
            return new JobDetailInputData();
        };

        JobDetailInputData.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(JobDetailInputData.build)
                    .filter(Boolean);
            }
            return JobDetailInputData.build(data);
        };

        return JobDetailInputData;
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').factory('JobDetailOutputData', function () {
        var JobDetailOutputData = function (name, workspace_id, files) {
            this.name = name;
            this.workspace_id = workspace_id;
            this.files = files;
        };

        // public methods
        JobDetailOutputData.prototype = {

        };

        // static methods, assigned to class
        JobDetailOutputData.build = function (data) {
            if (data) {
                return new JobDetailOutputData(
                    data.name,
                    data.workspace_id,
                    data.files
                );
            }
            return new JobDetailOutputData();
        };

        JobDetailOutputData.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(JobDetailOutputData.build)
                    .filter(Boolean);
            }
            return JobDetailOutputData.build(data);
        };

        return JobDetailOutputData;
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').factory('JobDetailEvent', function (JobDetailEventRule) {
        var JobDetailEvent = function (id, type, rule, occurred) {
            this.id = id;
            this.type = type;
            this.rule = JobDetailEventRule.transformer(rule);
            this.occurred = occurred;
        };

        // public methods
        JobDetailEvent.prototype = {

        };

        // static methods, assigned to class
        JobDetailEvent.build = function (data) {
            if (data) {
                return new JobDetailEvent(
                    data.id,
                    data.type,
                    data.rule,
                    data.occurred
                );
            }
            return new JobDetailEvent();
        };

        JobDetailEvent.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(JobDetailEvent.build)
                    .filter(Boolean);
            }
            return JobDetailEvent.build(data);
        };

        return JobDetailEvent;
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').factory('JobDetailEventRule', function () {
        var JobDetailEventRule = function (id, type, is_active, created, archived, last_modified) {
            this.id = id;
            this.type = type;
            this.is_active = is_active;
            this.created = created;
            this.archived = archived;
            this.last_modified = last_modified;
        };

        // public methods
        JobDetailEventRule.prototype = {

        };

        // static methods, assigned to class
        JobDetailEventRule.build = function (data) {
            if (data) {
                return new JobDetailEventRule(
                    data.id,
                    data.type,
                    data.is_active,
                    data.created,
                    data.archived,
                    data.last_modified
                );
            }
            return new JobDetailEventRule();
        };

        JobDetailEventRule.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(JobDetailEventRule.build)
                    .filter(Boolean);
            }
            return JobDetailEventRule.build(data);
        };

        return JobDetailEventRule;
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').service('jobService', function($http, $q, $resource, scaleConfig, Job, JobDetails, RunningJob, poller, pollerFactory) {

        var getJobsParams = function (page, page_size, started, ended, order, status, job_type_id, job_type_name, job_type_category, url) {
            return {
                page: page,
                page_size: page_size,
                started: started,
                ended: ended,
                order: order,
                status: status,
                job_type_id: job_type_id,
                job_type_name: job_type_name,
                job_type_category: job_type_category,
                url: url
            };
        };

        var getJobUpdateData = function (status) {
            return {
                status: status
            };
        };

        return {
            getJobs: function (params) {
                params = params || getJobsParams();
                params.url = params.url ? params.url : scaleConfig.urls.getJobs();

                var jobsResource = $resource(params.url, params),
                    jobsPoller = pollerFactory.newPoller(jobsResource, scaleConfig.pollIntervals.jobs);

                return jobsPoller.promise.then(null, null, function (data) {
                    if (data.$resolved) {
                        data.results = Job.transformer(data.results);
                    } else {
                        jobsPoller.stop();
                    }
                    return data;
                });
            },
            getJobsOnce: function (params) {
                params = params || getJobsParams();
                var d = $q.defer();

                $http({
                    url: params.url ? params.url : scaleConfig.urls.getJobs(),
                    method: 'GET',
                    params: params
                }).success(function (data) {
                    data.results = Job.transformer(data.results);
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });

                return d.promise;
            },
            getJobCountsByStatus: function (hour) {
                hour = hour || 3;
                var d = $q.defer();

                $http.get(scaleConfig.urls.getJobCountsByStatus(hour)).success(function (data) {
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getJobDetail: function (id) {
                var d = $q.defer();
                $http.get(scaleConfig.urls.getJobDetail(id)).success(function (data) {
                    d.resolve(JobDetails.transformer(data));
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getRunningJobs: function (pageNumber, pageSize) {
                var params = {
                    pageNumber: pageNumber,
                    pageSize: pageSize
                };
                var runningJobsResource = $resource(scaleConfig.urls.getRunningJobs(), params),
                    runningJobsPoller = pollerFactory.newPoller(runningJobsResource, scaleConfig.pollIntervals.runningJobs);

                return runningJobsPoller.promise.then(null, null, function (data) {
                    if (data.$resolved) {
                        data.results = RunningJob.transformer(data.results);
                    } else {
                        runningJobsPoller.stop();
                    }
                    return data;
                });
            },
            getRunningJobsOnce: function (pageNumber, pageSize) {
                var d = $q.defer();

                $http.get(scaleConfig.urls.getRunningJobs(pageNumber, pageSize)).success(function (data) {
                    data.results = RunningJob.transformer(data.results);
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            updateJob: function (id, data) {
                data = data || getJobUpdateData();
                var d = $q.defer();

                $http({
                    url: scaleConfig.urls.updateJob(id),
                    method: 'PATCH',
                    data: data
                }).success(function (result) {
                    d.resolve(result);
                }).error(function (error) {
                    d.reject(error);
                });

                return d.promise;
            }
        };
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').service('jobExecutionService', function ($http, $q, $resource, poller, scaleConfig, JobExecution, JobExecutionLog) {

        var getJobExecutionsParams = function( pageNumber, pageSize, filter ){
            var params = {
                page: pageNumber,
                page_size: pageSize
            };
            var jobTypeId = filter.job_type_id ? filter.jobTypeId : '';
            var jobStatus = filter.status ? filter.jobStatus : '';

            if (jobStatus && jobStatus !== '') {
                params.job_status = jobStatus;
            }
            return params;
        };

        return {
            getJobExecutions: function (pageNumber, pageSize, filter) {
                var jobExecutions = [],
                    d = $q.defer();

                var params = getJobExecutionsParams(pageNumber, pageSize, filter);
                $http({
                    url: scaleConfig.urls.getJobExecutions(),
                    method: 'GET',
                    params: params
                }).success(function (data) {
                    jobExecutions.executions = JobExecution.transformer(data.results);
                    jobExecutions.count = data.count;
                    d.resolve(jobExecutions);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getJobExecutionDetails: function (id) {
                var d = $q.defer();

                $http.get(scaleConfig.urls.getJobExecutionDetails(id)).success(function (data) {
                    d.resolve(JobExecution.transformer(data));
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getLogOnce: function(execId){
                var d = $q.defer();

                $http.get(scaleConfig.urls.getJobExecutionLog(execId)).success(function (data) {
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getLog: function(execId){
                var url = url || scaleConfig.urls.getJobExecutionLog(execId);

                // Update view. Since a promise can only be resolved or rejected once but we want
                // to keep track of all requests, poller service uses the notifyCallback. By default
                // poller only gets notified of success responses.
                var jobExecutionLogResource = $resource(url);
                var jobExecutionLogPoller = poller.get(jobExecutionLogResource, {
                        delay: scaleConfig.pollIntervals.jobExecutionLog
                    });

                return jobExecutionLogPoller.promise.then(null, null, function (result) {
                    if(result.$resolved){
                        result.execution_log = JobExecutionLog.transformer(result);
                        if(result.execution_log.status === 'COMPLETED' || result.execution_log.status === 'FAILED'){
                            jobExecutionLogPoller.stop();
                        }
                        return result;
                    } else {
                        jobExecutionLogPoller.stop();
                        return result;
                    }

                });
            }
        };
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').service('jobTypeService', function ($http, $q, $resource, poller, pollerFactory, scaleConfig, jobService, JobType, JobTypeDetails, JobTypeStatus) {
        /*var totalJobTypes = 5;

        var getTotalJobTypes = function () {
            return totalJobTypes;
        };

        var setTotalJobTypes = function () {
            totalJobTypes = Math.floor(Math.random() * (20 - 1 + 1)) + 1;
        };

        setInterval(function () {
            setTotalJobTypes();
        }, 3100);*/

        var getJobTypeStatusParams = function (page, page_size, started, ended) {
            var params = {};

            if (page) { params.page = page; }
            if (page_size) { params.page_size = page_size; }
            if (started) { params.started = started; }
            if (ended) { params.ended = ended; }

            return params;
        };

        return {
            getJobTypes: function (order) {
                order = order || ['name','version'];

                var jobTypesResource = $resource(scaleConfig.urls.getJobTypes(order)),
                    jobTypesPoller = pollerFactory.newPoller(jobTypesResource, scaleConfig.pollIntervals.jobTypes);

                return jobTypesPoller.promise.then(null, null, function (data) {
                    if (data.$resolved) {
                        /*var returnResult = {
                            $resolved: true,
                            job_types: []
                        };
                        for (var i = 1; i < getTotalJobTypes(); i++) {
                            returnResult.job_types.push(
                                {
                                    "is_system": true,
                                    "paused": null,
                                    "disk": 64.0,
                                    "id": i,
                                    "docker_image": null,
                                    "archived": null,
                                    "uses_docker": false,
                                    "priority": 10,
                                    "version": "1.0",
                                    "icon_code": scaleConfig.jobTypes[i - 1].code,
                                    "description": "Ingests a source file into a workspace",
                                    "mem": 64.0,
                                    "is_active": true,
                                    "cpus": 1.0,
                                    "last_modified": "2015-03-11T00:00:00Z",
                                    "max_tries": 3,
                                    "is_paused": false,
                                    "name": scaleConfig.jobTypes[i - 1].title,
                                    "created": "2015-03-11T00:00:00Z",
                                    "timeout": 1800,
                                    "is_long_running": false
                                }
                            )
                        }
                        result = returnResult;*/

                        data.results = JobType.transformer(data.results);
                        return data;
                    } else {
                        jobTypesPoller.stop();
                        return data;
                    }
                });
            },
            getJobTypesOnce: function (order) {
                order = order || ['name','version'];

                var d = $q.defer();

                $http({
                    url: scaleConfig.urls.getJobTypes(),
                    method: 'GET',
                    params: { order: order }
                }).success(function (data) {
                    data.results = JobType.transformer(data.results);
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getJobTypeStatus: function (page, page_size, started, ended) {
                var params = getJobTypeStatusParams(page, page_size, started, ended);

                var jobTypeStatusResource = $resource(scaleConfig.urls.getJobTypeStatus(), params),
                    jobTypeStatusPoller = pollerFactory.newPoller(jobTypeStatusResource, scaleConfig.pollIntervals.jobTypeStatus);

                return jobTypeStatusPoller.promise.then(null, null, function (data) {
                    if (data.$resolved) {
                        /*var returndata = {
                            $resolved: true,
                            job_type_stats: []
                        };
                        for (var i = 0; i < getTotalJobTypes(); i++) {
                            returndata.job_type_stats.push(
                                {
                                    "id": i,
                                    "icon_code": "",
                                    "name": "",
                                    "version": "",
                                    "num_completed": Math.floor(Math.random() * (20000 - 10000 + 1)) + 10000,
                                    "num_canceled": Math.floor(Math.random() * (100 - 20 + 1)) + 20,
                                    "num_error_DATA": Math.floor(Math.random() * (9000 - 20 + 1)) + 20,
                                    "num_error_SYSTEM": Math.floor(Math.random() * (9000 - 20 + 1)) + 20,
                                    "num_error_ALGORITHM": Math.floor(Math.random() * (9000 - 20 + 1)) + 20
                                }
                            )
                        }
                        data = returndata;*/

                        data.results = JobTypeStatus.transformer(data.results);
                    } else {
                        jobTypeStatusPoller.stop();
                    }
                    return data;
                });
            },
            getJobTypeStatusOnce: function (page, page_size, started, ended) {
                var d = $q.defer(),
                    params = getJobTypeStatusParams(page, page_size, started, ended);

                $http({
                    url: scaleConfig.urls.getJobTypeStatus(),
                    method: 'GET',
                    params: params
                }).success(function (data) {
                    data.results = JobTypeStatus.transformer(data.results);
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getJobTypeDetails: function (id) {
                var d = $q.defer();
                $http.get(scaleConfig.urls.getJobTypeDetails(id)).success(function (data) {
                    d.resolve(JobTypeDetails.transformer(data));
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            updateJobType: function (data){
                var updatedJobType = function(data){
                    return {
                        error_mappings: data.error_mappings,
                        is_paused: data.is_paused
                    };
                }
                var updatedData = updatedJobType(data);
                var d = $q.defer();

                $http({
                    url: scaleConfig.urls.updateJobType(data.id),
                    method: 'PATCH',
                    data: updatedData
                }).success(function (result) {
                    d.resolve(JobTypeDetails.transformer(result));
                }).error(function (error) {
                    d.reject(error);
                });                
                return d.promise;
            }
        };
    });
})();

angular.module('scaleApp').controller('aisJobSummaryController', function($scope, $element, $modal, nodeService, scaleConfig) {
    'use strict';

    $scope.chart = {};

    // Calculates the status of the host given the number of errors and
    // duration since last checkin time.
    $scope.getStatus = function (h) {
        return 'btn-' + h.execution_style;
    };

    $scope.getIcon = function (jobTitle) {
        var job = _.find(scaleConfig.jobTypes, {title: jobTitle});
        return job ? 'fa-' + job.icon : 'fa-cog';
    };

    $scope.modalContent = function (host) {
        console.log(host);
        var margin = {top: 20, right: 20, bottom: 30, left: 50},
            width = $('#' + $scope.name + '-chart-health').width() - margin.left - margin.right,
            height = 200 - margin.top - margin.bottom;

        var x = d3.time.scale.utc()
            .range([0, width]);

        var y = d3.scale.linear()
            .range([height, 0]);

        var xAxis = d3.svg.axis()
            .scale(x)
            .orient('bottom')
            .ticks(9);

        var yAxis = d3.svg.axis()
            .scale(y)
            .orient('left')
            .ticks(5);

        var line = d3.svg.line()
            .x(function(d) { return x(d.date); })
            .y(function(d) { return y(d.successRate); });

        var svg = d3.select('#' + $scope.name + '-chart-health').append('svg')
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom)
            .append('g')
            .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

        nodeService.getNode(host.id).then(function (node) {
            if (node) {
                var data = _.sortBy(node.nodeHistory, 'date'),
                    yMin = Math.floor(d3.min(_.pluck(data, 'successRate')));

                x.domain(d3.extent(data, function(d) { return d.date; }));
                y.domain([yMin > 2 ? yMin - 2 : yMin,100]);

                svg.append('g')
                    .attr('class', 'x axis')
                    .attr('transform', 'translate(0,' + height + ')')
                    .call(xAxis);

                svg.append('g')
                    .attr('class', 'y axis')
                    .call(yAxis)
                    .append('text')
                    .attr('transform', 'rotate(-90)')
                    .attr('y', 6)
                    .attr('dy', '.71em')
                    .style('text-anchor', 'end')
                    .text('Success Rate (%)');

                svg.append('path')
                    .datum(data)
                    .attr('class', 'line')
                    .attr('d', line);
            }
        }).fail(function (error) {
            $scope.status = 'Unable to load node data: ' + error.message;
            console.error($scope.status);
        });
    };

    $scope.showModal = function(jobtype,name){
        var modalInstance = $modal.open({
            animation: $scope.animationsEnabled,
            templateUrl: 'modalContentJobs.html',
            size: 'lg',
            controller: function dialogController($scope, $modalInstance) {
                $scope.jobtype = jobtype;
                $scope.name = name;
            }
        });

        modalInstance.opened.then(function (selectedItem) {
            setTimeout(function () {
                $scope.modalContent($scope.jobtype);
            }, 200);

        });
    };
})
.directive('aisJobSummary', function () {
    'use strict';
    /**
     * Usage: <ais-job-summary jobtype={jobtype} name={jobname}></ais-host-summary>
     */
    return {
        controller: 'aisJobSummaryController',
        restrict: 'E',
        templateUrl: 'modules/jobsummary/jobsummaryTemplate.html',
        scope: {
            jobtype: '=',
            name: '=',
            data: '='
        }
    };

});

/**
 * <ais-area />
 */
angular.module('scaleApp').directive('aisArea', function () {

    'use strict';

    /**
     * Usage: <ais-area data="dater" axis-type-x="time" axis-type-y="linear" value-x="abc" value-y="xyz" height="200" />
     */
    return {
        controller: 'aisAreaController',
        templateUrl: 'modules/charts/areaTemplate.html',
        restrict: 'E',
        scope: {
            name: '=',
            data: '=',
            axisTypeX: '=',
            axisTypeY: '=',
            valueX: '=',
            valueY: '=',
            height: '='
        }
    };

});

angular.module('scaleApp').controller('aisAreaController', function($scope, $location, navService, queueService, scaleConfig) {
    'use strict';

    $scope.zoomEnabled = false;
    $scope.zoomText = 'Enable Zoom';
    $scope.zoomClass = 'label-default';

    $scope.toggleZoom = function () {
        $scope.zoomEnabled = !$scope.zoomEnabled;
        if ($scope.zoomEnabled) {
            $scope.zoomClass = 'label-primary';
            $scope.zoomText = 'Disable Zoom';
            $('.area rect.overlay').css({'pointer-events': 'all'});
        } else {
            $scope.zoomClass = 'label-default';
            $scope.zoomText = 'Enable Zoom';
            $('.area rect.overlay').css({'pointer-events': 'none'});
        }
    };

    var initialize = function() {
        var values = [];
        _.forEach($scope.data.chart_data, function (d) {
            values = values.concat(d.values);
        });

        var margin = {top: 20, right: 30, bottom: 30, left: 60},
            width = $('.chart-container').width() - margin.left - margin.right,
            height = $scope.height - margin.top - margin.bottom,
            xStart = moment.utc(_.min(values, 'sort_str').label).toISOString(),
            xEnd = moment.utc(_.max(values, 'sort_str').label).toISOString(),
            x = $scope.axisTypeX === 'time' ? d3.time.scale.utc().range([0, width]) : d3.scale.linear().range([0, width]),
            y = $scope.axisTypeY === 'time' ? d3.time.scale.utc().range([height, 0]) : d3.scale.linear().range([height, 0]),
            color = d3.scale.category20();

        /*var tooltip = d3.select('body')
            .append('div')
            .attr('class', 'remove')
            .style('position', 'absolute')
            .style('z-index', '20')
            .style('visibility', 'hidden')
            .style('top', '30px')
            .style('left', '55px');*/

        var xAxis = d3.svg.axis()
            .scale(x)
            .orient('bottom');

        var yAxis = d3.svg.axis()
            .scale(y)
            .orient('left');

        var zoom = d3.behavior.zoom()
            .on('zoom', draw);

        var area = d3.svg.area()
            .x(function (d) { return x(d.date); })
            .y0(height)
            .y1(function (d) { return y(height + d.y); });

        var stack = d3.layout.stack()
            .values(function (d) { return d.values; });

        var chart = d3.select('.area')
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom)
            .append('g')
            .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

        chart.append('clipPath')
            .attr('id', 'clip')
            .append('rect')
            .attr('x', x(0))
            .attr('y', y(1))
            .attr('width', x(1) - x(0))
            .attr('height', y(0) - y(1));

        color.domain(_.pluck($scope.data.chart_data, 'key'));

        x.domain([xStart, xEnd]);
        y.domain([0, _.max(values, $scope.valueY)[$scope.valueY]]);
        zoom.x(x);

        var priorities = stack(color.domain().map(function(key) {
            return {
                key: key,
                values: _.find($scope.data.chart_data, 'key', key).values.map(function (d) {
                    return {date: moment.utc(d.label).toISOString(), y: d.value};
                })
            };
        }));

        var priority = chart.selectAll('.priority')
            .data(priorities)
            .enter().append('g')
            .attr('class', 'priority');

        priority.append('path')
            .attr('class', 'area')
            .attr('clip-path', 'url(#clip)');

        chart.append('rect')
            .attr('class', 'overlay')
            .attr('width', width)
            .attr('height', height)
            .call(zoom);

        chart.append('g')
            .attr('class', 'x axis')
            .attr('transform', 'translate(0,' + height + ')');

        chart.append('g')
            .attr('class', 'y axis');

        var legend = chart.append('g')
            .attr('class', 'legend')
            .attr('x', width - 65)
            .attr('y', 25)
            .attr('height', 100)
            .attr('width', 100);

        legend.selectAll('g').data(priorities)
            .enter()
            .append('g')
            .each(function(d, i) {
                var g = d3.select(this);
                g.append('rect')
                    .attr('x', width + 7)
                    .attr('y', i * 25)
                    .attr('width', 10)
                    .attr('height', 10)
                    .style('fill', color.range()[d.key.toString()]);

                g.append('text')
                    .attr('x', width + 22)
                    .attr('y', i * 25 + 8)
                    .attr('height',30)
                    .attr('width',100)
                    .style('fill', color.range()[d.key.toString()])
                    .text(d.key.toString());

            });

        chart.selectAll('.area')
            .attr('opacity', 1)
            .on('mouseover', function (d, i) {
                chart.selectAll('.area').transition()
                    .duration(250)
                    .attr('opacity', function(d, j) {
                        return j != i ? 0.05 : 1;
                    })})
            .on('mouseout', function () {
                chart.selectAll('.area').transition()
                    .duration(250)
                    .attr('opacity', 1)
            });
            /*.on('mousemove', function(d, i) {
                var datearray = [];
                var mousex = d3.mouse(this);
                mousex = mousex[0];
                var invertedx = x.invert(mousex);
                invertedx = invertedx.getMonth() + invertedx.getDate();
                var selected = (d.values);
                for (var k = 0; k < selected.length; k++) {
                    datearray[k] = selected[k].date;
                    datearray[k] = datearray[k].getMonth() + datearray[k].getDate();
                }

                var mousedate = datearray.indexOf(invertedx);
                var pro = d.values[mousedate].y;

                d3.select(this)
                    .classed('hover', true)
                    .attr('stroke', '#fff')
                    .attr('stroke-width', '0.5px'),
                    tooltip.html( "<p>" + d.key + "<br>" + pro + "</p>" ).style("visibility", "visible");

            });*/

        draw();

        function draw() {
            chart.select('g.x.axis').call(xAxis);
            chart.select('g.y.axis').call(yAxis);
            priority.select('path.area')
                .attr('d', function (d) { return area(d.values); })
                .style('fill', function (d) { return color(d.key); });
        }
    };

    $scope.$watch('data', function (arr) {
        if ($scope.data.chart_data) {
            initialize();
        }
    });
});

(function () {
    'use strict';

    angular.module('scaleApp').directive('aisQueueDepth', function () {
        /**
         * Usage: <ais-queue-depth data="dater" ticks="10" />
         */
        return {
            controller: 'aisQueueDepthController',
            templateUrl: 'modules/charts/queueDepthTemplate.html',
            restrict: 'E',
            scope: {
                data: '=',
                showFilter: '=', // show time range filter UI
                total: '=',
                cullLegend: '=' // only show job types in legend whose value is > 0
            }
        };

    });
})();
(function () {
    'use strict';

    angular.module('scaleApp').controller('aisQueueDepthController', function ($scope, scaleConfig, queueDepthService) {
        var chart = null,
            colArr = [],
            xArr = [],
            removeIds = [],
            legendHide = [];

        $scope.filterValue = 1;
        $scope.filterDuration = 'w';
        $scope.filterDurations = ['M', 'w', 'd'];
        $scope.zoomEnabled = false;
        $scope.zoomClass = 'btn-default';
        $scope.zoomText = 'Enable Zoom';
        $scope.groupBy = 'jobType';
        $scope.legendLabel = 'Job Types';
        $scope.priorityClass = 'btn-default';
        $scope.jobTypeClass = 'btn-primary';
        $scope.queueData = {};
        $scope.loadingQueue = true;
        $scope.queueDepthError = null;
        $scope.queueDepthErrorStatus = null;

        var colrs = scaleConfig.colors;
        $scope.colorPattern = [colrs.emo_1, colrs.emo_2, colrs.emo_3, colrs.emo_4, colrs.emo_5];

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
            removeIds = [];
            _.forEach(colArr, function (col) {
                if (col[0] !== 'x') {
                    removeIds.push(col[0].toString());
                }
            });
            colArr = [];
            xArr = [];
            legendHide = [];
            var queueDepthData = $scope.queueData;
            if ($scope.groupBy === 'jobType' && $scope.cullLegend) {
                var depths = _.pluck(queueDepthData.queue_depths, 'depth_per_job_type'),
                    values = [];
                _.forEach(queueDepthData.job_types, function (type, idx) {
                    values = [];
                    _.forEach(depths, function (d) {
                        values.push(d[idx]);
                    });
                    if (_.sum(values) === 0) {
                        legendHide.push(type.name);
                    }
                });
            }
            // x axis values
            xArr = _.pluck(queueDepthData.queue_depths, 'time');
            _.forEach(xArr, function (d, i) {
                xArr[i] = moment.utc(d).toDate();
            });
            xArr.unshift('x');
            colArr.push(xArr);

            // data values
            if ($scope.groupBy === 'priority') {
                _.forEach(queueDepthData.priorities, function (d, i) {
                    var idx = 'depth_per_priority[' + i + ']';
                    var tmpArr = _.pluck(queueDepthData.queue_depths, idx);
                    tmpArr.unshift(d.priority);
                    colArr.push(tmpArr);
                });
            } else {
                _.forEach(queueDepthData.job_types, function (d, i) {
                    var idx = 'depth_per_job_type[' + i + ']';
                    var tmpArr = _.pluck(queueDepthData.queue_depths, idx);
                    tmpArr.unshift(d.name);
                    colArr.push(tmpArr);
                });
            }

            var types = {},
                type = {},
                groups = [];
            _.forEach(colArr, function(col){
                    type = {};
                    if(col[0] !== 'x'){
                        type[col[0]] = 'area';
                        groups.push(col[0]);
                    }
                angular.extend(types, type);
            });

            if (chart) {
                chart.load({
                    columns: colArr,
                    types: types,
                    unload: removeIds
                });
                chart.groups([groups]);
                legend.hide(legendHide);
            } else {
                // chart config
                chart = c3.generate({
                    bindto: '#queue-depth',
                    data: {
                        x: 'x',
                        columns: colArr,
                        types: types,
                        groups: [groups]
                    },
                    transition: {
                        duration: 700
                    },
                    color: {
                        pattern: scaleConfig.colors.patternDefault
                    },
                    legend: {
                        hide: legendHide
                    },
                    tooltip: {
                        /*
                        // only show in tooltip if value is greater than zero
                        format: {
                            value: function(value, ratio, id, index) {
                                if(value > 0){
                                    return value;
                                }
                            }
                        }
                        */
                        //grouped: false
                        contents: function (d, defaultTitleFormat, defaultValueFormat, color) {
                            console.log(d);
                            return '<div style="background: #fff; padding: 10px;"><strong>' + moment(d[0].x).utc().format(scaleConfig.dateFormats.day_minute) + ':</strong> ' + _.sum(d, 'value') + ' jobs</div>';
                        }
                    },
                    axis: {
                        type: 'timeseries',
                        x: {
                            tick: {
                                format: function (d) {
                                    return moment.utc(d).format(scaleConfig.dateFormats.day);
                                },
                                values: function (d) {
                                    var dayDiff = moment.duration(moment.utc(d[1]).diff(moment.utc(d[0]))).days(),
                                        dayArr = [];
                                    dayArr.push(d[0]);
                                    for (var i = 1; i < dayDiff; i++) {
                                        dayArr.push(moment.utc(d[0]).add(i, 'd').valueOf());
                                    }
                                    dayArr.push(d[1]);
                                    return dayArr;
                                }
                            }
                        }
                    }
                });
            }

            $scope.loadingQueue = false;
            console.log(depths);
        };

        var getQueueDepth = function () {
            $scope.loadingQueue = true;
            var started = moment.utc().subtract($scope.filterValue, $scope.filterDuration).toISOString(),
                ended = moment.utc(started).add(1, $scope.filterDuration).toISOString();

            queueDepthService.getQueueDepth(started, ended).then(null, null, function (result) {
                if (result.$resolved) {
                    $scope.queueData = result;
                    initChart();
                    //console.log('redraw queue depth');
                } else {
                    if (result.statusText && result.statusText !== '') {
                        $scope.queueDepthErrorStatus = result.statusText;
                    }
                    $scope.queueDepthError = 'Unable to retrieve queue depth.';
                }
                $scope.loadingQueue = false;
            });
        };

        $scope.updateChart = function (type) {
            $scope.groupBy = type;
            $scope.priorityClass = type === 'priority' ? 'btn-primary' : 'btn-default';
            $scope.jobTypeClass = type === 'jobType' ? 'btn-primary' : 'btn-default';
            $scope.legendLabel = type === 'priority' ? 'Job Priorities' : 'Job Types';
            initChart();
        };

        $scope.updateQueueRange = function (action) {
            if (action === 'older') {
                $scope.filterValue++;
            } else if (action === 'newer') {
                if ($scope.filterValue > 1) {
                    $scope.filterValue--;
                }
            } else if (action === 'current') {
                $scope.filterValue = 1;
            }
            getQueueDepth();
        };

        $scope.$watch('filterValue', function (value) {
            var $queueNewer = $('.queue-newer'),
                $queueToday = $('.queue-current');

            if (value > 1) {
                $queueNewer.removeAttr('disabled');
                $queueToday.removeAttr('disabled');
            } else {
                $queueNewer.attr('disabled', 'disabled');
                $queueToday.attr('disabled', 'disabled');
            }
        });

        getQueueDepth();
    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').directive('aisGridChart', function () {
        /**
         * Usage: <ais-grid-chart data="dater" selector="'jobs' or 'nodes'" scale="1" />
         */
        return {
            controller: 'aisGridChartController',
            templateUrl: 'modules/charts/gridChartTemplate.html',
            restrict: 'E',
            scope: {
                data: '=',
                icons: '=', // indicates whether cell-text is entirely made up of icons
                scale: '=', // multiplier to increase cell size
                reveal: '=', // if true, less data will show when zoomed out
                mode: '@', // valid values are zoom or tooltip
                columns: '=',
                rows: '=',
                showAxes: '='
            }
        };

    });
})();

(function () {
    'use strict';

    angular.module('scaleApp').controller('aisGridChartController', function ($rootScope, $scope, $location, $modal, userService, scaleConfig) {
        var svg = null,
            rect = null,
            scale = parseFloat($scope.scale),
            tip = d3.tip()
                .attr('class', 'd3-tip')
                .offset([-10, 0])
                .html(function(d) {
                    return d.title + ' ' + d.version + '<br />' + getCellError(d) + '<br />' + getCellTotal(d);
                });

        $scope.loading = true;
        $scope.dataValues = [];
        $scope.cellWidth = 50 * scale;
        $scope.cellHeight = 50 * scale;
        $scope.enableZoom = typeof $scope.mode !== 'undefined' ? $scope.mode === 'zoom' : true;
        $scope.enableTooltip = typeof $scope.mode !== 'undefined' ? $scope.mode === 'tooltip' : false;
        $scope.enableReveal = typeof $scope.reveal !== 'undefined' ? $scope.reveal : true;
        $scope.user = userService.getUserCreds();
        $scope.pauseReason = '';
        $scope.gridData = [];
        $scope.gridClass = function () {
            return $scope.icons === true ? 'icons' : '';
        };

        var width = $('.grid-chart').width(),
            height = $scope.rows ? ($scope.cellHeight * $scope.rows) + 10 : ($scope.cellHeight * 6) + 10, // multiply cell height by 8 (highest zoom scale extent value) plus some breathing room
            cols = 0,
            rows = 0,
            cellFontLg = .4,
            cellFontSm = .3;

        var getDataValues = function (data) {
            $scope.gridData = [];
            $scope.dataValues = [];
            if (data.data) {
                var dataType = data.data.toString().split(',')[0];
                if (dataType === 'JobType') {
                    $scope.dataValues = _.sortByOrder(_.values(data.data), ['name'], ['asc']);
                    // associate JobType with JobTypeStatus
                    _.forEach($scope.dataValues, function (val) {
                        val.status = _.find(data.status, 'job_type.id', val.id);
                    });
                    $scope.dataValues = _.sortByOrder(_.values(data.data), ['status.has_running', 'status.description', 'name'], ['asc', 'asc', 'asc']);
                } else if (dataType === 'Node') {
                    $scope.dataValues = _.sortByOrder(_.values(data.data), ['hostname'], ['asc']);
                    // associate Node with NodeStatus
                    _.forEach($scope.dataValues, function (val) {
                        val.status = _.find(data.status, 'node.id', val.id);
                    });
                    $scope.dataValues = _.sortByOrder($scope.dataValues, ['hostname'], ['asc']); // sort by hostName asc
                } else {
                    $scope.dataValues = data.data;
                }

                cols = $scope.columns ? $scope.columns : Math.floor(width / $scope.cellWidth);
                rows = $scope.rows ? $scope.rows : Math.ceil($scope.dataValues.length / cols);

                d3.range(rows).map(function (row) {
                    d3.range(cols).map(function (col) {
                        if (col <= $scope.dataValues.length - 1) {
                            var dataObj = $scope.dataValues[(cols * row) + col];
                            if (dataObj) {
                                dataObj.coords = [col * $scope.cellHeight, row * $scope.cellWidth];
                                $scope.gridData.push(dataObj);
                            }
                        }
                    });
                });

                update();
            }
        };

        var revealData = function () {
            d3.selectAll('.cell-text')
                .style('display', 'none');
            d3.selectAll('.cell-text-detail')
                .style('display', 'block');
            d3.selectAll('.cell-pause-resume-icon')
                .style('display', 'block');
        };

        var hideData = function () {
            d3.selectAll('.cell-text')
                .style('display', 'block');
            d3.selectAll('.cell-text-detail')
                .style('display', 'none');
            d3.selectAll('.cell-pause-resume-icon')
                .style('display', 'none');
        };

        var initialize = function (data) {
            cols = $scope.columns ? $scope.columns : Math.floor(width / $scope.cellWidth);
            rows = $scope.rows ? $scope.rows : Math.ceil($scope.dataValues.length / cols);

            var tickValues = Array.apply(null, {length: rows}).map(Number.call, Number);

            var zoom = d3.behavior.zoom()
                .scaleExtent([1, 6])
                //.center([0, 0])
                .on('zoom', zoomed);

            if ($scope.enableZoom) {
                svg = d3.select('.grid-chart').append('svg')
                    .attr('width', width)
                    .attr('height', height)
                    .append('g')
                    .call(zoom)
                    .append('g');
            } else if ($scope.enableTooltip) {
                svg = d3.select('.grid-chart').append('svg')
                    .attr('width', width)
                    .attr('height', height)
                    .append('g')
                    .call(tip);
            } else {
                svg = d3.select('.grid-chart').append('svg')
                    .attr('width', width)
                    .attr('height', height)
                    .append('g');
            }

            svg.append('rect')
                .attr('class', 'overlay')
                .attr('width', width)
                .attr('height', height);

            if ($scope.showAxes) {
                var y = d3.scale.linear()
                    .domain([0, rows])
                    .range([0, height-10]);

                var yAxis = d3.svg.axis()
                    .scale(y)
                    .orient('left')
                    .tickValues(tickValues);

                svg.attr('transform', 'translate(' + 25 + ',' + 0 + ')')
                    .append('g')
                    .attr('class', 'y axis')
                    .attr('transform', 'translate(' + 0 + ',' + $scope.cellHeight / 2 + ')')
                    .call(yAxis);
            }

            getDataValues(data);

            function zoomed() {
                var s = d3.event.scale;

                if ($scope.enableReveal) {
                    if (s > 3) {
                        revealData();
                    } else {
                        hideData();
                    }
                }
                if (s === 1) {
                    if ($scope.showAxes) {
                        zoom.translate([25, 0]);
                    } else {
                        zoom.translate([0, 0]);
                    }
                }
                svg.attr('transform', 'translate(' + zoom.translate() + ')scale(' + d3.event.scale + ')');
            }

            $scope.loading = false;
        };

        var dragOffsetX = 0,
            dragOffsetY = 0,
            clickOffsetX = 0,
            clickOffsetY = 0;

        var drag = d3.behavior.drag()
            .on('dragstart', function () {
                // track offsetX and offsetY to distinguish between drag and click
                dragOffsetX = d3.event.sourceEvent.offsetX;
                dragOffsetY = d3.event.sourceEvent.offsetY;
            });

        var getCellFill = function (d) {
            if (d && d.status) {
                return d.status.getCellFill();
            }
            return 'none';
        };

        var getCellText = function (d) {
            if (d) {
                return d.getCellText();
            }
        };

        var getCellActivity = function (d) {
            if (d && d.status) {
                return d.status.getCellActivity();
            }
        };

        var getCellPauseResume = function (d) {
            if (d && d.status) {
                return d.status.getCellPauseResume();
            }
        };

        var getCellActivityTotal = function (d) {
            if (d && d.status) {
                return d.status.getCellActivityTotal();
            }
        };

        var getCellTitle = function (d) {
            if (d) {
                return d.getCellTitle();
            }
        };

        var getCellError = function (d) {
            if (d && d.status) {
                return d.status.getCellError();
            }
            return 'Failed: Unavailable';
        };

        var getCellTotal = function (d) {
            if (d && d.status) {
                return d.status.getCellTotal();
            }
            return 'Completed: Unavailable';
        };

        var getCellStatus = function (d) {
            if (d && d.status) {
                if (d.toString() === 'Node') {
                    return d.status.getCellStatus();
                }
            }
            return 'Status Unavailable';
        };

        var getCellJobs = function (d) {
            if (d && d.status) {
                if (d.toString() === 'Node') {
                    return d.status.getCellJobs();
                }
            }
        };

        var cellClickHandler = function (target) {
            // track offsetX and offsetY to distinguish between drag and click
            clickOffsetX = d3.event.offsetX;
            clickOffsetY = d3.event.offsetY;
            if (dragOffsetX === clickOffsetX && dragOffsetY === clickOffsetY) {
                // offsets are the same; no dragging occurred; process as click event
                $scope.$apply(function () {
                    if (target.toString() === 'JobType') {
                        $location.path('/jobs/types/' + target.id);
                    } else if (target.toString() === 'Node') {
                        $location.path('/nodes/' + target.id);
                    }
                });
            }
        };

        var update = function () {
            // DATA JOIN
            // Join new data with old elements, if any.
            if ($scope.enableTooltip) {
                var containerGroup = svg.selectAll('.cell-group')
                    .data($scope.gridData, function (d) { return d.coords; })
                    .on('mouseover', tip.show)
                    .on('mouseout', tip.hide)
                    .on('click', tip.hide);
            } else {
                var containerGroup = svg.selectAll('.cell-group')
                    .data($scope.gridData, function (d) { return d.coords; });
            }

            // UPDATE
            // Update old elements as needed.
            containerGroup.selectAll('.cell')
                .data($scope.gridData, function (d) { return d.coords; })
                .transition()
                .duration(750)
                .style('stroke', function (d) {
                    return d ? '#fff' : 'none';
                })
                .style('fill', function (d) {
                    return getCellFill(d);
                });

            containerGroup.selectAll('.cell-text')
                .data($scope.gridData, function (d) { return d.coords; })
                .html(function (d) {
                    return getCellText(d);
                });

            containerGroup.selectAll('.cell-total-active')
                .data($scope.gridData, function (d) { return d.coords; })
                .text(function (d) {
                    if (d.toString() === 'JobType') {
                        return getCellActivityTotal(d);
                    }
                });

            containerGroup.selectAll('.cell-pause-resume-icon')
                .data($scope.gridData, function (d) { return d.coords; })
                .html(function (d) {
                    return getCellPauseResume(d);
                });

            containerGroup.selectAll('.cell-activity-icon')
                .data($scope.gridData, function (d) { return d.coords; })
                .html(function (d) {
                    return getCellActivity(d);
                });

            containerGroup.selectAll('.cell-title')
                .data($scope.gridData, function (d) { return d.coords; })
                .html(function (d) {
                    return getCellTitle(d);
                });

            containerGroup.selectAll('.cell-error')
                .data($scope.gridData, function (d) { return d.coords; })
                .text(function (d) {
                    return getCellError(d, true);
                });

            containerGroup.selectAll('.cell-total')
                .data($scope.gridData, function (d) { return d.coords; })
                .text(function (d) {
                    return getCellTotal(d);
                });

            containerGroup.selectAll('.cell-status')
                .data($scope.gridData, function (d) { return d.coords; })
                .text(function (d) {
                    return getCellStatus(d);
                });

            containerGroup.selectAll('.cell-jobs')
                .data($scope.gridData, function (d) { return d.coords; })
                .html(function (d) {
                    return getCellJobs(d);
                });

            containerGroup.selectAll('.cell-overlay')
                .data($scope.gridData, function (d) { return d.coords; })
                .on('click', function (target) {
                    cellClickHandler(target);
                });

            // ENTER
            // Create new elements as needed.
            var cellGroup = containerGroup.enter()
                .append('g')
                .attr('class', 'cell-group');

            cellGroup.append('rect')
                .attr('class', 'cell')
                .attr('width', $scope.cellWidth)
                .attr('height', $scope.cellHeight)
                .style('fill', function (d) {
                    return getCellFill(d);
                })
                .style('stroke', function (d) {
                    return d ? '#fff' : 'none';
                })
                .transition()
                .duration(750);

            cellGroup.append('text')
                .attr('class', 'cell-text')
                .html(function (d) {
                    return getCellText(d);
                })
                .attr('text-anchor', 'middle')
                .attr('x', $scope.cellWidth / 2)
                .attr('y', ($scope.cellHeight / 2) + 12)
                .style('display', $scope.enableReveal ? 'block' : 'none');

            cellGroup.append('text')
                .attr('class', 'cell-total-active')
                .text(function (d) {
                    if (d.toString() === 'JobType') {
                        return getCellActivityTotal(d);
                    }
                })
                .attr('text-anchor', 'end')
                .attr('x', $scope.cellWidth - 2)
                .attr('y', $scope.cellHeight - 5)
                .style('display', $scope.enableReveal ? 'block' : 'none');

            cellGroup.append('g')
                .attr('class', 'cell-activity')
                .append('text')
                .attr('class', 'cell-activity-icon')
                .html(function (d) {
                    return getCellActivity(d);
                })
                .attr('text-anchor', 'end')
                .attr('x', $scope.cellWidth - 2)
                .attr('y', 14);

            var detail = cellGroup.append('text')
                .attr('class', 'cell-text-detail')
                .attr('text-anchor', 'middle')
                .attr('x', $scope.cellWidth / 2)
                .attr('y', Math.floor($scope.cellHeight *.15)) // 15% from top of cell
                .attr('dy', 0)
                .style('display', $scope.enableReveal ? 'none' : 'block');

            detail.append('tspan')
                .attr('class', 'cell-title')
                .attr('text-anchor', 'middle')
                .attr('x', $scope.cellWidth / 2)
                .attr('y', Math.floor($scope.cellHeight * .15)) // 15% from top of cell
                .attr('dy', 0)
                .style('font-size', cellFontSm * scale + 'em')
                .html(function (d) {
                    return getCellTitle(d);
                })
                .call(wrap);

            detail.append('tspan')
                .attr('class', 'cell-error')
                .attr('text-anchor', 'middle')
                .attr('x', $scope.cellWidth / 2)
                .attr('y', Math.floor($scope.cellHeight *.3)) // 30% from top of cell
                .attr('dy', 0)
                .style('font-size', cellFontSm * scale + 'em')
                .text(function (d) {
                    return getCellError(d);
                })
                .call(wrap);

            detail.append('tspan')
                .attr('class', 'cell-total')
                .attr('text-anchor', 'middle')
                .attr('x', $scope.cellWidth / 2)
                .attr('y', Math.floor($scope.cellHeight *.4)) // 40% from top of cell
                .attr('dy', 0)
                .style('font-size', cellFontSm * scale + 'em')
                .text(function (d) {
                    return getCellTotal(d);
                })
                .call(wrap);

            detail.append('tspan')
                .attr('class', 'cell-status')
                .attr('text-anchor', 'middle')
                .attr('x', $scope.cellWidth / 2)
                .attr('y', Math.floor($scope.cellHeight * .55)) // 55% from top of cell
                .attr('dy', 0)
                .style('font-size', cellFontLg * scale + 'em')
                .text(function (d) {
                    return getCellStatus(d);
                });

            detail.append('tspan')
                .attr('class', 'cell-jobs')
                .attr('text-anchor', 'middle')
                .attr('x', $scope.cellWidth / 2)
                .attr('y', Math.floor($scope.cellHeight * .75)) // 75% from top of cell
                .attr('dy', 0)
                .style('font-size', cellFontSm * scale + 'em')
                .html(function (d) {
                    return getCellJobs(d);
                })
                .call(wrap);

            cellGroup.append('rect')
                .attr('class', 'cell-overlay')
                .attr('width', $scope.cellWidth)
                .attr('height', $scope.cellHeight)
                .on('mouseover', function () {
                    d3.select(d3.select(this)[0][0].parentElement.children[0])
                        .style('fill-opacity', '0.75');
                })
                .on('mouseout', function () {
                    d3.select(d3.select(this)[0][0].parentElement.children[0])
                        .style('fill-opacity', '1.0');
                })
                .on('click', function (d) {
                    cellClickHandler(d);
                })
                .call(drag);

            if ($scope.user && $scope.user.is_admin) {
                cellGroup.append('text')
                    .attr('class', 'cell-pause-resume-icon')
                    .html(function (d) {
                        return getCellPauseResume(d);
                    })
                    .attr('text-anchor', 'start')
                    .attr('x', 5)
                    .attr('y', 20)
                    .style('display', $scope.enableReveal ? 'none' : 'block')
                    .style('font-size', '1.3em')
                    .on('mouseover', function () {
                        d3.select(this)
                            .style('cursor', 'pointer')
                            .style('fill', scaleConfig.colors.chart_blue);
                    })
                    .on('mouseout', function () {
                        d3.select(this)
                            .style('fill', 'white');
                    })
                    .on('click', function (target) {
                        var pauseResume = function () {
                            var targetData = {};
                            if (target && target.status) {
                                targetData = target;
                                targetData.status.pauseResumeCell($scope.pauseReason).then(function (updatedData) {
                                    if (targetData.toString() === 'Node') {
                                        // update target data values
                                        targetData.is_paused = updatedData.is_paused;
                                        targetData.pause_reason = updatedData.pause_reason;
                                        targetData.status.node = updatedData;
                                        $rootScope.$broadcast('updateNodeHealth');
                                    }
                                    // update grid cell
                                    updateCellFill();
                                    updatePauseResume();
                                    updateCellStatus();
                                });
                            }
                        };

                        // only prompt for reason when pausing (not resuming)
                        if (!target.is_paused) {
                            var modalInstance = $modal.open({
                                animation: true,
                                templateUrl: 'pauseDialog.html',
                                scope: $scope
                            });

                            modalInstance.result.then(function () {
                                pauseResume();
                            });
                        } else {
                            pauseResume();
                        }
                    });
            }

            // ENTER + UPDATE
            // Appending to the enter selection expands the update selection to include
            // entering elements; so, operations on the update selection after appending to
            // the enter selection will apply to both entering and updating nodes.
            containerGroup.transition()
                .duration(750)
                .attr('transform', function (d) {
                    return 'translate(' + d.coords + ')';
                });

            var updateCellFill = function () {
                containerGroup.selectAll('.cell')
                    .transition()
                    .duration(250)
                    .style('stroke', function (d) {
                        return d ? '#fff' : 'none';
                    })
                    .style('fill', function (d) {
                        return getCellFill(d);
                    });
            };

            var updatePauseResume = function () {
                containerGroup.selectAll('.cell-pause-resume-icon')
                    .html(function (d) {
                        return getCellPauseResume(d);
                    });
            };

            var updateCellStatus = function () {
                containerGroup.selectAll('.cell-status')
                    .text(function (d) {
                        return getCellStatus(d);
                    });
            };

            // EXIT
            // Remove old elements as needed.
            containerGroup.exit()
                .attr('class', 'cell-exit')
                .transition()
                .duration(750)
                .attr('transform', 'translate(0,0)')
                .remove();

            function wrap (text, width) {
                text.each(function () {
                    var text = d3.select(this),
                        words = text.text().split(/\s+/).reverse(),
                        word,
                        line = [],
                        lineNumber = 0,
                        lineHeight = 1.1,
                        y = text.attr('y'),
                        dy = parseFloat(text.attr('dy')),
                        tspan = text.text(null).append('tspan').attr('x', $scope.cellWidth / 2).attr('y', y).attr('dy', dy + 'em');
                    while (word = words.pop()) {
                        if (word !== 'undefined') {
                            line.push(word);
                            tspan.text(line.join(' '));
                            if (tspan.node().getComputedTextLength() > ($scope.cellWidth - 10)) {
                                line.pop();
                                tspan.text(line.join(' '));
                                line = [word];
                                tspan = text.append('tspan').attr('x', $scope.cellWidth / 2).attr('y', y).attr('dy', ++lineNumber * lineHeight + dy + 'em').text(word);
                            }
                        }
                    }
                });
            }
        };

        $scope.$watch('data', function (data) {
            if (_.keys(data).length > 0) {
                $('.grid-chart').empty();
                initialize(data);
            }
        });

        $scope.$on('redrawGrid', function (event, data) {
            getDataValues(data);
        });
    });
})();
