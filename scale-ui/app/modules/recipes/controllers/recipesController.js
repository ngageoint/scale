(function () {
    'use strict';

    angular.module('scaleApp').controller('recipesController', function ($rootScope, $scope, $location, scaleService, navService, gridFactory, uiGridConstants, scaleConfig, subnavService, recipeService) {

        var recipesParams = {
            page: null, page_size: null, started: null, ended: null, order: $rootScope.recipesControllerOrder || null, type_id: null, type_name: null, url: null
        };

        // check for recipesParams in query string, and update as necessary
        _.forEach(_.pairs(recipesParams), function (param) {
            var value = _.at($location.search(), param[0]);
            if (value.length > 0) {
                recipesParams[param[0]] = value.length > 1 ? value : value[0];
            }
        });

        var gridPageNumber = recipesParams.page || 1,
            filteredByRecipeType = recipesParams.type_id ? true : false,
            filteredByOrder = recipesParams.order ? true : false;

        // this file will be similar to jobsController
        $scope.recipesData = {};
        $scope.loading = true;
        $scope.recipeTypeValues = [];
        $scope.selectedRecipeType = recipesParams.type_id || 0;
        $scope.subnavLinks = scaleConfig.subnavLinks.recipes;
        $scope.gridStyle = '';

        subnavService.setCurrentPath('recipes');

        var defaultColumnDefs = [
            {
                field: 'recipe_type',
                displayName: 'Recipe Type',
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.recipe_type.title }} {{ row.entity.recipe_type.version }}</div>',
                filterHeaderTemplate: '<div class="ui-grid-filter-container"><select class="form-control input-sm" ng-model="grid.appScope.selectedRecipeType"><option ng-selected="{{ grid.appScope.recipeTypeValues[$index].id == grid.appScope.selectedRecipeType }}" value="{{ grid.appScope.recipeTypeValues[$index].id }}" ng-repeat="recipeType in grid.appScope.recipeTypeValues track by $index">{{ grid.appScope.recipeTypeValues[$index].title }} {{ grid.appScope.recipeTypeValues[$index].version }}</option></select>'
            },
            //{ field: 'created', enableFiltering: false, cellFilter: 'date:\'yyyy-MM-dd HH:mm:ss\''},
            { field: 'created', enableFiltering: false},
            {
                field: 'last_modified',
                enableFiltering: false,
                //cellFilter: 'date:\'yyyy-MM-dd HH:mm:ss\'',                
            },
            { field: 'duration', enableFiltering: false, enableSorting: false, cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.getDuration() }}</div>' }
        ];

        $scope.gridOptions = gridFactory.defaultGridOptions();
        $scope.gridOptions.paginationCurrentPage = parseInt(recipesParams.page || 1);
        $scope.gridOptions.paginationPageSize = parseInt(recipesParams.page_size) || $scope.gridOptions.paginationPageSize;
        var colDefs = $rootScope.recipeColDefs ? $rootScope.recipeColDefs : defaultColumnDefs;
        $scope.gridOptions.columnDefs = gridFactory.applySortConfig(colDefs, recipesParams);
        $scope.gridOptions.data = [];
        $scope.gridOptions.onRegisterApi = function (gridApi) {
            //set gridApi on scope
            $scope.gridApi = gridApi;
            $scope.gridApi.selection.on.rowSelectionChanged($scope, function (row) {
                $scope.$apply(function(){
                    $location.path('/recipes/recipe/' + row.entity.id);
                });

            });
            $scope.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                recipesParams.page = currentPage;
                recipesParams.page_size = pageSize;
                console.log('gridApi');
                $scope.filterResults();
            });
            $scope.gridApi.core.on.sortChanged($scope, function (grid, sortColumns) {
                $rootScope.recipeColDefs = null;
                _.forEach($scope.gridApi.grid.columns, function (col) {
                    col.colDef.sort = col.sort;
                });
                $rootScope.recipeColDefs = $scope.gridApi.grid.options.columnDefs;
                var sortArr = [];
                _.forEach(sortColumns, function (col) {
                    sortArr.push(col.sort.direction === 'desc' ? '-' + col.field : col.field);
                });
                updateRecipeOrder(sortArr);
            });
        };

        $scope.getPage = function (filter, pageNumber, pageSize, url) {
            $scope.loading = true;
            recipeService.getRecipes(filter, pageNumber, pageSize, url).then(function (data) {
                var newData = [];
                for (var i = 0; i < $scope.gridOptions.paginationPageSize; i++) {
                    if (data.results[i]) {
                        newData.push(data.results[i]);
                    }
                }
                $scope.gridOptions.data = newData;
                $scope.gridOptions.totalItems = data.count;
                $scope.jobsData = data;
                gridPageNumber = pageNumber;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        $scope.filterResults = function () {
            _.forEach(_.pairs(recipesParams), function (param) {
                $location.search(param[0], param[1]);
            });
            getRecipes();
        };

        var getRecipes = function () {
            recipeService.getRecipes(recipesParams).then(function (data) {
                $scope.recipesData = data;
                $scope.gridOptions.totalItems = data.count;
                $scope.gridOptions.data = data.results;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        var getRecipeTypes = function () {
            recipeService.getRecipeTypes().then(function (data) {
                $scope.recipeTypeValues = data;
                $scope.recipeTypeValues.unshift({ name: 'VIEW ALL', title: 'VIEW ALL', version: '', id: 0 });
                getRecipes();
            }).catch(function (error) {
                $scope.loading = false;
                console.log(error);
            });
        };

        var updateRecipeOrder = function (sortArr) {
            recipesParams.order = sortArr.length > 0 ? sortArr : null;
            filteredByOrder = sortArr.length > 0;
            $scope.filterResults();
        };

        var updateRecipeType = function (value) {
            if (value != recipesParams.type_id) {
                recipesParams.page = 1;
            }
            recipesParams.type_id = value == 0 ? null : value;
            recipesParams.page_size = $scope.gridOptions.paginationPageSize;
            console.log('selectedRecipeType');
            if (!$scope.loading) {
                $scope.filterResults();
            }
        };

        $scope.$watch('selectedRecipeType', function (value) {
            if ($scope.loading) {
                if (filteredByRecipeType) {
                    updateRecipeType(value);
                }
            } else {
                filteredByRecipeType = value != 0;
                updateRecipeType(value);
            }
        });

        var initialize = function () {
            if (typeof $rootScope.recipeColDefs === 'undefined') {
                // root column defs have not been altered by user, so set up defaults
                if (!recipesParams.order) {
                    recipesParams.order = '-last_modified';
                    $location.search('order', recipesParams.order).replace();
                }
                if (!recipesParams.page_size) {
                    recipesParams.page_size = $scope.gridOptions.paginationPageSize;
                    $location.search('page_size', recipesParams.page_size).replace();
                }
            }
            getRecipeTypes();
            navService.updateLocation('recipes');
        };

        initialize();

        angular.element(document).ready(function(){
           // set container height equal to available page height
            var viewport = scaleService.getViewportSize();
            var offset = scaleConfig.headerOffset;
            var gridMaxHeight = viewport.height - offset;
            $scope.gridStyle = 'height: ' + gridMaxHeight + 'px; max-height: ' + gridMaxHeight + 'px;';
        });
    });
})();
