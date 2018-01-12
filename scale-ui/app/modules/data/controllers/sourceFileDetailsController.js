(function () {
    'use strict';

    angular.module('scaleApp').controller('sourceFileDetailsController', function($scope, $location, $routeParams, $timeout, $uibModal, scaleConfig, stateService, navService, dataService, gridFactory, SourceFile, Product, moment) {
        var ctrl = this,
            sourceFileId = parseInt($routeParams.id),
            qs = $location.search();

        $scope.jobsData = null;
        $scope.productsData = null;
        $scope.ingestsData = null;
        $scope.hasParentCtrl = true;
        $scope.jobsParams = stateService.getParentJobsParams();
        $scope.productsParams = {
            order: ["-last_modified"],
            page: 1,
            page_size: 25
        };
        $scope.ingestsParams = stateService.getParentIngestsParams();

        ctrl.loading = true;
        ctrl._ = _;
        ctrl.sourceFile = null;
        ctrl.activeTab = qs.tab || 'jobs';

        ctrl.searchText = $scope.productsParams.file_name || '';
        ctrl.gridOptions = gridFactory.defaultGridOptions();
        ctrl.gridOptions.paginationCurrentPage = $scope.productsParams.page || 1;
        ctrl.gridOptions.paginationPageSize = $scope.productsParams.page_size || ctrl.gridOptions.paginationPageSize;
        ctrl.gridOptions.data = [];

        $timeout(function () {
            ctrl.gridOptions.paginationCurrentPage = $scope.productsParams.page || 1;
            ctrl.gridOptions.paginationPageSize = $scope.productsParams.page_size || ctrl.gridOptions.paginationPageSize;
        });

        var getSourceJobs = function () {
            dataService.getSourceDescendants(ctrl.sourceFile.id, 'jobs', $scope.jobsParams).then(function (data) {
                $scope.jobsData = data;
            });
        };

        var getSourceProducts = function () {
            dataService.getSourceDescendants(ctrl.sourceFile.id, 'products', $scope.productsParams).then(function (data) {
                $scope.productsData = data;
                ctrl.gridOptions.minRowsToShow = data.results.length;
                ctrl.gridOptions.virtualizationThreshold = data.results.length;
                ctrl.gridOptions.totalItems = data.count;
                ctrl.gridOptions.data = Product.transformer(data.results);
            });
        };

        var getSourceIngests = function () {
            dataService.getSourceDescendants(ctrl.sourceFile.id, 'ingests', $scope.ingestsParams).then(function (data) {
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

        ctrl.getFormattedDate = function (date) {
            if (date) {
                return _.capitalize(moment.utc(date).from(moment.utc())) + ' <small>' + moment.utc(date).format(scaleConfig.dateFormats.day_second_utc_nolabel) + '</small>';
            }
            return '';
        };

        var filteredByOrder = $scope.productsParams.order ? true : false;

        ctrl.colDefs = [
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
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.file_size_readable }}</div>'
            },
            {
                field: 'job_type',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents"><a ng-href="/#/jobs/job/{{ row.entity.job.id }}">{{ row.entity.job_type.title }} {{ row.entity.job_type.version }}</a></div>'
            },
            {
                field: 'data_started',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents"><span ng-bind-html="grid.appScope.ctrl.getFormattedDate(row.entity.data_started)"></span></div>'
            },
            {
                field: 'data_ended',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents"><span ng-bind-html="grid.appScope.ctrl.getFormattedDate(row.entity.data_ended)"></span></div>'
            },
            {
                field: 'countries',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.countries.join(\', \') }}</div>'
            },
            {
                field: 'last_modified',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.last_modified_formatted }}</div>'
            }
        ];

        ctrl.filterResults = function () {
            stateService.setSourceFileProductsParams($scope.productsParams);
            getSourceProducts();
        };

        ctrl.updateColDefs = function () {
            ctrl.gridOptions.columnDefs = gridFactory.applySortConfig(ctrl.colDefs, $scope.productsParams);
        };

        ctrl.updateSourceFileProductsOrder = function (sortArr) {
            $scope.productsParams.order = sortArr.length > 0 ? sortArr : null;
            filteredByOrder = sortArr.length > 0;
            ctrl.filterResults();
        };

        ctrl.gridOptions.onRegisterApi = function (gridApi) {
            //set gridApi on scope
            ctrl.gridApi = gridApi;
            ctrl.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                $scope.productsParams.page = currentPage;
                $scope.productsParams.page_size = pageSize;
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
                $scope.productsParams.file_name = ctrl.searchText;
                ctrl.filterResults();
            }
        };

        var initialize = function() {
            navService.updateLocation('data');
            ctrl.updateColDefs();
            getSourceFileDetails();
            if (!qs.tab) {
                qs.tab = ctrl.activeTab;
                $location.search(qs).replace();
            }
        };

        initialize();

        ctrl.showGrid = function (gridType) {
            qs.tab = gridType;
            ctrl.activeTab = gridType;
            $location.search(qs).replace();
        };

        ctrl.showMetadata = function () {
            // show modal
            $uibModal.open({
                animation: true,
                templateUrl: 'showMetadata.html',
                scope: $scope,
                windowClass: 'metadata-modal-window'
            });
        };

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
            $scope.productsParams = newValue;
            ctrl.updateColDefs();
        });
    });
})();
