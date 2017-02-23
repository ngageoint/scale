(function () {
    'use strict';

    angular.module('scaleApp').controller('batchDetailsController', function ($scope, $routeParams, scaleConfig, subnavService, userService, batchService, recipeService, jobTypeService, Batch, toastr) {
        var vm = this;

        vm.loading = false;
        vm.subnavLinks = scaleConfig.subnavLinks.batch;
        vm.mode = $routeParams.id > 0 ? 'details' : 'create';
        vm.name = $routeParams.id > 0 ? 'Batch Details' : null;
        vm.readonly = true;
        vm.saveBtnClass = 'btn-default';
        vm.batch = $routeParams.id > 0 ? {} : new Batch();
        vm.recipeTypes = [];
        vm.selectedRecipeType = {};
        vm.jobTypes = [];
        vm.selectedJobTypes = [];
        vm.dateModelOptions = {
            timezone: '+000'
        };
        vm.dateRangeStartedPopup = {
            opened: false
        };
        vm.openDateRangeStartedPopup = function ($event) {
            $event.stopPropagation();
            vm.dateRangeStartedPopup.opened = true;
        };
        vm.dateRangeEndedPopup = {
            opened: false
        };
        vm.openDateRangeEndedPopup = function ($event) {
            $event.stopPropagation();
            vm.dateRangeEndedPopup.opened = true;
        };

        subnavService.setCurrentPath(vm.mode === 'create' ? 'batch/0' : 'batch');

        vm.disableSaveBtn = function (invalid) {
            var returnVal = !(!invalid);
            vm.saveBtnClass = returnVal ? 'btn-default' : 'btn-success';
            return returnVal;
        };

        var getWarningsHtml = function (warnings) {
            var warningsHtml = '';
            _.forEach(warnings, function (warning) {
                warningsHtml += '<b>' + warning.id + ':</b> ' + warning.details + '<br /><br />';
            });
            warningsHtml += '<button type="button" class="btn btn-default btn-xs clear">Hide</button>';
            return warningsHtml;
        };

        vm.validateBatch = function () {
            vm.loading = true;
            batchService.validateBatch(vm.batch).then(function (data) {
                if (data.warnings && data.warnings.length > 0) {
                    // display the warnings
                    var warningsHtml = getWarningsHtml(data.warnings);
                    toastr['error'](warningsHtml);
                } else {
                    toastr['success']('Batch is valid.');
                }
            }).catch(function (error) {
                if (error && error.detail) {
                    toastr['error'](error.detail);
                } else {
                    toastr['error']('Error validating batch');
                }
            }).finally(function () {
                vm.loading = false;
            });
        };

        var getRecipeTypes = function () {
            recipeService.getRecipeTypes().then(function (data) {
                vm.recipeTypes = data.results;
            }).catch(function (e) {
                console.log('Error retrieving recipe types: ' + e);
            });
        };

        var getJobTypes = function () {
            jobTypeService.getJobTypesOnce().then(function (data) {
                _.forEach(data.results, function (result) {
                    vm.jobTypes.push({
                        label: result.title,
                        title: result.title,
                        value: result.name
                    });
                });
            }).catch(function (e) {
                console.log('Error retrieving job types: ' + e);
            });
        };

        var initialize = function () {
            var user = userService.getUserCreds();
            vm.readonly = !(user && user.is_admin);
            getRecipeTypes();
            getJobTypes();
        };

        initialize();
    });
})();
