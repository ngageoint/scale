(function () {
    'use strict';
    
    angular.module('scaleApp').controller('jobExecutionLogController', function ($scope, $location, $element, $timeout, scaleConfig, jobExecutionService, stateService, poller) {
        var vm = this,
                 latestScaleOrderNum = 0;
        
        var initialize = function () {
            vm.forceScroll = true;
            vm.jobLogError = null;
            vm.execLog = [];
            stateService.setLogArgs([]);

            // debounce this watch operation to prevent duplicate calls
            // set the timer for 100ms less than the job exe log poll interval
            $scope.$watch('execution', _.debounce(function () {
                if ($scope.execution) {
                    vm.status = $scope.execution.status.toLowerCase();
                    console.log($scope.execution);
                    jobExecutionService.getLog($scope.execution.id).then(null, null, function (result) {
                        if (result.$resolved) {
                            if (result.$status !== 204) {
                                // Content was returned, so add it to the log array
                                // get difference of max scroll length and current scroll length.var  = result.data;
                                var div = $($element[0]).find('.bash');
                                vm.scrollDiff = (div.scrollTop() + div.prop('offsetHeight')) - div.prop('scrollHeight');
                                if (vm.scrollDiff >= 0) {
                                    vm.forceScroll = true;
                                }
                                // concat new content and sort log array by timestamp and then by order num
                                vm.execLog = _.sortBy(vm.execLog.concat(result.hits.hits), ['_source.@timestamp', '_source.scale_order_num']);
                                if (vm.execLog && vm.execLog.length > 0) {
                                    var lastLog = _.last(vm.execLog)._source;
                                    if (lastLog.scale_order_num !== latestScaleOrderNum) {
                                        // new entries, so leave them on the array and report the new timestamp
                                        console.log('New entries - ' + lastLog.scale_order_num + ' : ' + latestScaleOrderNum);
                                        latestScaleOrderNum = lastLog.scale_order_num;
                                        stateService.setLogArgs([
                                            {
                                                // started: moment.utc(lastLog['@timestamp']).subtract(1, 's').toISOString()
                                                started: lastLog['@timestamp']
                                            }
                                        ]);
                                    } else {
                                        // duplicate entries, so remove them from the array
                                        console.log('Duplicate entries');
                                        vm.execLog = _.take(vm.execLog, vm.execLog.length - result.hits.hits.length);
                                    }
                                }
                            }
                        } else {
                            if (result.$statusText && result.$statusText !== '') {
                                vm.jobLogErrorStatus = result.$statusText;
                            }
                            $scope.jobLogError = 'Unable to retrieve job logs.';
                        }
                    });
                    $scope.$on('modal.closing', function () {
                        poller.stopAll();
                    });
                }
            }, scaleConfig.pollIntervals.jobExecutionLog - 100));
            $scope.$watch('vm.execLog', function () {
                if (vm.execLog) {
                    if (vm.forceScroll || vm.scrollDiff >= 0) {
                        $timeout(function () {
                            vm.forceScroll = false;
                            var scrlHeight = $($element[0]).find('.bash').prop('scrollHeight');
                            $($element[0]).find('.bash').scrollTop(scrlHeight);
                        }, 50);
                    }
                }
            });
        };

        vm.scrollitem = function (item) {
            console.log(item);
        };

        vm.stdoutChanged = function () {
            console.log('stdout changed.');
        };

        initialize();

    }).directive('jobExecutionLog', function () {
        return {
            controller: 'jobExecutionLogController',
            controllerAs: 'vm',
            templateUrl: 'modules/jobs/directives/jobExecutionLogTemplate.html',
            restrict: 'E',
            scope: {
                execution: '='
            }
        };
    });
})();
