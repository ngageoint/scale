
.. _algorithm_integration_step4:

Adding your dockerized algorithm as a Scale job
===============================================

Refer to Scale documentation on the Job Interface Specification: :ref:`architecture_jobs_interface`


Example of a simple, complete Job Type JSON Definition
------------------------------------------------------

.. code-block:: javascript
    :linenos:

    {
        "version": "1.0", 
        "recipe_types": [], 
        "errors": [], 
        "job_types": [
            {
                "name": "my-algorithm", 
                "version": "1.0.0", 
                "title": "My first algorithm", 
                "description": "Reads an HDF5 file and outputs two TIFF images and a CSV", 
                "category": "image-processing", 
                "author_name": "John_Doe", 
                "author_url": "http://www.example.com", 
                "is_operational": true, 
                "icon_code": "f27d", 
                "docker_privileged": true, 
                "docker_image": "10.4.4.10:5000/my_algorithm_1.0.0:dev", 
                "priority": 230, 
                "timeout": 3600, 
                "max_scheduled": null, 
                "max_tries": 3, 
                "cpus_required": 10.0, 
                "mem_required": 10240.0, 
                "disk_out_const_required": 0.0, 
                "disk_out_mult_required": 0.0, 
                "interface": {
                    "output_data": [
                        {
                            "media_type": "image/tiff", 
                            "required": true, 
                            "type": "file", 
                            "name": "output_file_tif"
                        }, 
                        {
                            "media_type": "image/tiff", 
                            "required": true, 
                            "type": "file", 
                            "name": "output_file_tif2"
                        },
                        {
                            "media_type": "text/csv", 
                            "required": true, 
                            "type": "file", 
                            "name": "output_file_csv"
                        }
                    ], 
                    "shared_resources": [], 
                    "command_arguments": "${input_file} ${job_output_dir}", 
                    "input_data": [
                        {
                            "media_types": [
                                "image/x-hdf5-image"
                            ], 
                            "required": true, 
                            "type": "file", 
                            "name": "input_file"
                        }
                    ], 
                    "version": "1.0", 
                    "command": "/app/my_wrapper.sh"
                }, 
                "error_mapping": {
                    "version": "1.0", 
                    "exit_codes": {}
                }, 
                "trigger_rule": null
            }
        ]
    }
    
Job JSON broken down:
^^^^^^^^^^^^^^^^^^^^^

Setting the algorithm attributes and resources
++++++++++++++++++++++++++++++++++++++++++++++

.. code-block:: javascript
    :linenos:
    :lineno-start: 1

    {
        "version": "1.0", 
        "recipe_types": [], 
        "errors": [], 
        "job_types": [
            {
                "name": "my-algorithm", 
                "version": "1.0.0", 
                "title": "My first algorithm", 
                "description": "Reads an HDF5 file and outputs two TIFF images and a CSV", 
                "category": "image-processing", 
                "author_name": "John_Doe", 
                "author_url": "http://www.example.com", 
                "is_operational": true, 
                "icon_code": "f27d", 
                "docker_privileged": true, 
                "docker_image": "10.4.4.10:5000/my_algorithm_1.0.0:dev", 
                "priority": 230, 
                "timeout": 3600, 
                "max_scheduled": null, 
                "max_tries": 3, 
                "cpus_required": 10.0, 
                "mem_required": 10240.0, 
                "disk_out_const_required": 0.0, 
                "disk_out_mult_required": 0.0, 

Lines 2-4:    These fields do not need to be filled out with additional information and the default values shown here
are sufficient for most users.

Line 7-8:     The "name" and "version" must be a unique combination from other jobs in Scale and be entirely lower
case.  For example, multiple jobs could be called "my-algorithm" as long as their "version" number is different. Common
convention is to use dashes (-) instead of underscores for the name and versions should use semantic versioning.

Line 9:       The "title" field is used for a pretty display of the job name

Line 10:      The "description" field should provide a brief abstract of what the algorithm does

Line 11:      The "category" field tags a job with other similar jobs

Lines 12-13:  The "author_name" field should identify the organization/individual responsible for the algorithm.  The
"author_url" is an optional link to a web page providing more information on the algorithm.

Line 14:      The "is_operational" field is a boolean defining if the results of the algorithm are for R&D purposes only
or are suitable for production use

Line 15:      The "icon_code" field maps to Font-Awesome codes and defines the icon symbol used to represent the
algorithm in Scale

Line 16:      The "docker_privileged" field is a boolean for jobs that must run with the docker run "--privileged" flag.
*This must be set to true for jobs that mount NFS directories*

Line 17:      The "docker_image" field specifies the name and optional index of the built docker image

Line 18:      The "priority" field specifies the importance of the Job in the queue.  Jobs with lower priority numbers
will execute **before** higher priority numbers

Line 19:      The "timeout" field is measured in minutes and will send a *kill* signal to the job if it has not
completed within this time

Lines 20-21:  The "max_scheduled" and "max_tries" fields define how many times the job can be scheduled and
automatically requeued respectively.  Failed jobs are automatically retried until the "max_tries" limit is reached.

Lines 22-25:  These lines define the necessary resources for the algorithm.  The "cpus_required" are the number of cores
required for the algorithm to run.  The "mem_required" is the amount of RAM in megabytes required.  The
"disk_out_const_required" is the amount of required disk space in megabytes in the docker container needed for the
algorithm.  Optionally, you can instead define the amount of disk space with the "disk_out_mult_required" field which is
a *multiple* of the total size of the input files.

Setting the algorithm inputs and outputs
++++++++++++++++++++++++++++++++++++++++

The "interface" section of the job type JSON definition defines the expected input and output file types and assigns
them variable names.  It also defines the command arguments that will be passed to Scale

.. code-block:: javascript
    :linenos:
    :lineno-start: 26
    
    "interface": {
        "input_data": [
            {
                "media_types": [
                    "image/x-hdf5-image"
                ], 
                "required": true, 
                "type": "file", 
                "name": "input_file"
            }
        ], 
        "output_data": [
            {
                "media_type": "image/tiff", 
                "required": true, 
                "type": "file", 
                "name": "output_file_tif"
            }, 
            {
                "media_type": "image/tiff", 
                "required": true, 
                "type": "file", 
                "name": "output_file_tif2"
            },
            {
                "media_type": "text/csv", 
                "required": true, 
                "type": "file", 
                "name": "output_file_csv"
            }
        ], 
        "shared_resources": [], 
        "command_arguments": "${input_file} ${job_output_dir}", 
        "version": "1.0", 
        "command": "/app/my_wrapper.sh"
    },

Lines 27-36:  The "input_data" section defines the inputs of the job that will be managed by Scale.  The "media_type"
defines the expected file_type of the input while the "type" keyword is a string defining whether in input is a file,
list of files, or a property.  The "required" field is optional and indicates if the input is an optional command
argument.  *If an input is optional, the job will still execute except replace the input with an empty string.* The
"name" field is a user-defined unique string.  **These input names match the variables in the command_arguments**
                
Lines 37-56:  The "output_data" section defines the expected outputs of the job.  The "media_type" defines the expected
file type of output while the "type" keyword defines whether it expects a file or a list of files.  The "required"
keyword is a boolean used if the output is guaranteed to be produced by the algorithm on a successful run.  By default,
the "required" keyword is set to true.  The "name" keyword must be a unique string defining the output.
**These names are matched with the names in the results manifest to capture results**
                
Line 57:      The "shared_resources" keyword is currently unused and reserved for future usage.  It should be set to [].

Line 58:      The "command_arguments" keyword defines what inputs are passed into the docker container.  You can think
of the arguments as appended to the end of the contents of your dockerfile's ENTRYPOINT for what command is executed.
The variables here **MUST** match the "name"(s) in your "input_data" section.  The special variable "${job_output_dir}"
is supplied by Scale and will be your empty output directory Scale will use to search for your results_manifest.json.

Line 59:      The "version" is an optional string defining the version of the definition specification used.  This
defaults to the latest version.

Line 60:      The "command" field defines the main command to execute on the command line.
*This should match your ENTRYPOINT in your dockerfile*.
