(function () {
    'use strict';

    angular.module('scaleApp').service('statusService', function ($resource, scaleConfig, poller, pollerFactory, Status) {
        return {
            getStatus: function () {
                var statusResource = $resource(scaleConfig.getUrlPrefix('status') + 'status/'),
                    statusPoller = pollerFactory.newPoller(statusResource, scaleConfig.pollIntervals.status);

                return statusPoller.promise.then(null, null, function (result) {
                    if (result.$resolved) {
                        result = Status.transformer(result);
                    } else {
                        statusPoller.stop();
                    }
                    return result;
                });
            }
        }
    });
})();