
.. _rest_v6_job:

v6 Job Services
===============

These services provide access to information about "all", "currently running" and "previously finished" jobs.

.. _rest_v6_job_list:

v6 Job List
-----------

**Example GET /v6/jobs/ API call**

Request: GET http://.../v6/jobs/?batch_id=1

Response: 200 OK

 .. code-block:: javascript 
 
    {
      "count": 1,
      "next": null,
      "previous": null,
      "results": [
        {
          "id": 3,
          "job_type": {
            "id": 1,
            "name": "scale-ingest",
            "title": "Scale Ingest",
            "description": "Ingests a source file into a workspace",
            "revision_num": 1,
            "icon_code": "f013"
          },
          "job_type_rev": {
            "id": 5,
            "job_type": {
              "id": 1
            },
            "revision_num": 1
          },
          "event": {
            "id": 3,
            "type": "STRIKE_TRANSFER",
            "occurred": "2015-08-28T17:57:24.261Z"
          },
          "recipe": { 
            "id": 1,
            "recipe_type": {
              "id": 208,
              "name": "my-recipe-type",
              "title": "My Recipe Type",
              "description": "My Recipe Type Description",
              "revision_num": 1
            }
            "recipe_type_rev": {
              "id": 1
            },
            "event": {
              "id": 1
            }
          },
          "batch": {
            "id": 1,
            "title": "My Batch",
            "description": "My batch of recipes",
            "created": "2015-08-28T17:55:41.005Z"
          },
          "is_superseded": false,
          "superseded_job": null,
          "status": "COMPLETED",
          "node": { 
            "id": 1,
            "hostname": "my-host.example.domain" 
          },
          "error": null,
          "num_exes": 1,
          "input_file_size": 64,
          "source_started": "2015-08-28T17:55:41.005Z",
          "source_ended": "2015-08-28T17:56:41.005Z",
          "created": "2015-08-28T17:55:41.005Z",
          "queued": "2015-08-28T17:56:41.005Z",
          "started": "2015-08-28T17:57:41.005Z",
          "ended": "2015-08-28T17:58:41.005Z",
          "last_status_change": "2015-08-28T17:58:45.906Z",
          "superseded": null,
          "last_modified": "2015-08-28T17:58:46.001Z"
        }
      ]
    }
 
+-------------------------------------------------------------------------------------------------------------------------+
| **Job List**                                                                                                            |
+=========================================================================================================================+
| Returns a list of all jobs.                                                                                             |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/jobs/                                                                                                       |
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
|                    |                   |          | Duplicate it to filter by multiple values.                          |
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
| batch_id           | Integer           | Optional | Return only jobs associated with the given batch identifier.        |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| recipe_id          | Integer           | Optional | Return only jobs associated with the given recipe identifier.       |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| error_category     | String            | Optional | Return only jobs that failed due to an error with a given category. |
|                    |                   |          | Choices: [SYSTEM, DATA, ALGORITHM].                                 |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| error_id           | Integer           | Optional | Return only jobs that failed with this error                        |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| is_superseded      | Boolean           | Optional | Return only jobs matching is_superseded flag. Defaults to all jobs. |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| count               | Integer           | The total number of results that match the query parameters.                  |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| next                | URL               | A URL to the next page of results.                                            |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| previous            | URL               | A URL to the previous page of results.                                        |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| results             | Array             | List of result JSON objects that match the query parameters.                  |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .id                 | Integer           | The unique identifier of the model. Can be passed to the details API call.    |
|                     |                   | (See :ref:`Job Details <rest_v6_job_details>`)                                |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .job_type           | JSON Object       | The job type that is associated with the job.                                 |
|                     |                   | (See :ref:`Job Type Details <rest__v6_job_type_details>`)                     |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .job_type_rev       | JSON Object       | The job type revision that is associated with the job.                        |
|                     |                   | This represents the definition at the time the job was scheduled.             |
|                     |                   | (See :ref:`Job Type Revision Details <rest_v6_job_type_rev_details>`)         |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .event              | JSON Object       | The trigger event that is associated with the job.                            |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .recipe             | JSON Object       | The recipe instance associated with this job.                                 |
|                     |                   | (See :ref:`Recipe Details <rest_v6_recipe_details>`)                          |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .batch              | JSON Object       | The batch instance associated with this job                                   |
|                     |                   | (See :ref:`Batch Details <rest_v6_batch_details>`)                            |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .is_superseded      | Boolean           | Whether this job has been replaced and is now obsolete.                       |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .superseded_job     | JSON Object       | The previous job in the chain that was superseded by this job.                |
|                     |                   | (See :ref:`Job Details <rest_v6_job_details>`)                                |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .status             | String            | The current status of the job.                                                |
|                     |                   | Choices: [QUEUED, RUNNING, FAILED, COMPLETED, CANCELED].                      |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .node               | JSON Object       | The node that the job is/was running on.                                      |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .error              | JSON Object       | The error that is associated with the job.                                    |
|                     |                   | (See :ref:`Error Details <rest_v6_error_details>`)                            |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .num_exes           | Integer           | The number of executions this job has had.                                    |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .input_file_size    | Decimal           | The amount of disk space in MiB required for input files for this job.        |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .source_started     | ISO-8601 Datetime | When collection of the source file started.                                   |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .source_ended       | ISO-8601 Datetime | When collection of the source file ended.                                     |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .created            | ISO-8601 Datetime | When the associated database model was initially created.                     |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .queued             | ISO-8601 Datetime | When the job was added to the queue to be run when resources are available.   |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .started            | ISO-8601 Datetime | When the job started running.                                                 |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .ended              | ISO-8601 Datetime | When the job stopped running, which could be due to success or failure.       |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .last_status_change | ISO-8601 Datetime | When the status of the job was last changed.                                  |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .superseded         | ISO-8601 Datetime | When the the job became superseded by another job.                            |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .last_modified      | ISO-8601 Datetime | When the associated database model was last saved.                            |
+---------------------+-------------------+-------------------------------------------------------------------------------+

.. _rest_job_details:

+-------------------------------------------------------------------------------------------------------------------------+
| **Job Details**                                                                                                         |
+=========================================================================================================================+
| Returns a specific job and all its related model information including executions, recipes, and products.               |
+-------------------------------------------------------------------------------------------------------------------------+
| **DEPRECATED**                                                                                                          |
|                This documentation describes the API **v5** version of the Job Details endpoint response.  Starting with |
|                API **v6** the following fields will be removed: *cpus_required*, *mem_required*, *disk_out_required*,   |
|                *inputs*, *outputs*, *job_exes*, *recipes*.  The following fields will be added: *resources*,            |
|                *execution*, *recipe*.  Additionally, *disk_in_required* is renamed to *input_file_size*, *data* is      |
|                renamed to *input*, and *results* is renamed to *output*.                                                |
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
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .node              | JSON Object       | The node that the job is/was running on.                                       |
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
| is_superseded      | Boolean           | Whether this job has been replaced and is now obsolete.                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| root_superseded_job| JSON Object       | The first job in the current chain of superseded jobs.                         |
|                    |                   | (See :ref:`Job Details <rest_job_details>`)                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| superseded_job     | JSON Object       | The previous job in the chain that was superseded by this job.                 |
|                    |                   | (See :ref:`Job Details <rest_job_details>`)                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| superseded_by_job  | JSON Object       | The next job in the chain that superseded this job.                            |
|                    |                   | (See :ref:`Job Details <rest_job_details>`)                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| delete_superseded  | Boolean           | Whether the products of the previous job should be deleted when superseded.    |
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
| superseded         | ISO-8601 Datetime | When the the job became superseded by another job.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| last_modified      | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| data               | JSON Object       | An interface description for all the job input and output files.               |
|                    |                   | (See :ref:`architecture_jobs_job_data_spec`)                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| results            | JSON Object       | An interface description for all the job results meta-data.                    |
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
| .type              | String            | The type of the input as defined by the job type interface.                    |
|                    |                   | (See :ref:`architecture_jobs_interface_spec`)                                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .value             | Various           | The actual value of the input, which can vary depending on the type. Simple    |
|                    |                   | property inputs will include primitive values, whereas the file or files type  |
|                    |                   | will include a full JSON representation of a Scale file object.                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| outputs            | Array             | A list of job interface outputs merged with their respective job result values.|
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .name              | String            | The name of the output as defined by the job type interface.                   |
|                    |                   | (See :ref:`architecture_jobs_interface_spec`)                                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .type              | String            | The type of the output as defined by the job type interface.                   |
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
|            "shared_mem_required": 0.0,                                                                                  |
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
|                "version": "1.1",                                                                                        |
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
|        "node": {                                                                                                        |
|            "id": 1,                                                                                                     |
|            "hostname": "my-host.example.domain"                                                                         |
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
|        "is_superseded": false,                                                                                          |
|        "root_superseded_job": null,                                                                                     |
|        "superseded_job": null,                                                                                          |
|        "superseded_by_job": null,                                                                                       |
|        "delete_superseded": true,                                                                                       |
|        "created": "2015-08-28T17:55:41.005Z",                                                                           |
|        "queued": "2015-08-28T17:56:41.005Z",                                                                            |
|        "started": "2015-08-28T17:57:41.005Z",                                                                           |
|        "ended": "2015-08-28T17:58:41.005Z",                                                                             |
|        "last_status_change": "2015-08-28T17:58:45.906Z",                                                                |
|        "superseded": null,                                                                                              |
|        "last_modified": "2015-08-28T17:58:46.001Z",                                                                     |
|        "data": {                                                                                                        |
|            "input_data": [                                                                                              |
|                {                                                                                                        |
|                    "name": "input_file",                                                                                |
|                    "file_id": 8480                                                                                      |
|                }                                                                                                        |
|            ],                                                                                                           |
|            "version": "1.1",                                                                                            |
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
| **DEPRECATED**                                                                                                          |
|                This documentation describes the API **v5** version of the Update Job endpoint response.  Starting with  |
|                API **v6** the following fields will be removed: *cpus_required*, *mem_required*, *disk_out_required*,   |
|                *inputs*, *outputs*, *job_exes*, *recipes*.  The following fields will be added: *resources*,            |
|                *execution*, *recipe*.  Additionally, *disk_in_required* is renamed to *input_file_size*, *data* is      |
|                renamed to *input*, and *results* is renamed to *output*.                                                |
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
| Returns a list of jobs with associated input files that changed status in the given time range. Jobs marked as          |
| superseded are excluded by default.                                                                                     |
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
| include_superseded | Boolean           | Optional | Whether to include superseded job instances. Defaults to false.     |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| count               | Integer           | The total number of results that match the query parameters.                  |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| next                | URL               | A URL to the next page of results.                                            |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| previous            | URL               | A URL to the previous page of results.                                        |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| results             | Array             | List of result JSON objects that match the query parameters.                  |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .id                 | Integer           | The unique identifier of the model. Can be passed to the details API call.    |
|                     |                   | (See :ref:`Job Details <rest_job_details>`)                                   |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .job_type           | JSON Object       | The job type that is associated with the job.                                 |
|                     |                   | (See :ref:`Job Type Details <rest_job_type_details>`)                         |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .job_type_rev       | JSON Object       | The job type revision that is associated with the job.                        |
|                     |                   | This represents the definition at the time the job was scheduled.             |
|                     |                   | (See :ref:`Job Type Revision Details <rest_job_type_rev_details>`)            |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .event              | JSON Object       | The trigger event that is associated with the job.                            |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .node               | JSON Object       | The node that the job is/was running on.                                      |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .error              | JSON Object       | The error that is associated with the job.                                    |
|                     |                   | (See :ref:`Error Details <rest_error_details>`)                               |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .status             | String            | The current status of the job.                                                |
|                     |                   | Choices: [QUEUED, RUNNING, FAILED, COMPLETED, CANCELED].                      |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .priority           | Integer           | The priority of the job.                                                      |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .num_exes           | Integer           | The number of executions this job has had.                                    |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .timeout            | Integer           | The maximum amount of time this job can run before being killed (in seconds). |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .max_tries          | Integer           | The maximum number of times to attempt this job when failed (minimum one).    |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .cpus_required      | Decimal           | The number of CPUs needed for a job of this type.                             |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .mem_required       | Decimal           | The amount of RAM in MiB needed for a job of this type.                       |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .disk_in_required   | Decimal           | The amount of disk space in MiB required for input files for this job.        |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .disk_out_required  | Decimal           | The amount of disk space in MiB required for output files for this job.       |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .is_superseded      | Boolean           | Whether this job has been replaced and is now obsolete.                       |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .root_superseded_job| JSON Object       | The first job in the current chain of superseded jobs.                        |
|                     |                   | (See :ref:`Job Details <rest_job_details>`)                                   |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .superseded_job     | JSON Object       | The previous job in the chain that was superseded by this job.                |
|                     |                   | (See :ref:`Job Details <rest_job_details>`)                                   |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .superseded_by_job  | JSON Object       | The next job in the chain that superseded this job.                           |
|                     |                   | (See :ref:`Job Details <rest_job_details>`)                                   |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .delete_superseded  | Boolean           | Whether the products of the previous job should be deleted when superseded.   |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .created            | ISO-8601 Datetime | When the associated database model was initially created.                     |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .queued             | ISO-8601 Datetime | When the job was added to the queue to be run when resources are available.   |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .started            | ISO-8601 Datetime | When the job started running.                                                 |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .ended              | ISO-8601 Datetime | When the job stopped running, which could be due to success or failure.       |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .last_status_change | ISO-8601 Datetime | When the status of the job was last changed.                                  |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .superseded         | ISO-8601 Datetime | When the the job became superseded by another job.                            |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .last_modified      | ISO-8601 Datetime | When the associated database model was last saved.                            |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .input_files        | JSON Object       | A list of files that the job used as input.                                   |
+---------------------+-------------------+-------------------------------------------------------------------------------+
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
|                "node": {                                                                                                |
|                    "id": 1,                                                                                             |
|                    "hostname": "my-host.example.domain"                                                                 |
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
|                "is_superseded": false,                                                                                  |
|                "root_superseded_job": null,                                                                             |
|                "superseded_job": null,                                                                                  |
|                "superseded_by_job": null,                                                                               |
|                "delete_superseded": true,                                                                               |
|                "created": "2015-08-28T17:55:41.005Z",                                                                   |
|                "queued": "2015-08-28T17:56:41.005Z",                                                                    |
|                "started": "2015-08-28T17:57:41.005Z",                                                                   |
|                "ended": "2015-08-28T17:58:41.005Z",                                                                     |
|                "last_status_change": "2015-08-28T17:58:45.906Z",                                                        |
|                "superseded": null,                                                                                      |
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
| Returns a list of all jobs with their latest execution. Jobs marked as superseded are excluded by default.              |
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
| error_category     | String            | Optional | Return only jobs that failed due to an error with a given category. |
|                    |                   |          | Choices: [SYSTEM, DATA, ALGORITHM].                                 |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| include_superseded | Boolean           | Optional | Whether to include superseded job instances. Defaults to false.     |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| count               | Integer           | The total number of results that match the query parameters.                  |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| next                | URL               | A URL to the next page of results.                                            |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| previous            | URL               | A URL to the previous page of results.                                        |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| results             | Array             | List of result JSON objects that match the query parameters.                  |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .id                 | Integer           | The unique identifier of the model. Can be passed to the details API call.    |
|                     |                   | (See :ref:`Job Details <rest_job_details>`)                                   |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .job_type           | JSON Object       | The job type that is associated with the count.                               |
|                     |                   | (See :ref:`Job Type Details <rest_job_type_details>`)                         |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .event              | JSON Object       | The trigger event that is associated with the count.                          |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .node               | JSON Object       | The node that the job is/was running on.                                      |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .error              | JSON Object       | The error that is associated with the count.                                  |
|                     |                   | (See :ref:`Error Details <rest_error_details>`)                               |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .status             | String            | The current status of the job.                                                |
|                     |                   | Choices: [QUEUED, RUNNING, FAILED, COMPLETED, CANCELED].                      |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .priority           | Integer           | The priority of the job.                                                      |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .num_exes           | Integer           | The number of executions this job has had.                                    |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .timeout            | Integer           | The maximum amount of time this job can run before being killed (in seconds). |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .max_tries          | Integer           | The maximum number of times to attempt this job when failed (minimum one).    |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .cpus_required      | Decimal           | The number of CPUs needed for a job of this type.                             |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .mem_required       | Decimal           | The amount of RAM in MiB needed for a job of this type.                       |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .disk_in_required   | Decimal           | The amount of disk space in MiB required for input files for this job.        |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .disk_out_required  | Decimal           | The amount of disk space in MiB required for output files for this job.       |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .is_superseded      | Boolean           | Whether this job has been replaced and is now obsolete.                       |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .root_superseded_job| JSON Object       | The first job in the current chain of superseded jobs.                        |
|                     |                   | (See :ref:`Job Details <rest_job_details>`)                                   |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .superseded_job     | JSON Object       | The previous job in the chain that was superseded by this job.                |
|                     |                   | (See :ref:`Job Details <rest_job_details>`)                                   |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .superseded_by_job  | JSON Object       | The next job in the chain that superseded this job.                           |
|                     |                   | (See :ref:`Job Details <rest_job_details>`)                                   |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .delete_superseded  | Boolean           | Whether the products of the previous job should be deleted when superseded.   |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .created            | ISO-8601 Datetime | When the associated database model was initially created.                     |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .queued             | ISO-8601 Datetime | When the job was added to the queue to be run when resources are available.   |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .started            | ISO-8601 Datetime | When the job started running.                                                 |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .ended              | ISO-8601 Datetime | When the job stopped running, which could be due to success or failure.       |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .last_status_change | ISO-8601 Datetime | When the status of the job was last changed.                                  |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .superseded         | ISO-8601 Datetime | When the the job became superseded by another job.                            |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .last_modified      | ISO-8601 Datetime | When the associated database model was last saved.                            |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .latest_job_exe     | JSON Object       | The most recent execution of the job.                                         |
|                     |                   | (See :ref:`Job Execution Details <rest_job_execution_details>`)               |
+---------------------+-------------------+-------------------------------------------------------------------------------+
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
|                "node": {                                                                                                |
|                    "id": 1,                                                                                             |
|                    "hostname": "my-host.example.domain"                                                                 |
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
|                "is_superseded": false,                                                                                  |
|                "root_superseded_job": null,                                                                             |
|                "superseded_job": null,                                                                                  |
|                "superseded_by_job": null,                                                                               |
|                "delete_superseded": true,                                                                               |
|                "created": "2015-08-28T17:55:41.005Z",                                                                   |
|                "queued": "2015-08-28T17:56:41.005Z",                                                                    |
|                "started": "2015-08-28T17:57:41.005Z",                                                                   |
|                "ended": "2015-08-28T17:58:41.005Z",                                                                     |
|                "last_status_change": "2015-08-28T17:58:45.906Z",                                                        |
|                "superseded": null,                                                                                      |
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

.. _rest_job_input_files:

+-------------------------------------------------------------------------------------------------------------------------+
| **Job Input Files**                                                                                                     |
+=========================================================================================================================+
| Returns detailed information about input files associated with a given Job ID.                                          |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /jobs/{id}/input_files/                                                                                         |
|         Where {id} is the unique identifier of an existing job.                                                         |
+-------------------------------------------------------------------------------------------------------------------------+
| **Query Parameters**                                                                                                    |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| started            | ISO-8601 Datetime | Optional | The start of the time range to query.                               |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| ended              | ISO-8601 Datetime | Optional | The end of the time range to query.                                 |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| time_field         | String            | Optional | Indicates the time field(s) that *started* and *ended* will use for |
|                    |                   |          | time filtering. Valid values are:                                   |
|                    |                   |          |                                                                     |
|                    |                   |          | - *last_modified* - last modification of source file meta-data      |
|                    |                   |          | - *data* - data time of input file (*data_started*, *data_ended*)   |
|                    |                   |          | - *source* - collection time of source file (*source_started*,      |
|                    |                   |          |              *source_ended*)                                        |
|                    |                   |          |                                                                     |
|                    |                   |          | The default value is *last_modified*.                               |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| file_name          | String            | Optional | Returns only input files with this file name.                       |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_input          | String            | Optional | Returns files for this job input.                                   |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| id                 | Integer           | The unique identifier of the file.                                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| file_name          | String            | The name of the file                                                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| file_path          | String            | The relative path of the file in the workspace.                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| file_type          | String            | The type of Scale file, either 'SOURCE' or 'PRODUCT'                           |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| file_size          | Integer           | The size of the file in bytes.                                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| media_type         | String            | The IANA media type of the file.                                               |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| data_type          | String            | A list of string data type "tags" for the file.                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| meta_data          | JSON Object       | A dictionary of key/value pairs that describe file-specific attributes.        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| url                | String            | A hyperlink to the file.                                                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| source_started     | ISO-8601 Datetime | When collection of the source file started.                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| source_ended       | ISO-8601 Datetime | When collection of the source file ended.                                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| data_started       | ISO-8601 Datetime | The start time of the source data being ingested.                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| data_ended         | ISO-8601 Datetime | The ended time of the source data being ingested.                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| created            | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| deleted            | ISO-8601 Datetime | When the file was deleted from storage.                                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| last_modified      | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| uuid               | String            | A unique string of characters that help determine if files are identical.      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| is_deleted         | Boolean           | A flag that will indicate if the file was deleted.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| workspace          | JSON Object       | The workspace storing the file.                                                |
|                    |                   | (See :ref:`Workspace Details <rest_workspace_details>`)                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .id                | Integer           | The unique identifier of the workspace.                                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .name              | String            | The name of the workspace                                                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| countries          | Array             | A list of zero or more strings with the ISO3 country codes for countries       |
|                    |                   | contained in the geographic boundary of this file.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| geometry           | Array             | The geo-spatial footprint of the file.                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| center_point       | Array             | The center point of the file in Lat/Lon Decimal Degree.                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|         "count": 68,                                                                                                    |
|         "next": null,                                                                                                   |
|         "previous": null,                                                                                               |
|         "results": [                                                                                                    |
|             {                                                                                                           |
|                 "id": 7,                                                                                                |
|                 "file_name": "foo.bar",                                                                                 |
|                 "file_path": "file/path/foo.bar",                                                                       |
|                 "file_type": "SOURCE",                                                                                  |
|                 "file_size": 100,                                                                                       |
|                 "media_type": "text/plain",                                                                             |
|                 "data_type": "",                                                                                        |
|                 "meta_data": {...},                                                                                     |
|                 "url": null,                                                                                            |
|                 "source_started": "2016-01-10T00:00:00Z",                                                               |
|                 "source_ended": "2016-01-11T00:00:00Z",                                                                 |
|                 "data_started": "2016-01-10T00:00:00Z",                                                                 |
|                 "data_ended": "2016-01-11T00:00:00Z",                                                                   |
|                 "created": "2017-10-12T18:59:24.398334Z",                                                               |
|                 "deleted": null,                                                                                        |
|                 "last_modified": "2017-10-12T18:59:24.398379Z",                                                         |
|                 "uuid": "",                                                                                             |
|                 "is_deleted": false,                                                                                    |
|                 "workspace": {                                                                                          |
|                     "id": 19,                                                                                           |
|                     "name": "workspace-19"                                                                              |
|                 },                                                                                                      |
|                 "countries": ["TCY", "TCT"],                                                                            |
|                 "geometry" :null,                                                                                       |
|                 "center_point": null                                                                                    |
|             }                                                                                                           |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_job_execution_list_v6:

.. TODO: un-version this rST table link and remove the note when API REST v5 is removed

+---------------------------------------------------------------------------------------------------------------------------+
| **Job Executions List**                                                                                                   |
+===========================================================================================================================+
| Returns a list of job executions associated with a given Job ID.  Returned job executions are ordered by exe_num          |
| descending (most recent first)                                                                                            |
+---------------------------------------------------------------------------------------------------------------------------+
| **NOTE**                                                                                                                  |
|                This API endpoint is available starting with API **v6**.  It replaces a very similar API endpoint which    |
|                you can see described here: :ref:`Job Execution List <rest_job_execution_list>`.                           |
+---------------------------------------------------------------------------------------------------------------------------+
| **GET** /jobs/{id}/executions/                                                                                            |
|         Where {id} is the unique identifier of an existing job.                                                           |
+---------------------------------------------------------------------------------------------------------------------------+
| **Query Parameters**                                                                                                      |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| page                 | Integer           | Optional | The page of the results to return. Defaults to 1.                   |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| page_size            | Integer           | Optional | The size of the page to use for pagination of results.              |
|                      |                   |          | Defaults to 100, and can be anywhere from 1-1000.                   |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| started              | ISO-8601 Datetime | Optional | The start of the time range to query.                               |
|                      |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                      |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| ended                | ISO-8601 Datetime | Optional | The end of the time range to query.                                 |
|                      |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                      |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| status               | String            | Optional | Return only executions with a status matching this string.          |
|                      |                   |          | Choices: [RUNNING, FAILED, COMPLETED, CANCELED].                    |
|                      |                   |          | Duplicate it to filter by multiple values.                          |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| node_id              | Integer           | Optional | Return only executions that ran on a given node.                    |
|                      |                   |          | Duplicate it to filter by multiple values.                          |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| **Successful Response**                                                                                                   |
+----------------------+----------------------------------------------------------------------------------------------------+
| **Status**           | 200 OK                                                                                             |
+----------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**     | *application/json*                                                                                 |
+----------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                           |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| count                | Integer           | The total number of results that match the query parameters.                   |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| next                 | URL               | A URL to the next page of results.                                             |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| previous             | URL               | A URL to the previous page of results.                                         |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| results              | Array             | List of result JSON objects that match the query parameters.                   |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .id                  | Integer           | The unique identifier of the model. Can be passed to the details API call.     |
|                      |                   | (See :ref:`Job Execution Details <rest_job_execution_details>`)                |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .status              | String            | The status of the job execution.                                               |
|                      |                   | Choices: [RUNNING, FAILED, COMPLETED, CANCELED].                               |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .exe_num             | Integer           | The unique job execution number for the job identifer.                         |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .cluster_id          | String            | The Scale cluster identifier.                                                  |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .created             | ISO-8601 Datetime | When the associated database model was initially created.                      |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .queued              | ISO-8601 Datetime | When the job was added to the queue for this run and went to QUEUED status.    |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .started             | ISO-8601 Datetime | When the job was scheduled and went to RUNNING status.                         |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .ended               | ISO-8601 Datetime | When the job execution ended. (FAILED, COMPLETED, or CANCELED)                 |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .job                 | JSON Object       | The job that is associated with the execution.                                 |
|                      |                   | (See :ref:`Job Details <rest_job_details>`)                                    |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .node                | JSON Object       | The node that ran the execution.                                               |
|                      |                   | (See :ref:`Node Details <rest_node_details>`)                                  |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .error               | JSON Object       | The last error that was recorded for the execution.                            |
|                      |                   | (See :ref:`Error Details <rest_error_details>`)                                |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .job_type            | JSON Object       | The job type that is associated with the execution.                            |
|                      |                   | (See :ref:`Job Type Details <rest_job_type_details>`)                          |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .timeout             | Integer           | The maximum amount of time this job can run before being killed (in seconds).  |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .input_file_size     | Float             | The total amount of disk space in MiB for all input files for this execution.  |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                                |
|                                                                                                                           |
|    {                                                                                                                      |
|        "count": 57,                                                                                                       |
|        "next": null,                                                                                                      |
|        "previous": null,                                                                                                  |
|        "results": [                                                                                                       |
|            {                                                                                                              |
|                "id": 3,                                                                                                   |
|                "status": "COMPLETED",                                                                                     |
|                "exe_num": 1,                                                                                              |
|                "cluster_id": "scale_job_1234_263x0",                                                                      |
|                "created": "2015-08-28T17:57:41.033Z",                                                                     |
|                "queued": "2015-08-28T17:57:41.010Z",                                                                      |
|                "started": "2015-08-28T17:57:44.494Z",                                                                     |
|                "ended": "2015-08-28T17:57:45.906Z",                                                                       |
|                "job": {                                                                                                   |
|                    "id": 3,                                                                                               |
|                },                                                                                                         |
|                "node": {                                                                                                  |
|                    "id": 1,                                                                                               |
|                    "hostname": "machine.com"                                                                              |
|                },                                                                                                         |
|                "error": null,                                                                                             |
|                "job_type": {                                                                                              |
|                    "id": 1,                                                                                               |
|                    "name": "scale-ingest",                                                                                |
|                    "version": "1.0",                                                                                      |
|                    "title": "Scale Ingest",                                                                               |
|                    "description": "Ingests a source file into a workspace",                                               |
|                    "category": "system",                                                                                  |
|                    "author_name": null,                                                                                   |
|                    "author_url": null,                                                                                    |
|                    "is_system": true,                                                                                     |
|                    "is_long_running": false,                                                                              |
|                    "is_active": true,                                                                                     |
|                    "is_operational": true,                                                                                |
|                    "is_paused": false,                                                                                    |
|                    "icon_code": "f013"                                                                                    |
|                },                                                                                                         |
|                "timeout": 1800,                                                                                           |
|                "input_file_size": 10.0                                                                                    |
|            }                                                                                                              |
|        ]                                                                                                                  |
|    }                                                                                                                      |
+---------------------------------------------------------------------------------------------------------------------------+

.. _rest_job_execution_details_v6:

.. TODO: un-version this rst table link and remove the note when API REST v5 is removed

+---------------------------------------------------------------------------------------------------------------------------+
| **Job Execution Details**                                                                                                 |
+===========================================================================================================================+
| Returns a specific job execution and all its related model information including job, node, environment, and results.     |
+---------------------------------------------------------------------------------------------------------------------------+
| **NOTE**                                                                                                                  |
|                This API endpoint is available starting with API **v6**.  It replaces a very similar API endpoint which    |
|                you can see described here: :ref:`Job Execution List <rest_job_execution_details>`.                        |
+---------------------------------------------------------------------------------------------------------------------------+
| **GET** /jobs/{id}/executions/{exe_num}                                                                                   |
|         Where {id} is the unique identifier of an existing job and {exe_num} is the execution number of a job execution   |
|         as it relates to the job.                                                                                         |
+----------------------+----------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                   |
+----------------------+----------------------------------------------------------------------------------------------------+
| **Status**           | 200 OK                                                                                             |
+----------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**     | *application/json*                                                                                 |
+----------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                           |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| id                   | Integer           | The unique identifier of the model. Can be passed to the details API call.     |
|                      |                   | (See :ref:`Job Execution Details <rest_job_execution_details>`)                |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| status               | String            | The status of the job execution.                                               |
|                      |                   | Choices: [RUNNING, FAILED, COMPLETED, CANCELED].                               |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| exe_num              | Integer           | The unique job execution number for the job identifer.                         |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| cluster_id           | String            | The Scale cluster identifier.                                                  |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| created              | ISO-8601 Datetime | When the associated database model was initially created.                      |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| queued               | ISO-8601 Datetime | When the job was added to the queue for this run and went to QUEUED status.    |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| started              | ISO-8601 Datetime | When the job was scheduled and went to RUNNING status.                         |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| ended                | ISO-8601 Datetime | When the job execution ended. (FAILED, COMPLETED, or CANCELED)                 |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| job                  | JSON Object       | The job that is associated with the execution.                                 |
|                      |                   | (See :ref:`Job Details <rest_job_details>`)                                    |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| node                 | JSON Object       | The node that ran the execution.                                               |
|                      |                   | (See :ref:`Node Details <rest_node_details>`)                                  |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| error                | JSON Object       | The last error that was recorded for the execution.                            |
|                      |                   | (See :ref:`Error Details <rest_error_details>`)                                |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| job_type             | JSON Object       | The job type that is associated with the execution.                            |
|                      |                   | (See :ref:`Job Type Details <rest_job_type_details>`)                          |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| timeout              | Integer           | The maximum amount of time this job can run before being killed (in seconds).  |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| input_file_size      | Float             | The total amount of disk space in MiB for all input files for this execution.  |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| task_results         | JSON Object       | JSON description of the task results for this execution.                       |
|                      |                   | (See :ref:`Job Task Results <architecture_jobs_task_results_spec>`)            |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| resources            | JSON Object       | JSON description describing the resources allocated to this execution.         |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| configuration        | JSON Object       | JSON description of the configuration for running the job                      |
|                      |                   | (See :ref:`Job Execution Configuration <architecture_jobs_exe_configuration>`) |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| output               | JSON Object       | JSON description of the job output.                                            |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                                |
|                                                                                                                           |
|  {                                                                                                                        |
|      "id": 3,                                                                                                             |
|      "status": "COMPLETED",                                                                                               |
|      "exe_num": 1,                                                                                                        |
|      "cluster_id": "scale_job_1234_263x0",                                                                                |
|      "created": "2015-08-28T17:57:41.033Z",                                                                               |
|      "queued": "2015-08-28T17:57:41.010Z",                                                                                |
|      "started": "2015-08-28T17:57:44.494Z",                                                                               |
|      "ended": "2015-08-28T17:57:45.906Z",                                                                                 |
|      "job": {                                                                                                             |
|          "id": 3,                                                                                                         |
|      },                                                                                                                   |
|      "node": {                                                                                                            |
|          "id": 1,                                                                                                         |
|          "hostname": "machine.com"                                                                                        |
|      },                                                                                                                   |
|      "error": null,                                                                                                       |
|      "job_type": {                                                                                                        |
|          "id": 1,                                                                                                         |
|          "name": "scale-ingest",                                                                                          |
|          "version": "1.0",                                                                                                |
|          "title": "Scale Ingest",                                                                                         |
|          "description": "Ingests a source file into a workspace",                                                         |
|          "category": "system",                                                                                            |
|          "author_name": null,                                                                                             |
|          "author_url": null,                                                                                              |
|          "is_system": true,                                                                                               |
|          "is_long_running": false,                                                                                        |
|          "is_active": true,                                                                                               |
|          "is_operational": true,                                                                                          |
|          "is_paused": false,                                                                                              |
|          "icon_code": "f013"                                                                                              |
|      },                                                                                                                   |
|      "timeout": 1800,                                                                                                     |
|      "input_file_size": 10.0,                                                                                             |
|      "task_results": null,                                                                                                |
|      "resources": {                                                                                                       |
|          "version": "1.0",                                                                                                |
|          "resources": {                                                                                                   |
|              "mem": 128.0,                                                                                                |
|              "disk": 11.0,                                                                                                |
|              "cpus": 1.0                                                                                                  |
|          }                                                                                                                |
|      },                                                                                                                   |
|      "configuration": {                                                                                                   |
|          "tasks": [...],                                                                                                  |
|          "version": "2.0"}                                                                                                |
|      "output": {                                                                                                          |
|          "output_data": [                                                                                                 |
|              {                                                                                                            |
|                  "name": "output_file",                                                                                   |
|                  "file_id": 3                                                                                             |
|              }                                                                                                            |
|          ],                                                                                                               |
|          "version": "1.0"                                                                                                 |
|      }                                                                                                                    |
|  }                                                                                                                        |
+---------------------------------------------------------------------------------------------------------------------------+

.. _rest_job_cancel:

+-------------------------------------------------------------------------------------------------------------------------+
| **Cancel Jobs**                                                                                                         |
+=========================================================================================================================+
| Cancels the jobs that fit the given filter criteria. The canceling will be done asynchronously, so the response will    |
| just indicate that the cancel request has been accepted.                                                                |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /jobs/cancel/                                                                                                  |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| started            | ISO-8601 Datetime | Optional | The start of the time range to query.                               |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| ended              | ISO-8601 Datetime | Optional | End of the time range to query, defaults to the current time.       |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| error_categories   | Array[String]     | Optional | Cancel only jobs that failed with these error categories            |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| error_ids          | Array[String]     | Optional | Cancel only jobs that failed with these errors                      |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_ids            | Array[Integer]    | Optional | Cancel only jobs with these IDs                                     |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| status             | String            | Optional | Cancel only jobs with this status                                   |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_ids       | Array[Integer]    | Optional | Cancel only jobs with these job types                               |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|         "started": "2016-01-01T00:00:00Z",                                                                              |
|         "ended": "2016-01-02T00:00:00Z",                                                                                |
|         "status": "FAILED",                                                                                             |
|         "job_type_ids": [1, 2, 3],                                                                                      |
|         "error_categories": ["SYSTEM"]                                                                                  |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 202 Accepted                                                                                       |
+--------------------+----------------------------------------------------------------------------------------------------+
| No response body                                                                                                        |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_job_requeue:

+-------------------------------------------------------------------------------------------------------------------------+
| **Requeue Jobs**                                                                                                        |
+=========================================================================================================================+
| Re-queues the FAILED/CANCELED jobs that fit the given filter criteria. The re-queuing will be done asynchronously, so   |
| the response will just indicate that the re-queue request has been accepted.                                            |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /jobs/requeue/                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| started            | ISO-8601 Datetime | Optional | The start of the time range to query.                               |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| ended              | ISO-8601 Datetime | Optional | End of the time range to query, defaults to the current time.       |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| error_categories   | Array[String]     | Optional | Re-queue only jobs that failed with these error categories          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| error_ids          | Array[String]     | Optional | Re-queue only jobs that failed with these errors                    |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_ids            | Array[Integer]    | Optional | Re-queue only jobs with these IDs                                   |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| status             | String            | Optional | Re-queue only jobs with this status                                 |
|                    |                   |          | Choices: [CANCELED, FAILED]                                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_ids       | Array[Integer]    | Optional | Re-queue only jobs with these job types                             |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| priority           | Integer           | Optional | Change the priority of matching jobs when adding them to the queue. |
|                    |                   |          | Defaults to jobs current priority, lower number is higher priority. |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|         "started": "2016-01-01T00:00:00Z",                                                                              |
|         "ended": "2016-01-02T00:00:00Z",                                                                                |
|         "status": "FAILED",                                                                                             |
|         "job_type_ids": [1, 2, 3],                                                                                      |
|         "error_categories": ["SYSTEM"]                                                                                  |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 202 Accepted                                                                                       |
+--------------------+----------------------------------------------------------------------------------------------------+
| No response body                                                                                                        |
+-------------------------------------------------------------------------------------------------------------------------+
