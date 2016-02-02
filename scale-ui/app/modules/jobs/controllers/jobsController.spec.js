describe('jobsController', function () {
    beforeEach(module('scaleApp'));

    var jobsController;
    var $scope;
    var $controller;
    var $modal;

    beforeEach(inject(function ($injector, $q, JobDetails) {
        var jobs = readJSON('app/test/data/jobs.json'),
            jobTypes = readJSON('app/test/data/jobTypes.json'),
            jobDetail = readJSON('app/test/data/jobDetails.json');

        $scope = $injector.get('$rootScope').$new();
        $controller = $injector.get('$controller');
        $modal = $injector.get('$modal');

        var _jobService_  = {
            getJobsOnce: function () {
                return $q.when(jobs);
            },
            getJobDetail: function () {
                return $q.when(JobDetails.transformer(jobDetail));
            }
        };

        var _jobTypeService_ = {
            getJobTypesOnce: function () {
                return $q.when(jobTypes);
            }
        };

        jobsController = $controller('jobsController', { $scope: $scope, jobService: _jobService_, jobTypeService: _jobTypeService_ });
    }));

    it ('should be defined.', function () {
        expect(jobsController).toBeDefined();
    });

    it ('should not have a job execution', function() {
        expect($scope.jobExecution).toBe(null);
    });

    it ('should be able to launch a modal window', function() {
        expect($modal).toBeDefined();
    });

    describe('afterActivation', function () {
        beforeEach(function () {
            $scope.$apply();
            //spyOn($modal, 'open');
            //spyOn(jobsController, 'getJobTypes');
        });

        //afterEach(function () {
        //    jobsController.getJobTypes.calls.reset();
        //});

        it ('should get job types', function () {
            $scope.$digest();

            expect($scope.jobTypeValues.length).toBeGreaterThan(0);
            expect($scope.jobsData.length).toBeGreaterThan(0);
        });

        //it ('should show a log', function () {
        //    $scope.showLog();
        //    $scope.$digest();
        //
        //    expect($scope.selectedJob).toBeDefined();
        //    expect($scope.jobExecution).not.toBeNull();
        //    expect($modal).toHaveBeenCalled();
        //});

    });
});