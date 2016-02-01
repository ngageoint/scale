describe('jobsController', function() {
    beforeEach(module('scaleApp'));

    var jobsController;
    var $scope;
    var $_modal_;

    beforeEach(inject(function($rootScope, $controller, $modal){
        $scope = $rootScope.$new();
        $_modal_ = $modal;
        jobsController = $controller('jobsController', { $scope: $scope });
    }));

    it('should be defined.', function() {
        expect(jobsController).toBeDefined();
    });

    it('should not have a job execution upon startup', function() {
        expect($scope.jobExecution).toBe(null);
    });

    it('should be able to launch a modal window', function() {
        expect($_modal_).toBeDefined();
    });

    it('')

});