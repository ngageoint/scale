(function () {
    'use strict';

    angular.module('scaleApp').directive('aisMultiselect', function () {
        return {
            restrict: 'A',
            require: '^ngModel',
            scope: {
                multiselectDataProvider: '=',
                enableFiltering: '=',
                maxHeight: '=',
                numberDisplayed: '=',
                includeSelectAllOption: '=',
                nonSelectedText: '=',
                ngModel: '='
            },
            link: function(scope, element, attributes) {
                element = $(element[0]);

                element.multiselect({
                    enableFiltering: scope.enableFiltering,
                    enableCaseInsensitiveFiltering: true,
                    maxHeight: scope.maxHeight || 300,
                    numberDisplayed: scope.numberDisplayed || 3,
                    includeSelectAllOption: scope.includeSelectAllOption,
                    nonSelectedText: scope.nonSelectedText || 'None Selected',
                    onChange: function (optionElement, checked) {
                        scope.$apply(function () {
                            scope.ngModel = element.val();
                        });
                    }
                });

                scope.$watchCollection('multiselectDataProvider', function (newValue, oldValue) {
                    if (angular.equals(newValue, oldValue)) {
                        return;
                    }
                    element.multiselect('dataprovider', newValue);
                });

                /*
                // Watch for any changes to the length of our select element
                scope.$watch(function () {
                    return element[0];
                }, function (newValue) {
                    debugger;
                    //element.multiselect('setOptions', element[0]);
                    //element.multiselect('rebuild');
                }, true);

                // Watch for any changes from outside the directive and refresh
                scope.$watch(attributes.ngModel, function () {
                    element.multiselect('refresh');
                });
                */
            }
        };
    })
})();
