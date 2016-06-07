(function () {
    'use strict';

    angular.module('scaleApp').factory('Workspace', function (scaleConfig) {
        var Workspace = function (id, name, title, description, base_url, is_active, json_config, created, last_modified, archived) {
            this.id = id;
            this.name = name;
            this.title = title;
            this.description = description;
            this.base_url = base_url;
            this.is_active = is_active;
            if (json_config) {
                this.json_config = json_config;
            } else {
                this.json_config = scaleConfig.workspaceTypes[0];
            }
            this.created = created;
            this.last_modified = last_modified;
            this.archived = archived;
            this.modified = false;
        };

        var validateField = function (field) {
            return !(field === '' || field === null || typeof field === 'undefined');
        };

        Workspace.prototype = {
            validate: function () {
                var isValid = true;
                if (!validateField(this.name)) {
                    isValid = false;
                }
                if (!validateField(this.title)) {
                    isValid = false;
                }
                if (!validateField(this.description)) {
                    isValid = false;
                }
                if (!validateField(this.base_url)) {
                    isValid = false;
                }
                if (_.keys(this.json_config).length === 0) {
                    isValid = false;
                }
                return isValid;
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
                    data.json_config,
                    data.created,
                    data.last_modified,
                    data.archived
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
