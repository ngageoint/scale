(function () {
    'use strict';
    
    angular.module('scaleApp').controller('jobExecutionLogController', function ($scope, $location, $element, $timeout, jobExecutionService, scaleConfig) {
        var vm = this;
        
        var initialize = function () {
            vm.forceScroll = true;
            vm.jobLogError = null;

            $scope.$watch('execution', function () {
                if ($scope.execution) {
                    vm.status = $scope.execution.status.toLowerCase();
                    console.log($scope.execution);
                    jobExecutionService.getLog($scope.execution.id).then(null, null, function (result) {
                        // get difference of max scroll length and current scroll length.var  = result.data;
                        if (result) {
                            var div = $($element[0]).find('.bash');
                            vm.scrollDiff = (div.scrollTop() + div.prop('offsetHeight')) - div.prop('scrollHeight');
                            if (vm.scrollDiff >= 0) {
                                vm.forceScroll = true;
                            }
                            vm.execLog = result;
                        } else {
                            if (result.statusText && result.statusText !== '') {
                                vm.jobLogErrorStatus = result.statusText;
                            }
                            $scope.jobLogError = 'Unable to retrieve job logs.';
                        }
                    });
                }
            });
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
