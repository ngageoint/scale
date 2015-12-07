(function () {
    'use strict';

    angular.module('scaleApp').factory('gridFactory', function (uiGridConstants) {

        var getSortConfig = function(orderParam){
            if(orderParam){
                var sortField = orderParam
                var sortDirection = 'asc';
                if(_.startsWith(orderParam, '-')){
                    sortDirection = 'desc';
                    sortField = sortField[0].length === 1 ? sortField.substring(1) : sortField[0].substring(1);
                }
                return {
                    direction: sortDirection,
                    field: sortField
                };
            }
            return {};
        };

        return {
            defaultGridOptions: function () {
                return {
                    enableRowSelection: true,
                    enableRowHeaderSelection: false,
                    enableHorizontalScrollbar: uiGridConstants.scrollbars.NEVER,
                    multiSelect: false,
                    enableFiltering: true,
                    useExternalSorting: true,
                    useExternalFiltering: true,
                    enableSorting: true,
                    minRowsToShow: 17,
                    paginationPageSizes: [25, 50, 75, 100],
                    paginationPageSize: 25,
                    useExternalPagination: true
                }
            },
            applySortConfig: function(columnDefs, gridParams){
                var sortConfig = getSortConfig(gridParams.order);
                if(sortConfig.field){
                    var colDef = _.find(columnDefs, {field: sortConfig.field});
                    if(colDef){
                        colDef.sort = {
                            direction: sortConfig.direction,
                            priority: 1
                        }
                    }
                }
                return columnDefs;
            }
        }
    });
})();
