(function () {
    'use strict';

    angular.module('scaleApp').controller('ingestRecordsController', function($scope, $rootScope, $location, scaleConfig, scaleService, gridFactory, navService, subnavService, feedService) {
        $scope.subnavLinks = scaleConfig.subnavLinks.feed;

        var gridParams = {
            page: 1, page_size: 25, started: null, ended: null, order: '-transfer_started', status: null
        };

        // check for gridParams in query string, and update as necessary
        _.forEach(_.pairs(gridParams), function (param) {
            var value = _.at($location.search(), param[0]);
            if (value.length > 0) {
                gridParams[param[0]] = value.length > 1 ? value : value[0];
            }
        });

        var filteredByStatus = gridParams.status ? true : false;
        var filteredByOrder = gridParams.order ? true : false;
        $scope.lastModifiedStart = gridParams.started ? moment.utc(gridParams.started).toDate() : moment.utc().subtract(1, 'weeks').startOf('d').toDate();

        $scope.lastModifiedStartPopup = {
            opened: false
        };
        $scope.openLastModifiedStartPopup = function ($event) {
            $event.stopPropagation();
            $scope.lastModifiedStartPopup.opened = true;
        };
        $scope.lastModifiedStop = gridParams.ended ? moment.utc(gridParams.ended).toDate() : moment.utc().endOf('d').toDate();
        $scope.lastModifiedStopPopup = {
            opened: false
        };
        $scope.openLastModifiedStopPopup = function ($event) {
            $event.stopPropagation();
            $scope.lastModifiedStopPopup.opened = true;
        };
        $scope.dateModelOptions = {
            timezone: '+000'
        };

        $scope.statusValues = scaleConfig.ingestStatus;
        $scope.selectedStatus = gridParams.status || $scope.statusValues[0];
        $scope.$watch('selectedStatus', function (value) {
            if ($scope.loading) {
                if (filteredByStatus) {
                    updateStatus(value);
                }
            } else {
                filteredByStatus = value !== 'VIEW ALL';
                updateStatus(value);
            }
        });

        $scope.$watch('lastModifiedStart', function (value) {
            if (!$scope.loading) {
                gridParams.started = value.toISOString();
                $scope.filterResults();
            }
        });

        $scope.$watch('lastModifiedStop', function (value) {
            if (!$scope.loading) {
                console.log(value);
                gridParams.ended = value.toISOString();
                $scope.filterResults();
            }
        });


        var updateStatus = function (value) {
            if (value != gridParams.status) {
                gridParams.page = 1;
            }
            gridParams.status = value === 'VIEW ALL' ? null : value;
            gridParams.page_size = $scope.gridOptions.paginationPageSize;
            if (!$scope.loading) {
                $scope.filterResults();
            }
        };

        var defaultColumnDefs = [
            { field: 'file_name', displayName: 'File Name', enableFiltering: false },
            {
                field: 'file_size',
                displayName: 'File Size',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.file_size_formatted }}</div>'
            },
            {
                field: 'strike.id',
                displayName: 'Strike Process',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.strike.id }}</div>'
            },
            {
                field: 'status',
                filterHeaderTemplate: '<div class="ui-grid-filter-container"><select class="form-control input-sm" ng-model="grid.appScope.selectedStatus"><option ng-selected="{{ grid.appScope.statusValues[$index] == grid.appScope.selectedStatus }}" value="{{ grid.appScope.statusValues[$index] }}" ng-repeat="status in grid.appScope.statusValues track by $index">{{ status.toUpperCase() }}</option></select></div>'
            },
            {
                field: 'transfer_started',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.transfer_started_formatted }}</div>'
            },
            {
                field: 'transfer_ended',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.transfer_ended_formatted }}</div>'
            },
            {
                field: 'ingest_started',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.ingest_started_formatted }}</div>'
            },
            {
                field: 'ingest_ended',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.ingest_ended_formatted }}</div>'
            }
        ];

        $scope.gridOptions = gridFactory.defaultGridOptions();
        $scope.gridOptions.paginationCurrentPage = parseInt(gridParams.page || 1);
        $scope.gridOptions.paginationPageSize = parseInt(gridParams.page_size) || $scope.gridOptions.paginationPageSize;
        $scope.gridOptions.columnDefs = gridFactory.applySortConfig(defaultColumnDefs, gridParams);
        $scope.gridOptions.data = [];
        $scope.gridOptions.onRegisterApi = function (gridApi) {
                //set gridApi on scope
                $scope.gridApi = gridApi;
                // $scope.gridApi.selection.on.rowSelectionChanged($scope, function (row) {
                //     if ($scope.actionClicked) {
                //         $scope.actionClicked = false;
                //     } else {
                //         $scope.$apply(function(){
                //             $location.path('/feed/ingests/' + row.entity.id);
                //         });
                //     }
                //
                // });
                $scope.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                    gridParams.page = currentPage;
                    gridParams.page_size = pageSize;
                    console.log('gridApi.paginationChanged');
                    $scope.filterResults();
                });
                $scope.gridApi.core.on.sortChanged($scope, function (grid, sortColumns) {
                    $rootScope.colDefs = null;
                    _.forEach($scope.gridApi.grid.columns, function (col) {
                        col.colDef.sort = col.sort;
                    });
                    $rootScope.colDefs = $scope.gridApi.grid.options.columnDefs;
                    var sortArr = [];
                    _.forEach(sortColumns, function (col) {
                        sortArr.push(col.sort.direction === 'desc' ? '-' + col.field : col.field);
                    });
                    updateOrder(sortArr);
                });
            };

        $scope.filterResults = function () {
            _.forEach(_.pairs(gridParams), function (param) {
                $location.search(param[0], param[1]);
            });
            getIngests();
        };

        var updateOrder = function (sortArr) {
            gridParams.order = sortArr.length > 0 ? sortArr : null;
            filteredByOrder = sortArr.length > 0;
            $scope.filterResults();
        };

        var getIngests = function () {
            $scope.loading = true;
            feedService.getIngestsOnce(gridParams).then(function (data) {
                $scope.ingests = data.results;
                $scope.gridOptions.totalItems = data.count;
                $scope.gridOptions.data = $scope.ingests;
                $scope.loading = false;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                $scope.loading = false;
            });
        };


        var initialize = function () {
            navService.updateLocation('feed');
            subnavService.setCurrentPath('feed/ingests');
            if (!gridParams.started) {
                console.log('lastModifiedStart: ' + $scope.lastModifiedStart);
                gridParams.started = moment.utc($scope.lastModifiedStart).toISOString();
                $location.search('started', gridParams.started).replace();
            }
            if (!gridParams.ended) {
                gridParams.ended = moment.utc($scope.lastModifiedStop).toISOString();
                $location.search('ended', gridParams.ended).replace();
            }
            getIngests();
        };

        initialize();

        angular.element(document).ready(function () {
            // set container heights equal to available page height
            var viewport = scaleService.getViewportSize(),
                offset = scaleConfig.headerOffset + scaleConfig.footerOffset + scaleConfig.dateFilterOffset,
                gridMaxHeight = viewport.height - offset;

            $scope.gridStyle = 'height: ' + gridMaxHeight + 'px; max-height: ' + gridMaxHeight + 'px; overflow-y: auto;';
        });
    });
})();
