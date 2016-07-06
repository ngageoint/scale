(function () {
    'use strict';

    angular.module('scaleApp').controller('ingestRecordsController', function ($scope, $location, scaleConfig, scaleService, stateService, feedService, navService, subnavService, gridFactory) {
        subnavService.setCurrentPath('feed/ingests');

        var self = this;

        $scope.ingestsParams = stateService.getIngestsParams();

        $scope.stateService = stateService;
        $scope.loading = true;
        $scope.subnavLinks = scaleConfig.subnavLinks.feed;
        $scope.ingestStatusValues = scaleConfig.ingestStatus;
        $scope.selectedIngestStatus = $scope.ingestsParams.status || $scope.ingestStatusValues[0];
        $scope.gridStyle = '';
        $scope.lastModifiedStart = moment.utc($scope.ingestsParams.started).toDate();
        $scope.lastModifiedStartPopup = {
            opened: false
        };
        $scope.openLastModifiedStartPopup = function ($event) {
            $event.stopPropagation();
            $scope.lastModifiedStartPopup.opened = true;
        };
        $scope.lastModifiedStop = moment.utc($scope.ingestsParams.ended).toDate();
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
        $scope.ingestData = [];
        $scope.searchText = '';
        $scope.gridOptions = gridFactory.defaultGridOptions();
        $scope.gridOptions.paginationCurrentPage = $scope.ingestsParams.page || 1;
        $scope.gridOptions.paginationPageSize = $scope.ingestsParams.page_size || $scope.gridOptions.paginationPageSize;
        $scope.gridOptions.data = [];

        $scope.refreshData = function () {
            //$scope.gridOptions.data = $filter('filter')($scope.ingestData, $scope.searchText, undefined);
            $scope.gridOptions.data = _.filter($scope.ingestData, function (d) {
                return d.file_name.toLowerCase().includes($scope.searchText.toLowerCase());
            });
        };

        var filteredByStatus = $scope.ingestsParams.status ? true : false,
            filteredByOrder = $scope.ingestsParams.order ? true : false;

        self.colDefs = [
            {
                field: 'file_name',
                displayName: 'Filename',
                enableFiltering: false
            },
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
                filterHeaderTemplate: '<div class="ui-grid-filter-container"><select class="form-control input-sm" ng-model="grid.appScope.selectedIngestStatus" ng-options="status.toUpperCase() for status in grid.appScope.ingestStatusValues"></select></div>'
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

        self.getIngests = function () {
            $scope.loading = true;
            feedService.getIngestsOnce($scope.ingestsParams).then(function (data) {
                $scope.ingestData = data.results;
                $scope.gridOptions.totalItems = data.count;
                $scope.gridOptions.data = data.results;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        self.filterResults = function () {
            stateService.setIngestsParams($scope.ingestsParams);
            $scope.loading = true;
            self.getIngests();
        };

        self.updateColDefs = function () {
            $scope.gridOptions.columnDefs = gridFactory.applySortConfig(self.colDefs, $scope.ingestsParams);
        };

        self.updateIngestOrder = function (sortArr) {
            $scope.ingestsParams.order = sortArr.length > 0 ? sortArr : null;
            filteredByOrder = sortArr.length > 0;
            self.filterResults();
        };

        self.updateIngestStatus = function (value) {
            if (value != $scope.ingestsParams.status) {
                $scope.ingestsParams.page = 1;
            }
            $scope.ingestsParams.status = value === 'VIEW ALL' ? null : value;
            $scope.ingestsParams.page_size = $scope.gridOptions.paginationPageSize;
            if (!$scope.loading) {
                self.filterResults();
            }
        };

        $scope.gridOptions.onRegisterApi = function (gridApi) {
            //set gridApi on scope
            $scope.gridApi = gridApi;
            $scope.gridApi.selection.on.rowSelectionChanged($scope, function (row) {
                $scope.$apply(function () {
                    $location.search({});
                    $location.path('/feed/ingests/' + row.entity.id);
                });
            });
            $scope.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                $scope.ingestsParams.page = currentPage;
                $scope.ingestsParams.page_size = pageSize;
                self.filterResults();
            });
            $scope.gridApi.core.on.sortChanged($scope, function (grid, sortColumns) {
                _.forEach($scope.gridApi.grid.columns, function (col) {
                    col.colDef.sort = col.sort;
                });
                stateService.setIngestsColDefs($scope.gridApi.grid.options.columnDefs);
                var sortArr = [];
                _.forEach(sortColumns, function (col) {
                    sortArr.push(col.sort.direction === 'desc' ? '-' + col.field : col.field);
                });
                self.updateIngestOrder(sortArr);
            });
        };

        self.initialize = function () {
            $scope.gridStyle = scaleService.setGridHeight(scaleConfig.headerOffset + scaleConfig.dateFilterOffset + scaleConfig.paginationOffset);
            stateService.setIngestsParams($scope.ingestsParams);
            self.updateColDefs();
            self.getIngests();
            navService.updateLocation('feed');
        };

        self.initialize();

        $scope.$watch('selectedIngestStatus', function (value) {
            if ($scope.loading) {
                if (filteredByStatus) {
                    self.updateIngestStatus(value);
                }
            } else {
                filteredByStatus = value !== 'VIEW ALL';
                self.updateIngestStatus(value);
            }
        });

        $scope.$watch('lastModifiedStart', function (value) {
            if (!$scope.loading) {
                $scope.ingestsParams.started = value.toISOString();
                self.filterResults();
            }
        });

        $scope.$watch('lastModifiedStop', function (value) {
            if (!$scope.loading) {
                $scope.ingestsParams.ended = value.toISOString();
                self.filterResults();
            }
        });

        $scope.$watchCollection('stateService.getIngestsColDefs()', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            self.colDefs = newValue;
            self.updateColDefs();
        });

        $scope.$watchCollection('stateService.getIngestsParams()', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            $scope.ingestsParams = newValue;
            self.updateColDefs();
        });
    });
})();