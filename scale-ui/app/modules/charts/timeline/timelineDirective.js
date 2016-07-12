(function () {
    'use strict';

    angular.module('scaleApp').controller('aisTimelineDirectiveController', function ($scope, $element, scaleConfig) {
        var vm = this,
            gantt = null,
            taskNames = [];

        $element[0].onresize = function () {
            console.log('element resize');
        };

        var initialize = function () {
            $scope.$watch('tasks', function (value) {
                drawTimeline();
            });
        };

        var drawTimeline = function () {
            if ($scope.tasks && $scope.tasks.length > 0) {
                $scope.tasks.sort(function (a, b) {
                    return a[$scope.ended] - b[$scope.ended];
                });

                taskNames = _($scope.tasks).pluck('taskName').uniq().value();
                var height = taskNames.length * 30 + 20;

                var width = $element[0].clientWidth;
                if (!width || width === 0) { width = 600; }


                $scope.tasks.sort(function (a, b) {
                    return a[$scope.started] - b[$scope.started];
                });
                var minDate = $scope.tasks[0][$scope.started];
                var maxDate = $scope.tasks[$scope.tasks.length - 1][$scope.ended];
                var daysDiff = moment.utc(maxDate).diff(moment.utc(minDate),'days');
                var format = '%H:%M:%S.%m';
                if (daysDiff > 0) {
                    format = "%m/%d/%y %H:%M";
                }

                gantt = d3.gantt().renderTo("#ais-timeline").taskTypes(taskNames).taskStatus(scaleConfig.taskStatusStyles).tickFormat(format).begin($scope.started).ended($scope.ended).height(height).width(width);

                gantt.timeDomainMode("fit");

                gantt($scope.tasks);

            }
        };

        vm.formatDate = function (date) {
            if (date) {
                return moment.utc(date).toISOString();
            }
            else {
                return date;
            }
        };
        initialize();

    }).directive('aisTimeline', function () {
        return {
            controller: 'aisTimelineDirectiveController',
            controllerAs: 'vm',
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
