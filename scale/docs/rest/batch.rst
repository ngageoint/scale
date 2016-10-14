
.. _rest_batch:

Batch Services
==============

These services provide access to information about registered batch re-processing requests.

.. _rest_batch_list:

+-------------------------------------------------------------------------------------------------------------------------+
| **Batch List**                                                                                                          |
+=========================================================================================================================+
| Returns a list of all batches.                                                                                          |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /batches/                                                                                                       |
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
|                    |                   |          | Duplicate it to multi-sort, (ex: order=title&order=status).         |
|                    |                   |          | Prefix fields with a dash to reverse the sort, (ex: order=-title).  |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| status             | String            | Optional | Return only batches with a status matching this string.             |
|                    |                   |          | Choices: [SUBMITTED, CREATED].                                      |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| recipe_type_id     | Integer           | Optional | Return only batches with a given recipe type identifier.            |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| recipe_type_name   | String            | Optional | Return only batches with a given recipe type name.                  |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
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
|                     |                   | (See :ref:`Batch Details <rest_batch_details>`)                               |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .title              | String            | The human readable display name of the batch.                                 |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .description        | String            | A longer description of the batch.                                            |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .status             | String            | The current status of the batch.                                              |
|                     |                   | Choices: [SUBMITTED, CREATED].                                                |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .recipe_type        | JSON Object       | The recipe type that is associated with the batch.                            |
|                     |                   | (See :ref:`Recipe Type Details <rest_recipe_type_details>`)                   |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .event              | JSON Object       | The trigger event that is associated with the batch.                          |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .creator_job        | JSON Object       | The job that is executed to create all the recipes defined by the batch.      |
|                     |                   | (See :ref:`Job Details <rest_job_details>`)                                   |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .created_count      | Integer           | The number of batch recipes created by this batch.                            |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .failed_count       | Integer           | The number of batch recipes failed by this batch.                             |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .total_count        | Integer           | An estimate of the total number of batch recipes to create for this batch.    |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .created            | ISO-8601 Datetime | When the associated database model was initially created.                     |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .last_modified      | ISO-8601 Datetime | When the associated database model was last saved.                            |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "count": 11,                                                                                                     |
|        "next": null,                                                                                                    |
|        "previous": null,                                                                                                |
|        "results": [                                                                                                     |
|            {                                                                                                            |
|                "id": 16,                                                                                                |
|                "title": "My Batch",                                                                                     |
|                "description": "My batch of recipes",                                                                    |
|                "status": "SUBMITTED",                                                                                   |
|                "recipe_type": {                                                                                         |
|                    "id": 1,                                                                                             |
|                    "name": "my-recipe",                                                                                 |
|                    "version": "2.0.0",                                                                                  |
|                    "title": "My Recipe",                                                                                |
|                    "description": "Does some stuff"                                                                     |
|                },                                                                                                       |
|                "event": {                                                                                               |
|                    "id": 7,                                                                                             |
|                    "type": "USER",                                                                                      |
|                    "rule": {                                                                                            |
|                        "id": 8,                                                                                         |
|                    },                                                                                                   |
|                    "occurred": "2015-06-15T19:03:26.346Z"                                                               |
|                },                                                                                                       |
|                "creator_job": {                                                                                         |
|                    "id": 3,                                                                                             |
|                    "job_type": {                                                                                        |
|                        "id": 1,                                                                                         |
|                        "name": "scale-batch-creator",                                                                   |
|                        "version": "1.0",                                                                                |
|                        "title": "Scale Batch Creator",                                                                  |
|                        "description": "Creates and queues the jobs and recipes for a Scale batch",                      |
|                        "category": "system",                                                                            |
|                        "author_name": null,                                                                             |
|                        "author_url": null,                                                                              |
|                        "is_system": true,                                                                               |
|                        "is_long_running": false,                                                                        |
|                        "is_active": true,                                                                               |
|                        "is_operational": true,                                                                          |
|                        "is_paused": false,                                                                              |
|                        "icon_code": "f0b1"                                                                              |
|                    },                                                                                                   |
|                    "job_type_rev": {                                                                                    |
|                        "id": 2                                                                                          |
|                    },                                                                                                   |
|                    "event": {                                                                                           |
|                        "id": 3                                                                                          |
|                    },                                                                                                   |
|                    "error": null,                                                                                       |
|                    "status": "RUNNING",                                                                                 |
|                    "priority": 20,                                                                                      |
|                    "num_exes": 1                                                                                        |
|                },                                                                                                       |
|                "created_count": 256,                                                                                    |
|                "failed_count": 0,                                                                                       |
|                "total_count": 512,                                                                                      |
|                "created": "2015-06-15T19:03:26.346Z",                                                                   |
|                "last_modified": "2015-06-15T19:05:26.346Z"                                                              |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_batch_details:
