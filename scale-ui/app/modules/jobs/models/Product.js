(function (){
    'use strict';

    angular.module('scaleApp').factory('Product', function (JobType, scaleService, scaleConfig) {
        var Product = function (id, workspace, file_name, media_type, file_size, data_type, is_deleted, uuid, url, created, deleted, data_started, data_ended, geometry, center_point, meta_data, countries, last_modified, is_operational, is_published, published, unpublished, job_type, job, job_exe, update, source_files) {
            this.id = id;
            this.workspace = workspace;
            this.file_name = file_name;
            this.media_type = media_type;
            this.file_size = file_size;
            this.file_size_readable = this.getReadableFileSize();
            this.data_type = data_type;
            this.is_deleted = is_deleted;
            this.uuid = uuid;
            this.url = url;
            this.created = created;
            this.created_formatted = created ? moment.utc(created).toISOString() : created;
            this.deleted = deleted;
            this.data_started = data_started;
            this.data_ended = data_ended;
            this.geometry = geometry;
            this.center_point = center_point;
            this.meta_data = meta_data;
            this.countries = countries;
            this.last_modified = last_modified;
            this.last_modified_formatted = last_modified ? moment.utc(last_modified).toISOString() : last_modified;
            this.is_operational = is_operational;
            this.is_operational_label = is_operational ? 'Operational' : 'R&amp;D';
            this.is_published = is_published;
            this.published = published;
            this.unpublished = unpublished;
            this.job_type = JobType.transformer(job_type);
            this.job = job;
            this.job_exe = job_exe;
            this.update = update;
            this.source_files = source_files;
        };

        // public methods
        Product.prototype = {
            getDuration: function () {
                return moment.utc(this.last_modified).diff(moment.utc(this.created));
            },
            getReadableFileSize: function () {
                return scaleService.calculateFileSizeFromBytes(this.file_size);
            }
        };

        // static methods, assigned to class
        Product.build = function (data) {
            if (data) {
                return new Product(
                    data.id,
                    data.workspace,
                    data.file_name,
                    data.media_type,
                    data.file_size,
                    data.data_type,
                    data.is_deleted,
                    data.uuid,
                    data.url,
                    data.created,
                    data.deleted,
                    data.data_started,
                    data.data_ended,
                    data.geometry,
                    data.center_point,
                    data.meta_data,
                    data.countries,
                    data.last_modified,
                    data.is_operational,
                    data.is_published,
                    data.published,
                    data.unpublished,
                    data.job_type,
                    data.job,
                    data.job_exe,
                    data.update,
                    data.source_files
                );
            }
            return new Product();
        };

        Product.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(Product.build)
                    .filter(Boolean);
            }
            return Product.build(data);
        };

        return Product;
    });
})();
