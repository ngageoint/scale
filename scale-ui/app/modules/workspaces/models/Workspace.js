(function () {
    'use strict';

    angular.module('scaleApp').factory('Workspace', function (scaleConfig) {
        var Workspace = function (id, name, title, description, base_url, is_active, used_size, total_size, created, archived, last_modified, json_config) {
            this.id = id;
            this.name = name;
            this.title = title;
            this.description = description;
            this.base_url = base_url;
            this.is_active = is_active;
            this.used_size = used_size;
            this.total_size = total_size;
            this.created = created;
            this.archived = archived;
            this.last_modified = last_modified;
            this.json_config = json_config || scaleConfig.workspaceTypes[0];
        };

        Workspace.prototype = {
            clean: function () {
                return {
                    name: this.name,
                    title: this.title,
                    description: this.description,
                    base_url: this.base_url,
                    is_active: this.is_active,
                    json_config: this.json_config
                };
            }
        };

        // static methods, assigned to class
        Workspace.build = function (data) {
            if (data) {
                return new Workspace(
                    data.id,
                    data.name,
                    data.title,
                    data.description,
                    data.base_url,
                    data.is_active,
                    data.used_size,
                    data.total_size,
                    data.created,
                    data.archived,
                    data.last_modified,
                    data.json_config
                );
            }
            return new Workspace();
        };

        Workspace.transformer = function (data) {
            if (angular.isArray(data)) {
                return data.map(Workspace.build);
            }
            return Workspace.build(data);
        };

        return Workspace;
    });
})();
