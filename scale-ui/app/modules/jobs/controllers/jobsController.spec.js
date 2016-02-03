describe('jobsController', function () {
    beforeEach(module('scaleApp'));

    var jobsController;
    var $scope;
    var $controller;
    var $modal;
    var $location;

    beforeEach(inject(function ($injector, $q, Job, JobDetails) {
        var jobs = readJSON('app/test/data/jobs.json'),
            jobTypes = readJSON('app/test/data/jobTypes.json'),
            jobDetail = readJSON('app/test/data/jobDetails.json');

        $scope = $injector.get('$rootScope').$new();
        $controller = $injector.get('$controller');
        $location = $injector.get('$location');
        $modal = jasmine.createSpyObj('modal', ['open']);

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

        jobsController = $controller('jobsController', { $scope: $scope, jobService: _jobService_, jobTypeService: _jobTypeService_, $modal: $modal, $location: $location });
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

        it ('should update the job type filter and get filtered results', function () {
            spyOn(jobsController, 'getJobs');
            $scope.selectedJobType = 73;

            $scope.$digest();

            expect(jobsController.jobsParams.job_type_id).toEqual(73);
            expect(jobsController.jobsParams.page).toEqual(1);
            expect($location.search().job_type_id).toEqual(73);
            expect(jobsController.getJobs).toHaveBeenCalled();

            jobsController.getJobs.calls.reset();
        });

        it ('should update the job status filter and get filtered results', function () {
            spyOn(jobsController, 'getJobs');
            $scope.selectedJobStatus = 'COMPLETED';

            $scope.$digest();

            expect(jobsController.jobsParams.status).toEqual('COMPLETED');
            expect(jobsController.jobsParams.page).toEqual(1);
            expect($location.search().status).toEqual('COMPLETED');
            expect(jobsController.getJobs).toHaveBeenCalled();

            jobsController.getJobs.calls.reset();
        });

        it ('should show a log', function () {
            $scope.showLog();

            // since we're calling the function directly (and not relying on the controller lifecycle for execution),
            // call digest to execute callbacks
            $scope.$digest();

            expect($scope.selectedJob).toBeDefined();
            expect($scope.jobExecution).not.toBeNull();
            expect($modal.open).toHaveBeenCalled();
        });
    });
});