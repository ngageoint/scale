
.. _rest_v6_recipe:

v6 Recipe Services
==================

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
| node_type                  | String         | Required | The type of the node, either 'job' or 'recipe'                     |
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
----------------

**Example POST /v6/recipe/ API call**

+-------------------------------------------------------------------------------------------------------------------------+
| **Queue New Recipe**                                                                                                    |
+=========================================================================================================================+
| Creates a new recipe and places it onto the queue                                                                       |
+-------------------------------------------------------------------------------------------------------------------------+
| **DEPRECATED**                                                                                                          |
|                This documentation describes the API **v5** version of the Queue New Recipe endpoint response.  Starting |
|                with API **v6** the *inputs* section will be removed, the *data* section will be renamed to *input*,     |
|                and the *recipe_type* section will only contain *id*, *name*, *version*, *title*, and *description*.     |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /v6/recipe/                                                                                             |
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