describe('jobsController', function() {
    beforeEach(module('scaleApp'));

    var jobsController;
    var $scope;

    beforeEach(inject(function($rootScope, $controller){
        $scope = $rootScope.$new();
        jobsController = $controller('jobsController', { $scope: $scope });
    }));

    it('should be defined.', function() {
        expect(jobsController).toBeDefined();
    });

    it('should not have a job execution upon startup', function() {
        expect($scope.jobExecution).toBe(null);
    });

    it('')

});