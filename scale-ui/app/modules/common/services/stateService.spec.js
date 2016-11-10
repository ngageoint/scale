describe('stateService', function () {
  beforeEach(module('scaleApp'));

  var stateService = {};
  var $scope;
  var $controller;
  var $uibModal;
  var $location;

  beforeEach(inject(function ($injector, _stateService_) {

    $scope = $injector.get('$rootScope').$new();
    $controller = $injector.get('$controller');
    $location = $injector.get('$location');
    $uibModal = jasmine.createSpyObj('modal', ['open']);

    stateService = _stateService_;

  }));

  it ('should be defined.', function () {
    expect(stateService).toBeDefined();
  });

  it ('should initialize jobTypesParams.show_rd to true', function () {
    var jobTypesParams = stateService.getJobTypesParams();
    expect(jobTypesParams.show_rd).toEqual(true);
  });

  it ('should update location.query_string.show_rd=false', function () {
    var jobTypesParams = stateService.getJobTypesParams();
    jobTypesParams.show_rd = false;
    stateService.setJobTypesParams(jobTypesParams);
    expect($location.search().show_rd).toEqual(false);
  });

  it ('should update location.query_string.show_rd=true', function () {
    var jobTypesParams = stateService.getJobTypesParams();
    jobTypesParams.show_rd = true;
    stateService.setJobTypesParams(jobTypesParams);
    expect($location.search().show_rd).toEqual(true);
  });

});