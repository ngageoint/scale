(function () {
    'use strict';

    angular.module('scaleApp').controller('recipeTypesController', function ($rootScope, $scope, $routeParams, $location, $uibModal, hotkeys, scaleService, navService, recipeService, subnavService, jobTypeService, scaleConfig, RecipeType, userService, localStorage) {
        var vm = this;
        
        vm.loading = true;
        vm.containerStyle = '';
        vm.recipeTypes = [];
        vm.recipeTypeIds = [];
        vm.requestedRecipeTypeId = parseInt($routeParams.id);
        vm.activeRecipeType = null;
        vm.percentage = 73;
        vm.date = new Date();
        vm.recipes = null;
        vm.mode = 'view'; // valid values are add, view, and edit
        vm.addBtnText = 'New Recipe';
        vm.addBtnClass = 'btn-primary';
        vm.addBtnIcon = 'fa-plus-circle';
        vm.editBtnText = 'Edit';
        vm.editBtnClass = 'btn-success';
        vm.editBtnIcon = 'fa-edit';
        vm.jobTypeValues = [];
        vm.isRecipeModified = false;
        vm.saveBtnClass = 'btn-default';
        vm.masterClass = 'col-xs-3';
        vm.detailClass = 'col-xs-9';
        vm.minimizeMaster = false;
        vm.minimizeBtnClass = 'fa fa-chevron-left';
        vm.user = userService.getUserCreds();
        vm.scaleConfig = scaleConfig;
        vm.localRecipeTypes = [];

        vm.subnavLinks = scaleConfig.subnavLinks.recipes;
        subnavService.setCurrentPath('recipes/types');

        var initialize = function () {
            navService.updateLocation('recipes');
            getRecipeTypes();
        };
        
        var getRecipeTypes = function () {
            recipeService.getRecipeTypes().then(function (data) {
                vm.recipeTypes = data.results;
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
                            vm.localRecipeTypes.push(type);
                            vm.recipeTypes.push(type);
                        }
                    });
                }
                vm.recipeTypeIds = _.pluck(data, 'id');
                vm.viewRecipeTypeDetail(vm.requestedRecipeTypeId);
                hotkeys.bindTo($scope)
                    .add({
                        combo: 'ctrl+up',
                        description: 'Previous Recipe Type',
                        callback: function () {
                            if (vm.activeRecipeType) {
                                var idx = _.indexOf(vm.recipeTypeIds, vm.activeRecipeType.id);
                                if (idx > 0) {
                                    vm.loadRecipeType(vm.recipeTypeIds[idx - 1]);
                                }
                            }
                        }
                    }).add({
                        combo: 'ctrl+down',
                        description: 'Next Recipe Type',
                        callback: function () {
                            if (vm.activeRecipeType) {
                                var idx = _.indexOf(vm.recipeTypeIds, vm.activeRecipeType.id);
                                if (idx < (vm.recipeTypeIds.length - 1)) {
                                    vm.loadRecipeType(vm.recipeTypeIds[idx + 1]);
                                }
                            }
                        }
                    });
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                if (vm.loading) {
                    vm.loading = false;
                }
            })
        };

        vm.clearLocalRecipeTypes = function () {
            _.forEach(vm.localRecipeTypes, function (type) {
                localStorage.removeItem('recipeType' + type.id);
            });
            $location.path('/recipes/types');
        };

        vm.newRecipeType = function(){
            $location.path('/recipes/types/0');
        };

        vm.viewRecipeTypeDetail = function (recipeTypeId) {
            if (recipeTypeId > 0) {
                recipeService.getRecipeTypeDetail(recipeTypeId).then(function (data) {
                    vm.activeRecipeType = data;
                });
            } else if( recipeTypeId === 0) {
                vm.activeRecipeType = new RecipeType();
            }
        };

        vm.loadRecipeType = function (id) {
            if (vm.activeRecipeType && vm.activeRecipeType.modified) {
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
                animation: vm.animationsEnabled,
                templateUrl: 'confirmDialog.html',
                scope: $scope,
                size: 'sm'
            });

            return modalInstance.result;
        };

        vm.toggleMaster = function (minimizeMaster) {
            if (typeof minimizeMaster !== 'undefined') {
                vm.minimizeMaster = minimizeMaster;
            } else {
                vm.minimizeMaster = !vm.minimizeMaster;
            }
            vm.masterClass = vm.minimizeMaster ? 'col-xs-1 minimized' : 'col-xs-3';
            vm.detailClass = vm.minimizeMaster ? 'col-xs-11' : 'col-xs-9';
            vm.minimizeBtnClass = vm.minimizeMaster ? 'fa fa-chevron-right' : 'fa fa-chevron-left';
        };

        $rootScope.$on('toggleEdit', function (event, data) {
            vm.toggleMaster(data === 'edit');
        });

        initialize();

        $rootScope.$on('recipeModified', function () {
            vm.isRecipeModified = true;
            vm.saveBtnClass = 'btn-success';
        });

        angular.element(document).ready(function () {
            // set container heights equal to available page height
            var viewport = scaleService.getViewportSize(),
                offset = scaleConfig.headerOffset,
                containerMaxHeight = viewport.height - offset;

            vm.containerStyle = 'height: ' + containerMaxHeight + 'px; max-height: ' + containerMaxHeight + 'px;';
        });
    });
})();