
.. _rest_job_execution:

Job Execution Services
======================

These services provide access to information about "all", "currently running" and "previously finished" job executions.

.. _rest_job_execution_list:

+-------------------------------------------------------------------------------------------------------------------------+
| **Job Execution List**                                                                                                  |
+=========================================================================================================================+
| Returns a list of all job executions.                                                                                   |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /job-executions/                                                                                                |
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
|                    |                   |          | Duplicate it to multi-sort, (ex: order=status&order=created).       |
|                    |                   |          | Nested objects require a delimiter (ex: order=job_type__name).      |
|                    |                   |          | Prefix fields with a dash to reverse the sort, (ex: order=-status). |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| status             | String            | Optional | Return only executions with a status matching this string.          |
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
| node_id            | Integer           | Optional | Return only executions that ran on a given node.                    |
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
|                    |                   | (See :ref:`Job Execution Details <rest_job_execution_details>`)                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .status            | String            | The status of the job execution.                                               |
|                    |                   | Choices: [QUEUED, RUNNING, FAILED, COMPLETED, CANCELED].                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .command_arguments | String            | The argument string to execute on the command line for this job execution.     | 
|                    |                   | This field is populated when the job execution is scheduled to run on a node   |
|                    |                   | and is updated when any needed pre-job steps are run.                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .timeout           | Integer           | The maximum amount of time this job can run before being killed (in seconds).  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .pre_started       | ISO-8601 Datetime | When the pre-job steps were started on a node.                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .pre_completed     | ISO-8601 Datetime | When the pre-job steps were completed on a node.                               |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .pre_exit_code     | Integer           | The exit code of the pre-steps job process for this job execution.             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .job_started       | ISO-8601 Datetime | When the actual job started running on a node.                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .job_completed     | ISO-8601 Datetime | When the actual job completed running on a node.                               |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .job_exit_code     | Integer           | The exit code of the main job process for this job execution.                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .post_started      | ISO-8601 Datetime | When the post-job steps were started on a node.                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .post_completed    | ISO-8601 Datetime | When the post-job steps were completed on a node.                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .post_exit_code    | Integer           | The exit code of the post-steps job process for this job execution.            |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .created           | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .queued            | ISO-8601 Datetime | When the job was added to the queue for this run and went to QUEUED status.    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .started           | ISO-8601 Datetime | When the job was scheduled and went to RUNNING status.                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .ended             | ISO-8601 Datetime | When the job execution ended. (FAILED, COMPLETED, or CANCELED)                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .last_modified     | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .job               | JSON Object       | The job that is associated with the execution.                                 |
|                    |                   | (See :ref:`Job Details <rest_job_details>`)                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .node              | JSON Object       | The node that ran the execution.                                               |
|                    |                   | (See :ref:`Node Details <rest_node_details>`)                                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .error             | JSON Object       | The last error that was recorded for the execution.                            |
|                    |                   | (See :ref:`Error Details <rest_error_details>`)                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "count": 57,                                                                                                     | 
|        "next": null,                                                                                                    |
|        "previous": null,                                                                                                |
|        "results": [                                                                                                     |
|            {                                                                                                            |
|                "id": 3,                                                                                                 |
|                "status": "COMPLETED",                                                                                   |
|                "command_arguments": "",                                                                                 |
|                "timeout": 1800,                                                                                         |
|                "pre_started": null,                                                                                     |
|                "pre_completed": null,                                                                                   |
|                "pre_exit_code": null,                                                                                   |
|                "job_started": "2015-08-28T17:57:44.703Z",                                                               |
|                "job_completed": "2015-08-28T17:57:45.906Z",                                                             |
|                "job_exit_code": null,                                                                                   |
|                "post_started": null,                                                                                    |
|                "post_completed": null,                                                                                  |
|                "post_exit_code": null,                                                                                  |
|                "created": "2015-08-28T17:57:41.033Z",                                                                   |
|                "queued": "2015-08-28T17:57:41.010Z",                                                                    |
|                "started": "2015-08-28T17:57:44.494Z",                                                                   |
|                "ended": "2015-08-28T17:57:45.906Z",                                                                     |
|                "last_modified": "2015-08-28T17:57:45.992Z",                                                             |
|                "job": {                                                                                                 |
|                    "id": 3,                                                                                             |
|                    "job_type": {                                                                                        |
|                        "id": 1,                                                                                         |
|                        "name": "scale-ingest",                                                                          |
|                        "version": "1.0",                                                                                |
|                        "title": "Scale Ingest",                                                                         |
|                        "description": "Ingests a source file into a workspace",                                         |
|                        "category": "system",                                                                            |
|                        "author_name": null,                                                                             |
|                        "author_url": null,                                                                              |
|                        "is_system": true,                                                                               |
|                        "is_long_running": false,                                                                        |
|                        "is_active": true,                                                                               |
|                        "is_operational": true,                                                                          |
|                        "is_paused": false,                                                                              |
|                        "icon_code": "f013"                                                                              |
|                    },                                                                                                   |
|                    "job_type_rev": {                                                                                    |
|                        "id": 2                                                                                          |
|                    },                                                                                                   |
|                    "event": {                                                                                           |
|                        "id": 3                                                                                          |
|                    },                                                                                                   |
|                    "error": null,                                                                                       |
|                    "status": "COMPLETED",                                                                               |
|                    "priority": 10,                                                                                      |
|                    "num_exes": 1                                                                                        |
|                },                                                                                                       |
|                "node": {                                                                                                |
|                    "id": 1,                                                                                             |
|                    "hostname": "machine.com",                                                                           |
|                    "port": 5051,                                                                                        |
|                    "slave_id": "20150821-123454-1683014024-5050-8216-S2"                                                |
|                },                                                                                                       |
|                "error": null                                                                                            |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_job_execution_details:

+---------------------------------------------------------------------------------------------------------------------------+
| **Job Execution Details**                                                                                                 |
+===========================================================================================================================+
| Returns a specific job execution and all its related model information including job, node, environment, and results.     |
+---------------------------------------------------------------------------------------------------------------------------+
| **GET** /job-executions/{id}/                                                                                             |
|         Where {id} is the unique identifier of an existing model.                                                         |
+---------------------------------------------------------------------------------------------------------------------------+
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
|                      |                   | Choices: [QUEUED, RUNNING, FAILED, COMPLETED, CANCELED].                       |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| command_arguments    | String            | The argument string to execute on the command line for this job execution.     | 
|                      |                   | This field is populated when the job execution is scheduled to run on a node   |
|                      |                   | and is updated when any needed pre-job steps are run.                          |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| timeout              | Integer           | The maximum amount of time this job can run before being killed (in seconds).  |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| pre_started          | ISO-8601 Datetime | When the pre-job steps were started on a node.                                 |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| pre_completed        | ISO-8601 Datetime | When the pre-job steps were completed on a node.                               |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| pre_exit_code        | Integer           | The exit code of the pre-steps job process for this job execution.             |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| job_started          | ISO-8601 Datetime | When the actual job started running on a node.                                 |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| job_completed        | ISO-8601 Datetime | When the actual job completed running on a node.                               |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| job_exit_code        | Integer           | The exit code of the main job process for this job execution.                  |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| post_started         | ISO-8601 Datetime | When the post-job steps were started on a node.                                |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| post_completed       | ISO-8601 Datetime | When the post-job steps were completed on a node.                              |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| post_exit_code       | Integer           | The exit code of the post-steps job process for this job execution.            |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| created              | ISO-8601 Datetime | When the associated database model was initially created.                      |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| queued               | ISO-8601 Datetime | When the job was added to the queue for this run and went to QUEUED status.    |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| started              | ISO-8601 Datetime | When the job was scheduled and went to RUNNING status.                         |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| ended                | ISO-8601 Datetime | When the job execution ended. (FAILED, COMPLETED, or CANCELED)                 |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| last_modified        | ISO-8601 Datetime | When the associated database model was last saved.                             |
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
| environment          | JSON Object       | An interface description for the environment the job execution executed in.    |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| cpus_scheduled       | Decimal           | The number of CPUs scheduled for the execution.                                |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| mem_scheduled        | Decimal           | The amount of RAM in MiB scheduled for the execution.                          |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| disk_in_scheduled    | Decimal           | The amount of disk space in MiB scheduled for input files for the execution.   |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| disk_out_scheduled   | Decimal           | The amount of disk space in MiB scheduled for output files for the execution.  |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| disk_total_scheduled | Decimal           | The total amount of disk space in MiB scheduled for the execution.             |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| results              | JSON Object       | An interface description for all the possible job results meta-data.           |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| results_manifest     | JSON Object       | An interface description for all the actual job results meta-data.             |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                                |
|                                                                                                                           |
|  {                                                                                                                        |
|      "id": 3,                                                                                                             |
|      "status": "COMPLETED",                                                                                               |
|      "command_arguments": "",                                                                                             |
|      "timeout": 1800,                                                                                                     |
|      "pre_started": null,                                                                                                 |
|      "pre_completed": null,                                                                                               |
|      "pre_exit_code": null,                                                                                               |
|      "job_started": "2015-08-28T17:57:44.703Z",                                                                           |
|      "job_completed": "2015-08-28T17:57:45.906Z",                                                                         |
|      "job_exit_code": null,                                                                                               |
|      "post_started": null,                                                                                                |
|      "post_completed": null,                                                                                              |
|      "post_exit_code": null,                                                                                              |
|      "created": "2015-08-28T17:57:41.033Z",                                                                               |
|      "queued": "2015-08-28T17:57:41.010Z",                                                                                |
|      "started": "2015-08-28T17:57:44.494Z",                                                                               |
|      "ended": "2015-08-28T17:57:45.906Z",                                                                                 |
|      "last_modified": "2015-08-28T17:57:45.992Z",                                                                         |
|      "job": {                                                                                                             |
|          "id": 3,                                                                                                         |
|          "job_type": {                                                                                                    |
|              "id": 1,                                                                                                     |
|              "name": "scale-ingest",                                                                                      |
|              "version": "1.0",                                                                                            |
|              "title": "Scale Ingest",                                                                                     |
|              "description": "Ingests a source file into a workspace",                                                     |
|              "category": "system",                                                                                        |
|              "author_name": null,                                                                                         |
|              "author_url": null,                                                                                          |
|              "is_system": true,                                                                                           |
|              "is_long_running": false,                                                                                    |
|              "is_active": true,                                                                                           |
|              "is_operational": true,                                                                                      |
|              "is_paused": false,                                                                                          |
|              "icon_code": "f013"                                                                                          |
|          },                                                                                                               |
|          "job_type_rev": {                                                                                                |
|              "id": 2                                                                                                      |
|          },                                                                                                               |
|          "event": {                                                                                                       |
|              "id": 3                                                                                                      |
|          },                                                                                                               |
|          "error": null,                                                                                                   |
|          "status": "COMPLETED",                                                                                           |
|          "priority": 10,                                                                                                  |
|          "num_exes": 1                                                                                                    |
|      },                                                                                                                   |
|      "node": {                                                                                                            |
|          "id": 1,                                                                                                         |
|          "hostname": "machine.com",                                                                                       |
|          "port": 5051,                                                                                                    |
|          "slave_id": "20150821-123454-1683014024-5050-8216-S2",                                                           |
|          "is_paused": false,                                                                                              |
|          "is_active": true,                                                                                               |
|          "archived": null,                                                                                                |
|          "created": "2015-09-02T18:05:54.730Z",                                                                           |
|          "last_modified": "2015-09-08T16:53:57.439Z"                                                                      |
|      },                                                                                                                   |
|      "error": null,                                                                                                       |
|      "environment": {...},                                                                                                |
|      "cpus_scheduled": 0.5,                                                                                               |
|      "mem_scheduled": 15360.0,                                                                                            |
|      "disk_in_scheduled": 1.0,                                                                                            |
|      "disk_out_scheduled": 0.0,                                                                                           |
|      "disk_total_scheduled": 1.0,                                                                                         |
|      "results": {                                                                                                         |
|          "output_data": [                                                                                                 |
|              {                                                                                                            |
|                  "name": "output_file",                                                                                   |
|                  "file_id": 3                                                                                             |
|              }                                                                                                            |
|          ],                                                                                                               |
|          "version": "1.0"                                                                                                 |
|      },                                                                                                                   |
|      "results_manifest": {                                                                                                |
|          "output_data": [],                                                                                               |
|          "version": "1.1",                                                                                                |
|          "errors": [],                                                                                                    |
|          "parse_results": []                                                                                              |
|      }                                                                                                                    |
|  }                                                                                                                        |
+---------------------------------------------------------------------------------------------------------------------------+

.. _rest_job_execution_logs:

+---------------------------------------------------------------------------------------------------------------------------+
| **Job Execution Logs**                                                                                                    |
+===========================================================================================================================+
| Returns job execution logs for stdout and stderr.                                                                         |
| This will dynamically load the stdout and stderr for the currently running Mesos task if this job execution has not       |
| completed. These additional calls can add some overhead and processing so care should be taken not to poll this           |
| with high frequency.                                                                                                      |
+---------------------------------------------------------------------------------------------------------------------------+
| **DEPRECATED** This interface is deprecated in favor of the stdout/stderr/combined interfaces below.                      |
|                It is being maintened for access to old job executions and will be removed in a future release.            |
+---------------------------------------------------------------------------------------------------------------------------+
| **GET** /job-executions/{id}/logs/                                                                                        |
|         Where {id} is the unique identifier of an existing model.                                                         |
+---------------------------------------------------------------------------------------------------------------------------+
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
|                      |                   | Choices: [QUEUED, RUNNING, FAILED, COMPLETED, CANCELED].                       |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| command_arguments    | String            | The argument string to execute on the command line for this job execution.     | 
|                      |                   | This field is populated when the job execution is scheduled to run on a node   |
|                      |                   | and is updated when any needed pre-job steps are run.                          |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| timeout              | Integer           | The maximum amount of time this job can run before being killed (in seconds).  |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| pre_started          | ISO-8601 Datetime | When the pre-job steps were started on a node.                                 |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| pre_completed        | ISO-8601 Datetime | When the pre-job steps were completed on a node.                               |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| pre_exit_code        | Integer           | The exit code of the pre-steps job process for this job execution.             |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| job_started          | ISO-8601 Datetime | When the actual job started running on a node.                                 |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| job_completed        | ISO-8601 Datetime | When the actual job completed running on a node.                               |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| job_exit_code        | Integer           | The exit code of the main job process for this job execution.                  |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| post_started         | ISO-8601 Datetime | When the post-job steps were started on a node.                                |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| post_completed       | ISO-8601 Datetime | When the post-job steps were completed on a node.                              |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| post_exit_code       | Integer           | The exit code of the post-steps job process for this job execution.            |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| created              | ISO-8601 Datetime | When the associated database model was initially created.                      |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| queued               | ISO-8601 Datetime | When the job was added to the queue for this run and went to QUEUED status.    |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| started              | ISO-8601 Datetime | When the job was scheduled and went to RUNNING status.                         |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| ended                | ISO-8601 Datetime | When the job execution ended. (FAILED, COMPLETED, or CANCELED)                 |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| last_modified        | ISO-8601 Datetime | When the associated database model was last saved.                             |
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
| stdout               | String            | Contents of stdout.                                                            |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| stderr               | String            | Contents of stderr.                                                            |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                                |
|                                                                                                                           |
|  {                                                                                                                        |
|      "id": 3,                                                                                                             |
|      "status": "COMPLETED",                                                                                               |
|      "command_arguments": "",                                                                                             |
|      "timeout": 1800,                                                                                                     |
|      "pre_started": null,                                                                                                 |
|      "pre_completed": null,                                                                                               |
|      "pre_exit_code": null,                                                                                               |
|      "job_started": "2015-08-28T17:57:44.703Z",                                                                           |
|      "job_completed": "2015-08-28T17:57:45.906Z",                                                                         |
|      "job_exit_code": null,                                                                                               |
|      "post_started": null,                                                                                                |
|      "post_completed": null,                                                                                              |
|      "post_exit_code": null,                                                                                              |
|      "created": "2015-08-28T17:57:41.033Z",                                                                               |
|      "queued": "2015-08-28T17:57:41.010Z",                                                                                |
|      "started": "2015-08-28T17:57:44.494Z",                                                                               |
|      "ended": "2015-08-28T17:57:45.906Z",                                                                                 |
|      "last_modified": "2015-08-28T17:57:45.992Z",                                                                         |
|      "job": {                                                                                                             |
|          "id": 3,                                                                                                         |
|          "job_type": {                                                                                                    |
|              "id": 1,                                                                                                     |
|              "name": "scale-ingest",                                                                                      |
|              "version": "1.0",                                                                                            |
|              "title": "Scale Ingest",                                                                                     |
|              "description": "Ingests a source file into a workspace",                                                     |
|              "category": "system",                                                                                        |
|              "author_name": null,                                                                                         |
|              "author_url": null,                                                                                          |
|              "is_system": true,                                                                                           |
|              "is_long_running": false,                                                                                    |
|              "is_active": true,                                                                                           |
|              "is_operational": true,                                                                                      |
|              "is_paused": false,                                                                                          |
|              "icon_code": "f013"                                                                                          |
|          },                                                                                                               |
|          "job_type_rev": {                                                                                                |
|              "id": 2                                                                                                      |
|          },                                                                                                               |
|          "event": {                                                                                                       |
|              "id": 3                                                                                                      |
|          },                                                                                                               |
|          "error": null,                                                                                                   |
|          "status": "COMPLETED",                                                                                           |
|          "priority": 10,                                                                                                  |
|          "num_exes": 1                                                                                                    |
|      },                                                                                                                   |
|      "node": {                                                                                                            |
|          "id": 1,                                                                                                         |
|          "hostname": "machine.com",                                                                                       |
|          "port": 5051,                                                                                                    |
|          "slave_id": "20150821-123454-1683014024-5050-8216-S2"                                                            |
|      },                                                                                                                   |
|      "error": null,                                                                                                       |
|      "is_finished": true,                                                                                                 |
|      "stdout": "Execution completed.",                                                                                    |
|      "stderr": ""                                                                                                         |
|  }                                                                                                                        |
+---------------------------------------------------------------------------------------------------------------------------+

.. _rest_specified_job_execution_logs:

+---------------------------------------------------------------------------------------------------------------------------+
| **Specific Job Execution Logs**                                                                                           |
+===========================================================================================================================+
| Returns just job execution logs for stdout, stderr, or a combined view.                                                   |
| This will return the text of the stdout, stderr, or a combined view of both logs.                                         |
| More advanced log polling can be accomplished by directly querying the elasticsearch database.                            |
+---------------------------------------------------------------------------------------------------------------------------+
| **GET** /job-executions/{id}/logs/stdout/                                                                                 |
|         Where {id} is the unique identifier of an existing model.                                                         |
+---------------------------------------------------------------------------------------------------------------------------+
| **GET** /job-executions/{id}/logs/stderr/                                                                                 |
|         Where {id} is the unique identifier of an existing model.                                                         |
+---------------------------------------------------------------------------------------------------------------------------+
| **GET** /job-executions/{id}/logs/combined/                                                                               |
|         Where {id} is the unique identifier of an existing model.                                                         |
+---------------------------------------------------------------------------------------------------------------------------+
| **Request Header Fields**                                                                                                 |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| Accept               | String            | Should be *application/json*, *text/plain*, or *text/html*.                    |
|                      |                   | *application/json* will return the raw Elasticsearch results.                  |
|                      |                   | *text/plain* will return the log entries, one per line, as UTF-8.              |
|                      |                   | *text/html* will return a simple HTML document with stdout/stderr CSS          |
|                      |                   | classes to distinguish stdout and stderr. stderr will be                       |
|                      |                   | colored red by default.                                                        |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| If-Modified-Since    | HTTP Date         | If new log data exists after the specified date, return as normal, otherwise   |
|                      |                   | return *304 Not Modified*                                                      |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| **Successful Response**                                                                                                   |
+----------------------+----------------------------------------------------------------------------------------------------+
| **Status**           | 304 Not Modified                                                                                   |
+----------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**     | No content returned                                                                                |
+----------------------+----------------------------------------------------------------------------------------------------+
| **Return description**                                                                                                    |
+---------------------------------------------------------------------------------------------------------------------------+
| No log data newer than the specified date is available.                                                                   |
+---------------------------------------------------------------------------------------------------------------------------+
| **Status**           | 200 OK                                                                                             |
+----------------------+----------------------------------------------------------------------------------------------------+
| **Header Fields**                                                                                                         |
+----------------------+----------------------------------------------------------------------------------------------------+
| Content-Type         | content type as requested                                                                          |
+----------------------+----------------------------------------------------------------------------------------------------+
| Last-Modified        | The latest timestamp in the returned log entries                                                   |
+----------------------+----------------------------------------------------------------------------------------------------+
| **Return description**                                                                                                    |
+---------------------------------------------------------------------------------------------------------------------------+
| If the requested encoding is *application/json* the raw Elasticsearch results are returned.                               |
| If the requested encoding is *text/plain* then the plain text of the requested log will be returned. This will be the     |
| complete text from the requested timestamp or the complete log since start of execution by default.                       |
| If *text/html* is requested as a valid encoding then each line of the log in the combined output will be wrapped in a     |
| *div* element with a *class* of *stdout* or *stderr* as appropriate. This can be used to modify the color or rendering    |
| style to distinguish error and standard output.                                                                           |
+---------------------------------------------------------------------------------------------------------------------------+
