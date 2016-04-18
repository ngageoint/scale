
.. _rest_queue:

Queue Services
========================================================================================================================

These services provide access to information about the current and historical queue state, as well as allowing a user to
place jobs and recipes on the queue for processing.

+-------------------------------------------------------------------------------------------------------------------------+
| **Job Load**                                                                                                            |
+=========================================================================================================================+
| Returns statistics about the current job load organized by job type. Jobs are counted when they are in the PENDING,     |
| QUEUED, and RUNNING states. NOTE: Time range must be within a one month period (31 days).                               |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /load/                                                                                                          |
+-------------------------------------------------------------------------------------------------------------------------+
| **Query Parameters**                                                                                                    |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| started            | ISO-8601 Datetime | Required | The start of the time range to query.                               |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
|                    |                   |          | Defaults to the past 1 week.                                        |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| ended              | ISO-8601 Datetime | Required | End of the time range to query, defaults to the current time.       |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_id        | Integer           | Optional | Count only jobs with a given job type identifier.                   |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_name      | String            | Optional | Count only jobs with a given job type name.                         |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_category  | String            | Optional | Count only jobs with a given job type category.                     |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_priority  | Integer           | Optional | Count only jobs with a given job type priority.                     |
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
| .time              | ISO-8601 Datetime | When the counts were actually recorded.                                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .pending_count     | Integer           | The number of jobs in the pending state at the measured time.                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .queued_count      | Integer           | The number of jobs in the queued state at the measured time.                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .running_count     | Integer           | The number of jobs in the running state at the measured time.                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "count": 28,                                                                                                     |
|        "next": null,                                                                                                    |
|        "previous": null,                                                                                                |
|        "results": [                                                                                                     |
|            {                                                                                                            |
|                "time": "2015-10-21T00:00:00Z",                                                                          |
|                "pending_count": 1,                                                                                      |
|                "queued_count": 0,                                                                                       |
|                "running_count": 0                                                                                       |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

+-------------------------------------------------------------------------------------------------------------------------+
| **Get Queue Status**                                                                                                    |
+=========================================================================================================================+
| Returns the current status of the queue by grouping the queued jobs by their types                                      |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /queue/status/                                                                                                  |
+-------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| queue_status       | List              | List of job types on the queue with meta-data                                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| count              | Integer           | The number of jobs of this type on the queue                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| longest_queued     | ISO-8601 Datetime | When the job that has been queued the longest of this type was queued          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| job_type_name      | String            | The name of this job type                                                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| job_type_version   | String            | The version of this job type                                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| highest_priority   | Integer           | The highest priority of any job of this type                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| is_job_type_paused | Boolean           | If this job type has been paused (jobs of this type won't be scheduled)        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "queue_status": [                                                                                                |
|           {                                                                                                             |
|              "count": 19,                                                                                               |
|              "longest_queued": "1970-01-01T00:00:00.000Z",                                                              |
|              "job_type_name": "My Job Type",                                                                            |
|              "job_type_version": "1.0",                                                                                 |
|              "highest_priority": 1,                                                                                     |
|              "is_job_type_paused": false                                                                                |
|           },                                                                                                            |
|           ...                                                                                                           |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

+-------------------------------------------------------------------------------------------------------------------------+
| **Queue New Job**                                                                                                       |
+=========================================================================================================================+
| Creates a new job and places it onto the queue                                                                          |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /queue/new-job/                                                                                                |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| job_type_id        | Integer           | The ID of the job type for the new job                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| job_data           | JSON Object       | JSON defining the data to run the job on, see :ref:`architecture_jobs_job_data`|
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "job_type_id": 1234,                                                                                             |
|        "job_data": {                                                                                                    |
|            "version": "1.0",                                                                                            |
|            "input_data": [                                                                                              |
|                {                                                                                                        |
|                    "name": "Param 1",                                                                                   |
|                    "value": "HELLO"                                                                                     |
|                },                                                                                                       |
|                {                                                                                                        |
|                    "name": "Param 2",                                                                                   |
|                    "file_id": 9876                                                                                      |
|                }                                                                                                        |
|            ],                                                                                                           |
|            "output_data": [                                                                                             |
|                {                                                                                                        |
|                    "name": "Param 3",                                                                                   |
|                    "workspace_id": 15                                                                                   |
|                }                                                                                                        |
|            ]                                                                                                            |
|        }                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 201 CREATED                                                                                        |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Location**       | URL pointing to the details for the newly queued job execution                                     |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
|                    | JSON Object       | All fields are the same as the job details model.                              |
|                    |                   | The status will always be QUEUED and a new job_exe will be included.           |
|                    |                   | (See :ref:`Job Details <rest_job_details>`)                                    |
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
|        "input_files": [                                                                                                 |
|            {                                                                                                            |
|                "id": 2,                                                                                                 |
|                "workspace": {                                                                                           |
|                    "id": 1,                                                                                             |
|                    "name": "Raw Source"                                                                                 |
|                },                                                                                                       |
|                "file_name": "input_file.txt",                                                                           | 
|                "media_type": "text/plain",                                                                              |
|                "file_size": 1234,                                                                                       |
|                "data_type": [],                                                                                         | 
|                "is_deleted": false,                                                                                     |
|                "uuid": "c8928d9183fc99122948e7840ec9a0fd",                                                              |
|                "url": "http://host.com/input_file.txt",                                                                 |
|                "created": "2015-09-10T15:24:53.962Z",                                                                   |
|                "deleted": null,                                                                                         |
|                "data_started": "2015-09-10T14:50:49Z",                                                                  |
|                "data_ended": "2015-09-10T14:51:05Z",                                                                    |
|                "geometry": null,                                                                                        |
|                "center_point": null,                                                                                    |
|                "meta_data": {...}                                                                                       |
|                "last_modified": "2015-09-10T15:25:02.808Z"                                                              |
|            }                                                                                                            |
|        ],                                                                                                               |
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
|        "products": [                                                                                                    |
|            {                                                                                                            |
|                "id": 8484,                                                                                              |
|                "workspace": {                                                                                           |
|                    "id": 2,                                                                                             | 
|                    "name": "Products"                                                                                   | 
|                },                                                                                                       |
|                "file_name": "file.kml",                                                                                 |
|                "media_type": "application/vnd.google-earth.kml+xml",                                                    |
|                "file_size": 1234,                                                                                       |
|                "data_type": [],                                                                                         |
|                "is_deleted": false,                                                                                     |
|                "uuid": "c8928d9183fc99122948e7840ec9a0fd",                                                              |
|                "url": "http://host.com/file/path/my_file.kml",                                                          | 
|                "created": "2015-09-01T17:27:48.477Z",                                                                   | 
|                "deleted": null,                                                                                         |
|                "data_started": null,                                                                                    |
|                "data_ended": null,                                                                                      |
|                "geometry": null,                                                                                        |
|                "center_point": null,                                                                                    | 
|                "meta_data": {},                                                                                         |
|                "last_modified": "2015-09-01T17:27:49.639Z",                                                             |
|                "is_operational": true,                                                                                  |
|                "is_published": true,                                                                                    |
|                "published": "2015-09-01T17:27:49.461Z",                                                                 |
|                "unpublished": null,                                                                                     |
|                "job_type": {                                                                                            |
|                    "id": 8                                                                                              |
|                },                                                                                                       |
|                "job": {                                                                                                 |
|                    "id": 35                                                                                             |
|                },                                                                                                       |
|                "job_exe": {                                                                                             |
|                    "id": 19                                                                                             |
|                }                                                                                                        |
|            }                                                                                                            |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

+-------------------------------------------------------------------------------------------------------------------------+
| **Queue New Recipe**                                                                                                    |
+=========================================================================================================================+
| Creates a new recipe and places it onto the queue                                                                       |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /queue/new-recipe/                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| recipe_type_id     | Integer           | The ID of the recipe type to queue                                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| recipe_data        | JSON Object       | Defines the data to run the recipe, see :ref:`architecture_jobs_recipe_data`   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "recipe_type_id": 1234,                                                                                          |
|        "recipe_data": {                                                                                                 |
|            "version": "1.0",                                                                                            |
|            "input_data": [                                                                                              |
|                {                                                                                                        |
|                    "name": "image",                                                                                     |
|                    "file_id": 1234                                                                                      |
|                },                                                                                                       |
|                {                                                                                                        |
|                    "name": "georeference_data",                                                                         |
|                    "file_id": 1235                                                                                      |
|                }                                                                                                        |
|            ],                                                                                                           |
|            "workspace_id": 12                                                                                           |
|        }                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 201 CREATED                                                                                        |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Location**       | URL pointing to the details for the newly queued recipe data                                       |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
|                    | JSON Object       | All fields are the same as the recipe details model.                           |
|                    |                   | (See :ref:`Recipe Details <rest_recipe_details>`)                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "id": 72,                                                                                                        |
|        "recipe_type": {                                                                                                 |
|            "id": 1,                                                                                                     |
|            "name": "MyRecipe",                                                                                          |
|            "version": "1.0.0",                                                                                          |
|            "description": "This is a description of the recipe",                                                        |
|            "is_active": true,                                                                                           |
|            "definition": {                                                                                              |
|                "input_data": [                                                                                          |
|                    {                                                                                                    |
|                        "media_types": [                                                                                 |
|                            "image/png"                                                                                  |
|                        ],                                                                                               |
|                        "type": "file",                                                                                  |
|                        "name": "input_file"                                                                             |
|                    }                                                                                                    |
|                ],                                                                                                       |
|                "version": "1.0",                                                                                        |
|                "jobs": [                                                                                                |
|                    {                                                                                                    |
|                        "recipe_inputs": [                                                                               |
|                            {                                                                                            |
|                                "job_input": "input_file",                                                               |
|                                "recipe_input": "input_file"                                                             |
|                            }                                                                                            |
|                        ],                                                                                               |
|                        "name": "kml",                                                                                   |
|                        "job_type": {                                                                                    |
|                            "name": "kml-footprint",                                                                     |
|                            "version": "1.2.3"                                                                           |
|                        }                                                                                                |
|                    }                                                                                                    |
|                ]                                                                                                        |
|            },                                                                                                           |
|            "created": "2015-06-15T19:03:26.346Z",                                                                       |
|            "last_modified": "2015-06-15T19:03:26.346Z",                                                                 |
|            "archived": null                                                                                             |
|        },                                                                                                               |
|        "event": {                                                                                                       |
|            "id": 7,                                                                                                     |
|            "type": "PARSE",                                                                                             |
|            "rule": {                                                                                                    |
|                "id": 8,                                                                                                 |
|                "type": "PARSE",                                                                                         |
|                "is_active": true,                                                                                       |
|                "configuration": {                                                                                       |
|                    "version": "1.0",                                                                                    |
|                    "condition": {                                                                                       |
|                        "media_type": "image/png",                                                                       |
|                        "data_types": []                                                                                 |
|                    },                                                                                                   |
|                    "data": {                                                                                            |
|                        "input_data_name": "input_file",                                                                 |
|                        "workspace_name": "products"                                                                     |
|                    }                                                                                                    |
|                }                                                                                                        |
|            },                                                                                                           |
|            "occurred": "2015-08-28T19:03:59.054Z",                                                                      |
|            "description": {                                                                                             |
|                "file_name": "data-file.png",                                                                            |
|                "version": "1.0",                                                                                        |
|                "parse_id": 1                                                                                            |
|            }                                                                                                            |
|        },                                                                                                               |
|        "created": "2015-06-15T19:03:26.346Z",                                                                           |
|        "completed": "2015-06-15T19:05:26.346Z",                                                                         |
|        "last_modified": "2015-06-15T19:05:26.346Z"                                                                      |
|        "data": {                                                                                                        |
|            "input_data": [                                                                                              |
|                {                                                                                                        |
|                    "name": "input_file",                                                                                |
|                    "file_id": 4,                                                                                        |
|                }                                                                                                        |
|            ],                                                                                                           |
|            "version": "1.0"                                                                                             |
|            "workspace_id": 2                                                                                            |
|        }                                                                                                                |
|        "input_files": [                                                                                                 |
|            {                                                                                                            |
|                "id": 4,                                                                                                 |
|                "workspace": {                                                                                           |
|                    "id": 1,                                                                                             |
|                    "name": "Raw Source"                                                                                 |
|                },                                                                                                       |
|                "file_name": "input_file.txt",                                                                           | 
|                "media_type": "text/plain",                                                                              |
|                "file_size": 1234,                                                                                       |
|                "data_type": [],                                                                                         | 
|                "is_deleted": false,                                                                                     |
|                "uuid": "c8928d9183fc99122948e7840ec9a0fd",                                                              |
|                "url": "http://host.com/input_file.txt",                                                                 |
|                "created": "2015-09-10T15:24:53.962Z",                                                                   |
|                "deleted": null,                                                                                         |
|                "data_started": "2015-09-10T14:50:49Z",                                                                  |
|                "data_ended": "2015-09-10T14:51:05Z",                                                                    |
|                "geometry": null,                                                                                        |
|                "center_point": null,                                                                                    |
|                "meta_data": {...}                                                                                       |
|                "last_modified": "2015-09-10T15:25:02.808Z"                                                              |
|            }                                                                                                            |
|        ],                                                                                                               |
|        "jobs": [                                                                                                        |
|            {                                                                                                            |
|                "job_name": "kml",                                                                                       |
|                "job": {                                                                                                 |
|                    "id": 7,                                                                                             |
|                    "job_type": {                                                                                        |
|                        "id": 8,                                                                                         |
|                        "name": "kml-footprint",                                                                         |
|                        "version": "1.2.3",                                                                              |
|                        "title": "KML Footprint",                                                                        |
|                        "description": "Creates a KML footprint",                                                        |
|                        "category": "footprint",                                                                         |
|                        "author_name": null,                                                                             |
|                        "author_url": null,                                                                              |
|                        "is_system": false,                                                                              |
|                        "is_long_running": false,                                                                        |
|                        "is_active": true,                                                                               |
|                        "is_operational": true,                                                                          |
|                        "is_paused": false,                                                                              |
|                        "icon_code": "f0ac"                                                                              |
|                    },                                                                                                   |
|                    "job_type_rev": {                                                                                    |
|                        "id": 5,                                                                                         |
|                        "job_type": {                                                                                    |
|                            "id": 8                                                                                      |
|                        },                                                                                               |
|                        "revision_num": 1                                                                                |
|                    },                                                                                                   |
|                    "event": {                                                                                           |
|                        "id": 7,                                                                                         |
|                        "type": "PARSE",                                                                                 |
|                        "rule": {                                                                                        |
|                            "id": 8                                                                                      |
|                        },                                                                                               |
|                        "occurred": "2015-08-28T19:03:59.054Z"                                                           |
|                    },                                                                                                   |
|                    "error": null,                                                                                       |
|                    "status": "COMPLETED",                                                                               |
|                    "priority": 210,                                                                                     |
|                    "num_exes": 1,                                                                                       |
|                    "timeout": 1800,                                                                                     |
|                    "max_tries": 3,                                                                                      |
|                    "cpus_required": 1.0,                                                                                |
|                    "mem_required": 15360.0,                                                                             |
|                    "disk_in_required": 2.0,                                                                             |
|                    "disk_out_required": 16.0,                                                                           |
|                    "created": "2015-08-28T17:55:41.005Z",                                                               |
|                    "queued": "2015-08-28T17:56:41.005Z",                                                                |
|                    "started": "2015-08-28T17:57:41.005Z",                                                               |
|                    "ended": "2015-08-28T17:58:41.005Z",                                                                 |
|                    "last_status_change": "2015-08-28T17:58:45.906Z",                                                    |
|                    "last_modified": "2015-08-28T17:58:46.001Z"                                                          |
|                }                                                                                                        |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

+-------------------------------------------------------------------------------------------------------------------------+
| **Requeue Jobs**                                                                                                        |
+=========================================================================================================================+
| Increases the maximum failure allowance for existing jobs and puts them back on the queue.                              |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /queue/requeue-jobs/                                                                                           |
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
| status             | String            | Optional | Queue only jobs with a status matching these strings.               |
|                    |                   |          | Choices: [CANCELED, FAILED].                                        |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_ids            | Array[Integer]    | Optional | Queue only jobs with a given identifier.                            |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_ids       | Array[Integer]    | Optional | Queue only jobs with a given job type identifier.                   |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_names     | Array[String]     | Optional | Queue only jobs with a given job type name.                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_categories| Array[String]     | Optional | Queue only jobs with a given job type category.                     |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| priority           | Integer           | Optional | Change the priority of matching jobs when adding them to the queue. |
|                    |                   |          | Defaults to jobs current priority, lower number is higher priority. |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
|                    | JSON Object       | All fields are the same as the jobs model.                                     |
|                    |                   | The status will be PENDING or BLOCKED if the job has never been queued.        |
|                    |                   | The status will be QUEUED if the job has been previously queued.               |
|                    |                   | (See :ref:`Job List <rest_job_list>`)                                          |
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
|                "status": "QUEUED",                                                                                      |
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
