
.. _rest_v6_recipe:

v6 Recipe Services
==================

These services allow for the creation and management of recipes. A recipe type is a user-defined workflow that allows
jobs and recipes to be connected together in order to pass output from jobs to the input of other jobs.

.. _rest_v6_recipe_definition:

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
