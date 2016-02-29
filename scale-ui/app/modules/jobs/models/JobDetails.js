(function () {
    'use strict';

    angular.module('scaleApp').factory('JobDetails', function (scaleConfig, JobType, JobExecution, Product, JobDetailInputData, JobDetailOutputData, Recipe, JobDetailEvent, scaleService) {
        var JobDetails = function (cpus_required, created, queued, started, ended, data, disk_in_required, disk_out_required, error, event, id, job_exes, job_type, last_modified, last_status_change, max_tries, mem_required, num_exes, priority, products, recipes, results, input_files, status, timeout ) {
            // decorate inputs and outputs to support data binding in details view
            data.input_data = decorateInputData(data.input_data, input_files);
            data.output_data = decorateOutputData(data.output_data, results, products);
            this.cpus_required = cpus_required;
            this.created = created;
            this.created_formatted = moment.utc(created).toISOString();
            this.queued = queued;
            this.queued_formatted = moment.utc(queued).toISOString();
            this.started = started;
            this.started_formatted = moment.utc(started).toISOString();
            this.ended = ended;
            this.ended_formatted = moment.utc(ended).toISOString();
            this.data = {
                input_data: JobDetailInputData.transformer(data.input_data),
                version: data.version,
                output_data: JobDetailOutputData.transformer(data.output_data)
            };
            this.disk_in_required = disk_in_required;
            this.disk_out_required = disk_out_required;
            this.error = error;
            this.event = JobDetailEvent.transformer(event);
            this.id = id;
            this.job_exes = JobExecution.transformer(job_exes);
            this.job_type = JobType.transformer(job_type);
            this.last_modified = last_modified;
            this.last_status_change = last_status_change;
            this.max_tries = max_tries;
            this.mem_required = mem_required;
            this.num_exes = num_exes;
            this.priority = priority;
            this.products = Product.transformer(products);
            this.recipes = Recipe.transformer(recipes);
            this.results = {
                output_data: JobDetailOutputData.transformer(results.output_data),
                version: results.version
            };
            this.input_files = input_files;
            this.status = status;
            this.timeout = timeout;
        };

        // private methods
        var decorateInputData = function(input_data, input_files){
            _.forEach(input_data, function(val){
                var file_ids = [];
                if(!val.files){ val.files = []; }

                if(val.file_id && val.file_id > 0){
                    file_ids = [val.file_id];
                }
                else if(val.file_ids && val.file_ids.length > 0){
                    // multiple files
                    file_ids = val.file_ids;
                }
                _.forEach(file_ids, function(file_id){
                    var infile = _.find(input_files, {id: file_id});
                    if(infile){
                        val.files.push(
                            {
                                file_name: infile.file_name,
                                url: infile.url,
                                created: infile.created,
                                last_modified: infile.last_modified,
                                file_size_formatted: scaleService.calculateFileSizeFromBytes(infile.file_size)
                            }
                        );
                    }
                });
            });
            return input_data;
        };

        var decorateOutputData = function(output_data, results, products){
            _.forEach(output_data, function(val){
                var file_ids = [];
                var result = _.find(results.output_data, { name: val.name });
                if(!val.files){ val.files = []; }

                if( result && result.file_id && result.file_id > 0 ){
                    // single file
                    file_ids = [result.file_id];
                }
                else if(result && result.file_ids && result.file_ids.length > 0){
                    // multiple files
                    file_ids = result.file_ids;
                }
                _.forEach(file_ids, function(file_id){
                    var outfile = _.find(products, {id: file_id});
                    console.log(file_id + ': ' + outfile.id);
                    if(outfile){
                        val.files.push(
                            {
                                file_name: outfile.file_name,
                                url: outfile.url,
                                created: outfile.created,
                                last_modified: outfile.last_modified,
                                file_size_formatted: scaleService.calculateFileSizeFromBytes(outfile.file_size)
                            }
                        );
                    }
                });
            });
            return output_data;
        };

        // public methods
        JobDetails.prototype = {
            getDuration: function () {
                return scaleService.calculateDuration(this.created, this.last_modified);
            },
            getLatestExecution: function(){
                if (this.num_exes > 0 ) {
                    return this.job_exes[0];
                }
                return null;
            },
            getStatusClass: function(){
                // if(this.status === 'COMPLETED'){
                //     return 'label-success';
                // }
                // else if( this.status === 'FAILED'){
                //     return 'label-default';//    return 'label-danger';
                // }
                // else{
                //     return 'label-default';
                // }
                return this.status.toLowerCase();
            }
        };

        // static methods, assigned to class
        JobDetails.build = function (data) {
            if (data) {
                return new JobDetails(
                    data.cpus_required,
                    data.created,
                    data.queued,
                    data.started,
                    data.ended,
                    data.data,
                    data.disk_in_required,
                    data.disk_out_required,
                    data.error,
                    data.event,
                    data.id,
                    data.job_exes,
                    data.job_type,
                    data.last_modified,
                    data.last_status_change,
                    data.max_tries,
                    data.mem_required,
                    data.num_exes,
                    data.priority,
                    data.products,
                    data.recipes,
                    data.results,
                    data.input_files,
                    data.status,
                    data.timeout
                );
            }
            return new JobDetails();
        };

        JobDetails.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(JobDetails.build)
                    .filter(Boolean);
            }
            return JobDetails.build(data);
        };

        return JobDetails;
    });
})();
