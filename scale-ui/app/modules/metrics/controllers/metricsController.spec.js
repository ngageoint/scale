describe('metricsController', function () {
    beforeEach(module('scaleApp'));

    var metricsController;
    var $scope;
    var $controller;
    var initChart;

    beforeEach(inject(function ($injector, $q) {
        var dataTypes = readJSON('app/test/data/metrics.json'),
            dataTypeOptions = readJSON('app/test/data/metricsJobTypes.json'),
            plotData = readJSON('app/test/data/metricsJobTypesPlotData.json');

        var ms  = {
            getDataTypes: function () {
                return $q.when(dataTypes);
            },
            getDataTypeOptions: function () {
                return $q.when(dataTypeOptions);
            },
            getPlotData: function () {
                return $q.when(plotData);
            }
        };

        $scope = $injector.get('$rootScope').$new();
        $controller = $injector.get('$controller');
        metricsController = $controller('metricsController', { $scope: $scope, metricsService: ms });
    }));

    it ('is defined', function () {
        expect(metricsController).toBeDefined();
    });

    it ('should have undefined availableDataTypes array', function () {
        expect($scope.availableDataTypes).toBeUndefined();
    });

    it ('should have an empty columns array', function () {
        expect($scope.columns.length).toEqual(0);
    });

    it ('should have empty chartArr and chartData arrays', function () {
        expect($scope.chartArr.length).toEqual(0);
        expect($scope.chartData.length).toEqual(0);
    });

    describe('afterActivation', function () {
        beforeEach(function () {
            $scope.$apply();
            spyOn(metricsController, 'initChart');
        });

        afterEach(function () {
            metricsController.initChart.calls.reset();
        });

        it ('should have availableDataTypes', function () {
            expect($scope.availableDataTypes.length).toBeGreaterThan(0);
        });

        it ('should update chart when addToChart is called', function () {
            $scope.addToChart();

            // since we're calling the function directly (and not relying on the controller lifecycle for execution),
            // call digest to execute callbacks
            $scope.$digest();

            expect(metricsController.initChart).toHaveBeenCalled();
            expect($scope.chartArr.length).toEqual(1);
            expect($scope.chartData.length).toEqual(1);
        });

        it ('should populate filters, columns, and groups when a data type is selected', function () {
            $scope.selectedDataType = $scope.availableDataTypes[0];
            $scope.changeDataTypeSelection();

            // since we're calling the function directly (and not relying on the controller lifecycle for execution),
            // call digest to execute callbacks
            $scope.$digest();

            expect($scope.filteredChoices.length).toBeGreaterThan(0);
            expect($scope.filteredChoicesOptions.length).toBeGreaterThan(0);
            expect($scope.columns.length).toBeGreaterThan(0);
            expect($scope.groups.length).toBeGreaterThan(0);
            expect($scope.columnGroupsOptions.length).toBeGreaterThan(0);
        });
    });
});