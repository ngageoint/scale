(function () {
    'use strict';

    angular.module('scaleApp').service('workspacesService', function ($http, $q, $resource, scaleConfig) {
        return {
            getWorkspaces: function () {
                var d = $q.defer();
                var url = scaleConfig.urls.apiPrefix + 'workspaces/';

                $http({
                    url: url,
                    method: 'GET',
                    params: { order: '-title' }
                }).success(function (data) {
                    d.resolve(data.results);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;
            },
            getWorkspaceDetails: function (id) {
                var d = $q.defer();
                var url = scaleConfig.urls.apiPrefix + 'workspaces/' + id + '/';

                $http({
                    url: url,
                    method: 'GET'
                }).success(function (data) {
                    d.resolve(data);
                }).error(function (error) {
                    d.reject(error);
                });
                return d.promise;

            },
            validateWorkspace: function (workspace) {
                var d = $q.defer();
                var cleanWorkspace = workspace.clean();

                $http.post(scaleConfig.urls.apiPrefix + 'workspaces/validation/', cleanWorkspace).success(function (result) {
                    d.resolve(result);
                }).error(function(error){
                    d.reject(error);
                });

                return d.promise;
            },
            saveWorkspace: function (workspace) {
                var d = $q.defer();

                if (!workspace.id) {
                    $http.post(scaleConfig.urls.apiPrefix + 'workspaces/', workspace.clean()).success(function (result) {
                        d.resolve(result);
                    }).error(function (error) {
                        d.reject(error);
                    });
                } else {
                    $http.patch(scaleConfig.urls.apiPrefix + 'workspaces/' + workspace.id + '/', workspace.clean()).success(function (result) {
                        workspace = result;
                        d.resolve(workspace);
                    }).error(function (error) {
                        d.reject(error);
                    });
                }

                return d.promise;
            }
        };
    });
})();
