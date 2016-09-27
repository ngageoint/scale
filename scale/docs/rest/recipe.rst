
.. _rest_recipe:

Recipe Services
===============

These services provide access to information about recipes.

.. _rest_recipe_list:

+-------------------------------------------------------------------------------------------------------------------------+
| **Recipe List**                                                                                                         |
+=========================================================================================================================+
| Returns a list of all recipes. Recipes marked as superseded are excluded by default.                                    |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /recipes/                                                                                                       |
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
| type_id            | Integer           | Optional | Return only recipes with a given recipe type identifier.            |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| type_name          | String            | Optional | Return only recipes with a given recipe type name.                  |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| include_superseded | Boolean           | Optional | Whether to include superseded recipe instances. Defaults to false.  |
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
|                        |                   | (See :ref:`Recipe Details <rest_recipe_details>`)                          |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .recipe_type           | JSON Object       | The recipe type that is associated with the recipe.                        |
|                        |                   | This represents the latest version of the definition.                      |
|                        |                   | (See :ref:`Recipe Type Details <rest_recipe_type_details>`)                |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .recipe_type_rev       | JSON Object       | The recipe type revision that is associated with the recipe.               |
|                        |                   | This represents the definition at the time the recipe was scheduled.       |
|                        |                   | (See :ref:`Recipe Type Revision Details <rest_recipe_type_rev_details>`)   |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .event                 | JSON Object       | The trigger event that is associated with the recipe.                      |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .is_superseded         | Boolean           | Whether this recipe has been replaced and is now obsolete.                 |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .root_superseded_recipe| JSON Object       | The first recipe in the current chain of superseded recipes.               |
|                        |                   | (See :ref:`Recipe Details <rest_recipe_details>`)                          |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .superseded_recipe     | JSON Object       | The previous recipe in the chain that was superseded by this recipe.       |
|                        |                   | (See :ref:`Recipe Details <rest_recipe_details>`)                          |
+------------------------+-------------------+----------------------------------------------------------------------------+
| .superseded_by_recipe  | JSON Object       | The next recipe in the chain that superseded this recipe.                  |
|                        |                   | (See :ref:`Recipe Details <rest_recipe_details>`)                          |
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
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "count": 15,                                                                                                     | 
|        "next": null,                                                                                                    | 
|        "previous": null,                                                                                                | 
|        "results": [                                                                                                     |
|            {                                                                                                            |
|                "id": 72,                                                                                                |
|                "recipe_type": {                                                                                         |
|                    "id": 1,                                                                                             |
|                    "name": "my-recipe",                                                                                 |
|                    "version": "1.0.0",                                                                                  |
|                    "description": "Does some stuff"                                                                     |
|                },                                                                                                       |
|                "recipe_type_rev": {                                                                                     |
|                    "id": 6,                                                                                             |
|                    "recipe_type": {                                                                                     |
|                        "id": 1                                                                                          |
|                    },                                                                                                   |
|                    "revision_num": 3                                                                                    |
|                },                                                                                                       |
|                "event": {                                                                                               |
|                    "id": 7,                                                                                             |
|                    "type": "PARSE",                                                                                     |
|                    "rule": {                                                                                            |
|                        "id": 8,                                                                                         |
|                    },                                                                                                   |
|                    "occurred": "2015-06-15T19:03:26.346Z"                                                               |
|                },                                                                                                       |
|                "is_superseded": false,                                                                                  |
|                "root_superseded_recipe": null,                                                                          |
|                "superseded_recipe": null,                                                                               |
|                "superseded_by_recipe": null,                                                                            |
|                "created": "2015-06-15T19:03:26.346Z",                                                                   |
|                "completed": "2015-06-15T19:05:26.346Z",                                                                 |
|                "superseded": null,                                                                                      |
|                "last_modified": "2015-06-15T19:05:26.346Z"                                                              |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_recipe_details:

+-------------------------------------------------------------------------------------------------------------------------+
| **Recipe Details**                                                                                                      |
+=========================================================================================================================+
| Returns a specific recipe and all its related model information including definition, event, data, and jobs.            |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /recipes/{id}/                                                                                                  |
|         Where {id} is the unique identifier of an existing model.                                                       |
+-------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+-----------------------+-------------------+-----------------------------------------------------------------------------+
| id                    | Integer           | The unique identifier of the model.                                         |
+-----------------------+-------------------+-----------------------------------------------------------------------------+
| recipe_type           | JSON Object       | The recipe type that is associated with the recipe.                         |
|                       |                   | (See :ref:`Recipe Type Details <rest_recipe_type_details>`)                 |
+-----------------------+-------------------+-----------------------------------------------------------------------------+
| recipe_type_rev       | JSON Object       | The recipe type revision that is associated with the recipe.                |
|                       |                   | This represents the definition at the time the recipe was scheduled.        |
|                       |                   | (See :ref:`Recipe Type Revision Details <rest_recipe_type_rev_details>`)    |
+-----------------------+-------------------+-----------------------------------------------------------------------------+
| event                 | JSON Object       | The trigger event that is associated with the recipe.                       |
+-----------------------+-------------------+-----------------------------------------------------------------------------+
| is_superseded         | Boolean           | Whether this recipe has been replaced and is now obsolete.                  |
+-----------------------+-------------------+-----------------------------------------------------------------------------+
| root_superseded_recipe| JSON Object       | The first recipe in the current chain of superseded recipes.                |
|                       |                   | (See :ref:`Recipe Details <rest_recipe_details>`)                           |
+-----------------------+-------------------+-----------------------------------------------------------------------------+
| superseded_recipe     | JSON Object       | The previous recipe in the chain that was superseded by this recipe.        |
|                       |                   | (See :ref:`Recipe Details <rest_recipe_details>`)                           |
+-----------------------+-------------------+-----------------------------------------------------------------------------+
| superseded_by_recipe  | JSON Object       | The next recipe in the chain that superseded this recipe.                   |
|                       |                   | (See :ref:`Recipe Details <rest_recipe_details>`)                           |
+-----------------------+-------------------+-----------------------------------------------------------------------------+
| created               | ISO-8601 Datetime | When the associated database model was initially created.                   |
+-----------------------+-------------------+-----------------------------------------------------------------------------+
| completed             | ISO-8601 Datetime | When every job in the recipe was completed successfully.                    |
|                       |                   | This field will remain null if a job in the recipe is blocked or failed.    |
+-----------------------+-------------------+-----------------------------------------------------------------------------+
| superseded            | ISO-8601 Datetime | When the the recipe became superseded by another recipe.                    |
+-----------------------+-------------------+-----------------------------------------------------------------------------+
| last_modified         | ISO-8601 Datetime | When the associated database model was last saved.                          |
+-----------------------+-------------------+-----------------------------------------------------------------------------+
| data                  | JSON Object       | JSON description defining the data used to execute a recipe instance.       |
|                       |                   | (See :ref:`architecture_jobs_recipe_data_spec`)                             |
+-----------------------+-------------------+-----------------------------------------------------------------------------+
| input_files           | JSON Object       | A list of files that the recipe used as input.                              |
|                       |                   | (See :ref:`Scale File Details <rest_scale_file_details>`)                   |
+-----------------------+-------------------+-----------------------------------------------------------------------------+
| jobs                  | Array             | The jobs associated with this recipe.                                       |
+-----------------------+-------------------+-----------------------------------------------------------------------------+
| .job_name             | String            | The name of the job for this recipe.                                        |
+-----------------------+-------------------+-----------------------------------------------------------------------------+
| .is_original          | Boolean           | Whether this is from the original recipe or copied from a superseded one.   |
+-----------------------+-------------------+-----------------------------------------------------------------------------+
| .job                  | JSON Object       | The job that is associated with the recipe.                                 |
|                       |                   | (See :ref:`Job Details <rest_job_details>`)                                 |
+-----------------------+-------------------+-----------------------------------------------------------------------------+
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
|        "recipe_type_rev": {                                                                                             |
|            "id": 5,                                                                                                     |
|            "recipe_type": {                                                                                             |
|                "id": 1                                                                                                  |
|            },                                                                                                           |
|            "revision_num": 3,                                                                                           |
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
|            "created": "2015-11-06T19:44:09.989Z"                                                                        |
|        },                                                                                                               |
|        "event": {                                                                                                       |
|            "id": 7,                                                                                                     |
|            "type": "PARSE",                                                                                             |
|            "rule": {                                                                                                    |
|                "id": 8,                                                                                                 |
|                "type": "PARSE",                                                                                         |
|                "name": "parse-png",                                                                                     |
|                "is_active": true,                                                                                       |
|                "configuration": {                                                                                       |
|                    "version": "1.0",                                                                                    |
|                    "data": {                                                                                            |
|                        "workspace_name": "products",                                                                    |
|                        "input_data_name": "input_file"                                                                  |
|                    },                                                                                                   |
|                    "condition": {                                                                                       |
|                        "media_type": "image/png",                                                                       |
|                        "data_types": []                                                                                 |
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
|        "is_superseded": false,                                                                                          |
|        "root_superseded_recipe": null,                                                                                  |
|        "superseded_recipe": null,                                                                                       |
|        "superseded_by_recipe": null,                                                                                    |
|        "created": "2015-06-15T19:03:26.346Z",                                                                           |
|        "completed": "2015-06-15T19:05:26.346Z",                                                                         |
|        "superseded": null,                                                                                              |
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
|                "is_original": true,                                                                                     |
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
|                        "revision_num": 1,                                                                               |
|                        "interface": {...},                                                                              |
|                        "created": "2015-11-06T21:30:34.622Z"                                                            |
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
|                    "is_superseded": false,                                                                              |
|                    "root_superseded_job": null,                                                                         |
|                    "superseded_job": null,                                                                              |
|                    "superseded_by_job": null,                                                                           |
|                    "delete_superseded": true,                                                                           |
|                    "created": "2015-08-28T17:55:41.005Z",                                                               |
|                    "queued": "2015-08-28T17:56:41.005Z",                                                                |
|                    "started": "2015-08-28T17:57:41.005Z",                                                               |
|                    "ended": "2015-08-28T17:58:41.005Z",                                                                 |
|                    "last_status_change": "2015-08-28T17:58:45.906Z",                                                    |
|                    "superseded": null,                                                                                  |
|                    "last_modified": "2015-08-28T17:58:46.001Z"                                                          |
|                }                                                                                                        |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+


.. _rest_recipe_reprocess:

+-------------------------------------------------------------------------------------------------------------------------+
| **Re-process Recipe**                                                                                                   |
+=========================================================================================================================+
| Creates a new recipe using its latest type revision by superseding an existing recipe and associated jobs.              |
| Note that if the recipe type definition has not changed since the recipe was created, then one or more job names must be|
| specified to force the recipe to be re-processed.                                                                       |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /recipes/{id}/reprocess/                                                                                       |
|          Where {id} is the unique identifier of an existing model.                                                      |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_names          | Array[String]     | Optional | The name of jobs within the recipe definition that should be        |
|                    |                   |          | included in the re-processing request, even when the definition for |
|                    |                   |          | those jobs has not changed between recipe type revisions.           |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| all_jobs           | Boolean           | Optional | A flag that indicates all jobs in the recipe should be re-processed,|
|                    |                   |          | even when the recipe type definitions are identical. This option    |
|                    |                   |          | overrides any job_name parameters and is typically used to          |
|                    |                   |          | re-process previously completed jobs with new algorithm updates.    |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "all_jobs": true                                                                                                 |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 201 CREATED                                                                                        |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Location**       | URL pointing to the details for the newly created recipe                                           |
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
|        "recipe_type_rev": {                                                                                             |
|            "id": 5,                                                                                                     |
|            "recipe_type": {                                                                                             |
|                "id": 1                                                                                                  |
|            },                                                                                                           |
|            "revision_num": 3,                                                                                           |
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
|            "created": "2015-11-06T19:44:09.989Z"                                                                        |
|        },                                                                                                               |
|        "event": {                                                                                                       |
|            "id": 7,                                                                                                     |
|            "type": "PARSE",                                                                                             |
|            "rule": {                                                                                                    |
|                "id": 8,                                                                                                 |
|                "type": "PARSE",                                                                                         |
|                "name": "parse-png",                                                                                     |
|                "is_active": true,                                                                                       |
|                "configuration": {                                                                                       |
|                    "version": "1.0",                                                                                    |
|                    "data": {                                                                                            |
|                        "workspace_name": "products",                                                                    |
|                        "input_data_name": "input_file"                                                                  |
|                    },                                                                                                   |
|                    "condition": {                                                                                       |
|                        "media_type": "image/png",                                                                       |
|                        "data_types": []                                                                                 |
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
|        "is_superseded": false,                                                                                          |
|        "root_superseded_recipe": {...},                                                                                 |
|        "superseded_recipe": {...},                                                                                      |
|        "superseded_by_recipe": null,                                                                                    |
|        "created": "2015-06-15T19:03:26.346Z",                                                                           |
|        "completed": "2015-06-15T19:05:26.346Z",                                                                         |
|        "superseded": null,                                                                                              |
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
|                "is_original": true,                                                                                     |
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
|                        "revision_num": 1,                                                                               |
|                        "interface": {...},                                                                              |
|                        "created": "2015-11-06T21:30:34.622Z"                                                            |
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
|                    "is_superseded": false,                                                                              |
|                    "root_superseded_job": null,                                                                         |
|                    "superseded_job": null,                                                                              |
|                    "superseded_by_job": null,                                                                           |
|                    "delete_superseded": true,                                                                           |
|                    "created": "2015-08-28T17:55:41.005Z",                                                               |
|                    "queued": "2015-08-28T17:56:41.005Z",                                                                |
|                    "started": "2015-08-28T17:57:41.005Z",                                                               |
|                    "ended": "2015-08-28T17:58:41.005Z",                                                                 |
|                    "last_status_change": "2015-08-28T17:58:45.906Z",                                                    |
|                    "superseded": null,                                                                                  |
|                    "last_modified": "2015-08-28T17:58:46.001Z"                                                          |
|                }                                                                                                        |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+
