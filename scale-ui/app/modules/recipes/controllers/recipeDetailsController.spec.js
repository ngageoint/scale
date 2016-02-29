describe('recipeDetailsController', function () {
    beforeEach(module('scaleApp'));

    var recipeDetailsController;
    var $scope;
    var $controller;

    beforeEach(inject(function ($injector, $q) {
        var recipeDetails = readJSON('app/test/data/recipeDetailComplex.json');
        var recipeTypeDetail = readJSON('app/test/data/recipeTypeDetail.json');

        var rs  = {
            getRecipeDetails: function () {
                return $q.when(recipeDetails);
            },
            getRecipeTypeDetail: function(){
                return $q.when(recipeTypeDetail);
            }
        };

        $scope = $injector.get('$rootScope').$new();
        $controller = $injector.get('$controller');
        recipeDetailsController = $controller('recipeDetailsController', { $scope: $scope, recipeService: rs });
    }));

    it ('is defined', function () {
        expect(recipeDetailsController).toBeDefined();
    });

    it ('should have recipe object', function () {
        expect($scope.recipe).toEqual({});
    });

});