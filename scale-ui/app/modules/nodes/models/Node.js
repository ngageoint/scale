(function(){
    'use strict';

    angular.module('scaleApp').factory('Node', function (NodeResources, scaleService) {
        var Node = function (id, hostname, is_paused, is_active, archived, created, last_modified, job_exes_running, resources) {
            this.id = id;
            this.hostname = hostname;
            this.is_paused = is_paused;
            this.is_active = is_active;
            this.archived = archived;
            this.created = created;
            this.last_modified = last_modified;
            this.job_exes_running = job_exes_running;
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
                    data.is_paused,
                    data.is_active,
                    data.archived,
                    data.created,
                    data.last_modified,
                    data.job_exes_running,
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
