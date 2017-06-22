(function () {
    'use strict';

    angular.module('scaleApp').controller('sourceFileDetailsController', function($scope, $location, $routeParams, $timeout, stateService, navService, dataService, gridFactory, SourceFile, Product) {
        var ctrl = this,
            sourceFileId = parseInt($routeParams.id),
            qs = $location.search();

        $scope.jobsData = null;
        $scope.productsData = null;
        $scope.ingestsData = null;
        $scope.hasParentCtrl = true;

        ctrl.loading = true;
        ctrl.sourceFile = null;
        ctrl.activeTab = qs.tab || 'jobs';
        ctrl.sourceFileProductsParams = stateService.getSourceFileProductsParams();
        ctrl.startDate = moment.utc(ctrl.sourceFileProductsParams.started).toDate();
        ctrl.startDatePopup = {
            opened: false
        };
        ctrl.openStartDatePopup = function ($event) {
            $event.stopPropagation();
            ctrl.startDatePopup.opened = true;
        };
        ctrl.stopDate = moment.utc(ctrl.sourceFileProductsParams.ended).toDate();
        ctrl.stopDatePopup = {
            opened: false
        };
        ctrl.openStopDatePopup = function ($event) {
            $event.stopPropagation();
            ctrl.stopDatePopup.opened = true;
        };
        ctrl.dateModelOptions = {
            timezone: '+000'
        };
        ctrl.searchText = ctrl.sourceFileProductsParams.file_name || '';
        ctrl.gridOptions = gridFactory.defaultGridOptions();
        ctrl.gridOptions.data = [];

        $timeout(function () {
            ctrl.gridOptions.paginationCurrentPage = ctrl.sourceFileProductsParams.page || 1;
            ctrl.gridOptions.paginationPageSize = ctrl.sourceFileProductsParams.page_size || ctrl.gridOptions.paginationPageSize;
        });

        var getSourceJobs = function () {
            dataService.getSourceDescendants(ctrl.sourceFile.id, 'jobs', stateService.getJobsParams()).then(function (data) {
                $scope.jobsData = data;
            });
        };

        var getSourceProducts = function () {
            dataService.getSourceDescendants(ctrl.sourceFile.id, 'products', ctrl.sourceFileProductsParams).then(function (data) {
                $scope.productsData = data;
                ctrl.gridOptions.minRowsToShow = data.results.length;
                ctrl.gridOptions.virtualizationThreshold = data.results.length;
                ctrl.gridOptions.totalItems = data.count;
                ctrl.gridOptions.data = Product.transformer(data.results);
            });
        };

        var getSourceIngests = function () {
            dataService.getSourceDescendants(ctrl.sourceFile.id, 'ingests', stateService.getIngestsParams()).then(function (data) {
                $scope.ingestsData = data;
            });
        };

        var getSourceFileDetails = function () {
            dataService.getSourceDetails(sourceFileId).then(function (data) {
                ctrl.sourceFile = SourceFile.transformer(data);
                getSourceIngests();
                getSourceProducts();
                getSourceJobs();
            }).finally(function () {
                ctrl.loading = false;
            });
        };

        ctrl.refreshData = function () {
            var filteredData = _.filter($scope.productsData, function (d) {
                return d.file_name.toLowerCase().includes(ctrl.searchText.toLowerCase());
            });
            ctrl.gridOptions.data = filteredData.length > 0 ? filteredData : ctrl.gridOptions.data;
        };

        var filteredByOrder = ctrl.sourceFileProductsParams.order ? true : false;

        ctrl.colDefs = [
            {
                field: 'file_name',
                displayName: 'File Name',
                //filterHeaderTemplate: '<div class="ui-grid-filter-container"><input ng-model="grid.appScope.vm.searchText" ng-change="grid.appScope.vm.refreshData()" class="form-control" placeholder="Search"></div>'
                enableFiltering: false
            },
            {
                field: 'file_size_readable',
                displayName: 'File Size',
                enableFiltering: false
            },
            {
                field: 'job_type',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.job_type.title }} {{ row.entity.job_type.version }}</div>'
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

        ctrl.filterResults = function () {
            stateService.setSourceFileProductsParams(ctrl.sourceFileProductsParams);
            getSourceProducts();
        };

        ctrl.updateColDefs = function () {
            ctrl.gridOptions.columnDefs = gridFactory.applySortConfig(ctrl.colDefs, ctrl.sourceFileProductsParams);
        };

        ctrl.updateSourceFileProductsOrder = function (sortArr) {
            ctrl.sourceFileProductsParams.order = sortArr.length > 0 ? sortArr : null;
            filteredByOrder = sortArr.length > 0;
            ctrl.filterResults();
        };

        ctrl.gridOptions.onRegisterApi = function (gridApi) {
            //set gridApi on scope
            ctrl.gridApi = gridApi;
            ctrl.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                ctrl.sourceFileProductsParams.page = currentPage;
                ctrl.sourceFileProductsParams.page_size = pageSize;
                ctrl.filterResults();
            });
            // ctrl.gridApi.selection.on.rowSelectionChanged($scope, function (row) {
            //     $location.path('/data/source/file/' + row.entity.id).search('');
            // });
            ctrl.gridApi.core.on.sortChanged($scope, function (grid, sortColumns) {
                _.forEach(ctrl.gridApi.grid.columns, function (col) {
                    col.colDef.sort = col.sort;
                });
                stateService.setSourceFileProductsColDefs(ctrl.gridApi.grid.options.columnDefs);
                var sortArr = [];
                _.forEach(sortColumns, function (col) {
                    sortArr.push(col.sort.direction === 'desc' ? '-' + col.field : col.field);
                });
                ctrl.updateSourceFileProductsOrder(sortArr);
            });
        };

        ctrl.filterByFilename = function (keyEvent) {
            if (!keyEvent || (keyEvent && keyEvent.which === 13)) {
                ctrl.sourceFileProductsParams.file_name = ctrl.searchText;
                ctrl.filterResults();
            }
        };

        var initialize = function() {
            navService.updateLocation('data');
            ctrl.updateColDefs();
            getSourceFileDetails();
            if (!qs.tab) {
                qs.tab = ctrl.activeTab;
                $location.search(qs);
            }
        };

        initialize();

        ctrl.showGrid = function (gridType) {
            qs.tab = gridType;
            ctrl.activeTab = gridType;
            $location.search(qs);
        };

        $scope.$watch('ctrl.startDate', function (value) {
            if ($scope.productsData) {
                ctrl.sourceFileProductsParams.started = value.toISOString();
                ctrl.filterResults();
            }
        });

        $scope.$watch('ctrl.stopDate', function (value) {
            if ($scope.productsData) {
                ctrl.sourceFilesParams.ended = value.toISOString();
                ctrl.filterResults();
            }
        });

        $scope.$watchCollection('ctrl.stateService.getSourceFileProductsColDefs()', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            ctrl.colDefs = newValue;
            ctrl.updateColDefs();
        });

        $scope.$watchCollection('ctrl.stateService.getSourceFileProductsParams()', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            ctrl.sourceFileProductsParams = newValue;
            ctrl.updateColDefs();
        });
    });
})();
