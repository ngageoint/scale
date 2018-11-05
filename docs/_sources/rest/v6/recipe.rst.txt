
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
