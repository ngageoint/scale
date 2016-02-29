(function(){
    'use strict';

    angular.module('scaleApp').factory('NodeResources', function(){
        var NodeResources = function (cpus, mem, disk) {
            this.cpus = cpus;
            this.mem = mem;
            this.disk = disk;
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
                    data.cpus,
                    data.mem,
                    data.disk
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
