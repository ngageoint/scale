(function () {
    'use strict';

    angular.module('scaleApp').controller('ingestRecordsController', function ($scope, scaleConfig, scaleService, stateService, feedService, navService, subnavService, gridFactory) {
        subnavService.setCurrentPath('feed/ingests');

        var self = this;

        self.ingestsParams = stateService.getIngestsParams();

        $scope.stateService = stateService;
        $scope.loading = true;
        $scope.subnavLinks = scaleConfig.subnavLinks.feed;
        $scope.ingestStatusValues = scaleConfig.ingestStatus;
        $scope.selectedIngestStatus = self.ingestsParams.status || $scope.ingestStatusValues[0];
        $scope.gridStyle = '';
        $scope.lastModifiedStart = moment.utc(self.ingestsParams.started).toDate();
        $scope.lastModifiedStartPopup = {
            opened: false
        };
        $scope.openLastModifiedStartPopup = function ($event) {
            $event.stopPropagation();
            $scope.lastModifiedStartPopup.opened = true;
        };
        $scope.lastModifiedStop = moment.utc(self.ingestsParams.ended).toDate();
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
        $scope.gridOptions = gridFactory.defaultGridOptions();
        $scope.gridOptions.paginationCurrentPage = self.ingestsParams.page || 1;
        $scope.gridOptions.paginationPageSize = self.ingestsParams.page_size || $scope.gridOptions.paginationPageSize;
        $scope.gridOptions.data = [];

        var filteredByStatus = self.ingestsParams.status ? true : false,
            filteredByOrder = self.ingestsParams.order ? true : false;

        self.colDefs = [
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
                filterHeaderTemplate: '<div class="ui-grid-filter-container"><select class="form-control input-sm" ng-model="grid.appScope.selectedIngestStatus"><option ng-selected="{{ grid.appScope.ingestStatusValues[$index] == grid.appScope.selectedIngestStatus }}" value="{{ grid.appScope.ingestStatusValues[$index] }}" ng-repeat="status in grid.appScope.ingestStatusValues track by $index">{{ status.toUpperCase() }}</option></select></div>'
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

        self.updateGridHeight = function () {
            angular.element(document).ready(function () {
                // set container heights equal to available page height
                var viewport = scaleService.getViewportSize(),
                    offset = $scope.gridOptions.totalItems > $scope.gridOptions.paginationPageSize ? scaleConfig.headerOffset + scaleConfig.dateFilterOffset + scaleConfig.paginationOffset : scaleConfig.headerOffset + scaleConfig.dateFilterOffset,
                    gridMaxHeight = viewport.height - offset;

                $scope.gridStyle = 'height: ' + gridMaxHeight + 'px; max-height: ' + gridMaxHeight + 'px; overflow-y: auto;';
            });
        };

        self.getIngests = function () {
            $scope.loading = true;
            feedService.getIngestsOnce(self.ingestsParams).then(function (data) {
                $scope.gridOptions.totalItems = data.count;
                $scope.gridOptions.data = data.results;
                self.updateGridHeight();
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        self.filterResults = function () {
            stateService.setIngestsParams(self.ingestsParams);
            $scope.loading = true;
            self.getIngests();
        };

        self.updateColDefs = function () {
            $scope.gridOptions.columnDefs = gridFactory.applySortConfig(self.colDefs, self.ingestsParams);
        };

        self.updateIngestOrder = function (sortArr) {
            self.ingestsParams.order = sortArr.length > 0 ? sortArr : null;
            filteredByOrder = sortArr.length > 0;
            self.filterResults();
        };

        self.updateIngestStatus = function (value) {
            if (value != self.ingestsParams.status) {
                self.ingestsParams.page = 1;
            }
            self.ingestsParams.status = value === 'VIEW ALL' ? null : value;
            self.ingestsParams.page_size = $scope.gridOptions.paginationPageSize;
            if (!$scope.loading) {
                self.filterResults();
            }
        };

        $scope.gridOptions.onRegisterApi = function (gridApi) {
            //set gridApi on scope
            $scope.gridApi = gridApi;
            $scope.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                self.ingestsParams.page = currentPage;
                self.ingestsParams.page_size = pageSize;
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
            stateService.setIngestsParams(self.ingestsParams);
            self.updateColDefs();
            self.getIngests();
            navService.updateLocation('feed');
            self.updateGridHeight();
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
                self.ingestsParams.started = value.toISOString();
                self.filterResults();
            }
        });

        $scope.$watch('lastModifiedStop', function (value) {
            if (!$scope.loading) {
                self.ingestsParams.ended = value.toISOString();
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
            self.ingestsParams = newValue;
            self.updateColDefs();
        });
    });
})();