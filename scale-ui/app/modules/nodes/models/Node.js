(function(){
    'use strict';

    angular.module('scaleApp').factory('Node', function (NodeResources, scaleService) {
        var Node = function (id, hostname, port, slave_id, pause_reason, is_paused, is_paused_errors, is_active, archived, created, last_offer, last_modified, resources) {
            this.id = id;
            this.hostname = hostname;
            this.port = port;
            this.slave_id = slave_id;
            this.pause_reason = pause_reason;
            this.is_paused = is_paused;
            this.is_paused_errors = is_paused_errors;
            this.is_active = is_active;
            this.archived = archived;
            this.created = created;
            this.last_offer = last_offer;
            this.last_modified = last_modified;
            this.resources = NodeResources.transformer(resources);
        };

        //public methods
        Node.prototype = {
            toString: function () {
                return 'Node';
            },
            getDuration: function () {
                return scaleService.calculateDuration(this.created, this.last_modified);
            },
            getCellText: function () {
                // this is only used reveal = true on gridChart directive
                return this.hostname;
            },
            getCellTitle: function () {
                return this.hostname;
            }
        };

        // static methods, assigned to class
        Node.build = function (data) {
            if (data) {
                return new Node(
                    data.id,
                    data.hostname,
                    data.port,
                    data.slave_id,
                    data.pause_reason,
                    data.is_paused,
                    data.is_paused_errors,
                    data.is_active,
                    data.archived,
                    data.created,
                    data.last_offer,
                    data.last_modified,
                    data.resources
                );
            }
            return new Node();
        };

        Node.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(Node.build);
            }
            return Node.build(data);
        };

        return Node;
    });
})();
