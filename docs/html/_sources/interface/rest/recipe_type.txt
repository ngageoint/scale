
.. _rest_recipe_type:

Recipe Types Services
===========================================================================================================================

These services provide access to information about recipe types.

.. _rest_recipe_type_list:

+-------------------------------------------------------------------------------------------------------------------------+
| **Recipe Type List**                                                                                                    |
+=========================================================================================================================+
| Returns recipe types and basic recipe type information                                                                  |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /recipe-types/                                                                                                  |
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
|                    |                   | (See :ref:`Recipe Type Details <rest_recipe_type_details>`)                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .name              | String            | The stable name of recipe job type used for queries.                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .version           | String            | The version of the recipe type.                                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .title             | String            | The human readable display name of the recipe type.                            |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .description       | String            | An optional description of the recipe type.                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .is_active         | Boolean           | Whether the recipe type is active (false once recipe type is archived).        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .definition        | JSON Object       | JSON description defining the interface for running a recipe of this type.     |
|                    |                   | (See :ref:`architecture_jobs_recipe_definition_spec`)                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .revision_num      | Integer           | The current revision number of the recipe type, incremented for each edit.     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .created           | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .last_modified     | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .archived          | ISO-8601 Datetime | When the recipe type was archived (no longer active).                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .trigger_rule      | JSON Object       | The linked trigger rule that automatically invokes the recipe type.            |
|                    |                   | (See :ref:`Trigger Rule Details <rest_trigger_rule_details>`)                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "count": 9,                                                                                                      |
|        "next": null,                                                                                                    |
|        "previous": null,                                                                                                |
|        "results": [                                                                                                     |
|            {                                                                                                            |
|                "id": 1,                                                                                                 |
|                "name": "my-recipe",                                                                                     |
|                "version": "1.0.0",                                                                                      |
|                "title": "My Recipe",                                                                                    |
|                "description": "This is a description of the recipe",                                                    |
|                "is_active": true,                                                                                       |
|                "definition": {                                                                                          |
|                    "input_data": [                                                                                      |
|                        {                                                                                                |
|                            "media_types": [                                                                             |
|                                "image/png"                                                                              |
|                            ],                                                                                           |
|                            "type": "file",                                                                              |
|                            "name": "input_file"                                                                         |
|                        }                                                                                                |
|                    ],                                                                                                   |
|                    "version": "1.0",                                                                                    |
|                    "jobs": [                                                                                            |
|                        {                                                                                                |
|                            "recipe_inputs": [                                                                           |
|                                {                                                                                        |
|                                    "job_input": "input_file",                                                           |
|                                    "recipe_input": "input_file"                                                         |
|                                }                                                                                        |
|                            ],                                                                                           |
|                            "name": "nitf",                                                                              |
|                            "job_type": {                                                                                |
|                                "name": "nitf-converter",                                                                |
|                                "version": "1.2.3"                                                                       |
|                            }                                                                                            |
|                        }                                                                                                |
|                    ]                                                                                                    |
|                },                                                                                                       |
|                "revision_num": 1,                                                                                       |
|                "created": "2015-06-15T19:03:26.346Z",                                                                   |
|                "last_modified": "2015-06-15T19:03:26.346Z",                                                             |
|                "archived": null,                                                                                        |
|                "trigger_rule": {                                                                                        |
|                    "id": 12                                                                                             |
|                }                                                                                                        |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_recipe_type_create:

+-------------------------------------------------------------------------------------------------------------------------+
| **Create Recipe Type**                                                                                                  |
+=========================================================================================================================+
| Creates a new recipe type with associated definition                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /recipe-types/                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| name               | String            | Required | The stable name of recipe type used for queries.                    |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| version            | String            | Required | The version of the recipe type.                                     |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| title              | String            | Optional | The human-readable name of the recipe type.                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| description        | String            | Optional | An optional description of the recipe type.                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| definition         | JSON Object       | Required | JSON description of the interface for running a recipe of this type.|
|                    |                   |          | (See :ref:`architecture_jobs_recipe_definition_spec`)               |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| trigger_rule       | JSON Object       | Optional | The linked trigger rule that automatically invokes the recipe type. |
|                    |                   |          | The type and configuration fields are required if setting a rule.   |
|                    |                   |          | The is_active field is optional and can be used to pause the recipe.|
|                    |                   |          | (See :ref:`Trigger Rule Details <rest_trigger_rule_details>`)       |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "name": "my-recipe",                                                                                             |
|        "version": "1.0",                                                                                                |
|        "title": "My Recipe",                                                                                            |
|        "description": "This is a description of the recipe",                                                            |
|        "definition": {                                                                                                  |
|            "input_data": [                                                                                              |
|                {                                                                                                        |
|                    "media_types": ["text/plain"],                                                                       |
|                    "type": "file",                                                                                      |
|                    "name": "input_file"                                                                                 |
|                }                                                                                                        |
|            ],                                                                                                           |
|            "jobs": [                                                                                                    |
|                {                                                                                                        |
|                    "recipe_inputs": [                                                                                   |
|                        {                                                                                                |
|                            "job_input": "input_file",                                                                   |
|                            "recipe_input": "input_file"                                                                 |
|                        }                                                                                                |
|                    ],                                                                                                   |
|                    "name": "MyJob1",                                                                                    |
|                    "job_type": {                                                                                        |
|                        "name": "my-job1",                                                                               |
|                        "version": "1.2.3"                                                                               |
|                    }                                                                                                    |
|                },                                                                                                       |
|                {                                                                                                        |
|                    "recipe_inputs": [                                                                                   |
|                        {                                                                                                |
|                            "job_input": "input_file",                                                                   |
|                            "recipe_input": "input_file"                                                                 |
|                        }                                                                                                |
|                    ],                                                                                                   |
|                    "name": "MyJob2",                                                                                    |
|                    "job_type": {                                                                                        |
|                        "name": "my-job2",                                                                               |
|                        "version": "4.5.6"                                                                               |
|                    }                                                                                                    |
|                }                                                                                                        |
|            ],                                                                                                           |
|        },                                                                                                               |
|        "trigger_rule": {                                                                                                |
|            "type": "PARSE",                                                                                             |
|            "is_active": true,                                                                                           |
|            "configuration": {                                                                                           |
|                "version": "1.0",                                                                                        |
|                "condition": {                                                                                           |
|                    "media_type": "text/plain",                                                                          |
|                    "data_types": []                                                                                     |
|                },                                                                                                       |
|                "data": {                                                                                                |
|                    "input_data_name": "input_file",                                                                     |
|                    "workspace_name": "rs"                                                                               |
|                }                                                                                                        |
|            }                                                                                                            |
|        }                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 201 CREATED                                                                                        |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
|                    | JSON Object       | All fields are the same as the recipe type details model.                      |
|                    |                   | (See :ref:`Recipe Type Details <rest_recipe_type_details>`)                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "id": 1,                                                                                                         |
|        "name": "my-recipe",                                                                                             |
|        "version": "1.0.0",                                                                                              |
|        "title": "My Recipe",                                                                                            |
|        "description": "This is a description of the recipe",                                                            |
|        "is_active": true,                                                                                               |
|        "definition": {                                                                                                  |
|            "input_data": [                                                                                              |
|                {                                                                                                        |
|                    "media_types": [                                                                                     |
|                        "image/png"                                                                                      |
|                    ],                                                                                                   |
|                    "type": "file",                                                                                      |
|                    "name": "input_file"                                                                                 |
|                }                                                                                                        |
|            ],                                                                                                           |
|            "version": "1.0",                                                                                            |
|            "jobs": [                                                                                                    |
|                {                                                                                                        |
|                    "recipe_inputs": [                                                                                   |
|                        {                                                                                                |
|                            "job_input": "input_file",                                                                   |
|                            "recipe_input": "input_file"                                                                 |
|                        }                                                                                                |
|                    ],                                                                                                   |
|                    "name": "my_job_type",                                                                               |
|                    "job_type": {                                                                                        |
|                        "name": "my-job-type",                                                                           |
|                        "version": "1.2.3"                                                                               |
|                    }                                                                                                    |
|                }                                                                                                        |
|            ]                                                                                                            |
|        },                                                                                                               |
|        "revision_num": 1,                                                                                               |
|        "created": "2015-06-15T19:03:26.346Z",                                                                           |
|        "last_modified": "2015-06-15T19:03:26.346Z",                                                                     |
|        "archived": null,                                                                                                |
|        "trigger_rule": {                                                                                                |
|            "id": 12,                                                                                                    |
|            "type": "PARSE",                                                                                             |
|            "name": "my-job-type-recipe",                                                                                |
|            "is_active": true,                                                                                           |
|            "configuration": {                                                                                           |
|                "version": "1.0",                                                                                        |
|                "data": {                                                                                                |
|                    "workspace_name": "products",                                                                        |
|                    "input_data_name": "input_file"                                                                      |
|                },                                                                                                       |
|                "condition": {                                                                                           |
|                    "media_type": "image/png",                                                                           |
|                    "data_types": [                                                                                      |
|                        "My-Type"                                                                                        |
|                    ]                                                                                                    |
|                }                                                                                                        |
|            }                                                                                                            |
|        },                                                                                                               |
|        "job_types": [                                                                                                   |
|            {                                                                                                            |
|                "id": 35,                                                                                                |
|                "name": "my-job-type",                                                                                   |
|                "version": "1.2.3",                                                                                      |
|                "title": "Job Type",                                                                                     |
|                "description": "This is a job type",                                                                     |
|                "category": "system",                                                                                    |
|                "author_name": null,                                                                                     |
|                "author_url": null,                                                                                      |
|                "is_system": false,                                                                                      |
|                "is_long_running": false,                                                                                |
|                "is_active": true,                                                                                       |
|                "is_operational": true,                                                                                  |
|                "is_paused": false,                                                                                      |
|                "icon_code": "f1c5",                                                                                     |
|                "interface": {                                                                                           |
|                    "input_data": [                                                                                      |
|                        {                                                                                                |
|                            "media_types": [                                                                             |
|                                "image/png"                                                                              |
|                            ],                                                                                           |
|                            "type": "file",                                                                              |
|                            "name": "input_file"                                                                         |
|                        }                                                                                                |
|                    ],                                                                                                   |
|                    "version": "1.0",                                                                                    |
|                    "command": "command_to_run.sh",                                                                      |
|                    "output_data": [                                                                                     |
|                        {                                                                                                |
|                            "media_type": "image/png",                                                                   |
|                            "type": "file",                                                                              |
|                            "name": "my_file_name"                                                                       |
|                        }                                                                                                |
|                    ],                                                                                                   |
|                    "command_arguments": "${input_file} ${job_output_dir}"                                               |
|                }                                                                                                        |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_recipe_type_validate:

+-------------------------------------------------------------------------------------------------------------------------+
| **Validate Recipe Type**                                                                                                |
+=========================================================================================================================+
| Validates a new recipe type without actually saving it                                                                  |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /recipe-types/validation/                                                                                      |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| name               | String            | Required | The stable name of recipe job type used for queries.                |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| version            | String            | Required | The version of the recipe type.                                     |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| title              | String            | Optional | The human-readable name of the recipe type.                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| description        | String            | Optional | An optional description of the recipe type.                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| definition         | JSON Object       | Required | JSON description defining the interface for running the recipe type.|
|                    |                   |          | (See :ref:`architecture_jobs_recipe_definition_spec`)               |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| trigger_rule       | JSON Object       | Optional | The linked trigger rule that automatically invokes the recipe type. |
|                    |                   |          | The type and configuration fields are required if setting a rule.   |
|                    |                   |          | The is_active field is optional and can be used to pause the recipe.|
|                    |                   |          | (See :ref:`Trigger Rule Details <rest_trigger_rule_details>`)       |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "name": "my-recipe",                                                                                             |
|        "version": "1.0",                                                                                                |
|        "title": "My Recipe",                                                                                            |
|        "description": "This is a description of the recipe",                                                            |
|        "input_data": [                                                                                                  |
|            {                                                                                                            |
|                "media_types": ["text/plain"],                                                                           |
|                "type": "file",                                                                                          |
|                "name": "input_file"                                                                                     |
|            }                                                                                                            |
|        ],                                                                                                               |
|        "jobs": [                                                                                                        |
|            {                                                                                                            |
|                "recipe_inputs": [                                                                                       |
|                    {                                                                                                    |
|                        "job_input": "input_file",                                                                       |
|                        "recipe_input": "input_file"                                                                     |
|                    }                                                                                                    |
|                ],                                                                                                       |
|                "name": "MyJob1",                                                                                        |
|                "job_type": {                                                                                            |
|                    "name": "my-job1",                                                                                   |
|                    "version": "1.2.3"                                                                                   |
|                }                                                                                                        |
|            },                                                                                                           |
|            {                                                                                                            |
|                "recipe_inputs": [                                                                                       |
|                    {                                                                                                    |
|                        "job_input": "input_file",                                                                       |
|                        "recipe_input": "input_file"                                                                     |
|                    }                                                                                                    |
|                ],                                                                                                       |
|                "name": "MyJob2",                                                                                        |
|                "job_type": {                                                                                            |
|                    "name": "my-job2",                                                                                   |
|                    "version": "4.5.6"                                                                                   |
|                }                                                                                                        |
|            }                                                                                                            |
|        ],                                                                                                               |
|        "trigger_rule": {                                                                                                |
|            "type": "PARSE",                                                                                             |
|            "is_active": true,                                                                                           |
|            "configuration": {                                                                                           |
|                "version": "1.0",                                                                                        |
|                "condition": {                                                                                           |
|                    "media_type": "text/plain",                                                                          |
|                    "data_types": []                                                                                     |
|                },                                                                                                       |
|                "data": {                                                                                                |
|                    "input_data_name": "input_file",                                                                     |
|                    "workspace_name": "rs"                                                                               |
|                }                                                                                                        |
|            }                                                                                                            |
|        }                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+---------------------+------------------------------------------------------------------------------+
| warnings           | Array               | A list of warnings discovered during validation.                             |
+--------------------+---------------------+------------------------------------------------------------------------------+
| .id                | String              | An identifier for the warning.                                               |
+--------------------+---------------------+------------------------------------------------------------------------------+
| .details           | String              | A human-readable description of the problem.                                 |
+--------------------+---------------------+------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "warnings": [                                                                                                    |
|            "id": "media_type",                                                                                          |
|            "details": "Invalid media type for data input: input_file -> image/png"                                      |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_recipe_type_details:

+-------------------------------------------------------------------------------------------------------------------------+
| **Recipe Type Details**                                                                                                 |
+=========================================================================================================================+
| Returns a specific recipe type and all its related model information.                                                   |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /recipe-types/{id}/                                                                                             |
|         Where {id} is the unique identifier of an existing model.                                                       |
+-------------------------------------------------------------------------------------------------------------------------+
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
| name               | String            | The human-readable name of the recipe type.                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| version            | String            | The version of the recipe type.                                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| description        | String            | An optional description of the recipe type.                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| is_active          | Boolean           | Whether the recipe type is active (false once recipe type is archived).        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| definition         | JSON Object       | JSON description defining the interface for running a recipe of this type.     |
|                    |                   | (See :ref:`architecture_jobs_recipe_definition_spec`)                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| revision_num       | Integer           | The current revision number of the recipe type, incremented for each edit.     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| created            | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| last_modified      | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| archived           | ISO-8601 Datetime | When the recipe type was archived (no longer active).                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| trigger_rule       | JSON Object       | The associated trigger rule that automatically invokes this recipe type.       |
|                    |                   | (See :ref:`Trigger Rule Details <rest_trigger_rule_details>`)                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| job_types          | Array             | List of all job_types that are referenced by this recipe type's definition     |
|                    |                   | (See :ref:`Job Type Details <rest_job_type_details>`)                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "id": 1,                                                                                                         |
|        "name": "my-recipe",                                                                                             |
|        "version": "1.0.0",                                                                                              |
|        "title": "My Recipe",                                                                                            |
|        "description": "This is a description of the recipe",                                                            |
|        "is_active": true,                                                                                               |
|        "definition": {                                                                                                  |
|            "input_data": [                                                                                              |
|                {                                                                                                        |
|                    "media_types": [                                                                                     |
|                        "image/png"                                                                                      |
|                    ],                                                                                                   |
|                    "type": "file",                                                                                      |
|                    "name": "input_file"                                                                                 |
|                }                                                                                                        |
|            ],                                                                                                           |
|            "version": "1.0",                                                                                            |
|            "jobs": [                                                                                                    |
|                {                                                                                                        |
|                    "recipe_inputs": [                                                                                   |
|                        {                                                                                                |
|                            "job_input": "input_file",                                                                   |
|                            "recipe_input": "input_file"                                                                 |
|                        }                                                                                                |
|                    ],                                                                                                   |
|                    "name": "my_job_type",                                                                               |
|                    "job_type": {                                                                                        |
|                        "name": "my-job-type",                                                                           |
|                        "version": "1.2.3"                                                                               |
|                    }                                                                                                    |
|                }                                                                                                        |
|            ]                                                                                                            |
|        },                                                                                                               |
|        "revision_num": 1,                                                                                               |
|        "created": "2015-06-15T19:03:26.346Z",                                                                           |
|        "last_modified": "2015-06-15T19:03:26.346Z",                                                                     |
|        "archived": null,                                                                                                |
|        "trigger_rule": {                                                                                                |
|            "id": 12,                                                                                                    |
|            "type": "PARSE",                                                                                             |
|            "name": "my-job-type-recipe",                                                                                |
|            "is_active": true,                                                                                           |
|            "configuration": {                                                                                           |
|                "version": "1.0",                                                                                        |
|                "data": {                                                                                                |
|                    "workspace_name": "products",                                                                        |
|                    "input_data_name": "input_file"                                                                      |
|                },                                                                                                       |
|                "condition": {                                                                                           |
|                    "media_type": "image/png",                                                                           |
|                    "data_types": [                                                                                      |
|                        "My-Type"                                                                                        |
|                    ]                                                                                                    |
|                }                                                                                                        |
|            }                                                                                                            |
|        },                                                                                                               |
|        "job_types": [                                                                                                   |
|            {                                                                                                            |
|                "id": 35,                                                                                                |
|                "name": "my-job-type",                                                                                   |
|                "version": "1.2.3",                                                                                      |
|                "title": "Job Type",                                                                                     |
|                "description": "This is a job type",                                                                     |
|                "category": "system",                                                                                    |
|                "author_name": null,                                                                                     |
|                "author_url": null,                                                                                      |
|                "is_system": false,                                                                                      |
|                "is_long_running": false,                                                                                |
|                "is_active": true,                                                                                       |
|                "is_operational": true,                                                                                  |
|                "is_paused": false,                                                                                      |
|                "icon_code": "f1c5",                                                                                     |
|                "interface": {                                                                                           |
|                    "input_data": [                                                                                      |
|                        {                                                                                                |
|                            "media_types": [                                                                             |
|                                "image/png"                                                                              |
|                            ],                                                                                           |
|                            "type": "file",                                                                              |
|                            "name": "input_file"                                                                         |
|                        }                                                                                                |
|                    ],                                                                                                   |
|                    "version": "1.0",                                                                                    |
|                    "command": "command_to_run.sh",                                                                      |
|                    "output_data": [                                                                                     |
|                        {                                                                                                |
|                            "media_type": "image/png",                                                                   |
|                            "type": "file",                                                                              |
|                            "name": "my_file_name"                                                                       |
|                        }                                                                                                |
|                    ],                                                                                                   |
|                    "command_arguments": "${input_file} ${job_output_dir}"                                               |
|                }                                                                                                        |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_recipe_type_edit:

+-------------------------------------------------------------------------------------------------------------------------+
| **Edit Recipe Type**                                                                                                    |
+=========================================================================================================================+
| Edits an existing recipe type with associated definition                                                                |
+-------------------------------------------------------------------------------------------------------------------------+
| **PATCH** /recipe-types/{id}/                                                                                           |
|         Where {id} is the unique identifier of an existing model.                                                       |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| title              | String            | Optional | The human-readable name of the recipe type.                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| description        | String            | Optional | An optional description of the recipe type.                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| definition         | JSON Object       | Optional | JSON description of the interface for running a recipe of this type.|
|                    |                   |          | (See :ref:`architecture_jobs_recipe_definition_spec`)               |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| trigger_rule       | JSON Object       | Optional | The linked trigger rule that automatically invokes the recipe type. |
|                    |                   |          | The type and configuration fields are required if setting a rule.   |
|                    |                   |          | The is_active field is optional and can be used to pause the recipe.|
|                    |                   |          | Set this field to null to remove the existing trigger rule.         |
|                    |                   |          | (See :ref:`Trigger Rule Details <rest_trigger_rule_details>`)       |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "title": "My Recipe",                                                                                            |
|        "description": "This is a description of the recipe",                                                            |
|        "definition": {                                                                                                  |
|            "input_data": [                                                                                              |
|                {                                                                                                        |
|                    "media_types": ["text/plain"],                                                                       |
|                    "type": "file",                                                                                      |
|                    "name": "input_file"                                                                                 |
|                }                                                                                                        |
|            ],                                                                                                           |
|            "jobs": [                                                                                                    |
|                {                                                                                                        |
|                    "recipe_inputs": [                                                                                   |
|                        {                                                                                                |
|                            "job_input": "input_file",                                                                   |
|                            "recipe_input": "input_file"                                                                 |
|                        }                                                                                                |
|                    ],                                                                                                   |
|                    "name": "MyJob1",                                                                                    |
|                    "job_type": {                                                                                        |
|                        "name": "my-job1",                                                                               |
|                        "version": "1.2.3"                                                                               |
|                    }                                                                                                    |
|                },                                                                                                       |
|                {                                                                                                        |
|                    "recipe_inputs": [                                                                                   |
|                        {                                                                                                |
|                            "job_input": "input_file",                                                                   |
|                            "recipe_input": "input_file"                                                                 |
|                        }                                                                                                |
|                    ],                                                                                                   |
|                    "name": "MyJob2",                                                                                    |
|                    "job_type": {                                                                                        |
|                        "name": "my-job2",                                                                               |
|                        "version": "4.5.6"                                                                               |
|                    }                                                                                                    |
|                }                                                                                                        |
|            ],                                                                                                           |
|        },                                                                                                               |
|        "trigger_rule": {                                                                                                |
|            "type": "PARSE",                                                                                             |
|            "is_active": true,                                                                                           |
|            "configuration": {                                                                                           |
|                "version": "1.0",                                                                                        |
|                "condition": {                                                                                           |
|                    "media_type": "text/plain",                                                                          |
|                    "data_types": []                                                                                     |
|                },                                                                                                       |
|                "data": {                                                                                                |
|                    "input_data_name": "input_file",                                                                     |
|                    "workspace_name": "rs"                                                                               |
|                }                                                                                                        |
|            }                                                                                                            |
|        }                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
|                    | JSON Object       | All fields are the same as the recipe type details model.                      |
|                    |                   | (See :ref:`Recipe Type Details <rest_recipe_type_details>`)                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "id": 1,                                                                                                         |
|        "name": "my-recipe",                                                                                             |
|        "version": "1.0.0",                                                                                              |
|        "title": "My Recipe",                                                                                            |
|        "description": "This is a description of the recipe",                                                            |
|        "is_active": true,                                                                                               |
|        "definition": {                                                                                                  |
|            "input_data": [                                                                                              |
|                {                                                                                                        |
|                    "media_types": [                                                                                     |
|                        "image/png"                                                                                      |
|                    ],                                                                                                   |
|                    "type": "file",                                                                                      |
|                    "name": "input_file"                                                                                 |
|                }                                                                                                        |
|            ],                                                                                                           |
|            "version": "1.0",                                                                                            |
|            "jobs": [                                                                                                    |
|                {                                                                                                        |
|                    "recipe_inputs": [                                                                                   |
|                        {                                                                                                |
|                            "job_input": "input_file",                                                                   |
|                            "recipe_input": "input_file"                                                                 |
|                        }                                                                                                |
|                    ],                                                                                                   |
|                    "name": "my_job_type",                                                                               |
|                    "job_type": {                                                                                        |
|                        "name": "my-job-type",                                                                           |
|                        "version": "1.2.3"                                                                               |
|                    }                                                                                                    |
|                }                                                                                                        |
|            ]                                                                                                            |
|        },                                                                                                               |
|        "revision_num": 2,                                                                                               |
|        "created": "2015-06-15T19:03:26.346Z",                                                                           |
|        "last_modified": "2015-06-15T19:03:26.346Z",                                                                     |
|        "archived": null,                                                                                                |
|        "trigger_rule": {                                                                                                |
|            "id": 12,                                                                                                    |
|            "type": "PARSE",                                                                                             |
|            "name": "my-job-type-recipe",                                                                                |
|            "is_active": true,                                                                                           |
|            "configuration": {                                                                                           |
|                "version": "1.0",                                                                                        |
|                "data": {                                                                                                |
|                    "workspace_name": "products",                                                                        |
|                    "input_data_name": "input_file"                                                                      |
|                },                                                                                                       |
|                "condition": {                                                                                           |
|                    "media_type": "image/png",                                                                           |
|                    "data_types": [                                                                                      |
|                        "My-Type"                                                                                        |
|                    ]                                                                                                    |
|                }                                                                                                        |
|            }                                                                                                            |
|        },                                                                                                               |
|        "job_types": [                                                                                                   |
|            {                                                                                                            |
|                "id": 35,                                                                                                |
|                "name": "my-job-type",                                                                                   |
|                "version": "1.2.3",                                                                                      |
|                "title": "Job Type",                                                                                     |
|                "description": "This is a job type",                                                                     |
|                "category": "system",                                                                                    |
|                "author_name": null,                                                                                     |
|                "author_url": null,                                                                                      |
|                "is_system": false,                                                                                      |
|                "is_long_running": false,                                                                                |
|                "is_active": true,                                                                                       |
|                "is_operational": true,                                                                                  |
|                "is_paused": false,                                                                                      |
|                "icon_code": "f1c5",                                                                                     |
|                "interface": {                                                                                           |
|                    "input_data": [                                                                                      |
|                        {                                                                                                |
|                            "media_types": [                                                                             |
|                                "image/png"                                                                              |
|                            ],                                                                                           |
|                            "type": "file",                                                                              |
|                            "name": "input_file"                                                                         |
|                        }                                                                                                |
|                    ],                                                                                                   |
|                    "version": "1.0",                                                                                    |
|                    "command": "command_to_run.sh",                                                                      |
|                    "output_data": [                                                                                     |
|                        {                                                                                                |
|                            "media_type": "image/png",                                                                   |
|                            "type": "file",                                                                              |
|                            "name": "my_file_name"                                                                       |
|                        }                                                                                                |
|                    ],                                                                                                   |
|                    "command_arguments": "${input_file} ${job_output_dir}"                                               |
|                }                                                                                                        |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_recipe_type_rev_details:
