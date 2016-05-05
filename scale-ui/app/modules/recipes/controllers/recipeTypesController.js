(function () {
    'use strict';

    angular.module('scaleApp').controller('recipeTypesController', function ($rootScope, $scope, $routeParams, $location, $uibModal, hotkeys, scaleService, navService, recipeService, subnavService, jobTypeService, scaleConfig, RecipeType, userService, localStorage) {
        $scope.loading = true;
        $scope.containerStyle = '';
        $scope.recipeTypes = [];
        $scope.recipeTypeIds = [];
        $scope.requestedRecipeTypeId = parseInt($routeParams.id);
        $scope.activeRecipeType = null;
        $scope.percentage = 73;
        $scope.date = new Date();
        $scope.recipes = null;
        $scope.mode = 'view'; // valid values are add, view, and edit
        $scope.addBtnText = 'New Recipe';
        $scope.addBtnClass = 'btn-primary';
        $scope.addBtnIcon = 'fa-plus-circle';
        $scope.editBtnText = 'Edit';
        $scope.editBtnClass = 'btn-success';
        $scope.editBtnIcon = 'fa-edit';
        $scope.jobTypeValues = [];
        $scope.isRecipeModified = false;
        $scope.saveBtnClass = 'btn-default';
        $scope.masterClass = 'col-xs-3';
        $scope.detailClass = 'col-xs-9';
        $scope.minimizeMaster = false;
        $scope.minimizeBtnClass = 'fa fa-chevron-left';
        $scope.user = userService.getUserCreds();
        $scope.scaleConfig = scaleConfig;
        $scope.localRecipeTypes = [];

        $scope.subnavLinks = scaleConfig.subnavLinks.recipes;
        subnavService.setCurrentPath('recipes/types');

        var initialize = function () {
            navService.updateLocation('recipes');
            $rootScope.user = userService.getUserCreds();
            getRecipeTypes();
            //getJobTypes();
        };
        
        var getRecipeTypes = function () {
            recipeService.getRecipeTypes().then(function (data) {
                $scope.recipeTypes = data;
                if (scaleConfig.static) {
                    var i = 0,
                        oJson = {},
                        sKey;
                    for (; sKey = localStorage.key(i); i++) {
                        oJson[sKey] = localStorage.getItem(sKey);
                    }
                    _.filter(_.pairs(oJson), function (o) {
                        if (_.contains(o[0], 'recipeType')) {
                            var type = JSON.parse(o[1]);
                            $scope.localRecipeTypes.push(type);
                            $scope.recipeTypes.push(type);
                        }
                    });
                }
                $scope.recipeTypeIds = _.pluck(data, 'id');
                $scope.viewRecipeTypeDetail($scope.requestedRecipeTypeId);
                hotkeys.bindTo($scope)
                    .add({
                        combo: 'ctrl+up',
                        description: 'Previous Recipe Type',
                        callback: function () {
                            if ($scope.activeRecipeType) {
                                var idx = _.indexOf($scope.recipeTypeIds, $scope.activeRecipeType.id);
                                if (idx > 0) {
                                    $scope.loadRecipeType($scope.recipeTypeIds[idx - 1]);
                                }
                            }
                        }
                    }).add({
                        combo: 'ctrl+down',
                        description: 'Next Recipe Type',
                        callback: function () {
                            if ($scope.activeRecipeType) {
                                var idx = _.indexOf($scope.recipeTypeIds, $scope.activeRecipeType.id);
                                if (idx < ($scope.recipeTypeIds.length - 1)) {
                                    $scope.loadRecipeType($scope.recipeTypeIds[idx + 1]);
                                }
                            }
                        }
                    });
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                if ($scope.loading) {
                    $scope.loading = false;
                }
            })
        };

        $scope.clearLocalRecipeTypes = function () {
            _.forEach($scope.localRecipeTypes, function (type) {
                localStorage.removeItem('recipeType' + type.id);
            });
            $location.path('/recipes/types');
        };

        $scope.newRecipeType = function(){
            $location.path('/recipes/types/0');
        };

        $scope.viewRecipeTypeDetail = function (recipeTypeId) {
            if (recipeTypeId > 0) {
                recipeService.getRecipeTypeDetail(recipeTypeId).then(function (data) {
                    $scope.activeRecipeType = data;
                });
            } else if( recipeTypeId === 0) {
                $scope.activeRecipeType = new RecipeType();
            }
        };

        $scope.loadRecipeType = function (id) {
            if ($scope.activeRecipeType && $scope.activeRecipeType.modified) {
                confirmChangeRecipe().then(function () {
                    // OK
                    $location.path('/recipes/types/' + id);
                }, function () {
                    // Cancel

                });
            } else {
                $location.path('/recipes/types/' + id);
            }
        };

        var confirmChangeRecipe = function () {
            var modalInstance = $uibModal.open({
                animation: $scope.animationsEnabled,
                templateUrl: 'confirmDialog.html',
                scope: $scope,
                size: 'sm'
            });

            return modalInstance.result;
        };

        $scope.toggleMaster = function (minimizeMaster) {
            if (typeof minimizeMaster !== 'undefined') {
                $scope.minimizeMaster = minimizeMaster;
            } else {
                $scope.minimizeMaster = !$scope.minimizeMaster;
            }
            $scope.masterClass = $scope.minimizeMaster ? 'col-xs-1 minimized' : 'col-xs-3';
            $scope.detailClass = $scope.minimizeMaster ? 'col-xs-11' : 'col-xs-9';
            $scope.minimizeBtnClass = $scope.minimizeMaster ? 'fa fa-chevron-right' : 'fa fa-chevron-left';
        };

        $rootScope.$on('toggleEdit', function (event, data) {
            $scope.toggleMaster(data === 'edit');
        });

        initialize();

        $rootScope.$on('recipeModified', function () {
            $scope.isRecipeModified = true;
            $scope.saveBtnClass = 'btn-success';
        });

        angular.element(document).ready(function () {
            // set container heights equal to available page height
            var viewport = scaleService.getViewportSize(),
                offset = scaleConfig.headerOffset,
                containerMaxHeight = viewport.height - offset;

            $scope.containerStyle = 'height: ' + containerMaxHeight + 'px; max-height: ' + containerMaxHeight + 'px;';
        });
    });
})();