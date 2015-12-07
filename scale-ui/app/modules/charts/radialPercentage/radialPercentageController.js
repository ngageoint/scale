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
