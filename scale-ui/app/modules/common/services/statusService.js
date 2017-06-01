(function () {
    'use strict';

    angular.module('scaleApp').service('statusService', function ($resource, scaleConfig, poller, pollerFactory, Status) {
        return {
            getStatus: function (isNodeStatus) {
                isNodeStatus = isNodeStatus || false;
                var statusResource = isNodeStatus ? $resource(scaleConfig.getUrlPrefix('nodeStatus') + 'status/') : $resource(scaleConfig.getUrlPrefix('status') + 'status/'),
                    statusPoller = isNodeStatus ? pollerFactory.newPoller(statusResource, scaleConfig.pollIntervals.nodeStatus) : pollerFactory.newPoller(statusResource, scaleConfig.pollIntervals.status);

                return statusPoller.promise.then(null, null, function (result) {
                    if (result.$resolved) {
                        result = isNodeStatus ? result : Status.transformer(result);
                    } else {
                        statusPoller.stop();
                    }
                    return result;
                });
            }
        }
    });
})();
