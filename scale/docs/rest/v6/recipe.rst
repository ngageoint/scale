
.. _rest_v6_recipe:

v6 Recipe Services
==================

These services allow for the creation and management of recipes. A recipe type is a user-defined workflow that allows
jobs and recipes to be connected together in order to pass output from jobs to the input of other jobs.

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
            "name": "node_a",
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
            "name": "node_b",
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
            "name": "node_c",
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
| name                       | String         | Required | The name of the recipe node                                        |
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
