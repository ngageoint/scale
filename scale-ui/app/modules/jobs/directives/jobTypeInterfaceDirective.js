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
