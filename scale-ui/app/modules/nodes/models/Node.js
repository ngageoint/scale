(function(){
    'use strict';

    angular.module('scaleApp').factory('Node', function (NodeResources, scaleService) {
        var Node = function (id, hostname, pause_reason, is_paused, is_active, deprecated, created, last_modified) {
            this.id = id;
            this.hostname = hostname;
            this.pause_reason = pause_reason;
            this.is_paused = is_paused;
            this.is_active = is_active;
            this.deprecated = deprecated;
            this.created = created;
            this.last_modified = last_modified;
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
            },
            isPaused: function () {
                return this.is_paused;
            }
        };

        // static methods, assigned to class
        Node.build = function (data) {
            if (data) {
                return new Node(
                    data.id,
                    data.hostname,
                    data.pause_reason,
                    data.is_paused,
                    data.is_active,
                    data.deprecated,
                    data.created,
                    data.last_modified
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
