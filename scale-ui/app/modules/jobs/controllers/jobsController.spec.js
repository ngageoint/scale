describe('jobsController', function() {
    beforeEach(module('scaleApp'));

    var jobsController;
    var $scope;

    beforeEach(inject(function($rootScope, $controller){
        $scope = $rootScope.$new();
        jobsController = $controller('jobsController', { $scope: $scope });
    }));

    it(' is defined', function() {
        expect(jobsController).toBeDefined();
    });

});