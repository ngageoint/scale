(function(){
    'use strict';

    angular.module('scaleApp').factory('NodeResources', function(){
        var NodeResources = function (total, scheduled, used) {
            this.total = total;
            this.scheduled = scheduled;
            this.used = used;
        };

        //public methods
        NodeResources.prototype = {
            // getDuration: function() {
                //return scaleService.calculateDuration(this.created, this.last_modified);
            // }
        };

        // static methods, assigned to class
        NodeResources.build = function (data) {
            if (data) {
                return new NodeResources(
                    data.total,
                    data.scheduled,
                    data.used
                );
            }
            return new NodeResources();
        };

        NodeResources.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(NodeResources.build)
                    .filter(Boolean);
            }
            return NodeResources.build(data);
        };

        return NodeResources;
    });
})();
