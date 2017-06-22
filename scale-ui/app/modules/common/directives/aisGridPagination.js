(function () {
    'use strict';

    angular.module('scaleApp').directive('aisGridPagination', function () {
        return {
            templateUrl: 'modules/common/directives/aisGridPaginationTemplate.html',
            restrict: 'E',
            scope: {
                gridOptions: '='
            }
        };
    });
})();
