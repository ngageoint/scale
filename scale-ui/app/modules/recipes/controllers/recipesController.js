(function () {
    'use strict';

    angular.module('scaleApp').controller('recipesController', function ($scope, $location, scaleConfig, scaleService, stateService, recipeService, navService, subnavService, gridFactory) {
        subnavService.setCurrentPath('recipes');

        var vm = this,
            recipeTypeViewAll = { name: 'VIEW ALL', title: 'VIEW ALL', version: '', id: 0 };

        vm.recipesParams = stateService.getRecipesParams();

        vm.stateService = stateService;
        vm.loading = true;
        vm.recipeTypeValues = [recipeTypeViewAll];
        vm.selectedRecipeType = vm.recipesParams.type_id ? vm.recipesParams.type_id : recipeTypeViewAll;
        vm.subnavLinks = scaleConfig.subnavLinks.recipes;
        vm.lastModifiedStart = moment.utc(vm.recipesParams.started).toDate();
        vm.lastModifiedStartPopup = {
            opened: false
        };
        vm.openLastModifiedStartPopup = function ($event) {
            $event.stopPropagation();
            vm.lastModifiedStartPopup.opened = true;
        };
        vm.lastModifiedStop = moment.utc(vm.recipesParams.ended).toDate();
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
        vm.gridOptions.paginationCurrentPage = vm.recipesParams.page || 1;
        vm.gridOptions.paginationPageSize = vm.recipesParams.page_size || vm.gridOptions.paginationPageSize;
        vm.gridOptions.data = [];

        var filteredByRecipeType = vm.recipesParams.type_id ? true : false,
            filteredByOrder = vm.recipesParams.order ? true : false;

        vm.colDefs = [
            {
                field: 'recipe_type',
                displayName: 'Recipe Type',
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.recipe_type.title }} {{ row.entity.recipe_type.version }}</div>',
                filterHeaderTemplate: '<div class="ui-grid-filter-container"><select class="form-control input-sm" ng-model="grid.appScope.vm.selectedRecipeType" ng-options="recipeType as (recipeType.title + \' \' + recipeType.version) for recipeType in grid.appScope.vm.recipeTypeValues"></select>'
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
            },
            {
                field: 'duration',
                enableFiltering: false,
                enableSorting: false,
                width: 120,
                cellTemplate: '<div class="ui-grid-cell-contents text-right">{{ row.entity.getDuration() }}</div>'
            },
            {
                field: 'completed',
                enableFiltering: false,
                enableSorting: true,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.completed_formatted }}</div>'
            }
        ];

        vm.getRecipes = function () {
            recipeService.getRecipes(vm.recipesParams).then(function (data) {
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

        vm.getRecipeTypes = function () {
            recipeService.getRecipeTypes().then(function (data) {
                vm.recipeTypeValues.push(data.results);
                vm.recipeTypeValues = _.flatten(vm.recipeTypeValues);
                vm.selectedRecipeType = _.find(vm.recipeTypeValues, { id: vm.recipesParams.type_id }) || recipeTypeViewAll;
                vm.getRecipes();
            }).catch(function (error) {
                vm.loading = false;
            });
        };

        vm.filterResults = function () {
            stateService.setRecipesParams(vm.recipesParams);
            vm.loading = true;
            vm.getRecipes();
            $('.ui-grid-pager-panel').remove();
        };

        vm.updateColDefs = function () {
            vm.gridOptions.columnDefs = gridFactory.applySortConfig(vm.colDefs, vm.recipesParams);
        };

        vm.updateRecipeOrder = function (sortArr) {
            vm.recipesParams.order = sortArr.length > 0 ? sortArr : null;
            filteredByOrder = sortArr.length > 0;
            vm.filterResults();
        };

        vm.updateRecipeType = function (value) {
            if (value.id !== vm.recipesParams.type_id) {
                vm.recipesParams.page = 1;
            }
            vm.recipesParams.type_id = value.id === 0 ? null : value.id;
            vm.recipesParams.page_size = vm.gridOptions.paginationPageSize;
            if (!vm.loading) {
                vm.filterResults();
            }
        };

        vm.gridOptions.onRegisterApi = function (gridApi) {
            //set gridApi on scope
            vm.gridApi = gridApi;
            vm.gridApi.selection.on.rowSelectionChanged($scope, function (row) {
                $location.path('/recipes/recipe/' + row.entity.id);
            });
            vm.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                vm.recipesParams.page = currentPage;
                vm.recipesParams.page_size = pageSize;
                vm.filterResults();
            });
            vm.gridApi.core.on.sortChanged($scope, function (grid, sortColumns) {
                _.forEach(vm.gridApi.grid.columns, function (col) {
                    col.colDef.sort = col.sort;
                });
                stateService.setRecipesColDefs(vm.gridApi.grid.options.columnDefs);
                var sortArr = [];
                _.forEach(sortColumns, function (col) {
                    sortArr.push(col.sort.direction === 'desc' ? '-' + col.field : col.field);
                });
                vm.updateRecipeOrder(sortArr);
            });
            vm.gridApi.core.on.rowsRendered($scope, function () {
                if (gridApi.grid.renderContainers.body.visibleRowCache.length === 0) { return; }
                $('.ui-grid-pager-panel').remove();
            });
        };

        vm.initialize = function () {
            stateService.setRecipesParams(vm.recipesParams);
            vm.updateColDefs();
            vm.getRecipeTypes();
            navService.updateLocation('recipes');
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

        $scope.$watch('vm.lastModifiedStart', function (value) {
            if (!vm.loading) {
                vm.recipesParams.started = value.toISOString();
                vm.filterResults();
            }
        });

        $scope.$watch('vm.lastModifiedStop', function (value) {
            if (!vm.loading) {
                vm.recipesParams.ended = value.toISOString();
                vm.filterResults();
            }
        });

        $scope.$watchCollection('vm.stateService.getRecipesColDefs()', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            vm.colDefs = newValue;
            vm.updateColDefs();
        });

        $scope.$watchCollection('vm.stateService.getRecipesParams()', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            vm.recipesParams = newValue;
            vm.updateColDefs();
        });
    });
})();