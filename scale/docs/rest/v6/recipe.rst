
.. _rest_v6_recipe:

v6 Recipe Services
==================

These services allow for the creation and management of recipes. A recipe type is a user-defined workflow that allows
jobs and recipes to be connected together in order to pass output from jobs to the input of other jobs.

.. _rest_v6_recipe_json_forced_nodes:

Recipe Forced Nodes JSON
------------------------

A recipe forced nodes JSON describes the set of recipe nodes (jobs, sub-recipes, etc) that should be forced to
re-process even if there are no changes to the node.

**Example recipe forced nodes:**

.. code-block:: javascript

   {
      "all": False,
      "nodes": ["job_a_1", "job_a_2", "recipe_b", "recipe_c"],
      "sub_recipes": {
         "recipe_b": {
            "all": True
         },
         "recipe_c": {
            "all": False,
            "nodes": ["job_c_1", "job_c_2"]
         }
      }
   }

+-----------------------------------------------------------------------------------------------------------------------------+
| **Recipe Forced Nodes**                                                                                                     |
+============================+================+==========+====================================================================+
| all                        | Boolean        | Required | If true, then all nodes within the recipe should be forced to      |
|                            |                |          | re-process and the 'nodes' and 'sub_recipes' fields should be      |
|                            |                |          | omitted. If false, then the 'nodes' array is used to indicate which|
|                            |                |          | nodes should be forced to re-process.                              |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| nodes                      | Array          | Optional | An array listing the names of the recipe nodes that should be      |
|                            |                |          | forced to re-process.                                              |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| sub_recipes                | JSON object    | Optional | A JSON object where the key names are the sub-recipe node names    |
|                            |                |          | that are being forced to re-process. The values are forced nodes   |
|                            |                |          | JSON objects that recursively define the nodes with the sub-recipe |
|                            |                |          | to force to reprocess.                                             |
+----------------------------+----------------+----------+--------------------------------------------------------------------+

.. _rest_v6_recipe_json_instance:

Recipe Instance JSON
--------------------

A recipe instance JSON describes an instance of a running recipe.

**Example recipe instance:**

.. code-block:: javascript

   {
      "nodes": {
         "node_a": {
            "dependencies": [],
            "node_type": {
               "node_type": "job",
               "job_type_name": "job-type-1",
               "job_type_version": "1.0",
               "job_type_revision": 1,
               "job_id": 1234,
               "status": "COMPLETED"
            }
         },
         "node_b": {
            "dependencies": [{"name": "node_a"}],
            "node_type": {
               "node_type": "job",
               "job_type_name": "job-type-2",
               "job_type_version": "2.0",
               "job_type_revision": 1,
               "job_id": 1235,
               "status": "COMPLETED"
            }
         },
         "node_c": {
            "dependencies": [{"name": "node_b"}],
            "node_type": {
               "node_type": "recipe",
               "recipe_type_name": "recipe-type-1",
               "recipe_type_revision": 5,
               "recipe_id": 100,
               "is_completed": false,
               "jobs_total": 12,
               "jobs_pending": 0,
               "jobs_blocked": 2,
               "jobs_queued": 3,
               "jobs_running": 2,
               "jobs_failed": 1,
               "jobs_completed": 4,
               "jobs_canceled": 0,
               "sub_recipes_total": 3,
               "sub_recipes_completed": 1
            }
         },
         "node_d": {
            "dependencies": [{"name": "node_a"}],
            "node_type": {
               "node_type": "condition",
               "condition_id": 999,
               "is_processed": true,
               "is_accepted": false
            }
         }
      }
   }

+-----------------------------------------------------------------------------------------------------------------------------+
| **Recipe Instance**                                                                                                         |
+============================+================+==========+====================================================================+
| nodes                      | JSON object    | Required | All of the nodes within the recipe stored by node name             |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| dependencies               | Array          | Required | The list of dependencies for this recipe node. Each JSON object in |
|                            |                |          | the list has a single string field called *name* giving the node   |
|                            |                |          | name of the dependency.                                            |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| node_type                  | JSON object    | Required | An object describing the type of the node                          |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| node_type                  | String         | Required | The type of the node, either 'job' or 'recipe'                     |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| condition_id               | Integer        | Required | ('condition' node) The unique ID of the condition                  |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| is_processed               | Boolean        | Required | ('condition' node) Whether the condition has been processed        |
|                            |                |          | (evaluated)                                                        |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| is_accepted                | Boolean        | Required | ('condition' node) Whether the condition has been accepted. If     |
|                            |                |          | accepted, the nodes depending on the condition will be created and |
|                            |                |          | processed. If not accepted, the nodes depending on the condition   |
|                            |                |          | will not be created or processed.                                  |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| job_type_name              | String         | Required | ('job' node) The name of the job type                              |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| job_type_version           | String         | Required | ('job' node) The version of the job type                           |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| job_type_revision          | Integer        | Required | ('job' node) The revision of the job type                          |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| job_id                     | Integer        | Required | ('job' node) The unique ID of the job                              |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| status                     | String         | Required | ('job' node) The job's status                                      |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| recipe_type_name           | String         | Required | ('recipe' node) The name of the recipe type                        |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| recipe_type_revision       | Integer        | Required | ('recipe' node) The revision of the recipe type                    |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| recipe_id                  | Integer        | Required | ('recipe' node) The unique ID of the recipe                        |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| is_completed               | Boolean        | Required | ('recipe' node) Whether the recipe has completed or not            |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| jobs_total                 | Integer        | Required | ('recipe' node) The total number of jobs in the recipe             |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| jobs_pending               | Integer        | Required | ('recipe' node) The number of PENDING jobs in the recipe           |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| jobs_blocked               | Integer        | Required | ('recipe' node) The number of BLOCKED jobs in the recipe           |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| jobs_queued                | Integer        | Required | ('recipe' node) The number of QUEUED jobs in the recipe            |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| jobs_running               | Integer        | Required | ('recipe' node) The number of RUNNING jobs in the recipe           |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| jobs_failed                | Integer        | Required | ('recipe' node) The number of FAILED jobs in the recipe            |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| jobs_completed             | Integer        | Required | ('recipe' node) The number of COMPLETED jobs in the recipe         |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| jobs_canceled              | Integer        | Required | ('recipe' node) The number of CANCELED jobs in the recipe          |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| sub_recipes_total          | Integer        | Required | ('recipe' node) The total number of sub-recipes in the recipe      |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| sub_recipes_completed      | Integer        | Required | ('recipe' node) The number of completed sub-recipes in the recipe  |
+----------------------------+----------------+----------+--------------------------------------------------------------------+

.. _rest_v6_recipe_queue_new_recipe:

Recipe Queue New Recipe
-----------------------

**Example POST /v6/recipes/ API call**

Request: POST http://.../v6/recipes/

.. code-block:: javascript

  {
   "input": :ref:`rest_v6_data_data`,
   "recipe_type_id": 4,
   "configuration": :ref:`rest_v6_recipe_type_configuration`
  }

Response: 201 CREATED

.. code-block:: javascript

  {
      "id": 1,
      "recipe_type": {
            "id": 1,
            "name": "test-recipe-type-1",
            "title": "Test Recipe Type 1",
            "description": "Test Description 1",
            "revision_num": 1
      },
      "recipe_type_rev": {
            "id": 1,
            "recipe_type": {
                  "id": 1
            },
            "revision_num": 1
      },
      "event": {
            "id": 3,
            "type": "USER",
            "occurred": "2018-11-01T13:59:38.462027Z"
      },
      "containing_recipe": null,
      "batch": null
      "is_superseded": false,
      "superseded_recipe": null,
      "superseded_by_recipe": null,
      "num_exes": 1,
      "input": {
        "files": {'input_a': [1234], 'input_b': [1235, 1236]},
        "json": {'input_c': 999, 'input_d': {'hello'}}
      },
      "input_file_size": 64.0,
      "source_started": "2015-08-28T17:55:41.005Z",
      "source_ended": "2015-08-28T17:56:41.005Z",
      "source_sensor_class": "classA",
      "source_sensor": "1",
      "source_collection": "12345",
      "source_task": "my-task",
      "jobs_total": 10,
      "jobs_pending": 0,
      "jobs_blocked": 0,
      "jobs_queued": 1,
      "jobs_running": 3,
      "jobs_failed": 0,
      "jobs_completed": 6,
      "jobs_canceled": 0,
      "sub_recipes_total": 2,
      "sub_recipes_completed": 1,
      "created": "2018-11-01T13:59:38.471071Z",
      "completed": null,
      "superseded": null,
      "last_modified": "2018-11-01T13:59:38.471175Z"
      "details":
      "job_types": [
        {
            "id": 1,
            "name": "my-job",
            "version": "1.0.0",
            "title": "My Job",
            "description": "A simple job type",
            "icon_code": "f013"
        },...
      ],
      "sub_recipe_types": [
        {
            "id": 1,
            "name": "test-recipe-type-1",
            "title": "Test Recipe Type 1",
            "description": "Test Description 1",
            "revision_num": 1
        },...
      ]
  }

+-------------------------------------------------------------------------------------------------------------------------+
| **Queue New Recipe**                                                                                                    |
+=========================================================================================================================+
| Creates a new recipe and places it onto the queue                                                                       |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /v6/recipes/                                                                                                   |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| recipe_type_id     | Integer           | Required | The ID of the recipe type to queue                                  |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| input              | JSON Object       | Required | JSON defining the data to run the recipe on.                        |
|                    |                   |          | See :ref:`Data JSON <rest_v6_data_data>`                            |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| configuration      | JSON Object       | optional | JSON defining the data to run the job on                            |
|                    |                   |          | See :ref:`Recipe Configuration <rest_v6_recipe_configuration>`      |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 201 CREATED                                                                                        |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Location**       | URL pointing to the details for the newly queued recipe data                                       |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Body**           | JSON containing the details of the newly queued recipe                                             |
|                    | see :ref:`Recipe Details <rest_v6_recipe_details`>                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+

.. _rest_v6_recipe_list:

V6 Recipe List
--------------

**Example GET /v6/recipes/ API call**

Request: GET http://.../v6/recipes/

Response: 200 OK

.. code-block:: javascript

    {
      "count": 1,
      "next": null,
      "previous": null,
      "results": [
        {
          "id": 1,
          "recipe_type": {
                "id": 1,
                "name": "test-recipe-type-1",
                "title": "Test Recipe Type 1",
                "description": "Test Description 1",
                "revision_num": 1
          },
          "recipe_type_rev": {
                "id": 1,
                "recipe_type": {
                      "id": 1
                },
                "revision_num": 1
          },
          "event": {
                "id": 3,
                "type": "USER",
                "occurred": "2018-11-01T13:59:38.462027Z"
          },
          "containing_recipe": null,
          "batch": null
          "is_superseded": false,
          "superseded_recipe": null,
          "num_exes": 1,
          "input_file_size": 64.0,
          "source_started": "2015-08-28T17:55:41.005Z",
          "source_ended": "2015-08-28T17:56:41.005Z",
          "source_sensor_class": "classA",
          "source_sensor": "1",
          "source_collection": "12345",
          "source_task": "my-task",
          "jobs_total": 10,
          "jobs_pending": 0,
          "jobs_blocked": 0,
          "jobs_queued": 1,
          "jobs_running": 3,
          "jobs_failed": 0,
          "jobs_completed": 6,
          "jobs_canceled": 0,
          "sub_recipes_total": 2,
          "sub_recipes_completed": 1,
          "created": "2018-11-01T13:59:38.471071Z",
          "completed": null,
          "superseded": null,
          "last_modified": "2018-11-01T13:59:38.471175Z"
      },...]
    }


+-------------------------------------------------------------------------------------------------------------------------+
| **Recipe List**                                                                                                         |
+=========================================================================================================================+
| Returns a list of all recipes.                                                                                          |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/recipes/                                                                                                    |
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
| source_sensor_class| String            | Optional | Return only recipes for the given source sensor class               |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| source_sensor      | String            | Optional | Return only recipes for the given source sensor                     |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| source_collection  | String            | Optional | Return only recipes for the given source collection                 |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| source_task        | String            | Optional | Return only recipes for the given source task                       |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| recipe_id          | Integer           | Optional | Return only recipes with a given recipe identifier.                 |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| recipe_type_id     | Integer           | Optional | Return only recipes with a given recipe type identifier.            |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| recipe_type_name   | String            | Optional | Return only recipes with a given recipe type name.                  |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| batch_id           | Integer           | Optional | Return only recipes associated with the given batch identifier.     |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| is_superseded      | Boolean           | Optional | Return only recipes that match this value, indicating if the recipe |
|                    |                   |          | has/has not been superseded.                                        |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| is_completed       | Boolean           | Optional | Return only recipes that match this value, indicating if the recipe |
|                    |                   |          | has/has not been completed.                                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| order              | String            | Optional | One or more fields to use when ordering the results.                |
|                    |                   |          | Duplicate it to multi-sort, (ex: order=name&order=version).         |
|                    |                   |          | Prefix fields with a dash to reverse the sort, (ex: order=-name).   |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+------------------------+-------------------+----------------------------------------------------------------------------+
| count                  | Integer           | The total number of results that match the query parameters.               |
+------------------------+-------------------+----------------------------------------------------------------------------+
| next                   | URL               | A URL to the next page of results.                                         |
+------------------------+-------------------+----------------------------------------------------------------------------+
| previous               | URL               | A URL to the previous page of results.                                     |
+------------------------+-------------------+----------------------------------------------------------------------------+
| results                | Array             | List of result JSON objects that match the query parameters.               |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .id                    | Integer           | The unique identifier of the model. Can be passed to the details API call. |
|                        |                   | (See :ref:`Recipe Details <rest_v6_recipe_details>`)                       |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .recipe_type           | JSON Object       | The recipe type that is associated with the recipe.                        |
|                        |                   | This represents the latest version of the definition.                      |
|                        |                   | (See :ref:`Recipe Type Details <rest_v6_recipe_type_details>`)             |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .recipe_type_rev       | JSON Object       | The recipe type revision that is associated with the recipe.               |
|                        |                   | This represents the definition at the time the recipe was scheduled.       |
|                        |                   | (See :ref:`Recipe Type Revision Details <rest_v6_recipe_type_rev_details>`)|
+------------------------+-------------------+----------------------------------------------------------------------------+
| .event                 | JSON Object       | The trigger event that is associated with the recipe.                      |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .containing_recipe     | JSON Object       | The recipe instance containing this recipe.                                |
|                        |                   | (See :ref:`Recipe Details <rest_v6_recipe_details>`)                       |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .batch                 | JSON Object       | The batch instance associated with this recipe                             |
|                        |                   | (See :ref:`Batch Details <rest_v6_batch_details>`)                         |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .is_superseded         | Boolean           | Whether this recipe has been replaced and is now obsolete.                 |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .superseded_recipe     | JSON Object       | The previous recipe in the chain that was superseded by this recipe.       |
|                        |                   | (See :ref:`Recipe Details <rest_v6_recipe_details>`)                       |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .num_exes              | Integer           | The number of executions this recipe has had.                              |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .input_file_size       | Decimal           | The amount of disk space in MiB required for input files for this job.     |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .source_started        | ISO-8601 Datetime | When collection of the underlying source file started.                     |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .source_ended          | ISO-8601 Datetime | When collection of the underlying source file ended.                       |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .source_sensor_class   | String            | The class of sensor used to produce the source file.                       |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .source_sensor         | String            | The specific identifier of the sensor used to produce the source file.     |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .source_collection     | String            | The collection of the source file.                                         |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .source_task           | String            | The task that produced the source file.                                    |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .jobs_total            | Integer           | The total count of jobs within this recipe                                 |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .jobs_pending          | Integer           | The count of PENDING jobs within this recipe                               |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .jobs_blocked          | Integer           | The count of BLOCKED jobs within this recipe                               |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .jobs_queued           | Integer           | The count of QUEUED jobs within this recipe                                |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .jobs_running          | Integer           | The count of RUNNING jobs within this recipe                               |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .jobs_failed           | Integer           | The count of FAILED jobs within this recipe                                |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .jobs_completed        | Integer           | The count of COMPLETED jobs within this recipe                             |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .jobs_canceled         | Integer           | The count of CANCELED jobs within this recipe                              |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .sub_recipes_total     | Integer           | The total count of sub-recipes within this recipe                          |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .sub_recipes_completed | Integer           | The count of completed sub-recipes within this recipe                      |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .is_completed          | Boolean           | Whether this recipe is completed                                           |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .created               | ISO-8601 Datetime | When the associated database model was initially created.                  |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .completed             | ISO-8601 Datetime | When every job in the recipe was completed successfully.                   |
|                        |                   | This field will remain null if a job in the recipe is blocked or failed.   |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .superseded            | ISO-8601 Datetime | When the the recipe became superseded by another recipe.                   |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .last_modified         | ISO-8601 Datetime | When the associated database model was last saved.                         |
+------------------------+-------------------+----------------------------------------------------------------------------+

.. _rest_v6_recipe_list:

V6 Recipe Details
-----------------

**Example GET /v6/recipes/{id}/ API call**

Request: GET http://.../v6/recipes/{id}/

Response: 200 OK

.. code-block:: javascript

  {
      "id": 1,
      "recipe_type": {
            "id": 1,
            "name": "test-recipe-type-1",
            "title": "Test Recipe Type 1",
            "description": "Test Description 1",
            "revision_num": 1
      },
      "recipe_type_rev": {
            "id": 1,
            "recipe_type": {
                  "id": 1
            },
            "revision_num": 1
      },
      "event": {
            "id": 3,
            "type": "USER",
            "occurred": "2018-11-01T13:59:38.462027Z",
            "description": {
                "file_name": "data-file.png",
                "version": "1.0",
                "parse_id": 1
            }
      },
      "containing_recipe": null,
      "batch": null
      "is_superseded": false,
      "superseded_recipe": null,
      "superseded_by_recipe": null,
      "num_exes": 1,
      "input": {
        "files": {'input_a': [1234], 'input_b': [1235, 1236]},
        "json": {'input_c': 999, 'input_d': {'hello'}}
      },
      "input_file_size": 64.0,
      "source_started": "2015-08-28T17:55:41.005Z",
      "source_ended": "2015-08-28T17:56:41.005Z",
      "source_sensor_class": "classA",
      "source_sensor": "1",
      "source_collection": "12345",
      "source_task": "my-task",
      "jobs_total": 10,
      "jobs_pending": 0,
      "jobs_blocked": 0,
      "jobs_queued": 1,
      "jobs_running": 3,
      "jobs_failed": 0,
      "jobs_completed": 6,
      "jobs_canceled": 0,
      "sub_recipes_total": 2,
      "sub_recipes_completed": 1,
      "created": "2018-11-01T13:59:38.471071Z",
      "completed": null,
      "superseded": null,
      "last_modified": "2018-11-01T13:59:38.471175Z"
      "details":
      "job_types": [
        {
            "id": 1,
            "name": "my-job",
            "version": "1.0.0",
            "title": "My Job",
            "description": "A simple job type",
            "icon_code": "f013"
        },...
      ],
      "sub_recipe_types": [
        {
            "id": 1,
            "name": "test-recipe-type-1",
            "title": "Test Recipe Type 1",
            "description": "Test Description 1",
            "revision_num": 1
        },...
      ]
  }


+-------------------------------------------------------------------------------------------------------------------------+
| **Recipe Details**                                                                                                      |
+=========================================================================================================================+
| Returns details for a given recipe                                                                                      |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/recipes/{id}/                                                                                               |
|         Where {id} is the unique identifier of an existing model.                                                       |
+-------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+------------------------+-------------------+----------------------------------------------------------------------------+
| id                     | Integer           | The unique identifier of the model. Can be passed to the details API call. |
|                        |                   | (See :ref:`Recipe Details <rest_v6_recipe_details>`)                       |
+------------------------+-------------------+----------------------------------------------------------------------------+
| recipe_type            | JSON Object       | The recipe type that is associated with the recipe.                        |
|                        |                   | This represents the latest version of the definition.                      |
|                        |                   | (See :ref:`Recipe Type Details <rest_v6_recipe_type_details>`)             |
+------------------------+-------------------+----------------------------------------------------------------------------+
| recipe_type_rev        | JSON Object       | The recipe type revision that is associated with the recipe.               |
|                        |                   | This represents the definition at the time the recipe was scheduled.       |
|                        |                   | (See :ref:`Recipe Type Revision Details <rest_v6_recipe_type_rev_details>`)|
+------------------------+-------------------+----------------------------------------------------------------------------+
| event                  | JSON Object       | The trigger event that is associated with the recipe.                      |
+------------------------+-------------------+----------------------------------------------------------------------------+
| containing_recipe      | JSON Object       | The recipe instance containing this recipe.                                |
|                        |                   | (See :ref:`Recipe Details <rest_v6_recipe_details>`)                       |
+------------------------+-------------------+----------------------------------------------------------------------------+
| batch                  | JSON Object       | The batch instance associated with this recipe                             |
|                        |                   | (See :ref:`Batch Details <rest_v6_batch_details>`)                         |
+------------------------+-------------------+----------------------------------------------------------------------------+
| is_superseded          | Boolean           | Whether this recipe has been replaced and is now obsolete.                 |
+------------------------+-------------------+----------------------------------------------------------------------------+
| superseded_recipe      | JSON Object       | The previous recipe in the chain that was superseded by this recipe.       |
|                        |                   | (See :ref:`Recipe Details <rest_v6_recipe_details>`)                       |
+------------------------+-------------------+----------------------------------------------------------------------------+
| superseded_by_recipe   | JSON Object       | The next recipe in the chain that superseded this recipe                   |
|                        |                   | (See :ref:`Recipe Details <rest_v6_recipe_details>`)                       |
+------------------------+-------------------+----------------------------------------------------------------------------+
| num_exes               | Integer           | The number of executions this recipe has had.                              |
+------------------------+-------------------+----------------------------------------------------------------------------+
| input                  | JSON Object       | The input data for the recipe.                                             |
|                        |                   | (See :ref:`Data <rest_v6_data_data>`)                                      |
+------------------------+-------------------+----------------------------------------------------------------------------+
| input_file_size        | Decimal           | The amount of disk space in MiB required for input files for this job.     |
+------------------------+-------------------+----------------------------------------------------------------------------+
| source_started         | ISO-8601 Datetime | When collection of the underlying source file started.                     |
+------------------------+-------------------+----------------------------------------------------------------------------+
| source_ended           | ISO-8601 Datetime | When collection of the underlying source file ended.                       |
+------------------------+-------------------+----------------------------------------------------------------------------+
| source_sensor_class    | String            | The class of sensor used to produce the source file.                       |
+------------------------+-------------------+----------------------------------------------------------------------------+
| source_sensor          | String            | The specific identifier of the sensor used to produce the source file.     |
+------------------------+-------------------+----------------------------------------------------------------------------+
| source_collection      | String            | The collection of the source file.                                         |
+------------------------+-------------------+----------------------------------------------------------------------------+
| source_task            | String            | The task that produced the source file.                                    |
+------------------------+-------------------+----------------------------------------------------------------------------+
| jobs_total             | Integer           | The total count of jobs within this recipe                                 |
+------------------------+-------------------+----------------------------------------------------------------------------+
| jobs_pending           | Integer           | The count of PENDING jobs within this recipe                               |
+------------------------+-------------------+----------------------------------------------------------------------------+
| jobs_blocked           | Integer           | The count of BLOCKED jobs within this recipe                               |
+------------------------+-------------------+----------------------------------------------------------------------------+
| jobs_queued            | Integer           | The count of QUEUED jobs within this recipe                                |
+------------------------+-------------------+----------------------------------------------------------------------------+
| jobs_running           | Integer           | The count of RUNNING jobs within this recipe                               |
+------------------------+-------------------+----------------------------------------------------------------------------+
| jobs_failed            | Integer           | The count of FAILED jobs within this recipe                                |
+------------------------+-------------------+----------------------------------------------------------------------------+
| jobs_completed         | Integer           | The count of COMPLETED jobs within this recipe                             |
+------------------------+-------------------+----------------------------------------------------------------------------+
| jobs_canceled          | Integer           | The count of CANCELED jobs within this recipe                              |
+------------------------+-------------------+----------------------------------------------------------------------------+
| sub_recipes_total      | Integer           | The total count of sub-recipes within this recipe                          |
+------------------------+-------------------+----------------------------------------------------------------------------+
| sub_recipes_completed  | Integer           | The count of completed sub-recipes within this recipe                      |
+------------------------+-------------------+----------------------------------------------------------------------------+
| created                | ISO-8601 Datetime | When the associated database model was initially created.                  |
+------------------------+-------------------+----------------------------------------------------------------------------+
| completed              | ISO-8601 Datetime | When every job in the recipe was completed successfully.                   |
|                        |                   | This field will remain null if a job in the recipe is blocked or failed.   |
+------------------------+-------------------+----------------------------------------------------------------------------+
| superseded             | ISO-8601 Datetime | When the the recipe became superseded by another recipe.                   |
+------------------------+-------------------+----------------------------------------------------------------------------+
| last_modified          | ISO-8601 Datetime | When the associated database model was last saved.                         |
+------------------------+-------------------+----------------------------------------------------------------------------+
| details                | JSON Object       | The running recipe instance details                                        |
|                        |                   | (See :ref:`Recipe Instance <rest_v6_recipe_json_instance>`)                |
+------------------------+-------------------+----------------------------------------------------------------------------+
| job_types              | Array             | List of job type revisions in the recipe definition                        |
|                        |                   | (See :ref:`Job Type Revision <rest_v6_job_type_revision_details>`)         |
+------------------------+-------------------+----------------------------------------------------------------------------+
| sub_recipe_types       | Array             | List of sub recipe types in the recipe definition                          |
|                        |                   | (See :ref:`Recipe Type Details <rest_v6_recipe_type_details>`)             |
+------------------------+-------------------+----------------------------------------------------------------------------+

.. _rest_v6_recipe_input_files:

v6 Recipe Input File List
-------------------------

**Example GET /v6/recipes/{id}/input_files/ API call**

Request: GET http://.../v6/recipes/{id}/input_files/

Response: 200 OK

 .. code-block:: javascript

See :ref:`Scale Files <rest_v6_scale_file_list>` for an example response

+-------------------------------------------------------------------------------------------------------------------------+
| **Recipe Input Files**                                                                                                  |
+=========================================================================================================================+
| Returns detailed information about input files associated with a given Job ID.                                          |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/recipes/{id}/input_files/                                                                                   |
|         Where {id} is the unique identifier of an existing recipe.                                                      |
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
| recipe_input       | String            | Optional | Returns files for this recipe input.                                |
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