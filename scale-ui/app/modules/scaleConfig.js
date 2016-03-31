(function () {
    'use strict';

    angular.module('scaleConfigModule', []).provider('scaleConfig', function () {
        var scaleConfig = {},
            scaleConfigLocal = {};

        this.$get = function () {
            var config = $.ajax({
                type: 'GET',
                url: '/config/scaleConfig.json',
                cache: false,
                async: false,
                contentType: 'application/json',
                dataType: 'json'
            });
            
            if (config.status === 200) {
                scaleConfig = config.responseJSON.scaleConfig;

                var configLocal = $.ajax({
                    type: 'GET',
                    url: '/config/scaleConfig.local.json',
                    cache: false,
                    async: false,
                    contentType: 'application/json',
                    dataType: 'json'
                });

                if (configLocal.status === 200) {
                    scaleConfigLocal = configLocal.responseJSON.scaleConfigLocal;
                }

                _.merge(scaleConfig, scaleConfigLocal);
            }

            return scaleConfig;
        }
    });
})();
