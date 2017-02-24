(function () {
    'use strict';

    angular.module('scaleApp').controller('batchesController', function ($scope, $location, scaleConfig, gridFactory, subnavService, userService, jobTypeService, recipeService, navService, stateService, batchService, Batch, moment) {
        subnavService.setCurrentPath('batch');

        var vm = this,
            jobTypeViewAll = { name: 'VIEW ALL', title: 'VIEW ALL', version: '', id: 0 },
            recipeTypeViewAll = { name: 'VIEW ALL', title: 'VIEW ALL', version: '', id: 0 };

        vm.batchesParams = stateService.getBatchesParams();

        vm.stateService = stateService;
        vm.subnavLinks = scaleConfig.subnavLinks.batch;
        vm.loading = true;
        vm.readonly = true;
        vm.jobTypeValues = [jobTypeViewAll];
        vm.selectedJobType = vm.batchesParams.job_type_id ? vm.batchesParams.job_type_id : jobTypeViewAll;
        vm.recipeTypeValues = [recipeTypeViewAll];
        vm.selectedRecipeType = vm.batchesParams.recipe_type_id ? vm.batchesParams.recipe_type_id : recipeTypeViewAll;
        vm.batchStatusValues = scaleConfig.batchStatus;
        vm.selectedBatchStatus = vm.batchesParams.status || vm.batchStatusValues[0];
        vm.lastModifiedStart = moment.utc(vm.batchesParams.started).toDate();
        vm.lastModifiedStartPopup = {
            opened: false
        };
        vm.openLastModifiedStartPopup = function ($event) {
            $event.stopPropagation();
            vm.lastModifiedStartPopup.opened = true;
        };
        vm.lastModifiedStop = moment.utc(vm.batchesParams.ended).toDate();
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
        vm.gridOptions = gridFactory.defaultGridOptions();
        vm.gridOptions.paginationCurrentPage = vm.batchesParams.page || 1;
        vm.gridOptions.paginationPageSize = vm.batchesParams.page_size || vm.gridOptions.paginationPageSize;
        vm.gridOptions.data = [];

        var filteredByJobType = vm.batchesParams.job_type_id ? true : false,
            filteredByBatchStatus = vm.batchesParams.status ? true : false,
            filteredByRecipeType = vm.batchesParams.recipe_type_id ? true : false,
            filteredByOrder = vm.batchesParams.order ? true : false;

        vm.colDefs = [
            {
                field: 'title',
                enableFiltering: false,
                displayName: 'Title'
            },
            {
                field: 'recipe_type',
                displayName: 'Recipe Type',
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.recipe_type.title }} {{ row.entity.recipe_type.version }}</div>',
                filterHeaderTemplate: '<div class="ui-grid-filter-container"><select class="form-control input-sm" ng-model="grid.appScope.vm.selectedRecipeType" ng-options="recipeType as (recipeType.title + \' \' + recipeType.version) for recipeType in grid.appScope.vm.recipeTypeValues"></select></div>'
            },
            {
                field: 'creator_job',
                displayName: 'Job Type',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents"><span ng-bind-html="row.entity.creator_job.job_type.getIcon()"></span> {{ row.entity.creator_job.job_type.title }} {{ row.entity.creator_job.job_type.version }}</div>'
            },
            {
                field: 'status',
                displayName: 'Status',
                filterHeaderTemplate: '<div class="ui-grid-filter-container"><select class="form-control input-sm" ng-model="grid.appScope.vm.selectedBatchStatus"><option ng-selected="{{ grid.appScope.vm.batchStatusValues[$index] == grid.appScope.vm.selectedBatchStatus }}" value="{{ grid.appScope.vm.batchStatusValues[$index] }}" ng-repeat="status in grid.appScope.vm.batchStatusValues track by $index">{{ status.toUpperCase() }}</option></select></div>'
            },
            {
                field: 'created_count',
                enableFiltering: false,
                displayName: 'Failure Rate',
                cellTemplate: 'failureRate.html'
            },
            {
                field: 'created',
                displayName: 'Created (Z)',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.created_formatted }}</div>'
            },
            {
                field: 'last_modified',
                displayName: 'Last Modified (Z)',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.last_modified_formatted }}</div>'
            }
        ];

        vm.failRateStyle = function (error, total) {
            var percentage = ((error / total) * 100).toFixed(0);
            return percentage > 0 ? 'width: ' + percentage + '%' : 'display: none';
        };

        vm.getBatches = function () {
            batchService.getBatches(vm.batchesParams).then(function (data) {
                vm.loading = false;
                vm.gridOptions.totalItems = data.count;
                vm.gridOptions.minRowsToShow = data.results.length;
                vm.gridOptions.virtualizationThreshold = data.results.length;
                vm.gridOptions.data = Batch.transformer(data.results);
            }).catch(function (e) {
                console.log('Error retrieving batches: ' + e);
                vm.loading = false;
            });
        };

        vm.getRecipeTypes = function () {
            return recipeService.getRecipeTypes().then(function (data) {
                vm.recipeTypeValues.push(data.results);
                vm.recipeTypeValues = _.flatten(vm.recipeTypeValues);
                vm.selectedRecipeType = _.find(vm.recipeTypeValues, { id: vm.batchesParams.recipe_type_id }) || recipeTypeViewAll;
            }).catch(function (e) {
                console.log('Error retrieving recipe types: ' + e);
            });
        };

        vm.filterResults = function () {
            stateService.setBatchesParams(vm.batchesParams);
            vm.loading = true;
            vm.getBatches();
        };

        vm.updateColDefs = function () {
            vm.gridOptions.columnDefs = gridFactory.applySortConfig(vm.colDefs, vm.batchesParams);
        };

        vm.updateBatchOrder = function (sortArr) {
            vm.batchesParams.order = sortArr.length > 0 ? sortArr : null;
            filteredByOrder = sortArr.length > 0;
            vm.filterResults();
        };

        vm.updateRecipeType = function (value) {
            if (value.id !== vm.batchesParams.recipe_type_id) {
                vm.batchesParams.page = 1;
            }
            vm.batchesParams.recipe_type_id = value.id === 0 ? null : value.id;
            vm.batchesParams.page_size = vm.gridOptions.paginationPageSize;
            if (!vm.loading) {
                vm.filterResults();
            }
        };

        vm.updateBatchStatus = function (value) {
            if (value != vm.batchesParams.status) {
                vm.batchesParams.page = 1;
            }
            vm.batchesParams.status = value === 'VIEW ALL' ? null : value;
            vm.batchesParams.page_size = vm.gridOptions.paginationPageSize;
            if (!vm.loading) {
                vm.filterResults();
            }
        };

        vm.failRateStyle = function (error, total) {
            var percentage = ((error / total) * 100).toFixed(0);
            return percentage > 0 ? 'width: ' + percentage + '%' : 'display: none';
        };

        vm.gridOptions.onRegisterApi = function (gridApi) {
            //set gridApi on scope
            vm.gridApi = gridApi;
            vm.gridApi.selection.on.rowSelectionChanged($scope, function (row) {
                $location.path('/batch/' + row.entity.id).search('');
            });
            vm.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                vm.batchesParams.page = currentPage;
                vm.batchesParams.page_size = pageSize;
                vm.filterResults();
            });
            vm.gridApi.core.on.sortChanged($scope, function (grid, sortColumns) {
                _.forEach(vm.gridApi.grid.columns, function (col) {
                    col.colDef.sort = col.sort;
                });
                stateService.setBatchesColDefs(vm.gridApi.grid.options.columnDefs);
                var sortArr = [];
                _.forEach(sortColumns, function (col) {
                    sortArr.push(col.sort.direction === 'desc' ? '-' + col.field : col.field);
                });
                vm.updateBatchOrder(sortArr);
            });
        };

        vm.initialize = function () {
            stateService.setBatchesParams(vm.batchesParams);
            vm.updateColDefs();
            var user = userService.getUserCreds();
            vm.readonly = !(user && user.is_admin);
            vm.getRecipeTypes()
                .then(vm.getBatches);
            navService.updateLocation('batch');
        };

        vm.initialize();

        $scope.$watch('vm.selectedRecipeType', function (value) {
            if (parseInt(value)) {
                value = _.find(vm.recipeTypeValues, {id: parseInt(value)});
            }
            if (value) {
                if (vm.loading) {
                    if (filteredByRecipeType) {
                        vm.updateRecipeType(value);
                    }
                } else {
                    filteredByRecipeType = !angular.equals(value, recipeTypeViewAll);
                    vm.updateRecipeType(value);
                }
            }
        });

        $scope.$watch('vm.selectedBatchStatus', function (value) {
            if (vm.loading) {
                if (filteredByBatchStatus) {
                    vm.updateBatchStatus(value);
                }
            } else {
                filteredByBatchStatus = value !== 'VIEW ALL';
                vm.updateBatchStatus(value);
            }
        });

        $scope.$watch('vm.lastModifiedStart', function (value) {
            if (!vm.loading) {
                vm.batchesParams.started = value.toISOString();
                vm.filterResults();
            }
        });

        $scope.$watch('vm.lastModifiedStop', function (value) {
            if (!vm.loading) {
                vm.batchesParams.ended = value.toISOString();
                vm.filterResults();
            }
        });

        $scope.$watchCollection('vm.stateService.getBatchesColDefs()', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            vm.colDefs = newValue;
            vm.updateColDefs();
        });

        $scope.$watchCollection('vm.stateService.getBatchesParams()', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            vm.batchesParams = newValue;
            vm.updateColDefs();
        });
    });
})();
