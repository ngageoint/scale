(function () {
    'use strict';

    angular.module('scaleApp').controller('scansController', function ($scope, $location, $timeout, scaleConfig, scaleService, stateService, scanService, Scan, navService, subnavService, gridFactory) {
        subnavService.setCurrentPath('feed/scans');

        var vm = this;

        vm.scansParams = stateService.getScansParams();
        vm.stateService = stateService;
        vm.loading = true;
        vm.subnavLinks = scaleConfig.subnavLinks.feed;
        vm.lastModifiedStart = moment.utc(vm.scansParams.started).toDate();
        vm.lastModifiedStartPopup = {
            opened: false
        };
        vm.openLastModifiedStartPopup = function ($event) {
            $event.stopPropagation();
            vm.lastModifiedStartPopup.opened = true;
        };
        vm.lastModifiedStop = moment.utc(vm.scansParams.ended).toDate();
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
        vm.scanData = [];
        vm.searchText = vm.scansParams.name || '';
        vm.gridOptions = gridFactory.defaultGridOptions();
        vm.gridOptions.data = [];
        vm.sortableOptions = {
            handle: '.sortable-handle'
        };

        $timeout(function () {
            vm.gridOptions.paginationCurrentPage = vm.scansParams.page || 1;
            vm.gridOptions.paginationPageSize = vm.scansParams.page_size || vm.gridOptions.paginationPageSize;
        });

        vm.refreshData = function () {
            var filteredData = _.filter(vm.scanData, function (d) {
                return d.name.toLowerCase().includes(vm.searchText.toLowerCase());
            });
            vm.gridOptions.data = filteredData.length > 0 ? filteredData : vm.gridOptions.data;
        };

        var filteredByOrder = vm.scansParams.order ? true : false;

        vm.colDefs = [
            {
                field: 'name',
                displayName: 'Name',
                //filterHeaderTemplate: '<div class="ui-grid-filter-container"><input ng-model="grid.appScope.vm.searchText" ng-change="grid.appScope.vm.refreshData()" class="form-control" placeholder="Search"></div>'
                enableFiltering: false
            },
            {
                field: 'file_count',
                displayName: 'File Count',
                enableFiltering: false
            },
            {
                field: 'job',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.job.job_type.title }}</div>'
            },
            {
                field: 'created',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.created_formatted }}</div>'
            },
            {
                field: 'last_modified',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.last_modified_formatted }}</div>'
            }
        ];

        vm.getScans = function () {
            vm.loading = true;
            scanService.getScans(vm.scansParams).then(function (data) {
                vm.scanData = Scan.transformer(data.results);
                vm.gridOptions.minRowsToShow = data.results.length;
                vm.gridOptions.virtualizationThreshold = data.results.length;
                vm.gridOptions.totalItems = data.count;
                vm.gridOptions.data = vm.scanData = Scan.transformer(data.results);;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                vm.loading = false;
            });
        };

        vm.filterResults = function () {
            stateService.setScansParams(vm.scansParams);
            vm.getScans();
        };

        vm.updateColDefs = function () {
            vm.gridOptions.columnDefs = gridFactory.applySortConfig(vm.colDefs, vm.scansParams);
        };

        vm.updateScanOrder = function (sortArr) {
            vm.scansParams.order = sortArr.length > 0 ? sortArr : null;
            filteredByOrder = sortArr.length > 0;
            vm.filterResults();
        };

        vm.gridOptions.onRegisterApi = function (gridApi) {
            //set gridApi on scope
            vm.gridApi = gridApi;
            vm.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                vm.scansParams.page = currentPage;
                vm.scansParams.page_size = pageSize;
                vm.filterResults();
            });
            vm.gridApi.selection.on.rowSelectionChanged($scope, function (row) {
                $location.path('/feed/scans/' + row.entity.id).search('');

            });
            vm.gridApi.core.on.sortChanged($scope, function (grid, sortColumns) {
                _.forEach(vm.gridApi.grid.columns, function (col) {
                    col.colDef.sort = col.sort;
                });
                stateService.setScansColDefs(vm.gridApi.grid.options.columnDefs);
                var sortArr = [];
                _.forEach(sortColumns, function (col) {
                    sortArr.push(col.sort.direction === 'desc' ? '-' + col.field : col.field);
                });
                vm.updateScanOrder(sortArr);
            });
        };

        vm.filterByName = function (keyEvent) {
            if (!keyEvent || (keyEvent && keyEvent.which === 13)) {
                vm.scansParams.name = vm.searchText;
                vm.filterResults();
            }
        };

        vm.initialize = function () {
            vm.getScans();
            stateService.setScansParams(vm.scansParams);
            vm.updateColDefs();
            navService.updateLocation('feed');
        };

        vm.initialize();

        $scope.$watch('vm.lastModifiedStart', function (value) {
            if (!vm.loading) {
                vm.scansParams.started = value.toISOString();
                vm.filterResults();
            }
        });

        $scope.$watch('vm.lastModifiedStop', function (value) {
            if (!vm.loading) {
                vm.scansParams.ended = value.toISOString();
                vm.filterResults();
            }
        });

        $scope.$watchCollection('vm.stateService.getScansColDefs()', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            vm.colDefs = newValue;
            vm.updateColDefs();
        });

        $scope.$watchCollection('vm.stateService.getScansParams()', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            vm.scansParams = newValue;
            vm.updateColDefs();
        });
    });
})();
