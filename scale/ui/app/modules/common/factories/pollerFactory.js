(function () {
    'use strict';

    angular.module('scaleApp').factory('pollerFactory', function (poller) {
        return {
            newPoller: function (resource, interval) {
                return poller.get(resource, {
                    delay: interval,
                    catchError: true
                });
            }
        }
    });
})();