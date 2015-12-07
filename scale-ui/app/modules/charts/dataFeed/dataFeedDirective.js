(function () {
    'use strict';

    angular.module('scaleApp').controller('aisDataFeedController', function ($scope, scaleConfig, loadService, scaleService) {
        $scope.days = [];
        $scope.hours = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23];
        $scope.values = {};
        var processNewFeed = function(){
            var currentDay = moment.utc();
            $scope.days = [];
            var day = '';
            if($scope.feed){
                _.forEach($scope.feed.values, function(val){
                    var valday = moment.utc(val.time).format(scaleConfig.dateFormats.day);
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
