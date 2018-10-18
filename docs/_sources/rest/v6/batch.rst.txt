
.. _rest_v6_batch:

v6 Batch Services
=================

These services allow for the creation and management of batches. A batch is a user-created collection of recipes of a
single recipe type. Batches can be used for running recipes over a given data set or for performing iterative test runs
for algorithm development and validation.

.. _rest_v6_batch_list:

v6 Retrieve Batch List
----------------------

**Example GET /v6/batches/ API call**

Request: GET http://.../v6/batches/?recipe_type_id=208

Response: 200 OK

.. code-block:: javascript

   {
      "count": 1,
      "next": null,
      "previous": null,
      "results": [{
         "id": 1234,
         "title": "My Batch",
         "description": "My Batch Description",
         "recipe_type": {
            "id": 208,
            "name": "my-recipe-type",
            "title": "My Recipe Type",
            "description": "My Recipe Type Description",
            "revision_num": 1
         },
         "recipe_type_rev": {
            "id": 4,
            "recipe_type": {
               "id": 208
            },
            "revision_num": 1
         },
         "event": {
            "id": 4000,
            "type": "USER",
            "rule": null,
            "occurred": "1970-01-01T00:00:00Z"
         },
         "is_superseded": true,
         "root_batch": {
            "id": 1232,
            "title": "My Root Batch",
            "description": "My Root Batch Description",
            "created": "1970-01-01T00:00:00Z"
         },
         "superseded_batch": {
            "id": 1233,
            "title": "My Superseded Batch",
            "description": "My Superseded Batch Description",
            "created": "1970-01-01T00:00:00Z"
         },
         "is_creation_done": true,
         "jobs_total": 10,
         "jobs_pending": 0,
         "jobs_blocked": 0,
         "jobs_queued": 1,
         "jobs_running": 3,
         "jobs_failed": 0,
         "jobs_completed": 6,
         "jobs_canceled": 0,
         "recipes_estimated": 2,
         "recipes_total": 2,
         "recipes_completed": 1,
         "created": "1970-01-01T00:00:00Z",
         "superseded": "1970-01-01T00:00:00Z",
         "last_modified": "1970-01-01T00:00:00Z"
      }]
   }

+-----------------------------------------------------------------------------------------------------------------------------+
| **Batch List**                                                                                                              |
+=============================================================================================================================+
| Returns a list of batches that match the given filter criteria                                                              |
+-----------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/batches/                                                                                                        |
+-----------------------------------------------------------------------------------------------------------------------------+
| **Query Parameters**                                                                                                        |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| page                    | Integer           | Optional | The page of the results to return. Defaults to 1.                  |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| page_size               | Integer           | Optional | The size of the page to use for pagination of results.             |
|                         |                   |          | Defaults to 100, and can be anywhere from 1-1000.                  |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| started                 | ISO-8601 Datetime | Optional | The start of the time range to query.                              |
|                         |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z).|
|                         |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).             |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| ended                   | ISO-8601 Datetime | Optional | End of the time range to query, defaults to the current time.      |
|                         |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z).|
|                         |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).             |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| recipe_type_id          | Integer           | Optional | Return only batches for a given recipe type.                       |
|                         |                   |          | Duplicate it to filter by multiple values.                         |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| is_creation_done        | Boolean           | Optional | Return only batches that match this value, indicating if the batch |
|                         |                   |          | has/has not finishing creating its recipes.                        |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| is_superseded           | Boolean           | Optional | Return only batches that match this value, indicating if the batch |
|                         |                   |          | has/has not been superseded.                                       |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| root_batch_id           | Integer           | Optional | Return only batches that belong to the chain with this root batch. |
|                         |                   |          | Duplicate it to filter by multiple values.                         |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| order                   | String            | Optional | One or more fields to use when ordering the results.               |
|                         |                   |          | Duplicate it to multi-sort, (ex: order=title&order=recipe_type_id).|
|                         |                   |          | Prefix fields with a dash to reverse the sort, (ex: order=-title). |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| **Successful Response**                                                                                                     |
+-------------------------+---------------------------------------------------------------------------------------------------+
| **Status**              | 200 OK                                                                                            |
+-------------------------+---------------------------------------------------------------------------------------------------+
| **Content Type**        | *application/json*                                                                                |
+-------------------------+---------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                             |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| count                   | Integer           | The total number of results that match the query parameters                   |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| next                    | URL               | A URL to the next page of results                                             |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| previous                | URL               | A URL to the previous page of results                                         |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| results                 | Array             | List of result JSON objects that match the query parameters                   |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| id                      | Integer           | The unique identifier of the batch                                            |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| title                   | String            | The human readable display name of the batch                                  |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| description             | String            | A longer description of the batch                                             |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| recipe_type             | JSON Object       | The recipe type that is associated with the batch                             |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| recipe_type_rev         | JSON Object       | The recipe type revision that is associated with the batch                    |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| event                   | JSON Object       | The trigger event that is associated with the batch                           |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| is_superseded           | Boolean           | Whether this batch has been superseded (re-processed) by another batch        |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| root_batch              | JSON Object       | The root batch for the chain that contains this batch, possibly null          |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| superseded_batch        | JSON Object       | The previous batch in the chain superseded by this batch, possibly null       |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| is_creation_done        | Boolean           | Whether this batch has finished creating all of its recipes                   |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| jobs_total              | Integer           | The total count of jobs within this batch's recipes                           |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| jobs_pending            | Integer           | The count of PENDING jobs within this batch's recipes                         |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| jobs_blocked            | Integer           | The count of BLOCKED jobs within this batch's recipes                         |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| jobs_queued             | Integer           | The count of QUEUED jobs within this batch's recipes                          |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| jobs_running            | Integer           | The count of RUNNING jobs within this batch's recipes                         |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| jobs_failed             | Integer           | The count of FAILED jobs within this batch's recipes                          |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| jobs_completed          | Integer           | The count of COMPLETED jobs within this batch's recipes                       |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| jobs_canceled           | Integer           | The count of CANCELED jobs within this batch's recipes                        |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| recipes_estimated       | Integer           | The estimated count of recipes (including sub-recipes) that will be created   |
|                         |                   | for this batch                                                                |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| recipes_total           | Integer           | The total count of recipes (including sub-recipes) within this batch          |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| recipes_completed       | Integer           | The count of completed recipes (including sub-recipes) within this batch      |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| created                 | ISO-8601 Datetime | When the batch was initially created                                          |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| superseded              | ISO-8601 Datetime | When the batch was superseded                                                 |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| last_modified           | ISO-8601 Datetime | When the batch was last updated                                               |
+-------------------------+-------------------+-------------------------------------------------------------------------------+

.. _rest_v6_batch_create:

v6 Create Batch
---------------

**Example POST /v6/batches/ API call**

Request: POST http://.../v6/batches/

.. code-block:: javascript

   {
      "title": "My Batch",
      "description": "My Batch Description",
      "recipe_type_id": 208,
      "definition": {
         "previous_batch": {
            "root_batch_id": 104
         }
      },
      "configuration": {
         "priority": 100
      }
   }

Response: 201 Created
Headers:
Location http://.../v6/batches/105/

.. code-block:: javascript

   {
      "id": 105,
      "title": "My Batch",
      "description": "My Batch Description",
      "recipe_type": {
         "id": 208,
         "name": "my-recipe-type",
         "title": "My Recipe Type",
         "description": "My Recipe Type Description",
         "revision_num": 1,
      },
      "recipe_type_rev": {
         "id": 4,
         "recipe_type": {
            "id": 208
         },
         "revision_num": 1,
         "definition": {...},
         "created": "1970-01-01T00:00:00Z"
      },
      "event": {
         "id": 4000,
         "type": "USER",
         "rule": null,
         "occurred": "1970-01-01T00:00:00Z",
         "description": {
            "user": "Anonymous"
         }
      },
      "is_superseded": true,
      "root_batch": {
         "id": 104,
         "title": "My Superseded Batch",
         "description": "My Superseded Batch Description",
         "created": "1970-01-01T00:00:00Z"
      },
      "superseded_batch": {
         "id": 104,
         "title": "My Superseded Batch",
         "description": "My Superseded Batch Description",
         "created": "1970-01-01T00:00:00Z"
      },
      "is_creation_done": true,
      "jobs_total": 10,
      "jobs_pending": 0,
      "jobs_blocked": 0,
      "jobs_queued": 1,
      "jobs_running": 3,
      "jobs_failed": 0,
      "jobs_completed": 6,
      "jobs_canceled": 0,
      "recipes_estimated": 2,
      "recipes_total": 2,
      "recipes_completed": 1,
      "created": "1970-01-01T00:00:00Z",
      "superseded": "1970-01-01T00:00:00Z",
      "last_modified": "1970-01-01T00:00:00Z",
      "definition": {
         "previous_batch": {
            "root_batch_id": 104
         }
      },
      "configuration": {
         "priority": 100
      },
      "job_metrics": {
         "job_a": {
            "jobs_total": 10,
            "jobs_pending": 0,
            "jobs_blocked": 0,
            "jobs_queued": 1,
            "jobs_running": 3,
            "jobs_failed": 0,
            "jobs_completed": 6,
            "jobs_canceled": 0,
            "min_seed_duration": "PT9M2S",
            "avg_seed_duration": "PT10M12S",
            "max_seed_duration": "PT15M45S",
            "min_job_duration": "PT9M50S",
            "avg_job_duration": "PT10M59S",
            "max_job_duration": "PT16M49S"
         }
      }
   }

+-------------------------------------------------------------------------------------------------------------------------+
| **Create Batch**                                                                                                        |
+=========================================================================================================================+
| Creates a new batch with the given fields                                                                               |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /batches/                                                                                                      |
+---------------------+---------------------------------------------------------------------------------------------------+
| **Content Type**    | *application/json*                                                                                |
+---------------------+---------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+---------------------+-------------------+----------+--------------------------------------------------------------------+
| title               | String            | Optional | The human-readable name of the batch                               |
+---------------------+-------------------+----------+--------------------------------------------------------------------+
| description         | String            | Optional | A human-readable description of the batch                          |
+---------------------+-------------------+----------+--------------------------------------------------------------------+
| recipe_type_id      | Integer           | Required | The ID of the recipe type for this batch's recipes                 |
+---------------------+-------------------+----------+--------------------------------------------------------------------+
| definition          | JSON Object       | Required | JSON definition for processing the batch                           |
|                     |                   |          | See :ref:`rest_v6_batch_json_definition`                           |
+---------------------+-------------------+----------+--------------------------------------------------------------------+
| configuration       | JSON Object       | Optional | JSON configuration for processing the batch                        |
|                     |                   |          | See :ref:`rest_v6_batch_json_configuration`                        |
+---------------------+-------------------+----------+--------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 201 Created                                                                                        |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Location**       | URL for retrieving the details of the newly created batch                                          |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Body**           | JSON containing the details of the newly created batch, see :ref:`rest_v6_batch_details`           |
+--------------------+----------------------------------------------------------------------------------------------------+

.. _rest_v6_batch_comparison:

v6 Batch Comparison
-------------------

**Example GET /v6/batches/comparison/{batch-id}/ API call**

Request: GET http://.../v6/batches/comparison/101/

Response: 200 OK

.. code-block:: javascript

   {
      "batches": [{
         "id": 101,
         "title": "My Batch",
         "description": "My Batch Description",
         "created": "1970-01-01T00:00:00Z"
      }, {
         "id": 102,
         "title": "My Other Batch",
         "description": "My Other Batch Description",
         "created": "1970-01-01T00:00:00Z"
      }],
      "metrics": {
         "jobs_total": [10, 10],
         "jobs_pending": [0, 0],
         "jobs_blocked": [0, 0],
         "jobs_queued": [0, 1],
         "jobs_running": [0, 3],
         "jobs_failed": [0, 0],
         "jobs_completed": [10, 6],
         "jobs_canceled": [0, 0],
         "recipes_estimated": [2, 2],
         "recipes_total": [2, 2],
         "recipes_completed": [2, 1],
         "job_metrics": {
            "job_a": {
               "jobs_total": [5, 5],
               "jobs_pending": [0, 0],
               "jobs_blocked": [0, 0],
               "jobs_queued": [0, 1],
               "jobs_running": [0, 1],
               "jobs_failed": [0, 0],
               "jobs_completed": [5, 3],
               "jobs_canceled": [0, 0],
               "min_seed_duration": ["PT12S", "PT11S"],
               "avg_seed_duration": ["PT18S", "PT17S"],
               "max_seed_duration": ["PT23S", "PT22S"],
               "min_job_duration": ["PT15S", "PT14S"],
               "avg_job_duration": ["PT21S", "PT20S"],
               "max_job_duration": ["PT26S", "PT25S"]
            },
            "job_b": {
               "jobs_total": [5, 5],
               "jobs_pending": [0, 0],
               "jobs_blocked": [0, 0],
               "jobs_queued": [0, 0],
               "jobs_running": [0, 2],
               "jobs_failed": [0, 0],
               "jobs_completed": [5, 3],
               "jobs_canceled": [0, 0],
               "min_seed_duration": ["PT46S", "PT41S"],
               "avg_seed_duration": ["PT50S", "PT45S"],
               "max_seed_duration": ["PT57S", "PT52S"],
               "min_job_duration": ["PT48S", "PT43S"],
               "avg_job_duration": ["PT52S", "PT47S"],
               "max_job_duration": ["PT59S", "PT54S"]
            }
         }
      }
   }

+-----------------------------------------------------------------------------------------------------------------------------+
| **Batch Comparison**                                                                                                        |
+=============================================================================================================================+
| Returns the list of batches with the given root batch ID along with their metrics                                           |
+-----------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/batches/comparison/{id}/                                                                                        |
|         Where {id} is the root batch ID of a chain of batches                                                               |
+-----------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                     |
+-------------------------+---------------------------------------------------------------------------------------------------+
| **Status**              | 200 OK                                                                                            |
+-------------------------+---------------------------------------------------------------------------------------------------+
| **Content Type**        | *application/json*                                                                                |
+-------------------------+---------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                             |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| batches                 | Array             | List of batches in the chain with the given root batch ID                     |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| metrics                 | JSON Object       | Contains the top-level and per job metrics fields for each batch in the       |
|                         |                   | chain. This is similar to the metrics in a batch details response, except     |
|                         |                   | that instead of each metric containing a single value, each metric here holds |
|                         |                   | an array of values. The order of the values in each array corresponds to the  |
|                         |                   | order of the batches in the *batches* array. See :ref:`rest_v6_batch_details` |
|                         |                   | for a description of the various metrics fields.                              |
+-------------------------+-------------------+-------------------------------------------------------------------------------+

.. _rest_v6_batch_validation:

v6 Validate Batch
-----------------

**Example POST /v6/batches/validation/ API call**

Request: POST http://.../v6/batches/validation/

.. code-block:: javascript

   {
      "recipe_type_id": 208,
      "definition": {
         "previous_batch": {
            "root_batch_id": 104
         }
      },
      "configuration": {
         "priority": 100
      }
   }

Response: 200 OK

.. code-block:: javascript

   {
      "is_valid": true,
      "errors": [],
      "warnings": [{"name": "EXAMPLE_WARNING", "description": "This is an example warning."}],
      "recipes_estimated": 10,
      "recipe_type": {
         "id": 208,
         "name": "my-recipe-type",
         "title": "My Recipe Type",
         "description": "My Recipe Type Description",
         "revision_num": 1
      },
      "prev_batch": {
         "recipe_type_rev": {
            "id": 4,
            "recipe_type": {
               "id": 208
            },
            "revision_num": 1
         },
         "diff": {...}
      }
   }

+-------------------------------------------------------------------------------------------------------------------------+
| **Validate Batch**                                                                                                      |
+=========================================================================================================================+
| Validates the given fields for creating a new batch                                                                     |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /batches/validation/                                                                                           |
+---------------------+---------------------------------------------------------------------------------------------------+
| **Content Type**    | *application/json*                                                                                |
+---------------------+---------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+---------------------+-------------------+----------+--------------------------------------------------------------------+
| recipe_type_id      | Integer           | Required | The ID of the recipe type for this batch's recipes                 |
+---------------------+-------------------+----------+--------------------------------------------------------------------+
| definition          | JSON Object       | Required | JSON definition for processing the batch                           |
|                     |                   |          | See :ref:`rest_v6_batch_json_definition`                           |
+---------------------+-------------------+----------+--------------------------------------------------------------------+
| configuration       | JSON Object       | Optional | JSON configuration for processing the batch                        |
|                     |                   |          | See :ref:`rest_v6_batch_json_configuration`                        |
+---------------------+-------------------+----------+--------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| is_valid           | Boolean           | Indicates if the given fields were valid for creating a new batch. If this is  |
|                    |                   | true, then submitting the same fields to the /batches/ API will successfully   |
|                    |                   | create a new batch.                                                            |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| errors             | Array             | Lists any errors causing *is_valid* to be false. The errors are JSON objects   |
|                    |                   | with *name* and *description* string fields.                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| warnings           | Array             | Lists any warnings found. Warnings are useful to present to the user, but do   |
|                    |                   | not cause *is_valid* to be false. The warnings are JSON objects with *name*    |
|                    |                   | and *description* string fields.                                               |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| recipes_estimated  | Integer           | The estimated number of recipes that would be created by this batch            |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| recipe_type        | JSON Object       | The recipe type that is associated with the batch                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| prev_batch         | JSON Object       | Object containing information about the previous batch (will be omitted if     |
|                    |                   | there is no previous batch)                                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| recipe_type_rev    | JSON Object       | The recipe type revision of the previous batch                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| diff               | JSON Object       | The recipe graph diff between the batch's recipe type revision and the previous|
|                    |                   | batch's recipe type revision. The diff explains which recipe jobs will be      |
|                    |                   | reprocessed by the new batch. See :ref:`rest_v6_recipe_json_diff`              |
+--------------------+-------------------+--------------------------------------------------------------------------------+

.. _rest_v6_batch_details:

v6 Retrieve Batch Details
-------------------------

**Example GET /v6/batches/{batch-id}/ API call**

Request: GET http://.../v6/batches/105/

Response: 200 OK

.. code-block:: javascript

   {
      "id": 105,
      "title": "My Batch",
      "description": "My Batch Description",
      "recipe_type": {
         "id": 208,
         "name": "my-recipe-type",
         "title": "My Recipe Type",
         "description": "My Recipe Type Description"
      },
      "recipe_type_rev": {
         "id": 4,
         "recipe_type": {
            "id": 208
         },
         "revision_num": 1,
         "definition": {...},
         "created": "1970-01-01T00:00:00Z"
      },
      "event": {
         "id": 4000,
         "type": "USER",
         "rule": null,
         "occurred": "1970-01-01T00:00:00Z",
         "description": {
            "user": "Anonymous"
         }
      },
      "is_superseded": true,
      "root_batch": {
         "id": 1232,
         "title": "My Root Batch",
         "description": "My Root Batch Description",
         "created": "1970-01-01T00:00:00Z"
      },
      "superseded_batch": {
         "id": 1233,
         "title": "My Superseded Batch",
         "description": "My Superseded Batch Description",
         "created": "1970-01-01T00:00:00Z"
      },
      "is_creation_done": true,
      "jobs_total": 10,
      "jobs_pending": 0,
      "jobs_blocked": 0,
      "jobs_queued": 1,
      "jobs_running": 3,
      "jobs_failed": 0,
      "jobs_completed": 6,
      "jobs_canceled": 0,
      "recipes_estimated": 2,
      "recipes_total": 2,
      "recipes_completed": 1,
      "created": "1970-01-01T00:00:00Z",
      "superseded": "1970-01-01T00:00:00Z",
      "last_modified": "1970-01-01T00:00:00Z",
      "definition": {
         "previous_batch": {
            "root_batch_id": 104
         }
      },
      "configuration": {
         "priority": 100
      },
      "job_metrics": {
         "job_a": {
            "jobs_total": 10,
            "jobs_pending": 0,
            "jobs_blocked": 0,
            "jobs_queued": 1,
            "jobs_running": 3,
            "jobs_failed": 0,
            "jobs_completed": 6,
            "jobs_canceled": 0,
            "min_seed_duration": "PT9M2S",
            "avg_seed_duration": "PT10M12S",
            "max_seed_duration": "PT15M45S",
            "min_job_duration": "PT9M50S",
            "avg_job_duration": "PT10M59S",
            "max_job_duration": "PT16M49S"
         }
      }
   }

+-----------------------------------------------------------------------------------------------------------------------------+
| **Batch Details**                                                                                                           |
+=============================================================================================================================+
| Returns the details for a specific batch                                                                                    |
+-----------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/batches/{id}/                                                                                                   |
|         Where {id} is the unique ID of the batch to retrieve                                                                |
+-----------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                     |
+-------------------------+---------------------------------------------------------------------------------------------------+
| **Status**              | 200 OK                                                                                            |
+-------------------------+---------------------------------------------------------------------------------------------------+
| **Content Type**        | *application/json*                                                                                |
+-------------------------+---------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                             |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| id                      | Integer           | The unique identifier of the batch                                            |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| title                   | String            | The human readable display name of the batch                                  |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| description             | String            | A longer description of the batch                                             |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| recipe_type             | JSON Object       | The recipe type that is associated with the batch                             |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| recipe_type_rev         | JSON Object       | The recipe type revision that is associated with the batch                    |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| event                   | JSON Object       | The trigger event that is associated with the batch                           |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| is_superseded           | Boolean           | Whether this batch has been superseded (re-processed) by another batch        |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| root_batch              | JSON Object       | The root batch for the chain that contains this batch, possibly null          |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| superseded_batch        | JSON Object       | The previous batch in the chain superseded by this batch, possibly null       |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| is_creation_done        | Boolean           | Whether this batch has finished creating all of its recipes                   |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| jobs_total              | Integer           | The total count of jobs within this batch's recipes                           |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| jobs_pending            | Integer           | The count of PENDING jobs within this batch's recipes                         |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| jobs_blocked            | Integer           | The count of BLOCKED jobs within this batch's recipes                         |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| jobs_queued             | Integer           | The count of QUEUED jobs within this batch's recipes                          |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| jobs_running            | Integer           | The count of RUNNING jobs within this batch's recipes                         |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| jobs_failed             | Integer           | The count of FAILED jobs within this batch's recipes                          |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| jobs_completed          | Integer           | The count of COMPLETED jobs within this batch's recipes                       |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| jobs_canceled           | Integer           | The count of CANCELED jobs within this batch's recipes                        |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| recipes_estimated       | Integer           | The estimated count of recipes (including sub-recipes) that will be created   |
|                         |                   | for this batch                                                                |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| recipes_total           | Integer           | The total count of recipes (including sub-recipes) within this batch          |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| recipes_completed       | Integer           | The count of completed recipes (including sub-recipes) within this batch      |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| created                 | ISO-8601 Datetime | When the batch was initially created                                          |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| superseded              | ISO-8601 Datetime | When the batch was superseded                                                 |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| last_modified           | ISO-8601 Datetime | When the batch was last updated                                               |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| definition              | JSON Object       | The definition of the batch                                                   |
|                         |                   | See :ref:`rest_v6_batch_json_definition`                                      |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| configuration           | JSON Object       | The configuration of the batch                                                |
|                         |                   | See :ref:`rest_v6_batch_json_configuration`                                   |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| job_metrics             | JSON Object       | The metrics for each top level recipe job (not in a sub-recipe) in the batch. |
|                         |                   | Each recipe job name maps to the metrics for that job. The job count metrics  |
|                         |                   | (e.g. jobs_total) are similar to the top level batch metrics. The duration    |
|                         |                   | metrics (e.g. min_seed_duration) detail the minimum, average, and maximum     |
|                         |                   | durations for completing the Seed run and completing the overall Scale job.   |
|                         |                   | The durations are provided in the ISO-8601 duration format.                   |
+-------------------------+-------------------+-------------------------------------------------------------------------------+

.. _rest_v6_batch_edit:

v6 Edit Batch
-------------

**Example PATCH /v6/batches/{batch-id}/ API call**

Request: PATCH http://.../v6/batches/100/

.. code-block:: javascript

   {
      "title": "My New Batch Title",
      "description": "My New Batch Description",
      "configuration": {
         "priority": 200
      }
   }

Response: 204 No Content

+-------------------------------------------------------------------------------------------------------------------------+
| **Edit Batch**                                                                                                          |
+=========================================================================================================================+
| Edits a batch to change the given fields                                                                                |
+-------------------------------------------------------------------------------------------------------------------------+
| **PATCH** /v6/batches/{id}/                                                                                             |
|           Where {id} is the unique ID of the batch to edit                                                              |
+---------------------+---------------------------------------------------------------------------------------------------+
| **Content Type**    | *application/json*                                                                                |
+---------------------+---------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+---------------------+-------------------+----------+--------------------------------------------------------------------+
| title               | String            | Optional | The human-readable name of the batch                               |
+---------------------+-------------------+----------+--------------------------------------------------------------------+
| description         | String            | Optional | A human-readable description of the batch                          |
+---------------------+-------------------+----------+--------------------------------------------------------------------+
| configuration       | JSON Object       | Optional | JSON configuration for processing the batch                        |
|                     |                   |          | See :ref:`rest_v6_batch_json_configuration`                        |
+---------------------+-------------------+----------+--------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 204 No Content                                                                                     |
+--------------------+----------------------------------------------------------------------------------------------------+

.. _rest_v6_batch_json_definition:

Batch Definition JSON
---------------------

A batch definition JSON defines what a batch is going to run. Currently the v6 batch definition only supports running a
batch that re-processes the same set of recipes that ran in a previous batch.

**Example batch definition:**

.. code-block:: javascript

   {
      "previous_batch": {
         "root_batch_id": 1234,
         "forced_nodes": {
            "all": False,
            "nodes": ['job_a', 'job_b'],
         }
      }
   }

+-----------------------------------------------------------------------------------------------------------------------------+
| **Batch Definition**                                                                                                        |
+=========================+===================+==========+====================================================================+
| previous_batch          | JSON object       | Optional | Indicates that the batch should re-process the recipes from a      |
|                         |                   |          | previous batch. This will link the previous and new batch together |
|                         |                   |          | so that their metrics can be easily compared. The previous batch   |
|                         |                   |          | must have the same recipe type as the new batch and must have      |
|                         |                   |          | finished creating all of its recipes.                              |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| root_batch_id           | Integer           | Required | The root batch ID of the previous batch. Scale will find the last  |
|                         |                   |          | (non-superseded) batch with this root ID and it will be            |
|                         |                   |          | re-processed by this batch.                                        |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| forced_nodes            | JSON object       | Optional | A forced nodes JSON object that defines the batch recipe nodes to  |
|                         |                   |          | force to re-process even if there are no changes to them.          |
|                         |                   |          | See :ref:`rest_v6_recipe_json_forced_nodes`                        |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+

.. _rest_v6_batch_json_configuration:

Batch Configuration JSON
------------------------

A batch configuration JSON configures how the jobs and recipes within a batch should be run.

**Example batch configuration:**

.. code-block:: javascript

   {
      "priority": 100
   }

+-----------------------------------------------------------------------------------------------------------------------------+
| **Batch Definition**                                                                                                        |
+=========================+===================+==========+====================================================================+
| priority                | Integer           | Optional | Sets a new priority to use for all jobs within the batch           |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
