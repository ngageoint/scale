describe('Toggle Switch', function() {
  var $scope, $compile;

  var baseTemplate = '<toggle-switch ng-model="switchState">\n</toggle-switch>';
  var onLabelTemplate = '<toggle-switch ng-model="switchState" on-label="CUSTOM-ON">\n</toggle-switch>';
  var offLabelTemplate = '<toggle-switch ng-model="switchState" off-label="CUSTOM-OFF">\n</toggle-switch>';
  var knobLabelTemplate = '<toggle-switch ng-model="switchState" knob-label="CUSTOM">\n</toggle-switch>';
  var htmlLabelsTemplate = '<toggle-switch ng-model="switchState" on-label="<i class=\'icon-ok icon-white\'></i>" off-label="<i class=\'icon-remove\'></i>">\n</toggle-switch>';
  var disabledTemplate = '<toggle-switch ng-model="switchState" is-disabled="isDisabled">\n</toggle-switch>';
  var changeTemplate = '<toggle-switch ng-model="switchState" ng-change="changedState()">\n</toggle-switch>';
  var tabindexTemplate = '<toggle-switch ng-model="switchState" tabindex="2">\n</toggle-switch>';

  // Load up just our module
  beforeEach(module('toggle-switch'));

  beforeEach(inject(function($rootScope, _$compile_) {
    // Get an isolated scope
    $scope = $rootScope.$new();
    $compile = _$compile_;
  }));

  function compileDirective(template, scope) {
    // Compile Directive
    var elm = angular.element(template);
    $compile(elm)(scope);
    scope.$apply();
    return elm;
  }

  describe('default labels', function() {
    var elm;

    beforeEach(function() {
      elm = compileDirective(baseTemplate, $scope);
    });

    it('onLabel', function() {
      expect(elm.text()).toContain('On');
    });

    it('offLabel', function() {
      expect(elm.text()).toContain('Off');
    });
  });

  describe('when state is null', function() {
    it('changes model to true when clicked', function() {
      var elm = compileDirective(baseTemplate, $scope);
      elm.triggerHandler('click');
      expect($scope.switchState).toEqual(true);
    });
  });

  describe('when state is true', function() {
    // Change state to true
    beforeEach(function() {
      $scope.$apply(function() {
        $scope.switchState = true;
      });
      $scope.changedState = function(){};
      spyOn($scope, 'changedState');
    });

    it('changes model to false when clicked', function() {
      var elm = compileDirective(baseTemplate, $scope);
      elm.triggerHandler('click');
      expect($scope.switchState).toEqual(false);
    });

    it('change handler is called when clicked', function() {
      var elm = compileDirective(changeTemplate, $scope);
      elm.triggerHandler('click');
      expect($scope.changedState).toHaveBeenCalled();
    });
  });

  describe('when state is false', function() {
    // Change state to true
    beforeEach(function() {
      $scope.$apply(function() {
        $scope.switchState = false;
      });
      $scope.changedState = function(){};
      spyOn($scope, 'changedState');
    });

    it('changes model to true when clicked', function() {
      var elm = compileDirective(baseTemplate, $scope);
      elm.triggerHandler('click');
      expect($scope.switchState).toEqual(true);
    });

    it('change handler is called when clicked', function() {
      var elm = compileDirective(changeTemplate, $scope);
      elm.triggerHandler('click');
      expect($scope.changedState).toHaveBeenCalled();
    });
  });

  describe('when a key is pressed', function() {
    // Change state to true
    beforeEach(function() {
      $scope.$apply(function() {
        $scope.switchState = false;
      });
      $scope.changedState = function(){};
      spyOn($scope, 'changedState');
    });

    it('and it is "space" change handler gets called', function() {
      var elm = compileDirective(changeTemplate, $scope);
      var event = {
        type: 'keypress',
        charCode: 32
      };
      elm.triggerHandler(event);
      expect($scope.changedState).toHaveBeenCalled();
    });

    it('and it is "space" but modifier is set do not call change handler', function() {
      var elm = compileDirective(changeTemplate, $scope);
      var event = {
        type: 'keypress',
        charCode: 32,
        ctrlKey: true
      };
      elm.triggerHandler(event);
      expect($scope.changedState).not.toHaveBeenCalled();
    });

    it('and it is not "space" do not call change handler', function() {
      var elm = compileDirective(changeTemplate, $scope);
      var event = {
        type: 'keypress',
        charCode: 12
      };
      elm.triggerHandler(event);
      expect($scope.changedState).not.toHaveBeenCalled();
    });
  });

  describe('when there is a custom `on-label`', function () {
    // @TODO: figure out how to deal with html in Angular 1.2
    //describe('is html', function() {
    //  it('sets the on label', function() {
    //    var elm = compileDirective(htmlLabelsTemplate, $scope);
    //    expect(elm.html()).toContain('<i class="icon-ok icon-white"></i>');
    //  });
    //});

    describe('is string', function() {
      it('sets the on label', function() {
        var elm = compileDirective(onLabelTemplate, $scope);
        expect(elm.text()).toContain('CUSTOM-ON');
      });
    });
  });

  describe('when there is a custom `off-label`', function () {
    // @TODO: figure out how to deal with html in Angular 1.2
    //describe('is html', function() {
    //  it('sets the on label', function() {
    //    var elm = compileDirective(htmlLabelsTemplate, $scope);
    //    expect(elm.html()).toContain('<i class="icon-remove"></i>');
    //  });
    //});

    describe('is string', function() {
      it('sets the on label', function() {
        var elm = compileDirective(offLabelTemplate, $scope);
        expect(elm.text()).toContain('CUSTOM-OFF');
      });
    });
  });

  describe('when there is a custom `knob-label`', function () {
    it('sets the on label', function() {
      var elm = compileDirective(knobLabelTemplate, $scope);
      expect(elm.text()).toContain('CUSTOM');
    });
  });

  describe('when toggle is disabled', function() {
    it('ngModel does not change on click', function() {
      $scope.switchState = true;
      $scope.isDisabled = true;
      var elm = compileDirective(disabledTemplate, $scope);
      elm.triggerHandler('click');
      expect($scope.switchState).toEqual(true);
    });
  });

  describe('tabindex is set', function() {
    it('to default value', function() {
      var elm = compileDirective(baseTemplate, $scope);
      expect(elm.attr('tabindex')).toEqual('0');
    });

    it('to custom value', function() {
      var elm = compileDirective(tabindexTemplate, $scope);
      expect(elm.attr('tabindex')).toEqual('2');
    });
  });
});
