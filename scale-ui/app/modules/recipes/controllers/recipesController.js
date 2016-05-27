(function () {
    'use strict';

    angular.module('scaleApp').controller('recipesController', function ($scope, $location, scaleConfig, scaleService, stateService, recipeService, navService, subnavService, gridFactory) {
        subnavService.setCurrentPath('recipes');

        var self = this,
            recipeTypeViewAll = { name: 'VIEW ALL', title: 'VIEW ALL', version: '', id: 0 };

        self.recipesParams = stateService.getRecipesParams();

        $scope.stateService = stateService;
        $scope.loading = true;
        $scope.recipeTypeValues = [recipeTypeViewAll];
        $scope.selectedRecipeType = self.recipesParams.type_id ? self.recipesParams.type_id : recipeTypeViewAll;
        $scope.subnavLinks = scaleConfig.subnavLinks.recipes;
        $scope.gridStyle = '';
        $scope.lastModifiedStart = moment.utc(self.recipesParams.started).toDate();
        $scope.lastModifiedStartPopup = {
            opened: false
        };
        $scope.openLastModifiedStartPopup = function ($event) {
            $event.stopPropagation();
            $scope.lastModifiedStartPopup.opened = true;
        };
        $scope.lastModifiedStop = moment.utc(self.recipesParams.ended).toDate();
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
        $scope.gridOptions.paginationCurrentPage = self.recipesParams.page || 1;
        $scope.gridOptions.paginationPageSize = self.recipesParams.page_size || $scope.gridOptions.paginationPageSize;
        $scope.gridOptions.data = [];

        var filteredByRecipeType = self.recipesParams.type_id ? true : false,
            filteredByOrder = self.recipesParams.order ? true : false;

        self.colDefs = [
            {
                field: 'recipe_type',
                displayName: 'Recipe Type',
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.recipe_type.title }} {{ row.entity.recipe_type.version }}</div>',
                filterHeaderTemplate: '<div class="ui-grid-filter-container"><select class="form-control input-sm" ng-model="grid.appScope.selectedRecipeType" ng-options="recipeType as (recipeType.title + \' \' + recipeType.version) for recipeType in grid.appScope.recipeTypeValues"></select>'
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

        self.getRecipes = function () {
            recipeService.getRecipes(self.recipesParams).then(function (data) {
                $scope.gridOptions.totalItems = data.count;
                $scope.gridOptions.data = data.results;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        self.getRecipeTypes = function () {
            recipeService.getRecipeTypes().then(function (data) {
                $scope.recipeTypeValues.push(data.results);
                $scope.recipeTypeValues = _.flatten($scope.recipeTypeValues);
                $scope.selectedRecipeType = _.find($scope.recipeTypeValues, { id: self.recipesParams.type_id }) || recipeTypeViewAll;
                self.getRecipes();
            }).catch(function (error) {
                $scope.loading = false;
            });
        };

        self.filterResults = function () {
            stateService.setRecipesParams(self.recipesParams);
            $scope.loading = true;
            self.getRecipes();
        };

        self.updateColDefs = function () {
            $scope.gridOptions.columnDefs = gridFactory.applySortConfig(self.colDefs, self.recipesParams);
        };

        self.updateRecipeOrder = function (sortArr) {
            self.recipesParams.order = sortArr.length > 0 ? sortArr : null;
            filteredByOrder = sortArr.length > 0;
            self.filterResults();
        };

        self.updateRecipeType = function (value) {
            if (value.id !== self.recipesParams.type_id) {
                self.recipesParams.page = 1;
            }
            self.recipesParams.type_id = value.id === 0 ? null : value.id;
            self.recipesParams.page_size = $scope.gridOptions.paginationPageSize;
            if (!$scope.loading) {
                self.filterResults();
            }
        };

        $scope.gridOptions.onRegisterApi = function (gridApi) {
            //set gridApi on scope
            $scope.gridApi = gridApi;
            $scope.gridApi.selection.on.rowSelectionChanged($scope, function (row) {
                $scope.$apply(function () {
                    $location.path('/recipes/recipe/' + row.entity.id);
                });
            });
            $scope.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                self.recipesParams.page = currentPage;
                self.recipesParams.page_size = pageSize;
                self.filterResults();
            });
            $scope.gridApi.core.on.sortChanged($scope, function (grid, sortColumns) {
                _.forEach($scope.gridApi.grid.columns, function (col) {
                    col.colDef.sort = col.sort;
                });
                stateService.setJobsColDefs($scope.gridApi.grid.options.columnDefs);
                var sortArr = [];
                _.forEach(sortColumns, function (col) {
                    sortArr.push(col.sort.direction === 'desc' ? '-' + col.field : col.field);
                });
                self.updateRecipeOrder(sortArr);
            });
        };

        self.initialize = function () {
            stateService.setRecipesParams(self.recipesParams);
            self.updateColDefs();
            self.getRecipeTypes();
            navService.updateLocation('recipes');
        };

        self.initialize();

        angular.element(document).ready(function () {
            // set container heights equal to available page height
            var viewport = scaleService.getViewportSize(),
                offset = scaleConfig.headerOffset + scaleConfig.dateFilterOffset,
                gridMaxHeight = viewport.height - offset;

            $scope.gridStyle = 'height: ' + gridMaxHeight + 'px; max-height: ' + gridMaxHeight + 'px; overflow-y: auto;';
        });

        $scope.$watch('selectedRecipeType', function (value) {
            if (parseInt(value)) {
                value = _.find($scope.recipeTypeValues, {id: parseInt(value)});
            }
            if (value) {
                if ($scope.loading) {
                    if (filteredByRecipeType) {
                        self.updateRecipeType(value);
                    }
                } else {
                    filteredByRecipeType = !angular.equals(value, recipeTypeViewAll);
                    self.updateRecipeType(value);
                }
            }
        });

        $scope.$watch('lastModifiedStart', function (value) {
            if (!$scope.loading) {
                self.recipesParams.started = value.toISOString();
                self.filterResults();
            }
        });

        $scope.$watch('lastModifiedStop', function (value) {
            if (!$scope.loading) {
                self.recipesParams.ended = value.toISOString();
                self.filterResults();
            }
        });

        $scope.$watchCollection('stateService.getRecipesColDefs()', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            self.colDefs = newValue;
            self.updateColDefs();
        });

        $scope.$watchCollection('stateService.getRecipesParams()', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            self.recipesParams = newValue;
            self.updateColDefs();
        });
    });
})();