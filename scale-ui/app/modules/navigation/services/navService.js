(function () {
    'use strict';
    /**
     * See: http://stackoverflow.com/questions/12576798/angularjs-how-to-watch-service-variables/17558885#17558885
     * Doing things this way so that ssNavbarController can get notified
     * when the location changes. Then, our controllers just need to call into
     * this service to updateLocation.
     *
     * The only thing I don't like about this is that the individual
     * controllers have to call in and tell the ssNavigationService what
     * page they are showing.
     */
    angular.module('scaleApp').service('navService', function ($location) {

        this.location = 'overview'; // where the app starts

        var observers = [];

        this.registerObserver = function(callback) {
            observers.push(callback);
        };

        this.notifyObservers = function() {
            angular.forEach(observers, function(observer) {
                observer();
            });
        };

        this.updateLocation = function(locationIn) {
            this.location = locationIn;
            this.notifyObservers();
        };

    });
})();
