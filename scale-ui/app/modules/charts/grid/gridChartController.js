(function () {
    'use strict';

    angular.module('scaleApp').controller('aisGridChartController', function ($rootScope, $scope, $location, $uibModal, userService, scaleConfig) {
        var svg = null,
            rect = null,
            scale = parseFloat($scope.scale),
            tip = d3.tip()
                .attr('class', 'd3-tip')
                .offset([-10, 0])
                .html(function(d) {
                    var failures = d.status.getFailures(),
                        failStr = '';

                    _.forEach(failures, function (f) {
                        failStr = failStr + _.capitalize(f.status.toLowerCase()) + ' Errors: ' + f.count + '<br />';
                    });
                    return d.title + ' ' + d.version + '<br />' + failStr + getCellTotal(d);
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

        var getCellFailures = function (d) {
            if (d && d.status) {
                if (d.toString() === 'JobType') {
                    return d.status.getCellFailures();
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
                        $location.path('/jobs').search('job_type_id', target.id).search('status', target.status.has_running.status);
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

            containerGroup.selectAll('.cell-failure-system')
                .data($scope.gridData, function (d) { return d.coords; })
                .transition()
                .duration(750)
                .attr('x', 0)
                .attr('y', 0)
                .attr('width', function (d) {
                    var failures = getCellFailures(d);
                    if (failures && failures.length > 0) {
                        return $scope.cellWidth / failures.length;
                    }
                    return $scope.cellWidth;
                })
                .style('fill', function (d) {
                    var failures = getCellFailures(d);
                    if (_.findWhere(failures, 'SYSTEM')) {
                        return '#1F77B4';
                    }
                    return 'none';
                })
                .style('display', function (d) {
                    var display = _.findWhere(getCellFailures(d), 'SYSTEM');
                    return display ? 'block' : 'none';
                })
                .style('stroke', function (d) {
                    return d.toString() === 'JobType' ? '#fff' : 'none';
                });

            containerGroup.selectAll('.cell-failure-data')
                .data($scope.gridData, function (d) { return d.coords; })
                .transition()
                .duration(750)
                .attr('x', function (d) {
                    var failures = getCellFailures(d);
                    if (failures && failures.length > 0) {
                        if (_.findWhere(failures, 'SYSTEM')) {
                            return $scope.cellWidth / failures.length;
                        }
                    }
                    return 0;
                })
                .attr('y', 0)
                .attr('width', function (d) {
                    var failures = getCellFailures(d);
                    if (failures && failures.length > 0) {
                        return $scope.cellWidth / failures.length;
                    }
                    return $scope.cellWidth;
                })
                .style('fill', function (d) {
                    var failures = getCellFailures(d);
                    if (_.findWhere(failures, 'DATA')) {
                        return '#FF7F0E';
                    }
                    return 'none';
                })
                .style('display', function (d) {
                    var display = _.findWhere(getCellFailures(d), 'DATA');
                    return display ? 'block' : 'none';
                })
                .style('stroke', function (d) {
                    return d.toString() === 'JobType' ? '#fff' : 'none';
                });

            containerGroup.selectAll('.cell-failure-algorithm')
                .data($scope.gridData, function (d) { return d.coords; })
                .transition()
                .duration(750)
                .attr('x', function (d) {
                    var failures = getCellFailures(d);
                    if (failures && failures.length > 0) {
                        if (_.findWhere(failures, 'DATA') && _.findWhere(failures, 'SYSTEM')) {
                            return ($scope.cellWidth / failures.length) + ($scope.cellWidth / failures.length);
                        } else if (_.findWhere(failures, 'DATA') && !_.findWhere(failures, 'SYSTEM')) {
                            return $scope.cellWidth / failures.length;
                        } else if (_.findWhere(failures, 'SYSTEM') && !_.findWhere(failures, 'DATA')) {
                            return $scope.cellWidth / failures.length;
                        }
                    }
                    return 0;
                })
                .attr('y', 0)
                .attr('width', function (d) {
                    var failures = getCellFailures(d);
                    if (failures && failures.length > 0) {
                        return Math.floor($scope.cellWidth / failures.length);
                    }
                    return $scope.cellWidth;
                })
                .style('fill', function (d) {
                    var failures = getCellFailures(d);
                    if (_.findWhere(failures, 'ALGORITHM')) {
                        return '#2CA02C';
                    }
                    return 'none';
                })
                .style('display', function (d) {
                    var display = _.findWhere(getCellFailures(d), 'ALGORITHM');
                    return display ? 'block' : 'none';
                })
                .style('stroke', function (d) {
                    return d.toString() === 'JobType' ? '#fff' : 'none';
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

            cellGroup.append('rect')
                .attr('class', 'cell-failure-system')
                .attr('width', $scope.cellWidth - 2)
                .attr('height', $scope.cellHeight / 7)
                .attr('x', 0)
                .attr('y', 0)
                .style('fill', 'none');

            cellGroup.append('rect')
                .attr('class', 'cell-failure-data')
                .attr('width', $scope.cellWidth - 2)
                .attr('height', $scope.cellHeight / 7)
                .attr('x', 0)
                .attr('y', 0)
                .style('fill', 'none');

            cellGroup.append('rect')
                .attr('class', 'cell-failure-algorithm')
                .attr('width', $scope.cellWidth - 2)
                .attr('height', $scope.cellHeight / 7)
                .attr('x', 0)
                .attr('y', 0)
                .style('fill', 'none');

            cellGroup.append('text')
                .attr('class', 'cell-text')
                .html(function (d) {
                    return getCellText(d);
                })
                .attr('text-anchor', 'middle')
                .attr('x', $scope.cellWidth / 2)
                .attr('y', ($scope.cellHeight / 2) + 8)
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
                .attr('text-anchor', 'start')
                .attr('x', 2)
                .attr('y', $scope.cellHeight - 4);

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
                            var modalInstance = $uibModal.open({
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
