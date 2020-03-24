
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
            "version": "1.0.0",
            "title": "Scale Ingest",
            "description": "Ingests a source file into a workspace",
            "is_active": true,
            "is_system": true,
            "is_paused": false,
            "is_published": false,
            "icon_code": "f013",
            "unmet_resources": "chocolate,vanilla"
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
          "input_files": {
              "INPUT_FILE": ["my-file.file"]
          },
          "source_started": "2015-08-28T17:55:41.005Z",
          "source_ended": "2015-08-28T17:56:41.005Z",
          "source_sensor_class": "classA",
          "source_sensor": "1",
          "source_collection": "12345",
          "source_task": "my-task",
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
| source_started     | ISO-8601 Datetime | Optional | The start of the source file time range to query.                   |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| source_ended       | ISO-8601 Datetime | Optional | End of the source file time range to query, default is current time.|
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| source_sensor_class| String            | Optional | Return only jobs for the given source sensor class                  |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| source_sensor      | String            | Optional | Return only jobs for the given source sensor                        |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| source_collection  | String            | Optional | Return only jobs for the given source collection                    |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| source_tasks       | String            | Optional | Return only jobs for the given source task                          |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
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
|                     |                   | (See :ref:`Job Type Details <rest_v6_job_type_details>`)                      |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .job_type_rev       | JSON Object       | The job type revision that is associated with the job.                        |
|                     |                   | This represents the definition at the time the job was scheduled.             |
|                     |                   | (See :ref:`Job Type Revision Details <rest_v6_job_type_revision_details>`)    |
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
| .input_files        | JSON Object       | The input files associated with the job.                                      |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .source_started     | ISO-8601 Datetime | When collection of the source file started.                                   |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .source_ended       | ISO-8601 Datetime | When collection of the source file ended.                                     |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .source_sensor_class| String            | The class of sensor used to produce the source file.                          |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .source_sensor      | String            | The specific identifier of the sensor used to produce the source file.        |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .source_collection  | String            | The collection of the source file.                                            |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .source_task        | String            | The task that produced the source file.                                       |
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

.. _rest_v6_job_queue_new_job:

v6 Job Queue new Job
--------------------

**Example POST /v6/jobs/ API call**

Request: POST http://.../v6/jobs/

.. code-block:: javascript

 {
   "input": :ref:`rest_v6_data_data`,
   "job_type_id": 1,
   "configuration": :ref:`rest_v6_job_type_configuration`
 }

Response: 201 Created
Headers:
Location http://.../v6/job/1/

.. code-block:: javascript

  {
      "id": 1,
      "job_type": {
          "id": 1,
          "name": "test-job",
          "version": "1.0.0",
          "title": null,
          "description": null,
          "is_active": true,
          "is_paused": false,
          "is_system": true,
          "is_published": false,
          "icon_code": null,
          "unmet_resources": "chocolate,vanilla"
      },
      "status": "QUEUED",
      "job_type_rev": {
          "id": 1,
          "job_type": {
              "id": 1,
              "name": "test-job",
              "version": "1.0.0",
              "title": null,
              "description": null,
              "is_active": true,
              "is_paused": false,
              "is_system": true,
              "is_published": false,
              "icon_code": null,
              "unmet_resources": "chocolate,vanilla"
          },
          "revision_num": 1,
          "docker_image": "fake",
          "created": "2018-11-01T13:30:22.485611Z",
          "manifest": {
              "job": {
                  "maintainer": {
                      "name": "John Doe",
                      "email": "jdoe@example.com"
                  },
                  "jobVersion": "1.0.0",
                  "title": "Test Job",
                  "description": "This is a test job",
                  "timeout": 10,
                  "interface": {
                      "inputs": {
                          "files": [
                              {
                                  "name": "input_a"
                              }
                          ]
                      },
                      "command": "",
                      "outputs": {
                          "files": [
                              {
                                  "pattern": "*.png",
                                  "multiple": true,
                                  "name": "output_a"
                              }
                          ]
                      }
                  },
                  "packageVersion": "1.0.0",
                  "name": "test-job"
              },
              "seedVersion": "1.0.0"
          }
      },
      "event": {
          "id": 1,
          "type": "USER",
          "occurred": "2018-11-01T13:30:22.522060Z"
      },
      "recipe": null,
      "batch": null,
      "is_superseded": false,
      "superseded_job": null,
      "node": null,
      "error": null,
      "num_exes": 1,
      "input_file_size": 1.0,
      "input_files": {
          "input_a": ["my-file.file"]
      },
      "source_started": null,
      "source_ended": null,
      "created": "2018-11-01T13:30:22.530638Z",
      "queued": "2018-11-01T13:30:22.593052Z",
      "started": null,
      "ended": null,
      "last_status_change": "2018-11-01T13:30:22.593052Z",
      "superseded": null,
      "last_modified": "2018-11-01T13:30:23.026289Z",
      "superseded_by_job": null,
      "resources": {
          "resources": {
              "mem": 128.0,
              "gpus": 0.0,
              "disk": 1.0,
              "cpus": 0.25
          }
      },
      "execution": null,
      "input": {
          "files": {
              "input_a": [
                  1
              ]
          },
          "json": {}
      },
      "output": {
          "files": {},
          "json": {}
      }
  }

+-------------------------------------------------------------------------------------------------------------------------+
| **Queue New Job**                                                                                                       |
+=========================================================================================================================+
| Creates a new job and places it onto the queue                                                                          |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /v6/job/                                                                                                       |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_id        | Integer           | Required | The ID of the job type for the new job                              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| input              | JSON Object       | Required | JSON defining the data to run the job on.                           |
|                    |                   |          | See :ref:`Data JSON <rest_v6_data_data>`                            |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| configuration      | JSON Object       | optional | JSON defining the data to run the job on                            |
|                    |                   |          | See :ref:`Job Type Configuration <rest_v6_job_type_configuration>`  |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 201 CREATED                                                                                        |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Location**       | URL pointing to the details for the newly queued job                                               |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Body**           | JSON containing the details of the newly queued job, see :ref:`Job Details <rest_v6_job_details>`  |
+--------------------+----------------------------------------------------------------------------------------------------+

.. _rest_v6_job_details:

v6 Job Details
--------------

**Example GET /v6/jobs/{id}/ API call**

Request: GET http://.../v6/jobs/{id}/

Response: 200 OK

.. code-block:: javascript

    {
      "id": 3,
      "job_type": {
        "id": 1,
        "name": "scale-ingest",
        "version": "1.0.0",
        "title": "Scale Ingest",
        "description": "Ingests a source file into a workspace",
        "is_active": true,
        "is_paused": false,
        "is_system": true,
        "is_published": false,
        "icon_code": "f013",
        "unmet_resources": "chocolate,vanilla"
      },
      "job_type_rev": {
        "id": 5,
        "job_type": {
          "name": "scale-ingest",
          "version": "1.0.0",
          "title": "Scale Ingest",
          "description": "Ingests a source file into a workspace",
          "icon_code": "f013",
          "num_versions": 1,
          "latest_version": "1.0.0"
        },
        "revision_num": 1,
        "docker_image": "scale-ingest-1.0.0-seed:1.0.0",
        "created": "2015-08-28T17:55:41.005Z",
        "manifest": {...}
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
      "superseded_by_job": null,
      "status": "COMPLETED",
      "node": { 
        "id": 1,
        "hostname": "my-host.example.domain" 
      },
      "resources": {
        "resources": { 
          "mem": 128.0,
          "disk": 11.0,
          "cpus": 1.0
        }      
      },
      "error": null,
      "max_tries": 3,
      "num_exes": 1,
      "execution": {
        "id": 3,
         "status": "COMPLETED",
         "exe_num": 1,
         "cluster_id": "scale_job_1234_263x0",
         "created": "2015-08-28T17:57:41.033Z",
         "queued": "2015-08-28T17:57:41.010Z",
         "started": "2015-08-28T17:57:44.494Z",
         "ended": "2015-08-28T17:57:45.906Z",
         "job": {
             "id": 3,
         },
         "node": {
             "id": 1,
             "hostname": "machine.com"
         },
         "error": null,
         "job_type": {
            "id": 1,
            "name": "scale-ingest",
            "version": "1.0.0",
            "title": "Scale Ingest",
            "description": "Ingests a source file into a workspace",
            "is_active": true,
            "is_paused": false,
            "is_system": true,
            "is_published": false,
            "icon_code": "f013",
            "unmet_resources": "chocolate,vanilla"
         },
         "timeout": 1800,
         "input_file_size": 64.0,
         "task_results": null,
         "resources": {
             "resources": {
                 "mem": 128.0,
                 "disk": 11.0,
                 "cpus": 1.0
             }
         },
         "configuration": {
             "tasks": [...],
         },
         "output": {
             "output_data": [
                 {
                     "name": "output_file",
                     "file_id": 3
                 }
             ]
         }
      },
      "input": {
        "files": {'input_a': [1234], 'input_b': [1235, 1236]},
        "json": {'input_c': 999, 'input_d': {'hello'}}
      },
      "input_file_size": 64,
      "input_files": {
          "INPUT_FILE": ["my-file.file"]
      },
      "output": {
        "files": {'output_a': [456]},
        "json": {'output_b': 'success'}
      },
      "source_started": "2015-08-28T17:55:41.005Z",
      "source_ended": "2015-08-28T17:56:41.005Z",
      "source_sensor_class": "classA",
      "source_sensor": "1",
      "source_collection": "12345",
      "source_task": "my-task",
      "created": "2015-08-28T17:55:41.005Z",
      "queued": "2015-08-28T17:56:41.005Z",
      "started": "2015-08-28T17:57:41.005Z",
      "ended": "2015-08-28T17:58:41.005Z",
      "last_status_change": "2015-08-28T17:58:45.906Z",
      "superseded": null,
      "last_modified": "2015-08-28T17:58:46.001Z",
      "configuration": {
        "mounts": {},
        "priority": 50,
        "output_workspaces": {
            "default": "defaultworkspace",
            "outputs": {}
        },
        "settings": {}
      }
    }

+-------------------------------------------------------------------------------------------------------------------------+
| **Job Details**                                                                                                         |
+=========================================================================================================================+
| Returns a specific job and all its related model information.                                                           |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/jobs/{id}/                                                                                                  |
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
| job_type           | JSON Object       | The job type that is associated with the job.                                  |
|                    |                   | (See :ref:`Job Type Details <rest_v6_job_type_details>`)                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| job_type_rev       | JSON Object       | The job type revision that is associated with the job.                         |
|                    |                   | This represents the definition at the time the job was scheduled.              |
|                    |                   | (See :ref:`Job Type Revision Details <rest_v6_job_type_revision_details>`)     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| event              | JSON Object       | The trigger event that is associated with the job.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| recipe             | JSON Object       | The recipe instance associated with this job.                                  |
|                    |                   | (See :ref:`Recipe Details <rest_v6_recipe_details>`)                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| batch              | JSON Object       | The batch instance associated with this job                                    |
|                    |                   | (See :ref:`Batch Details <rest_v6_batch_details>`)                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| is_superseded      | Boolean           | Whether this job has been replaced and is now obsolete.                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| superseded_job     | JSON Object       | The previous job in the chain that was superseded by this job.                 |
|                    |                   | (See :ref:`Job Details <rest_v6_job_details>`)                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| superseded_by_job  | JSON Object       | The next job in the chain that superseded this job.                            |
|                    |                   | (See :ref:`Job Details <rest_v6_job_details>`)                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| status             | String            | The current status of the job.                                                 |
|                    |                   | Choices: [QUEUED, RUNNING, FAILED, COMPLETED, CANCELED].                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| node               | JSON Object       | The node that the job is/was running on.                                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| resources          | JSON Object       | JSON description describing the resources required for this job.               |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| error              | JSON Object       | The error that is associated with the job.                                     |
|                    |                   | (See :ref:`Error Details <rest_v6_error_details>`)                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| max_tries          | Integer           | Number of times this job will be automatically retried after an error.         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| num_exes           | Integer           | The number of executions this job has had.                                     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| execution          | JSON Object       | The most recent execution of the job.                                          |
|                    |                   | (See :ref:`Job Execution Details <rest_v6_job_execution_details>`)             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| input              | JSON Object       | The input data for the job.                                                    |
|                    |                   | (See :ref:`Data <rest_v6_data_data>`)                                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| input_file_size    | Decimal           | The amount of disk space in MiB required for input files for this job.         |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| input_files        | JSON Object       | The input files associated with the job.                                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| output             | JSON Object       | The output data for the job.                                                   |
|                    |                   | (See :ref:`Data <rest_v6_data_data>`)                                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| source_started     | ISO-8601 Datetime | When collection of the source file started.                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| source_ended       | ISO-8601 Datetime | When collection of the source file ended.                                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| source_sensor_class| String            | The class of sensor used to produce the source file.                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| source_sensor      | String            | The specific identifier of the sensor used to produce the source file.         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| source_collection  | String            | The collection of the source file.                                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| source_task        | String            | The task that produced the source file.                                        |
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
| configuration      | JSON Object       | JSON description of the configuration for running the job                      |
|                    |                   | (See :ref:`rest_v6_job_type_configuration`)                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+

.. _rest_v6_job_input_files:

v6 Job Input File List
----------------------

**Example GET /v6/jobs/{id}/input_files/ API call**

Request: GET http://.../v6/jobs/{id}/input_files/

Response: 200 OK

 .. code-block:: javascript

See :ref:`Scale Files <rest_v6_scale_file_list>` for an example response

+-------------------------------------------------------------------------------------------------------------------------+
| **Job Input Files**                                                                                                     |
+=========================================================================================================================+
| Returns detailed information about input files associated with a given Job ID.                                          |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/jobs/{id}/input_files/                                                                                      |
|         Where {id} is the unique identifier of an existing job.                                                         |
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
| count              | Integer           | The total number of results that match the query parameters.                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| next               | URL               | A URL to the next page of results.                                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| previous           | URL               | A URL to the previous page of results.                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| results            | Array             | List of result JSON objects that match the query parameters.                   |
|                    |                   | (See :ref:`Scale Files <rest_v6_scale_file_list>`)                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+

.. _rest_v6_job_execution_list:

v6 Job Executions List
----------------------

**Example GET /v6/jobs/{id}/executions/ API call**

Request: GET http://.../v6/jobs/{id}/executions/

Response: 200 OK

 .. code-block:: javascript

    {
      "count": 57,
      "next": null,
      "previous": null,
      "results": [
        {
          "id": 3,
          "status": "COMPLETED",
          "exe_num": 1,
          "cluster_id": "scale_job_1234_263x0",
          "created": "2015-08-28T17:57:41.033Z",
          "queued": "2015-08-28T17:57:41.010Z",
          "started": "2015-08-28T17:57:44.494Z",
          "ended": "2015-08-28T17:57:45.906Z",
          "job": {
            "id": 3
          },
          "node": {
            "id": 1,
            "hostname": "machine.com"
          },
          "error": null,
          "job_type": {
            "id": 1,
            "name": "scale-ingest",
            "version": "1.0.0",
            "title": "Scale Ingest",
            "description": "Ingests a source file into a workspace",
            "is_active": true,
            "is_paused": false,
            "is_system": true,
            "is_published": false,
            "icon_code": "f013",
            "unmet_resources": "chocolate,vanilla"
          },
          "timeout": 1800,
          "input_file_size": 10
        }
      ]
    }

+---------------------------------------------------------------------------------------------------------------------------+
| **Job Executions List**                                                                                                   |
+===========================================================================================================================+
| Returns a list of job executions associated with a given Job ID.  Returned job executions are ordered by exe_num          |
| descending (most recent first)                                                                                            |
+---------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/jobs/{id}/executions/                                                                                         |
|         Where {id} is the unique identifier of an existing job.                                                           |
+---------------------------------------------------------------------------------------------------------------------------+
| **Query Parameters**                                                                                                      |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| page                 | Integer           | Optional | The page of the results to return. Defaults to 1.                   |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| page_size            | Integer           | Optional | The size of the page to use for pagination of results.              |
|                      |                   |          | Defaults to 100, and can be anywhere from 1-1000.                   |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| status               | String            | Optional | Return only executions with a status matching this string.          |
|                      |                   |          | Choices: [RUNNING, FAILED, COMPLETED, CANCELED].                    |
|                      |                   |          | Duplicate it to filter by multiple values.                          |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| node_id              | Integer           | Optional | Return only executions that ran on a given node.                    |
|                      |                   |          | Duplicate it to filter by multiple values.                          |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| error_id             | Integer           | Optional | Return only executions that had the given error.                    |
|                      |                   |          | Duplicate it to filter by multiple values.                          |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| error_category       | Integer           | Optional | Return only executions that had an error in the given category.     |
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
|                      |                   | (See :ref:`Job Execution Details <rest_v6_job_execution_details>`)             |
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
|                      |                   | (See :ref:`Job Details <rest_v6_job_details>`)                                 |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .node                | JSON Object       | The node that ran the execution.                                               |
|                      |                   | (See :ref:`Node Details <rest_v6_node_details>`)                               |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .error               | JSON Object       | The last error that was recorded for the execution.                            |
|                      |                   | (See :ref:`Error Details <rest_v6_error_details>`)                             |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .job_type            | JSON Object       | The job type that is associated with the execution.                            |
|                      |                   | (See :ref:`Job Type Details <rest_v6_job_type_details>`)                       |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .timeout             | Integer           | The maximum amount of time this job can run before being killed (in seconds).  |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .input_file_size     | Float             | The total amount of disk space in MiB for all input files for this execution.  |
+----------------------+-------------------+--------------------------------------------------------------------------------+

.. _rest_v6_job_execution_details:

v6 Job Execution Details
------------------------

**Example GET /v6/jobs/{id}/executions/{exe_num}/ API call**

Request: GET http://.../v6/jobs/{id}/executions/{exe_num}/

Response: 200 OK

 .. code-block:: javascript

  {
    "id": 3,
    "status": "COMPLETED",
    "exe_num": 1,
    "cluster_id": "scale_job_1234_263x0",
    "created": "2015-08-28T17:57:41.033Z",
    "queued": "2015-08-28T17:57:41.010Z",
    "started": "2015-08-28T17:57:44.494Z",
    "ended": "2015-08-28T17:57:45.906Z",
    "job": {
      "id": 3
    },
    "node": {
      "id": 1,
      "hostname": "machine.com"
    },
    "error": null,
    "job_type": {
      "id": 1,
      "name": "scale-ingest",
      "version": "1.0.0",
      "title": "Scale Ingest",
      "description": "Ingests a source file into a workspace",
      "is_active": true,
      "is_paused": false,
      "is_system": true,
      "is_published": false,
      "icon_code": "f013",
      "unmet_resources": "chocolate,vanilla"
    },
    "timeout": 1800,
    "input_file_size": 10,
    "task_results": null,
    "resources": {
      "resources": {
        "mem": 128,
        "disk": 11,
        "cpus": 1
      }
    },
    "configuration": {
      <architecture_jobs_exe_configuration>
    },
    "output": {
      "output_data": [
        {
          "name": "output_file",
          "file_id": 3
        }
      ]
    }
  }

+---------------------------------------------------------------------------------------------------------------------------+
| **Job Execution Details**                                                                                                 |
+===========================================================================================================================+
| Returns a specific job execution and all its related model information including job, node, environment, and results.     |
+---------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/jobs/{id}/executions/{exe_num}                                                                                |
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
|                      |                   | (See :ref:`Job Execution Details <rest_v6_job_execution_details>`)             |
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
|                      |                   | (See :ref:`Job Details <rest_v6_job_details>`)                                 |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| node                 | JSON Object       | The node that ran the execution.                                               |
|                      |                   | (See :ref:`Node Details <rest_v6_node_details>`)                               |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| error                | JSON Object       | The last error that was recorded for the execution.                            |
|                      |                   | (See :ref:`Error Details <rest_v6_error_details>`)                                |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| job_type             | JSON Object       | The job type that is associated with the execution.                            |
|                      |                   | (See :ref:`Job Type Details <rest_v6_job_type_details>`)                       |
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

.. _rest_v6_job_cancel:

v6 Cancel Jobs
--------------

**Example POST /v6/jobs/cancel/ API call**

Request: POST http://.../v6/jobs/cancel/

 .. code-block:: javascript
 
  {
    "started": "2016-01-01T00:00:00Z",
    "ended": "2016-01-02T00:00:00Z",
    "status": "FAILED",
    "job_ids": [ 101, 102, 103 ],
    "job_type_ids": [ 1, 2, 3 ],
    "job_types": [ {"name": "my-job-type", "version": "1.0.0"} ],
    "job_type_names": [ 'test-job-type' ],
    "batch_ids": [ 201, 202, 203 ],
    "recipe_ids": [ 301, 302, 303 ],
    "error_categories": [ "SYSTEM" ],
    "error_ids": [ 11, 22, 33 ],
    "is_superseded": true
  }
    
Response: 202 ACCEPTED

+-------------------------------------------------------------------------------------------------------------------------+
| **Cancel Jobs**                                                                                                         |
+=========================================================================================================================+
| Cancels the jobs that fit the given filter criteria. The canceling will be done asynchronously, so the response will    |
| just indicate that the cancel request has been accepted.                                                                |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /v6/jobs/cancel/                                                                                               |
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
| status             | String            | Optional | Cancel only jobs with this status                                   |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_ids            | Array[Integer]    | Optional | Cancel only jobs with these IDs                                     |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_ids       | Array[Integer]    | Optional | Cancel only jobs with these job types                               |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_types          | Array             | Optional | Cancel only jobs with these job types specified by name/version     |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_names     | Array[String]     | Optional | Cancel only jobs with these job type names                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| batch_ids          | Array[Integer]    | Optional | Cancel only jobs that were part of these batches                    |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| recipe_ids         | Array[Integer]    | Optional | Cancel only jobs that were part of these recipes                    |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| error_categories   | Array[String]     | Optional | Cancel only jobs that failed with these error categories            |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| error_ids          | Array[String]     | Optional | Cancel only jobs that failed with these errors                      |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 202 Accepted                                                                                       |
+--------------------+----------------------------------------------------------------------------------------------------+
| No response body                                                                                                        |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_v6_job_requeue:

v6 Requeue Jobs
---------------

**Example POST /v6/jobs/requeue/ API call**

Request: POST http://.../v6/jobs/requeue/

 .. code-block:: javascript
 
  {
    "started": "2016-01-01T00:00:00Z",
    "ended": "2016-01-02T00:00:00Z",
    "status": "FAILED",
    "job_ids": [ 101, 102, 103 ],
    "job_type_ids": [ 1, 2, 3 ],
    "job_types": [ {"name": "my-job-type", "version": "1.0.0"} ],
    "job_type_names": [ 'test-job-type' ],
    "batch_ids": [ 201, 202, 203 ],
    "recipe_ids": [ 301, 302, 303 ],
    "error_categories": [ "SYSTEM" ],
    "error_ids": [ 11, 22, 33 ],
    "is_superseded": true,
    "priority": 101
  }
    
Response: 202 ACCEPTED

+-------------------------------------------------------------------------------------------------------------------------+
| **Requeue Jobs**                                                                                                        |
+=========================================================================================================================+
| Re-queues the FAILED/CANCELED jobs that fit the given filter criteria. The re-queuing will be done asynchronously, so   |
| the response will just indicate that the re-queue request has been accepted.                                            |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /v6/jobs/requeue/                                                                                              |
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
| status             | String            | Optional | Re-queue only jobs with this status                                 |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_ids            | Array[Integer]    | Optional | Re-queue only jobs with these IDs                                   |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_ids       | Array[Integer]    | Optional | Re-queue only jobs with these job types                             |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_types          | Array             | Optional | Re-queue only jobs with these job types specified by name/version   |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_names     | Array[String]     | Optional | Re-queue only jobs with these job type names                        |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| batch_ids          | Array[Integer]    | Optional | Re-queue only jobs that were part of these batches                  |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| recipe_ids         | Array[Integer]    | Optional | Re-queue only jobs that were part of these recipes                  |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| error_categories   | Array[String]     | Optional | Re-queue only jobs that failed with these error categories          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| error_ids          | Array[String]     | Optional | Re-queue only jobs that failed with these errors                    |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| priority           | Integer           | Optional | Change the priority of matching jobs when adding them to the queue. |
|                    |                   |          | Defaults to jobs current priority, lower number is higher priority. |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 202 Accepted                                                                                       |
+--------------------+----------------------------------------------------------------------------------------------------+

.. _rest_v6_job_execution_log:

v6 Job Execution Log
--------------------

**Example GET /v6/job-executions/{job_exe_id}/logs/{log_id}/ API call**

Request: GET http://.../v6/job-executions/{job_exe_id}/logs/{log_id}/

Response: 200 OK

 .. code-block:: javascript

  {
    [
        "message": "<log from job execution>",
        "@timestamp": "2015-08-28T17:57:41.033Z",
        "scale_order_num": 1,
        "scale_task": 123,
        "scale_job_exe": "scale_job_1234_263x0",
        "scale_node": "machine.com",
        "stream": "stdout"
    ]
  }

+---------------------------------------------------------------------------------------------------------------------------+
| **Job Execution Log**                                                                                                     |
+===========================================================================================================================+
| Returns the log for a specific job execution.                                                                             |
+---------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/job-executions/{job_exe_id}/logs/{log_id}/                                                                    |
|         Where {job_exe_id} is the unique identifier of an existing job execution and {log_id} specifies which output to   |
|         include (stdout | stderr | combined).                                                                             |
+----------------------+----------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                   |
+----------------------+----------------------------------------------------------------------------------------------------+
| **Status**           | 200 OK                                                                                             |
+----------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**     | *application/json*                                                                                 |
+----------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                           |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .message             | String            | The log message.                                                               |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .@timestamp          | ISO-8601 Datetime | The ISO-8601 timestamp marking when the message was logged.                    |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .scale_order_num     | Integer           | A sequence number used to indicate correct log message order when multiple     |
|                      |                   | messages share the same @timestamp value.                                      |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .scale_task          | Integer           | The ID of the Scale task that produced this log message.                       |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .scale_job_exe       | String            | The unique cluster ID of the Scale job execution that produced this log message|
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .scale_node          | String            | The host name of the Scale node that executed the Scale task                   |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .stream              | String            | Indicates which stream produced the log message, either “stdout” or “stderr”   |
+----------------------+-------------------+--------------------------------------------------------------------------------+