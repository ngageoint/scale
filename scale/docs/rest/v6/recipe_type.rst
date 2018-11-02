.. _rest_v6_recipe_type:

v6 Recipe Type Services
=======================

These services allow for the creation and management of recipes. A recipe type is a user-defined workflow that allows
jobs and recipes to be connected together in order to pass output from jobs to the input of other jobs.

.. _rest_v6_recipe_json_definition:

Recipe Definition JSON
----------------------

A recipe definition JSON describes a workflow of jobs and recipes connected together and able to pass output from one to
another.

**Example recipe definition:**

.. code-block:: javascript

   {
      "input": {
         "files": [{'name': 'foo', 'media_types': ['image/tiff'], 'required': True, 'multiple': True}],
         "json": [{'name': 'bar', 'type': 'integer', 'required': False}]
      },
      "nodes": {
         "node_a": {
            "dependencies": [],
            "input": {
               "input_1": {"type": "recipe", "input": "foo"}
            },
            "node_type": {
               "node_type": "job",
               "job_type_name": "job-type-1",
               "job_type_version": "1.0",
               "job_type_revision": 1
            }
         },
         "node_b": {
            "dependencies": [{"name": "node_a"}],
            "input": {
               "input_1": {"type": "recipe", "input": "foo"},
               "input_2": {"type": "dependency", "node": "node_a", "output": "output_1"}
            },
            "node_type": {
               "node_type": "job",
               "job_type_name": "job-type-2",
               "job_type_version": "2.0",
               "job_type_revision": 1
            }
         },
         "node_c": {
            "dependencies": [{"name": "node_b"}],
            "input": {
               "input_1": {"type": "recipe", "input": "bar"},
               "input_2": {"type": "dependency", "node": "node_b", "output": "output_1"}
            },
            "node_type": {
               "node_type": "recipe",
               "recipe_type_name": "recipe-type-1",
               "recipe_type_revision": 5
            }
         }
      }
   }

+-----------------------------------------------------------------------------------------------------------------------------+
| **Recipe Definition**                                                                                                       |
+============================+================+==========+====================================================================+
| input                      | JSON object    | Required | The input interface for the recipe                                 |
|                            |                |          | See :ref:`rest_v6_data_interface`                                  |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| nodes                      | JSON object    | Required | All of the nodes within the recipe stored by node name             |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| dependencies               | Array          | Required | The list of dependencies for this recipe node. Each JSON object in |
|                            |                |          | the list has a single string field called *name* giving the node   |
|                            |                |          | name of the dependency.                                            |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| input                      | JSON object    | Required | An object describing the connections to the input parameters of    |
|                            |                |          | the node, where each key is the input name and each value is an    |
|                            |                |          | object describing the connection                                   |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| type                       | String         | Required | The type of the connection, either 'recipe' or 'dependency'        |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| input                      | String         | Required | ('recipe' connection) The name of the recipe input being connected |
|                            |                |          | to the node input                                                  |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| node                       | String         | Required | ('dependency' connection) The name of the node being connected to  |
|                            |                |          | this node                                                          |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| output                     | String         | Required | ('dependency' connection) The name of the dependency node's output |
|                            |                |          | being connected to this node                                       |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| node_type                  | JSON object    | Required | An object describing the type of the node                          |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| node_type                  | String         | Required | The type of the node, either 'job' or 'recipe'                     |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| job_type_name              | String         | Required | ('job' node) The name of the job type                              |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| job_type_version           | String         | Required | ('job' node) The version of the job type                           |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| job_type_revision          | Integer        | Required | ('job' node) The revision of the job type                          |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| recipe_type_name           | String         | Required | ('recipe' node) The name of the recipe type                        |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| recipe_type_revision       | Integer        | Required | ('recipe' node) The revision of the recipe type                    |
+----------------------------+----------------+----------+--------------------------------------------------------------------+

.. _rest_v6_recipe_json_diff:

Recipe Diff JSON
----------------

A recipe diff JSON describes the differences between two recipe definitions (two revisions). The differences explain
which pieces (nodes) within the recipe will be reprocessed when a newer recipe type revision is run.

**Example recipe diff:**

.. code-block:: javascript

   {
      "can_be_reprocessed": true,
      "reasons": [],
      "nodes": {
         "node_a": {
            "status": "UNCHANGED",
            "changes": [],
            "reprocess_new_node": false,
            "force_reprocess": false,
            "dependencies": [],
            "node_type": {
               "node_type": "job",
               "job_type_name": "job-type-1",
               "job_type_version": "1.0",
               "job_type_revision": 1
            }
         },
         "node_b": {
            "status": "CHANGED",
            "changes": [{"name": "JOB_TYPE_VERSION_CHANGE", "description": "Job type version changed from 1.0 to 2.0"}],
            "reprocess_new_node": true,
            "force_reprocess": false,
            "dependencies": [{"name": "node_a"}],
            "node_type": {
               "node_type": "job",
               "job_type_name": "job-type-2",
               "job_type_version": "2.0",
               "prev_job_type_version": "1.0",
               "job_type_revision": 1
            }
         },
         "node_c": {
            "status": "NEW",
            "changes": [],
            "reprocess_new_node": true,
            "force_reprocess": false,
            "dependencies": [{"name": "node_b"}],
            "node_type": {
               "node_type": "recipe",
               "recipe_type_name": "recipe-type-1",
               "recipe_type_revision": 5
            }
         },
         "node_d": {
            "status": "CHANGED",
            "changes": [{"name": "FILTER_CHANGE", "description": "Data filter changed"}],
            "reprocess_new_node": true,
            "force_reprocess": false,
            "dependencies": [{"name": "node_a"}],
            "node_type": {
               "node_type": "condition"
            }
         },
         "node_e": {
            "status": "CHANGED",
            "changes": [{"name": "PARENT_CHANGED", "description": "Parent node node_d changed"}],
            "reprocess_new_node": true,
            "force_reprocess": false,
            "dependencies": [{"name": "node_d"}],
            "node_type": {
               "node_type": "job",
               "job_type_name": "job-type-3",
               "job_type_version": "1.0",
               "prev_job_type_version": "1.0",
               "job_type_revision": 1
            }
         }
      }
   }

+-----------------------------------------------------------------------------------------------------------------------------+
| **Recipe Diff**                                                                                                             |
+============================+================+==========+====================================================================+
| can_be_reprocessed         | Boolean        | Required | Indicates whether recipes from the previous revision can be        |
|                            |                |          | reprocessed as the newer revision.                                 |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| reasons                    | Array          | Required | Lists any reasons causing *can_be_reprocessed* to be false. The    |
|                            |                |          | reasons are JSON objects with *name* and *description* string      |
|                            |                |          | fields.                                                            |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| nodes                      | JSON object    | Required | All of the diffs for each recipe node between the two revisions,   |
|                            |                |          | stored by node name                                                |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| status                     | String         | Required | The status indicating the node differences between the two         |
|                            |                |          | revisions. The possible statuses are:                              |
|                            |                |          |                                                                    |
|                            |                |          | - *DELETED* - the node existed in the previous revision and has    |
|                            |                |          |               been removed in the newer revision                   |
|                            |                |          | - *UNCHANGED* - the node did not change between the revisions      |
|                            |                |          | - *CHANGED* - the node changed between the revisions, see the      |
|                            |                |          |               *changes* list for more details                      |
|                            |                |          | - *NEW* - the node did not exist in the previous revision and was  |
|                            |                |          |           added in the newer revision                              |
|                            |                |          |                                                                    |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| changes                    | Array          | Required | If *status* is *CHANGED*, lists the job's changes between the two  |
|                            |                |          | revisions. Each change is a JSON object with *name* and            |
|                            |                |          | *description* string fields.                                       |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| reprocess_new_node         | Boolean        | Required | Indicates whether this node will be superseded by a new node if    |
|                            |                |          | the recipe is reprocessed                                          |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| force_reprocess            | Boolean        | Required | Indicates whether the user has requested that this node be         |
|                            |                |          | reprocessed regardless of whether it has changed                   |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| dependencies               | Array          | Required | The list of dependencies for this recipe node. Each JSON object in |
|                            |                |          | the list has a single string field called *name* giving the node   |
|                            |                |          | name of the dependency.                                            |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| prev_node_type             | String         | Optional | The type of the node in the previous revision, if changed in the   |
|                            |                |          | newer revision                                                     |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| node_type                  | JSON object    | Required | An object describing the type of the node                          |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| node_type                  | String         | Required | The type of the node, either 'condition', 'job' or 'recipe'        |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| job_type_name              | String         | Required | ('job' node) The name of the job type                              |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| job_type_version           | String         | Required | ('job' node) The version of the job type                           |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| job_type_revision          | Integer        | Required | ('job' node) The revision of the job type                          |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| prev_job_type_name         | String         | Optional | ('job' node) The name of the job type in the previous revision, if |
|                            |                |          | changed in the newer revision                                      |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| prev_job_type_version      | String         | Optional | ('job' node) The version of the job type in the previous revision, |
|                            |                |          | if changed in the newer revision                                   |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| prev_job_type_revision     | String         | Optional | ('job' node) The revision of the job type in the previous revision,|
|                            |                |          | if changed in the newer revision                                   |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| recipe_type_name           | String         | Required | ('recipe' node) The name of the recipe type                        |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| recipe_type_revision       | Integer        | Required | ('recipe' node) The revision of the recipe type                    |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| prev_recipe_type_name      | String         | Optional | ('recipe' node) The name of the recipe type in the previous        |
|                            |                |          | revision, if changed in the newer revision                         |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| prev_recipe_type_revision  | String         | Optional | ('recipe' node) The revision of the recipe type in the previous    |
|                            |                |          | revision, if changed in the newer revision                         |
+----------------------------+----------------+----------+--------------------------------------------------------------------+

.. _rest_v6_recipe_type_list:

v6 Recipe Type List
-------------------

**Example GET /v6/recipe-types/ API call**

Request: GET http://.../v6/recipe-types/

Response: 200 OK

 .. code-block:: javascript

    {
      "count": 1,
      "next": null,
      "previous": null,
      "results": [
        {
          "id": 1,
          "name": "my-recipe",
          "title": "My Recipe",
          "description": "A simple recipe type",
          "is_active": true,
          "is_system": false,
          "revision_num": 1,
          "created": "2015-06-15T19:03:26.346Z",
          "deprecated": "2015-07-15T19:03:26.346Z",
          "last_modified": "2015-06-15T19:03:26.346Z"
        }
      ]
    }
    

+-------------------------------------------------------------------------------------------------------------------------+
| **Recipe Type List**                                                                                                    |
+=========================================================================================================================+
| Returns recipe types and basic recipe type information                                                                  |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/recipe-types/                                                                                               |
+-------------------------------------------------------------------------------------------------------------------------+
| **Query Parameters**                                                                                                    |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| page               | Integer           | Optional | The page of the results to return. Defaults to 1.                   |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| page_size          | Integer           | Optional | The size of the page to use for pagination of results.              |
|                    |                   |          | Defaults to 100, and can be anywhere from 1-1000.                   |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| keyword            | String            | Optional | Performs a like search on name, title, description and tags         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| is_active          | Boolean           | Optional | Return only recipe types with one version that matches is_active    |
|                    |                   |          | flag.  Defaults to all recipe types.                                |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| is_system          | Boolean           | Optional | Return only recipe types that are system (True) or user (False).    |
|                    |                   |          | Defaults to all recipe types.                                       |
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
| .id                | Integer           | The unique identifier of the model.                                            |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .name              | String            | The identifying name of recipe job type used for queries.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .title             | String            | The human readable display name of the recipe type.                            |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .description       | String            | An optional description of the recipe type.                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .is_active         | Boolean           | Whether the recipe type is active (false once recipe type is deprecated).      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .is_system         | Boolean           | Whether the recipe type is a built-in system type.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .revision_num      | Integer           | The current revision number of the recipe type, incremented for each edit.     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .created           | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .deprecated        | ISO-8601 Datetime | When the recipe type was deprecated (no longer active; previously archived).   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .last_modified     | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+

.. _rest_v6_recipe_type_create:

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
| name               | String            | Required | The identifying name of recipe type used for queries.               |
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
|                    "workspace_name": "raw"                                                                              |
|                }                                                                                                        |
|            }                                                                                                            |
|        }                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 201 CREATED                                                                                        |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Location**       | URL pointing to the details for the newly created recipe type                                      |
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
|        "is_system": false,                                                                                              |
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
| name               | String            | Required | The identifying name of recipe job type used for queries.           |
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
|                    "workspace_name": "raw"                                                                              |
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

.. _rest_v6_recipe_type_details:

v6 Recipe Type Details
----------------------

**Example GET /v6/recipe-types/{name}/ API call**

Request: GET http://.../v6/recipe-types/{name}/

Response: 200 OK

 .. code-block:: javascript

    {
      "id": 1,
      "name": "my-recipe",
      "title": "My Recipe",
      "description": "A simple recipe type",
      "is_active": true,
      "is_system": false,
      "revision_num": 1,
      "definition": {:ref: `Recipe Definition <rest_v6_recipe_json_definition>`},
      "job_types": [:ref: `Job Type Details <rest_v6_job_type_details>`],
      "sub_recipe_types": [:ref:`Recipe Type Details <rest_v6_recipe_type_details>`],
      "created": "2015-06-15T19:03:26.346Z",
      "deprecated": "2015-07-15T19:03:26.346Z",
      "last_modified": "2015-06-15T19:03:26.346Z"
    }
    
+-------------------------------------------------------------------------------------------------------------------------+
| **Recipe Type Details**                                                                                                 |
+=========================================================================================================================+
| Returns a specific recipe type and all its related model information.                                                   |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/recipe-types/{name}/                                                                                        |
|         Where {name} is the name of the recipe type.                                                                    |
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
| name               | String            | The name of the recipe type.                                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| title              | String            | The human-readable display name of the recipe type.                            |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| description        | String            | An optional description of the recipe type.                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| is_active          | Boolean           | Whether the recipe type is active (false once recipe type is deprecated).      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| is_system          | Boolean           | Whether the recipe type is a built-in system type.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| revision_num       | Integer           | The current revision number of the recipe type, incremented for each edit.     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| definition         | JSON Object       | JSON description defining the interface for running a recipe of this type.     |
|                    |                   | (See :ref:`rest_v6_recipe_json_definition`)                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| job_types          | Array             | List of all job_types that are referenced by this recipe type's definition     |
|                    |                   | (See :ref:`Job Type Details <rest_v6_job_type_details>`)                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| sub_recipe_types   | Array             | List of all recipe_types that are referenced by this recipe type's definition  |
|                    |                   | (See :ref:`Recipe Type Details <rest_v6_recipe_type_details>`)                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| created            | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| deprecated         | ISO-8601 Datetime | When the recipe type was deprecated (no longer active; previously archived).   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| last_modified      | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+

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
|                    "workspace_name": "raw"                                                                              |
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
|        "is_system": false,                                                                                              |
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


.. _rest_v6_recipe_type_revisions:


v6 Recipe Type Revisions
------------------------

**Example GET /v6/recipe-types/{name}/revisions/ API call**

Request: GET http://.../v6/recipe-types/{name}/revisions/

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
            "name": "my-recipe",
            "title": "My Recipe",
            "description": "A simple recipe type",
            "revision_num": 1
          },
          "revision_num": 1,
          "created": "2015-06-15T19:03:26.346Z"
        }
      ]
    }

+-------------------------------------------------------------------------------------------------------------------------+
| **Recipe Type Revisions**                                                                                               |
+=========================================================================================================================+
| Returns the revisions for a recipe type.                                                                                |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/recipe-types/{name}/revisions                                                                               |
|         Where {name} is the name of the recipe type.                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+
| **Query Parameters**                                                                                                    |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| page               | Integer           | Optional | The page of the results to return. Defaults to 1.                   |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| page_size          | Integer           | Optional | The size of the page to use for pagination of results.              |
|                    |                   |          | Defaults to 100, and can be anywhere from 1-1000.                   |
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
| .id                | Integer           | The unique identifier of the model.                                            |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .recipe_type       | String            | The recipe type for this revision.                                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .revision_num      | Integer           | The revision number for this revision.                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .created           | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+


.. _rest_v6_recipe_type_revision_details:

v6 Recipe Type Revision Details
-------------------------------

**Example GET /v6/recipe-types/{name}/revisions/{revision_num}/ API call**

Request: GET http://.../v6/recipe-types/{name}/revisions/{revision_num}

Response: 200 OK

 .. code-block:: javascript

    {
      "id": 1,
      "recipe_type": {
        "id": 1,
        "name": "my-recipe",
        "title": "My Recipe",
        "description": "A simple recipe type",
        "is_active": true,
        "is_system": false,
        "revision_num": 1,
        "created": "2015-06-15T19:03:26.346Z",
        "deprecated": "2015-07-15T19:03:26.346Z",
        "last_modified": "2015-06-15T19:03:26.346Z"
      },
      "revision_num": 1,
      "definition": {<rest_v6_recipe_json_definition>},
      "created": "2015-06-15T19:03:26.346Z"
    }

+-------------------------------------------------------------------------------------------------------------------------+
| **Recipe Type Revision Details**                                                                                        |
+=========================================================================================================================+
| Returns a specific recipe type revision and all its related model information.                                          |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/recipe-types/{name}/{revision_num}/                                                                         |
|         Where {name} is the name of the recipe type and {revision_num} is the revision number.                          |
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
| recipe_type        | String            | The recipe type for this revision. (See :ref:`<rest_v6_recipe_type_list>`)     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| revision_num       | Integer           | The revision number for this revision of the recipe type.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| definition         | JSON Object       | JSON description defining the interface for running a recipe of this type.     |
|                    |                   | (See :ref:`rest_v6_recipe_json_definition`)                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| created            | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
