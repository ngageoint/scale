(function () {
    'use strict';

    angular.module('scaleApp').controller('aisDataFeedController', function ($scope, scaleConfig, loadService, scaleService) {
        var days = [],
            hours = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23],
            values = {};
        
        var processNewFeed = function () {
            days = [];
            var day = '';
            if ($scope.feed) {
                _.forEach($scope.feed.values, function (val) {
                    var valday = moment.utc(val.time).format(scaleConfig.dateFormats.day);
                    var valhour = moment.utc(val.time).hour();
                    var id = valday + '_' + valhour;
                    values[id] = val;
                    if (valday !== day) {
                        day = valday;
                        days.push(valday);
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
            for(day in days) {
                table_html += '<td class="day-label" title="' + days[day] + '"><div class="day-of-week">' + scaleService.getDayString(moment(days[day]).day()) + '</div>' + moment(days[day]).format('MM/DD') + '</td>';
            }
            table_html += '</tr>';
            for(var hour in hours) {
                hour = 23-hour;
                table_html += '<tr>';
                table_html += '<th title="' + hours[hour] + ':00">' + hours[hour] + '</th>';

                for(var day in days) {
                    var key =  days[day] + '_' + hours[hour];
                    var files = values[key].files;
                    var size = values[key].size;
                    var cls = 'good';
                    if (days[day] === currDay) {
                        if (hours[hour] === currHour) {
                            cls = 'current';
                        }
                        else if (hours[hour] > currHour) {
                            cls = 'future';
                        }
                    }
                    if (files === 0 && size === 0 && cls !== 'current' && cls !== 'future') {
                        cls = 'unknown';
                    }
                    table_html += '<td id="' + key + '" title="' + days[day] + ' ' + hours[hour] + ':00">';
                    if (cls === 'future') {
                        table_html += '<span class="' + cls + '" id="span_' + days[day] + '_' + hours[hour] + '" style="display: block;">&nbsp;</span></td>';
                    }
                    else{
                        table_html += '<span class="' + cls + '" id="span_' + days[day] + '_' + hours[hour] + '" style="display: block;">' + scaleService.calculateFileSizeFromBytes(size,1) + ' / ' + files + '</span></td>';
                    }

                }
                table_html += '</tr>';
            }
            table_html += '</table></div>';
            $('#history').html(table_html);
        };

        var initialize = function () {

            $scope.$watch('feed', function (value) {
                if ($scope.feed) {
                    processNewFeed();
                }
            });
        };

        initialize();
    }).directive('aisDataFeed', function () {
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
