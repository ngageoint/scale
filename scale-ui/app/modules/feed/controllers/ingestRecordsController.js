(function () {
    'use strict';

    angular.module('scaleApp').controller('ingestRecordsController', function ($scope, $location, $timeout, scaleConfig, scaleService, stateService, feedService, strikeService, navService, subnavService, Ingest, gridFactory, poller) {
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
        vm.strikeData = [];
        vm.selectedStrike = {};
        vm.searchText = vm.ingestsParams.file_name || '';
        vm.gridOptions = gridFactory.defaultGridOptions();
        vm.gridOptions.data = [];

        $timeout(function () {
            vm.gridOptions.paginationCurrentPage = vm.ingestsParams.page || 1;
            vm.gridOptions.paginationPageSize = vm.ingestsParams.page_size || vm.gridOptions.paginationPageSize;
        });

        vm.refreshData = function () {
            var filteredData = _.filter(vm.ingestData, function (d) {
                return d.file_name.toLowerCase().includes(vm.searchText.toLowerCase());
            });
            vm.gridOptions.data = filteredData.length > 0 ? filteredData : vm.gridOptions.data;
        };

        var filteredByStatus = vm.ingestsParams.status ? true : false,
            filteredByStrike = vm.ingestsParams.strike_id ? true : false,
            filteredByOrder = vm.ingestsParams.order ? true : false;

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
                field: 'strike.title',
                displayName: 'Strike Process',
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.strike.title }}</div>',
                filterHeaderTemplate: '<div class="ui-grid-filter-container"><select class="form-control input-sm" ng-model="grid.appScope.vm.selectedStrike" ng-options="strike as strike.title.toUpperCase() for strike in grid.appScope.vm.strikeData"></select></div>'
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
            if ($scope.$parent.ingestsData) {
                vm.ingestData = $scope.$parent.ingestsData.results;
                vm.gridOptions.minRowsToShow = $scope.$parent.ingestsData.results.length;
                vm.gridOptions.virtualizationThreshold = $scope.$parent.ingestsData.results.length;
                vm.gridOptions.totalItems = $scope.$parent.ingestsData.count;
                vm.gridOptions.data = Ingest.transformer($scope.$parent.ingestsData.results);
            } else {
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
            }
        };

        vm.filterResults = function () {
            poller.stopAll();
            stateService.setIngestsParams(vm.ingestsParams);
            vm.getIngests();
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

        vm.updateIngestStrike = function (value) {
            if (value.title) {
                if (value.id !== vm.ingestsParams.strike_id) {
                    vm.ingestsParams.page = 1;
                }
                vm.ingestsParams.strike_id = value.title === 'VIEW ALL' ? null : value.id;
                vm.ingestsParams.page_size = vm.gridOptions.paginationPageSize;
                if (!vm.loading) {
                    vm.filterResults();
                }
            }
        };

        vm.getStrikes = function () {
            strikeService.getStrikes().then(function (data) {
                var strikeViewAll = {
                    id: 0,
                    name: 'viewall',
                    title: 'VIEW ALL'
                };
                vm.strikeData = data;
                vm.strikeData.unshift(strikeViewAll);
                vm.selectedStrike = _.find(vm.strikeData, { id: vm.ingestsParams.strike_id }) || data[0];
                vm.getIngests();
            });
        };

        vm.gridOptions.onRegisterApi = function (gridApi) {
            //set gridApi on scope
            vm.gridApi = gridApi;
            vm.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                vm.ingestsParams.page = currentPage;
                vm.ingestsParams.page_size = pageSize;
                vm.filterResults();
            });
            vm.gridApi.selection.on.rowSelectionChanged($scope, function (row) {
                if(row.entity.source_file && row.entity.source_file.id){
                    $location.path('/feed/ingests/' + row.entity.source_file.id).search('');
                } else {
                    toastr["info"]('Source file is undefined for ' + row.entity.file_name);
                }

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
        };

        vm.filterByFilename = function (keyEvent) {
            if (!keyEvent || (keyEvent && keyEvent.which === 13)) {
                vm.ingestsParams.file_name = vm.searchText;
                vm.filterResults();
            }
        };

        vm.initialize = function () {
            stateService.setIngestsParams(vm.ingestsParams);
            vm.updateColDefs();
            vm.getStrikes();
            if (!$scope.$parent.hasParentCtrl) {
                navService.updateLocation('feed');
            }
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

        $scope.$watch('vm.selectedStrike', function (value) {
            if (vm.loading) {
                if (filteredByStrike) {
                    vm.updateIngestStrike(value);
                }
            } else {
                filteredByStrike = value.title !== 'VIEW ALL';
                vm.updateIngestStrike(value);
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
