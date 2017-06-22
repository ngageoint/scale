(function () {
    'use strict';

    angular.module('scaleApp').controller('sourceFilesController', function ($scope, $location, $timeout, scaleConfig, scaleService, stateService, dataService, navService, subnavService, SourceFile, gridFactory) {
        subnavService.setCurrentPath('data/source');
        var vm = this;
        vm.sourceFilesParams = stateService.getSourceFilesParams();
        vm.stateService = stateService;
        vm.loading = true;
        vm.subnavLinks = scaleConfig.subnavLinks.data;
        vm.startDate = moment.utc(vm.sourceFilesParams.started).toDate();
        vm.startDatePopup = {
            opened: false
        };
        vm.openStartDatePopup = function ($event) {
            $event.stopPropagation();
            vm.startDatePopup.opened = true;
        };
        vm.stopDate = moment.utc(vm.sourceFilesParams.ended).toDate();
        vm.stopDatePopup = {
            opened: false
        };
        vm.openStopDatePopup = function ($event) {
            $event.stopPropagation();
            vm.stopDatePopup.opened = true;
        };
        vm.dateFieldOptions = _.clone(scaleConfig.sourceFileDateFields);
        vm.selectedDateField = vm.sourceFilesParams.time_field;
        vm.dateModelOptions = {
            timezone: '+000'
        };
        vm.sourceFileData = [];
        vm.searchText = vm.sourceFilesParams.file_name || '';
        vm.gridOptions = gridFactory.defaultGridOptions();
        vm.gridOptions.data = [];

        $timeout(function () {
            vm.gridOptions.paginationCurrentPage = vm.sourceFilesParams.page || 1;
            vm.gridOptions.paginationPageSize = vm.sourceFilesParams.page_size || vm.gridOptions.paginationPageSize;
        });

        vm.refreshData = function () {
            var filteredData = _.filter(vm.sourceFileData, function (d) {
                return d.file_name.toLowerCase().includes(vm.searchText.toLowerCase());
            });
            vm.gridOptions.data = filteredData.length > 0 ? filteredData : vm.gridOptions.data;
        };

        var filteredByOrder = vm.sourceFilesParams.order ? true : false;

        vm.colDefs = [
            {
                field: 'file_name',
                displayName: 'File Name',
                //filterHeaderTemplate: '<div class="ui-grid-filter-container"><input ng-model="grid.appScope.vm.searchText" ng-change="grid.appScope.vm.refreshData()" class="form-control" placeholder="Search"></div>'
                enableFiltering: false
            },
            {
                field: 'file_size',
                displayName: 'File Size',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.file_size_formatted }}</div>'
            },
            {
                field: 'data_started',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.data_started_formatted }}</div>'
            },
            {
                field: 'data_ended',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.data_ended_formatted }}</div>'
            },
            {
                field: 'countries',
                enableFiltering: false
            },
            {
                field: 'last_modified',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.last_modified_formatted }}</div>'
            }
        ];

        vm.getSourceFiles = function () {
            vm.loading = true;
            dataService.getSources(vm.sourceFilesParams).then(function (data) {
                vm.sourceFileData = SourceFile.transformer(data.results);
                vm.gridOptions.minRowsToShow = vm.sourceFileData.length;
                vm.gridOptions.virtualizationThreshold = vm.sourceFileData.length;
                vm.gridOptions.totalItems = data.count;
                vm.gridOptions.data = vm.sourceFileData;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                vm.loading = false;
            });
        };

        vm.filterResults = function () {
            stateService.setSourceFilesParams(vm.sourceFilesParams);
            vm.getSourceFiles();
        };

        vm.updateColDefs = function () {
            vm.gridOptions.columnDefs = gridFactory.applySortConfig(vm.colDefs, vm.sourceFilesParams);
        };

        vm.updateSourceFilesOrder = function (sortArr) {
            vm.sourceFilesParams.order = sortArr.length > 0 ? sortArr : null;
            filteredByOrder = sortArr.length > 0;
            vm.filterResults();
        };

        vm.gridOptions.onRegisterApi = function (gridApi) {
            //set gridApi on scope
            vm.gridApi = gridApi;
            vm.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                vm.sourceFilesParams.page = currentPage;
                vm.sourceFilesParams.page_size = pageSize;
                vm.filterResults();
            });
            vm.gridApi.selection.on.rowSelectionChanged($scope, function (row) {
                $location.path('/data/source/file/' + row.entity.id).search('');
            });
            vm.gridApi.core.on.sortChanged($scope, function (grid, sortColumns) {
                _.forEach(vm.gridApi.grid.columns, function (col) {
                    col.colDef.sort = col.sort;
                });
                stateService.setSourceFilesColDefs(vm.gridApi.grid.options.columnDefs);
                var sortArr = [];
                _.forEach(sortColumns, function (col) {
                    sortArr.push(col.sort.direction === 'desc' ? '-' + col.field : col.field);
                });
                vm.updateSourceFilesOrder(sortArr);
            });
        };

        vm.filterByFilename = function (keyEvent) {
            if (!keyEvent || (keyEvent && keyEvent.which === 13)) {
                vm.sourceFilesParams.file_name = vm.searchText;
                vm.filterResults();
            }
        };

        vm.initialize = function () {
            stateService.setSourceFilesParams(vm.sourceFilesParams);
            vm.updateColDefs();
            vm.getSourceFiles();
            navService.updateLocation('data');
        };

        vm.initialize();

        $scope.$watch('vm.startDate', function (value) {
            if (!vm.loading) {
                vm.sourceFilesParams.started = value.toISOString();
                vm.filterResults();
            }
        });

        $scope.$watch('vm.stopDate', function (value) {
            if (!vm.loading) {
                vm.sourceFilesParams.ended = value.toISOString();
                vm.filterResults();
            }
        });

        $scope.$watch('vm.selectedDateField', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            vm.sourceFilesParams.time_field = newValue;
            vm.filterResults();
        });

        $scope.$watchCollection('vm.stateService.getSourceFilesColDefs()', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            vm.colDefs = newValue;
            vm.updateColDefs();
        });

        $scope.$watchCollection('vm.stateService.getSourceFilesParams()', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            vm.sourceFilesParams = newValue;
            vm.updateColDefs();
        });
    });
})();
