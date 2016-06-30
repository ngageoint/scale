(function () {
    'use strict';

    angular.module('scaleApp').controller('ingestRecordsController', function ($scope, scaleConfig, scaleService, stateService, feedService, navService, subnavService, gridFactory) {
        subnavService.setCurrentPath('feed/ingests');

        var vm = this;

        vm.ingestsParams = stateService.getIngestsParams();

        vm.stateService = stateService;
        vm.loading = true;
        vm.subnavLinks = scaleConfig.subnavLinks.feed;
        vm.ingestStatusValues = scaleConfig.ingestStatus;
        vm.selectedIngestStatus = vm.ingestsParams.status || vm.ingestStatusValues[0];
        vm.lastModifiedStart = moment.utc(vm.ingestsParams.started).toDate();
        vm.lastModifiedStartPopup = {
            opened: false
        };
        vm.openLastModifiedStartPopup = function ($event) {
            $event.stopPropagation();
            vm.lastModifiedStartPopup.opened = true;
        };
        vm.lastModifiedStop = moment.utc(vm.ingestsParams.ended).toDate();
        vm.lastModifiedStopPopup = {
            opened: false
        };
        vm.openLastModifiedStopPopup = function ($event) {
            $event.stopPropagation();
            vm.lastModifiedStopPopup.opened = true;
        };
        vm.dateModelOptions = {
            timezone: '+000'
        };
        vm.ingestData = [];
        vm.searchText = '';
        vm.gridOptions = gridFactory.defaultGridOptions();
        vm.gridOptions.paginationCurrentPage = vm.ingestsParams.page || 1;
        vm.gridOptions.paginationPageSize = vm.ingestsParams.page_size || vm.gridOptions.paginationPageSize;
        vm.gridOptions.data = [];

        vm.refreshData = function () {
            var filteredData = _.filter(vm.ingestData, function (d) {
                return d.file_name.toLowerCase().includes(vm.searchText.toLowerCase());
            });
            vm.gridOptions.data = filteredData.length > 0 ? filteredData : vm.gridOptions.data;
        };

        var filteredByStatus = vm.ingestsParams.status ? true : false,
            filteredByOrder = vm.ingestsParams.order ? true : false;

        vm.colDefs = [
            {
                field: 'file_name',
                displayName: 'File Name',
                filterHeaderTemplate: '<div class="ui-grid-filter-container"><input ng-model="grid.appScope.vm.searchText" ng-change="grid.appScope.vm.refreshData()" class="form-control" placeholder="Search"></div>'
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
                filterHeaderTemplate: '<div class="ui-grid-filter-container"><select class="form-control input-sm" ng-model="grid.appScope.vm.selectedIngestStatus" ng-options="status.toUpperCase() for status in grid.appScope.vm.ingestStatusValues"></select></div>'
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

        vm.getIngests = function () {
            vm.loading = true;
            feedService.getIngestsOnce(vm.ingestsParams).then(function (data) {
                vm.ingestData = data.results;
                vm.gridOptions.minRowsToShow = data.results.length;
                vm.gridOptions.virtualizationThreshold = data.results.length;
                vm.gridOptions.totalItems = data.count;
                vm.gridOptions.data = data.results;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                vm.loading = false;
            });
        };

        vm.filterResults = function () {
            stateService.setIngestsParams(vm.ingestsParams);
            vm.loading = true;
            vm.getIngests();
            $('.ui-grid-pager-panel').remove();
        };

        vm.updateColDefs = function () {
            vm.gridOptions.columnDefs = gridFactory.applySortConfig(vm.colDefs, vm.ingestsParams);
        };

        vm.updateIngestOrder = function (sortArr) {
            vm.ingestsParams.order = sortArr.length > 0 ? sortArr : null;
            filteredByOrder = sortArr.length > 0;
            vm.filterResults();
        };

        vm.updateIngestStatus = function (value) {
            if (value != vm.ingestsParams.status) {
                vm.ingestsParams.page = 1;
            }
            vm.ingestsParams.status = value === 'VIEW ALL' ? null : value;
            vm.ingestsParams.page_size = vm.gridOptions.paginationPageSize;
            if (!vm.loading) {
                vm.filterResults();
            }
        };

        vm.gridOptions.onRegisterApi = function (gridApi) {
            //set gridApi on scope
            vm.gridApi = gridApi;
            vm.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                vm.ingestsParams.page = currentPage;
                vm.ingestsParams.page_size = pageSize;
                vm.filterResults();
            });
            vm.gridApi.core.on.sortChanged($scope, function (grid, sortColumns) {
                _.forEach(vm.gridApi.grid.columns, function (col) {
                    col.colDef.sort = col.sort;
                });
                stateService.setIngestsColDefs(vm.gridApi.grid.options.columnDefs);
                var sortArr = [];
                _.forEach(sortColumns, function (col) {
                    sortArr.push(col.sort.direction === 'desc' ? '-' + col.field : col.field);
                });
                vm.updateIngestOrder(sortArr);
            });
            vm.gridApi.core.on.rowsRendered($scope, function () {
                if (gridApi.grid.renderContainers.body.visibleRowCache.length === 0) { return; }
                $('.ui-grid-pager-panel').remove();
            });
        };

        vm.initialize = function () {
            stateService.setIngestsParams(vm.ingestsParams);
            vm.updateColDefs();
            vm.getIngests();
            navService.updateLocation('feed');
        };

        vm.initialize();

        $scope.$watch('vm.selectedIngestStatus', function (value) {
            if (vm.loading) {
                if (filteredByStatus) {
                    vm.updateIngestStatus(value);
                }
            } else {
                filteredByStatus = value !== 'VIEW ALL';
                vm.updateIngestStatus(value);
            }
        });

        $scope.$watch('vm.lastModifiedStart', function (value) {
            if (!vm.loading) {
                vm.ingestsParams.started = value.toISOString();
                vm.filterResults();
            }
        });

        $scope.$watch('vm.lastModifiedStop', function (value) {
            if (!vm.loading) {
                vm.ingestsParams.ended = value.toISOString();
                vm.filterResults();
            }
        });

        $scope.$watchCollection('vm.stateService.getIngestsColDefs()', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            vm.colDefs = newValue;
            vm.updateColDefs();
        });

        $scope.$watchCollection('vm.stateService.getIngestsParams()', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            vm.ingestsParams = newValue;
            vm.updateColDefs();
        });
    });
})();