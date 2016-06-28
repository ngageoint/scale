(function () {
    'use strict';

    angular.module('scaleApp').factory('gridFactory', function (uiGridConstants) {

        var getSortConfig = function (orderParam) {
            var sortArr = [];

            if (orderParam) {
                _.forEach(orderParam, function (param) {
                    var sortField = param;
                    var sortDirection = 'asc';
                    if (_.startsWith(param, '-')) {
                        sortDirection = 'desc';
                    }
                    sortArr.push({
                        direction: sortDirection,
                        field: sortField
                    })
                });
            }

            return sortArr;
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
                    useExternalPagination: true,
                    enablePaginationControls: false,
                    paginationCurrentPage: 1
                }
            },
            applySortConfig: function (columnDefs, gridParams) {
                var sortConfig = getSortConfig(gridParams.order);
                _.forEach(sortConfig, function (config, idx) {
                    var field = _.startsWith(config.field, '-') ? config.field.substring(1) : config.field,
                        colDef = _.find(columnDefs, {field: field});

                    if (colDef) {
                        colDef.sort = {
                            direction: config.direction,
                            priority: idx
                        };
                    }
                });
                return columnDefs;
            }
        }
    });
})();
