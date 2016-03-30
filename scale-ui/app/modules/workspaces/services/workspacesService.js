(function () {
    'use strict';

    angular.module('scaleApp').service('workspacesService', function($http, $q, $resource, scaleConfig) {

        return {
            getWorkspaces: function () {
                var d = $q.defer();
                var url = scaleConfig.urls.apiPrefix + 'workspaces/';

                $http({
                    url: url,
                    method: 'GET'
                }).success(function (data) {
                    d.resolve(data.results);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            }//,
            //getWorkspaceDetails: function(id) {
            //
            //}
        };
    });
})();
