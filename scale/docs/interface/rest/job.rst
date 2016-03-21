
.. _rest_job:

Job Services
===============================================================================

These services provide access to information about "all", "currently running" and "previously finished" jobs.

.. _rest_job_list:

+-------------------------------------------------------------------------------------------------------------------------+
| **Job List**                                                                                                            |
+=========================================================================================================================+
| Returns a list of all jobs.                                                                                             |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /jobs/                                                                                                          |
+-------------------------------------------------------------------------------------------------------------------------+
| **Query Parameters**                                                                                                    |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| page               | Integer           | Optional | The page of the results to return. Defaults to 1.                   |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| page_size          | Integer           | Optional | The size of the page to use for pagination of results.              |
|                    |                   |          | Defaults to 100, and can be anywhere from 1-1000.                   |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| started            | ISO-8601 Datetime | Optional | The start of the time range to query.                               |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| ended              | ISO-8601 Datetime | Optional | End of the time range to query, defaults to the current time.       |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| order              | String            | Optional | One or more fields to use when ordering the results.                |
|                    |                   |          | Duplicate it to multi-sort, (ex: order=name&order=version).         |
|                    |                   |          | Prefix fields with a dash to reverse the sort, (ex: order=-name).   |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| status             | String            | Optional | Return only jobs with a status matching this string.                |
|                    |                   |          | Choices: [QUEUED, RUNNING, FAILED, COMPLETED, CANCELED].            |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_id             | Integer           | Optional | Return only jobs with a given identifier.                           |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_id        | Integer           | Optional | Return only jobs with a given job type identifier.                  |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_name      | String            | Optional | Return only jobs with a given job type name.                        |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_category  | String            | Optional | Return only jobs with a given job type category.                    |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| count              | Integer           | The total number of results that match the query parameters.                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| next               | URL               | A URL to the next page of results.                                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| previous           | URL               | A URL to the previous page of results.                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| results            | Array             | List of result JSON objects that match the query parameters.                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .id                | Integer           | The unique identifier of the model. Can be passed to the details API call.     |
|                    |                   | (See :ref:`Job Details <rest_job_details>`)                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .job_type          | JSON Object       | The job type that is associated with the job.                                  |
|                    |                   | (See :ref:`Job Type Details <rest_job_type_details>`)                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .job_type_rev      | JSON Object       | The job type revision that is associated with the job.                         |
|                    |                   | This represents the definition at the time the job was scheduled.              |
|                    |                   | (See :ref:`Job Type Revision Details <rest_job_type_rev_details>`)             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .event             | JSON Object       | The trigger event that is associated with the job.                             |
|                    |                   | (See :ref:`Trigger Event Details <rest_trigger_event_details>`)                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .error             | JSON Object       | The error that is associated with the job.                                     |
|                    |                   | (See :ref:`Error Details <rest_error_details>`)                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .status            | String            | The current status of the job.                                                 |
|                    |                   | Choices: [QUEUED, RUNNING, FAILED, COMPLETED, CANCELED].                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .priority          | Integer           | The priority of the job.                                                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .num_exes          | Integer           | The number of executions this job has had.                                     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .timeout           | Integer           | The maximum amount of time this job can run before being killed (in seconds).  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .max_tries         | Integer           | The maximum number of times to attempt this job when failed (minimum one).     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .cpus_required     | Decimal           | The number of CPUs needed for a job of this type.                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .mem_required      | Decimal           | The amount of RAM in MiB needed for a job of this type.                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .disk_in_required  | Decimal           | The amount of disk space in MiB required for input files for this job.         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .disk_out_required | Decimal           | The amount of disk space in MiB required for output files for this job.        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .created           | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .queued            | ISO-8601 Datetime | When the job was added to the queue to be run when resources are available.    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .started           | ISO-8601 Datetime | When the job started running.                                                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .ended             | ISO-8601 Datetime | When the job stopped running, which could be due to success or failure.        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .last_status_change| ISO-8601 Datetime | When the status of the job was last changed.                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .last_modified     | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "count": 68,                                                                                                     |
|        "next": null,                                                                                                    |
|        "previous": null,                                                                                                |
|        "results": [                                                                                                     |
|            {                                                                                                            |
|                "id": 3,                                                                                                 |
|                "job_type": {                                                                                            |
|                    "id": 1,                                                                                             |
|                    "name": "scale-ingest",                                                                              |
|                    "version": "1.0",                                                                                    |
|                    "title": "Scale Ingest",                                                                             |
|                    "description": "Ingests a source file into a workspace",                                             |
|                    "is_system": true,                                                                                   |
|                    "is_long_running": false,                                                                            |
|                    "is_active": true,                                                                                   |
|                    "is_operational": true,                                                                              |
|                    "is_paused": false,                                                                                  |
|                    "icon_code": "f013"                                                                                  |
|                },                                                                                                       |
|                "job_type_rev": {                                                                                        |
|                    "id": 5,                                                                                             |
|                    "job_type": {                                                                                        |
|                        "id": 1                                                                                          |
|                    },                                                                                                   |
|                    "revision_num": 1                                                                                    |
|                },                                                                                                       |
|                "event": {                                                                                               |
|                    "id": 3,                                                                                             |
|                    "type": "STRIKE_TRANSFER",                                                                           |
|                    "rule": null,                                                                                        |
|                    "occurred": "2015-08-28T17:57:24.261Z"                                                               |
|                },                                                                                                       |
|                "error": null,                                                                                           |
|                "status": "COMPLETED",                                                                                   |
|                "priority": 10,                                                                                          |
|                "num_exes": 1,                                                                                           |
|                "timeout": 1800,                                                                                         |
|                "max_tries": 3,                                                                                          |
|                "cpus_required": 1.0,                                                                                    |
|                "mem_required": 64.0,                                                                                    |
|                "disk_in_required": 0.0,                                                                                 |
|                "disk_out_required": 64.0,                                                                               |
|                "created": "2015-08-28T17:55:41.005Z",                                                                   |
|                "queued": "2015-08-28T17:56:41.005Z",                                                                    |
|                "started": "2015-08-28T17:57:41.005Z",                                                                   |
|                "ended": "2015-08-28T17:58:41.005Z",                                                                     |
|                "last_status_change": "2015-08-28T17:58:45.906Z",                                                        |
|                "last_modified": "2015-08-28T17:58:46.001Z"                                                              |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_job_details:

+-------------------------------------------------------------------------------------------------------------------------+
| **Job Details**                                                                                                         |
+=========================================================================================================================+
| Returns a specific job and all its related model information including executions, recipes, and products.               |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /jobs/{id}/                                                                                                     |
|         Where {id} is the unique identifier of an existing model.                                                       |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| id                 | Integer           | The unique identifier of the model.                                            |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| job_type           | JSON Object       | The job type that is associated with the count.                                |
|                    |                   | (See :ref:`Job Type Details <rest_job_type_details>`)                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .job_type_rev      | JSON Object       | The job type revision that is associated with the job.                         |
|                    |                   | This represents the definition at the time the job was scheduled.              |
|                    |                   | (See :ref:`Job Type Revision Details <rest_job_type_rev_details>`)             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| event              | JSON Object       | The trigger event that is associated with the count.                           |
|                    |                   | (See :ref:`Trigger Event Details <rest_trigger_event_details>`)                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| error              | JSON Object       | The error that is associated with the count.                                   |
|                    |                   | (See :ref:`Error Details <rest_error_details>`)                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| status             | String            | The current status of the job.                                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| priority           | Integer           | The priority of the job.                                                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| num_exes           | Integer           | The number of executions this job has had.                                     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| timeout            | Integer           | The maximum amount of time this job can run before being killed (in seconds).  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| max_tries          | Integer           | The maximum number of times to attempt this job when failed (minimum one).     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| cpus_required      | Decimal           | The number of CPUs needed for a job of this type.                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| mem_required       | Decimal           | The amount of RAM in MiB needed for a job of this type.                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| disk_in_required   | Decimal           | The amount of disk space in MiB required for input files for this job.         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| disk_out_required  | Decimal           | The amount of disk space in MiB required for output files for this job.        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| created            | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| queued             | ISO-8601 Datetime | When the job was added to the queue to be run when resources are available.    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| started            | ISO-8601 Datetime | When the job started running.                                                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ended              | ISO-8601 Datetime | When the job stopped running, which could be due to success or failure.        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| last_status_change | ISO-8601 Datetime | When the status of the job was last changed.                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| last_modified      | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| data               | JSON Object       | An interface description for all the job input and output files.               |
|                    |                   | (See :ref:`architecture_jobs_job_data_spec`)                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| results            | JSON Object       | An interface description for all the job results meta-data.                    |
|                    |                   | (See :ref:`architecture_jobs_job_results_spec`)                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| recipes            | Array             | A list of all recipes associated with the job.                                 |
|                    |                   | (See :ref:`Recipe Details <rest_recipe_details>`)                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| job_exes           | Array             | A list of all job executions associated with the job.                          |
|                    |                   | (See :ref:`Job Execution Details <rest_job_execution_details>`)                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| inputs             | Array             | A list of job interface inputs merged with their respective job data values.   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .name              | String            | The name of the input as defined by the job type interface.                    |
|                    |                   | (See :ref:`architecture_jobs_interface_spec`)                                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .type              | String            | The type of the input as defined by teh job type interface.                    |
|                    |                   | (See :ref:`architecture_jobs_interface_spec`)                                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .value             | Various           | The actual value of the input, which can vary depending on the type. Simple    |
|                    |                   | property inputs will include primitive values, whereas the file or files type  |
|                    |                   | will include a full JSON representation of a Scale file object.                |
|                    |                   | (See :ref:`Scale File Details <rest_scale_file_details>`)                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| outputs            | Array             | A list of job interface outputs merged with their respective job result values.|
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .name              | String            | The name of the output as defined by the job type interface.                   |
|                    |                   | (See :ref:`architecture_jobs_interface_spec`)                                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .type              | String            | The type of the output as defined by teh job type interface.                   |
|                    |                   | (See :ref:`architecture_jobs_interface_spec`)                                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .value             | Various           | The actual value of the output, which can vary depending on the type. A file or|
|                    |                   | files type will include a full JSON representation of a Product file object.   |
|                    |                   | (See :ref:`Product Details <rest_product_details>`)                            |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "id": 15096,                                                                                                     |
|        "job_type": {                                                                                                    |
|            "id": 8,                                                                                                     |
|            "name": "kml-footprint",                                                                                     |
|            "version": "1.0.0",                                                                                          |
|            "title": "KML Footprint",                                                                                    |
|            "description": "Creates a KML representation of the data",                                                   |
|            "is_system": false,                                                                                          |
|            "is_long_running": false,                                                                                    |
|            "is_active": true,                                                                                           |
|            "is_operational": true,                                                                                      |
|            "is_paused": false,                                                                                          |
|            "icon_code": "f0ac",                                                                                         |
|            "uses_docker": false,                                                                                        |
|            "docker_privileged": false,                                                                                  |
|            "docker_image": null,                                                                                        |
|            "priority": 2,                                                                                               |
|            "timeout": 600,                                                                                              |
|            "max_tries": 1,                                                                                              |
|            "cpus_required": 0.5,                                                                                        |
|            "mem_required": 128.0,                                                                                       |
|            "disk_out_const_required": 0.0,                                                                              |
|            "disk_out_mult_required": 0.0,                                                                               |
|            "created": "2015-06-01T00:00:00Z",                                                                           |
|            "archived": null,                                                                                            |
|            "paused": null,                                                                                              |
|            "last_modified": "2015-06-01T00:00:00Z"                                                                      |
|        },                                                                                                               |
|        "job_type_rev": {                                                                                                |
|            "id": 5,                                                                                                     |
|            "job_type": {                                                                                                |
|                "id": 8                                                                                                  |
|            },                                                                                                           |
|            "revision_num": 1,                                                                                           |
|            "interface": {                                                                                               |
|                "input_data": [                                                                                          |
|                    {                                                                                                    |
|                        "type": "file",                                                                                  |
|                        "name": "input_file"                                                                             |
|                    }                                                                                                    |
|                ],                                                                                                       |
|                "output_data": [                                                                                         |
|                    {                                                                                                    |
|                        "media_type": "application/vnd.google-earth.kml+xml",                                            |
|                        "type": "file",                                                                                  |
|                        "name": "output_file"                                                                            |
|                    }                                                                                                    |
|                ],                                                                                                       |
|                "version": "1.0",                                                                                        |
|                "command": "/usr/local/bin/python2.7 /app/parser/manage.py create_footprint_kml",                        |
|                "command_arguments": "${input_file} ${job_output_dir}"                                                   |
|            },                                                                                                           |
|            "created": "2015-11-06T00:00:00Z"                                                                            |
|        },                                                                                                               |
|        "event": {                                                                                                       |
|            "id": 10278,                                                                                                 |
|            "type": "PARSE",                                                                                             |
|            "rule": {                                                                                                    |
|                "id": 8,                                                                                                 |
|                "type": "PARSE",                                                                                         |
|                "is_active": true,                                                                                       |
|                "created": "2015-08-28T18:31:29.282Z",                                                                   |
|                "archived": null,                                                                                        |
|                "last_modified": "2015-08-28T18:31:29.282Z"                                                              |
|            },                                                                                                           |
|            "occurred": "2015-09-01T17:27:31.467Z"                                                                       |
|        },                                                                                                               |
|        "error": null,                                                                                                   |
|        "status": "COMPLETED",                                                                                           |
|        "priority": 210,                                                                                                 |
|        "num_exes": 1,                                                                                                   | 
|        "timeout": 1800,                                                                                                 |
|        "max_tries": 3,                                                                                                  |
|        "cpus_required": 1.0,                                                                                            |
|        "mem_required": 15360.0,                                                                                         |
|        "disk_in_required": 2.0,                                                                                         |
|        "disk_out_required": 16.0,                                                                                       |
|        "created": "2015-08-28T17:55:41.005Z",                                                                           |
|        "queued": "2015-08-28T17:56:41.005Z",                                                                            |
|        "started": "2015-08-28T17:57:41.005Z",                                                                           |
|        "ended": "2015-08-28T17:58:41.005Z",                                                                             |
|        "last_status_change": "2015-08-28T17:58:45.906Z",                                                                |
|        "last_modified": "2015-08-28T17:58:46.001Z",                                                                     |
|        "data": {                                                                                                        |
|            "input_data": [                                                                                              |
|                {                                                                                                        |
|                    "name": "input_file",                                                                                |
|                    "file_id": 8480                                                                                      |
|                }                                                                                                        |
|            ],                                                                                                           |
|            "version": "1.0",                                                                                            |
|            "output_data": [                                                                                             |
|                {                                                                                                        |
|                    "name": "output_file",                                                                               |
|                    "workspace_id": 2                                                                                    |
|                }                                                                                                        |
|            ]                                                                                                            |
|        },                                                                                                               |
|        "results": {                                                                                                     |
|            "output_data": [                                                                                             |
|                {                                                                                                        |
|                    "name": "output_file",                                                                               |
|                    "file_id": 8484                                                                                      |
|                }                                                                                                        |
|            ],                                                                                                           |
|            "version": "1.0"                                                                                             |
|        },                                                                                                               |
|        "recipes": [                                                                                                     |
|            {                                                                                                            |
|                "id": 4832,                                                                                              |
|                "recipe_type": {                                                                                         |
|                    "id": 6,                                                                                             |
|                    "name": "Recipe",                                                                                    |
|                    "version": "1.0.0",                                                                                  |
|                    "description": "Recipe description"                                                                  |
|                },                                                                                                       |
|                "event": {                                                                                               |
|                    "id": 7,                                                                                             |
|                    "type": "PARSE",                                                                                     |
|                    "rule": {                                                                                            |
|                        "id": 2                                                                                          |
|                    },                                                                                                   |
|                    "occurred": "2015-08-28T17:58:45.280Z"                                                               |
|                },                                                                                                       |
|                "created": "2015-09-01T20:32:20.912Z",                                                                   |
|                "completed": "2015-09-01T20:35:20.912Z",                                                                 |
|                "last_modified": "2015-09-01T20:35:20.912Z"                                                              |
|            }                                                                                                            |
|        ],                                                                                                               |
|        "job_exes": [                                                                                                    |
|            {                                                                                                            |
|                "id": 14552,                                                                                             |
|                "status": "COMPLETED",                                                                                   |
|                "command_arguments": "${input_file} ${job_output_dir}",                                                  |
|                "timeout": 1800,                                                                                         |
|                "pre_started": "2015-09-01T17:27:32.435Z",                                                               |
|                "pre_completed": "2015-09-01T17:27:34.346Z",                                                             |
|                "pre_exit_code": null,                                                                                   |
|                "job_started": "2015-09-01T17:27:42.437Z",                                                               |
|                "job_completed": "2015-09-01T17:27:46.762Z",                                                             |
|                "job_exit_code": null,                                                                                   |
|                "post_started": "2015-09-01T17:27:47.246Z",                                                              |
|                "post_completed": "2015-09-01T17:27:49.461Z",                                                            |
|                "post_exit_code": null,                                                                                  |
|                "created": "2015-09-01T17:27:31.753Z",                                                                   |
|                "queued": "2015-09-01T17:27:31.716Z",                                                                    |
|                "started": "2015-09-01T17:27:32.022Z",                                                                   |
|                "ended": "2015-09-01T17:27:49.461Z",                                                                     |
|                "last_modified": "2015-09-01T17:27:49.606Z",                                                             |
|                "job": {                                                                                                 |
|                    "id": 15586                                                                                          |
|                },                                                                                                       |
|                "node": {                                                                                                |
|                    "id": 1                                                                                              |
|                },                                                                                                       |
|                "error": null                                                                                            |
|            }                                                                                                            |
|        ],                                                                                                               |
|        "inputs": [                                                                                                      |
|            {                                                                                                            |
|                "name": "input_file",                                                                                    |
|                "type": "file",                                                                                          |
|                "value": {                                                                                               |
|                    "id": 2,                                                                                             |
|                    "workspace": {                                                                                       |
|                        "id": 1,                                                                                         |
|                        "name": "Raw Source"                                                                             |
|                    },                                                                                                   |
|                    "file_name": "input_file.txt",                                                                       |
|                    "media_type": "text/plain",                                                                          |
|                    "file_size": 1234,                                                                                   |
|                    "data_type": [],                                                                                     |
|                    "is_deleted": false,                                                                                 |
|                    "uuid": "c8928d9183fc99122948e7840ec9a0fd",                                                          |
|                    "url": "http://host.com/input_file.txt",                                                             |
|                    "created": "2015-09-10T15:24:53.962Z",                                                               |
|                    "deleted": null,                                                                                     |
|                    "data_started": "2015-09-10T14:50:49Z",                                                              |
|                    "data_ended": "2015-09-10T14:51:05Z",                                                                |
|                    "geometry": null,                                                                                    |
|                    "center_point": null,                                                                                |
|                    "meta_data": {...}                                                                                   |
|                    "last_modified": "2015-09-10T15:25:02.808Z"                                                          |
|                }                                                                                                        |
|            }                                                                                                            |
|        ],                                                                                                               |
|        "outputs": [                                                                                                     |
|            {                                                                                                            |
|                "name": "output_file",                                                                                   |
|                "type": "file",                                                                                          |
|                "value": {                                                                                               |
|                    "id": 8484,                                                                                          |
|                    "workspace": {                                                                                       |
|                        "id": 2,                                                                                         |
|                        "name": "Products"                                                                               |
|                    },                                                                                                   |
|                    "file_name": "file.kml",                                                                             |
|                    "media_type": "application/vnd.google-earth.kml+xml",                                                |
|                    "file_size": 1234,                                                                                   |
|                    "data_type": [],                                                                                     |
|                    "is_deleted": false,                                                                                 |
|                    "uuid": "c8928d9183fc99122948e7840ec9a0fd",                                                          |
|                    "url": "http://host.com/file/path/my_file.kml",                                                      |
|                    "created": "2015-09-01T17:27:48.477Z",                                                               |
|                    "deleted": null,                                                                                     |
|                    "data_started": null,                                                                                |
|                    "data_ended": null,                                                                                  |
|                    "geometry": null,                                                                                    |
|                    "center_point": null,                                                                                |
|                    "meta_data": {},                                                                                     |
|                    "last_modified": "2015-09-01T17:27:49.639Z",                                                         |
|                    "is_operational": true,                                                                              |
|                    "is_published": true,                                                                                |
|                    "published": "2015-09-01T17:27:49.461Z",                                                             |
|                    "unpublished": null,                                                                                 |
|                    "job_type": {                                                                                        |
|                        "id": 8                                                                                          |
|                    },                                                                                                   |
|                    "job": {                                                                                             |
|                        "id": 35                                                                                         |
|                    },                                                                                                   |
|                    "job_exe": {                                                                                         |
|                        "id": 19                                                                                         |
|                    }                                                                                                    |
|                }                                                                                                        |
|            }                                                                                                            |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_job_update:

+-------------------------------------------------------------------------------------------------------------------------+
| **Update Job**                                                                                                          |
+=========================================================================================================================+
| Update the details of a job.                                                                                            |
+-------------------------------------------------------------------------------------------------------------------------+
| **PATCH** /jobs/{id}/                                                                                                   |
|         Where {id} is the unique identifier of an existing job.                                                         |
|         The fields below are currently allowed. Additional fields are not tolerated.                                    |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| status             | String            | The new status for the job. The only status change currently allowed is:       |
|                    |                   |   CANCELED - This will cancel a running, queued, or blocked job.               |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| Response format is identical to GET but contains the updated data.                                                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| **Error Responses**                                                                                                     |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 400 BAD REQUEST                                                                                    |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *text/plain*                                                                                       |
+--------------------+----------------------------------------------------------------------------------------------------+
| Unexpected fields were specified. An error message lists them. Or no fields or invalid values were specified.           |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 404 NOT FOUND                                                                                      |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *text/plain*                                                                                       |
+--------------------+----------------------------------------------------------------------------------------------------+
| The specified job or associated job executions (if applicable) were not found in the database.                          |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 500 SERVER ERROR                                                                                   |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *text/plain*                                                                                       |
+--------------------+----------------------------------------------------------------------------------------------------+
| A miscellaneous (and rare) server error or database timing error occurred. Repeating the request may result in success. |
| The exact error reason will appear in the response content.                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+

.. _rest_job_updates:

+-------------------------------------------------------------------------------------------------------------------------+
| **Job Updates**                                                                                                         |
+=========================================================================================================================+
| Returns a list of jobs with associated input files that changed status in the given time range.                         |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /jobs/updates/                                                                                                  |
+-------------------------------------------------------------------------------------------------------------------------+
| **Query Parameters**                                                                                                    |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| page               | Integer           | Optional | The page of the results to return. Defaults to 1.                   |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| page_size          | Integer           | Optional | The size of the page to use for pagination of results.              |
|                    |                   |          | Defaults to 100, and can be anywhere from 1-1000.                   |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| started            | ISO-8601 Datetime | Optional | The start of the time range to query.                               |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| ended              | ISO-8601 Datetime | Optional | End of the time range to query, defaults to the current time.       |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| order              | String            | Optional | One or more fields to use when ordering the results.                |
|                    |                   |          | Duplicate it to multi-sort, (ex: order=name&order=version).         |
|                    |                   |          | Prefix fields with a dash to reverse the sort, (ex: order=-name).   |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| status             | String            | Optional | Return only jobs with a status matching this string.                |
|                    |                   |          | Choices: [QUEUED, RUNNING, FAILED, COMPLETED, CANCELED].            |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_id        | Integer           | Optional | Return only jobs with a given job type identifier.                  |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_name      | String            | Optional | Return only jobs with a given job type name.                        |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_category  | String            | Optional | Return only jobs with a given job type category.                    |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| count              | Integer           | The total number of results that match the query parameters.                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| next               | URL               | A URL to the next page of results.                                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| previous           | URL               | A URL to the previous page of results.                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| results            | Array             | List of result JSON objects that match the query parameters.                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .id                | Integer           | The unique identifier of the model. Can be passed to the details API call.     |
|                    |                   | (See :ref:`Job Details <rest_job_details>`)                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .job_type          | JSON Object       | The job type that is associated with the job.                                  |
|                    |                   | (See :ref:`Job Type Details <rest_job_type_details>`)                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .job_type_rev      | JSON Object       | The job type revision that is associated with the job.                         |
|                    |                   | This represents the definition at the time the job was scheduled.              |
|                    |                   | (See :ref:`Job Type Revision Details <rest_job_type_rev_details>`)             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .event             | JSON Object       | The trigger event that is associated with the job.                             |
|                    |                   | (See :ref:`Trigger Event Details <rest_trigger_event_details>`)                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .error             | JSON Object       | The error that is associated with the job.                                     |
|                    |                   | (See :ref:`Error Details <rest_error_details>`)                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .status            | String            | The current status of the job.                                                 |
|                    |                   | Choices: [QUEUED, RUNNING, FAILED, COMPLETED, CANCELED].                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .priority          | Integer           | The priority of the job.                                                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .num_exes          | Integer           | The number of executions this job has had.                                     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .timeout           | Integer           | The maximum amount of time this job can run before being killed (in seconds).  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .max_tries         | Integer           | The maximum number of times to attempt this job when failed (minimum one).     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .cpus_required     | Decimal           | The number of CPUs needed for a job of this type.                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .mem_required      | Decimal           | The amount of RAM in MiB needed for a job of this type.                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .disk_in_required  | Decimal           | The amount of disk space in MiB required for input files for this job.         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .disk_out_required | Decimal           | The amount of disk space in MiB required for output files for this job.        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .created           | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .queued            | ISO-8601 Datetime | When the job was added to the queue to be run when resources are available.    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .started           | ISO-8601 Datetime | When the job started running.                                                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .ended             | ISO-8601 Datetime | When the job stopped running, which could be due to success or failure.        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .last_status_change| ISO-8601 Datetime | When the status of the job was last changed.                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .last_modified     | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .input_files       | JSON Object       | A list of files that the job used as input.                                    |
|                    |                   | (See :ref:`Scale File Details <rest_scale_file_details>`)                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "count": 68,                                                                                                     |
|        "next": null,                                                                                                    |
|        "previous": null,                                                                                                |
|        "results": [                                                                                                     |
|            {                                                                                                            |
|                "id": 3,                                                                                                 |
|                "job_type": {                                                                                            |
|                    "id": 1,                                                                                             |
|                    "name": "scale-ingest",                                                                              |
|                    "version": "1.0",                                                                                    |
|                    "title": "Scale Ingest",                                                                             |
|                    "description": "Ingests a source file into a workspace",                                             |
|                    "is_system": true,                                                                                   |
|                    "is_long_running": false,                                                                            |
|                    "is_active": true,                                                                                   |
|                    "is_operational": true,                                                                              |
|                    "is_paused": false,                                                                                  |
|                    "icon_code": "f013"                                                                                  |
|                },                                                                                                       |
|                "job_type_rev": {                                                                                        |
|                    "id": 5,                                                                                             |
|                    "job_type": {                                                                                        |
|                        "id": 1                                                                                          |
|                    },                                                                                                   |
|                    "revision_num": 1                                                                                    |
|                },                                                                                                       |
|                "event": {                                                                                               |
|                    "id": 3,                                                                                             |
|                    "type": "STRIKE_TRANSFER",                                                                           |
|                    "rule": null,                                                                                        |
|                    "occurred": "2015-08-28T17:57:24.261Z"                                                               |
|                },                                                                                                       |
|                "error": null,                                                                                           |
|                "status": "COMPLETED",                                                                                   |
|                "priority": 10,                                                                                          |
|                "num_exes": 1,                                                                                           |
|                "timeout": 1800,                                                                                         |
|                "max_tries": 3,                                                                                          |
|                "cpus_required": 1.0,                                                                                    |
|                "mem_required": 64.0,                                                                                    |
|                "disk_in_required": 0.0,                                                                                 |
|                "disk_out_required": 64.0,                                                                               |
|                "created": "2015-08-28T17:55:41.005Z",                                                                   |
|                "queued": "2015-08-28T17:56:41.005Z",                                                                    |
|                "started": "2015-08-28T17:57:41.005Z",                                                                   |
|                "ended": "2015-08-28T17:58:41.005Z",                                                                     |
|                "last_status_change": "2015-08-28T17:58:45.906Z",                                                        |
|                "last_modified": "2015-08-28T17:58:46.001Z",                                                             |
|                "input_files": [                                                                                         |
|                    {                                                                                                    |
|                        "id": 2,                                                                                         |
|                        "workspace": {                                                                                   |
|                            "id": 1,                                                                                     |
|                            "name": "Raw Source"                                                                         |
|                        },                                                                                               |
|                        "file_name": "input_file.txt",                                                                   | 
|                        "media_type": "text/plain",                                                                      |
|                        "file_size": 1234,                                                                               |
|                        "data_type": [],                                                                                 | 
|                        "is_deleted": false,                                                                             |
|                        "uuid": "c8928d9183fc99122948e7840ec9a0fd",                                                      |
|                        "url": "http://host.com/input_file.txt",                                                         |
|                        "created": "2015-09-10T15:24:53.962Z",                                                           |
|                        "deleted": null,                                                                                 |
|                        "data_started": "2015-09-10T14:50:49Z",                                                          |
|                        "data_ended": "2015-09-10T14:51:05Z",                                                            |
|                        "geometry": null,                                                                                |
|                        "center_point": null,                                                                            |
|                        "meta_data": {...}                                                                               |
|                        "last_modified": "2015-09-10T15:25:02.808Z"                                                      |
|                    }                                                                                                    |
|                ]                                                                                                        |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_job_with_execution_list:

+-------------------------------------------------------------------------------------------------------------------------+
| **Job with Execution List**                                                                                             |
+=========================================================================================================================+
| Returns a list of all jobs with their latest execution.                                                                 |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /jobs/executions/                                                                                               |
+-------------------------------------------------------------------------------------------------------------------------+
| **Query Parameters**                                                                                                    |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| page               | Integer           | Optional | The page of the results to return. Defaults to 1.                   |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| page_size          | Integer           | Optional | The size of the page to use for pagination of results.              |
|                    |                   |          | Defaults to 100, and can be anywhere from 1-1000.                   |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| started            | ISO-8601 Datetime | Optional | The start of the time range to query.                               |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| ended              | ISO-8601 Datetime | Optional | End of the time range to query, defaults to the current time.       |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| order              | String            | Optional | One or more fields to use when ordering the results.                |
|                    |                   |          | Duplicate it to multi-sort, (ex: order=name&order=version).         |
|                    |                   |          | Prefix fields with a dash to reverse the sort, (ex: order=-name).   |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| status             | String            | Optional | Return only jobs with a status matching this string.                |
|                    |                   |          | Choices: [QUEUED, RUNNING, FAILED, COMPLETED, CANCELED].            |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_id        | Integer           | Optional | Return only jobs with a given job type identifier.                  |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_name      | String            | Optional | Return only jobs with a given job type name.                        |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_category  | String            | Optional | Return only jobs with a given job type category.                    |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| count              | Integer           | The total number of results that match the query parameters.                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| next               | URL               | A URL to the next page of results.                                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| previous           | URL               | A URL to the previous page of results.                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| results            | Array             | List of result JSON objects that match the query parameters.                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .id                | Integer           | The unique identifier of the model. Can be passed to the details API call.     |
|                    |                   | (See :ref:`Job Details <rest_job_details>`)                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .job_type          | JSON Object       | The job type that is associated with the count.                                |
|                    |                   | (See :ref:`Job Type Details <rest_job_type_details>`)                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .event             | JSON Object       | The trigger event that is associated with the count.                           |
|                    |                   | (See :ref:`Trigger Event Details <rest_trigger_event_details>`)                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .error             | JSON Object       | The error that is associated with the count.                                   |
|                    |                   | (See :ref:`Error Details <rest_error_details>`)                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .status            | String            | The current status of the job.                                                 |
|                    |                   | Choices: [QUEUED, RUNNING, FAILED, COMPLETED, CANCELED].                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .priority          | Integer           | The priority of the job.                                                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .num_exes          | Integer           | The number of executions this job has had.                                     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .timeout           | Integer           | The maximum amount of time this job can run before being killed (in seconds).  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .max_tries         | Integer           | The maximum number of times to attempt this job when failed (minimum one).     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .cpus_required     | Decimal           | The number of CPUs needed for a job of this type.                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .mem_required      | Decimal           | The amount of RAM in MiB needed for a job of this type.                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .disk_in_required  | Decimal           | The amount of disk space in MiB required for input files for this job.         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .disk_out_required | Decimal           | The amount of disk space in MiB required for output files for this job.        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .created           | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .queued            | ISO-8601 Datetime | When the job was added to the queue to be run when resources are available.    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .started           | ISO-8601 Datetime | When the job started running.                                                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .ended             | ISO-8601 Datetime | When the job stopped running, which could be due to success or failure.        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .last_status_change| ISO-8601 Datetime | When the status of the job was last changed.                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .last_modified     | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .latest_job_exe    | JSON Object       | The most recent execution of the job.                                          |
|                    |                   | (See :ref:`Job Execution Details <rest_job_execution_details>`)                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "count": 68,                                                                                                     |
|        "next": null,                                                                                                    |
|        "previous": null,                                                                                                |
|        "results": [                                                                                                     |
|            {                                                                                                            |
|                "id": 3,                                                                                                 |
|                "job_type": {                                                                                            |
|                    "id": 1,                                                                                             |
|                    "name": "scale-ingest",                                                                              |
|                    "version": "1.0",                                                                                    |
|                    "title": "Scale Ingest",                                                                             |
|                    "description": "Ingests a source file into a workspace",                                             |
|                    "category": "system",                                                                                |
|                    "author_name": null,                                                                                 |
|                    "author_url": null,                                                                                  |
|                    "is_system": true,                                                                                   |
|                    "is_long_running": false,                                                                            |
|                    "is_active": true,                                                                                   |
|                    "is_operational": true,                                                                              |
|                    "is_paused": false,                                                                                  |
|                    "icon_code": "f013"                                                                                  |
|                },                                                                                                       |
|                "job_type_rev": {                                                                                        |
|                    "id": 5,                                                                                             |
|                    "job_type": {                                                                                        |
|                        "id": 1                                                                                          |
|                    },                                                                                                   |
|                    "revision_num": 1                                                                                    |
|                },                                                                                                       |
|                "event": {                                                                                               |
|                    "id": 3,                                                                                             |
|                    "type": "STRIKE_TRANSFER",                                                                           |
|                    "rule": null,                                                                                        |
|                    "occurred": "2015-08-28T17:57:24.261Z"                                                               |
|                },                                                                                                       |
|                "error": null,                                                                                           |
|                "status": "COMPLETED",                                                                                   |
|                "priority": 10,                                                                                          |
|                "num_exes": 1,                                                                                           |
|                "timeout": 1800,                                                                                         |
|                "max_tries": 3,                                                                                          |
|                "cpus_required": 1.0,                                                                                    |
|                "mem_required": 64.0,                                                                                    |
|                "disk_in_required": 0.0,                                                                                 |
|                "disk_out_required": 64.0,                                                                               |
|                "created": "2015-08-28T17:55:41.005Z",                                                                   |
|                "queued": "2015-08-28T17:56:41.005Z",                                                                    |
|                "started": "2015-08-28T17:57:41.005Z",                                                                   |
|                "ended": "2015-08-28T17:58:41.005Z",                                                                     |
|                "last_status_change": "2015-08-28T17:58:45.906Z",                                                        |
|                "last_modified": "2015-08-28T17:58:46.001Z",                                                             |
|                "latest_job_exe": {                                                                                      |
|                    "id": 3,                                                                                             |
|                    "status": "COMPLETED",                                                                               |
|                    "command_arguments": "",                                                                             |
|                    "timeout": 1800,                                                                                     |
|                    "pre_started": null,                                                                                 |
|                    "pre_completed": null,                                                                               |
|                    "pre_exit_code": null,                                                                               |
|                    "job_started": "2015-08-28T17:57:44.703Z",                                                           |
|                    "job_completed": "2015-08-28T17:57:45.906Z",                                                         |
|                    "job_exit_code": null,                                                                               |
|                    "post_started": null,                                                                                |
|                    "post_completed": null,                                                                              |
|                    "post_exit_code": null,                                                                              |
|                    "created": "2015-08-28T17:57:41.033Z",                                                               |
|                    "queued": "2015-08-28T17:57:41.010Z",                                                                |
|                    "started": "2015-08-28T17:57:44.494Z",                                                               |
|                    "ended": "2015-08-28T17:57:45.906Z",                                                                 |
|                    "last_modified": "2015-08-28T17:57:45.992Z",                                                         |
|                    "job": {                                                                                             |
|                        "id": 4                                                                                          |
|                    },                                                                                                   |
|                    "node": {                                                                                            |
|                        "id": 2                                                                                          |
|                    },                                                                                                   |
|                    "error": null                                                                                        |
|                }                                                                                                        |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+
