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
