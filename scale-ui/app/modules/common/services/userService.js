(function () {
    'use strict';

    angular.module('scaleApp').service('userService', function (stateService) {
        return {
            getUserCreds: function(){
                var creds = localStorage.getItem('userCreds');
                try {
                    return JSON.parse(creds);
                } catch (e) {
                    console.log('Error parsing user credentials');
                    return creds;
                }
            },
            setUserCreds: function (user) {
                stateService.setUser(user);
                if (user !== null) {
                    localStorage.setItem('userCreds', JSON.stringify(user));
                } else {
                    localStorage.removeItem('userCreds');
                }

            },
            login: function (username) {
                var user = {
                    username: username,
                    is_admin: true
                };
                this.setUserCreds(user);
                return user;
            },
            logout: function () {
                this.setUserCreds(null);
            }
        }
    });
})();
