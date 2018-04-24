
.. _rest_v6_recipe:

v6 Recipe Services
==================

These services allow for the creation and management of recipes. A recipe type is a user-defined workflow of jobs that
allows jobs to be connected together in order to pass output from jobs to the input of other jobs.

.. _rest_v6_recipe_json_diff:

Recipe Graph Diff JSON
----------------------

A recipe graph diff JSON describes the differences between two recipe graphs (two revisions). The differences explain
which recipe jobs will be reprocessed when a newer recipe type revision is run.

**Example recipe graph diff:**

.. code-block:: javascript

   {
      "can_be_reprocessed": true,
      "reasons": [],
      "jobs": [{
         "name": "job_a",
         "will_be_reprocessed": false,
         "force_reprocess": false,
         "status": "UNCHANGED",
         "changes": [],
         "job_type": {
            "name": "job-type-1",
            "version": "1.0"
         },
         "dependencies": []
      }, {
         "name": "job_b",
         "will_be_reprocessed": true,
         "force_reprocess": false,
         "status": "CHANGED",
         "changes": [{"name": "JOB_TYPE_VERSION_CHANGE", "description": "Job type version changed from 1.0 to 2.0"}],
         "job_type": {
            "name": "job-type-2",
            "version": "2.0",
            "prev_version": "1.0"
         },
         "dependencies": [{"name": "job_a"}]
      }, {
         "name": "job_c",
         "will_be_reprocessed": true,
         "force_reprocess": false,
         "status": "NEW",
         "changes": [],
         "job_type": {
            "name": "job-type-3",
            "version": "0.1"
         },
         "dependencies": [{"name": "job_b"}]
      }]
   }

+-----------------------------------------------------------------------------------------------------------------------------+
| **Recipe Graph Diff**                                                                                                       |
+=========================+===================+==========+====================================================================+
| can_be_reprocessed      | Boolean           | Required | Indicates whether recipes from the previous revision can be        |
|                         |                   |          | reprocessed as the newer revision.                                 |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| reasons                 | Array             | Required | Lists any reasons causing *can_be_reprocessed* to be false. The    |
|                         |                   |          | reasons are JSON objects with *name* and *description* string      |
|                         |                   |          | fields.                                                            |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| jobs                    | Array             | Required | Lists all of the jobs in the two recipe type revisions             |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| name                    | String            | Required | The name of the recipe job                                         |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| will_be_reprocessed     | Boolean           | Required | Indicates whether this job will be superseded by a new created job |
|                         |                   |          | if the recipe is reprocessed                                       |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| force_reprocess         | Boolean           | Required | Indicates whether the user has requested that this job be          |
|                         |                   |          | reprocessed regardless of whether it has changed                   |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| status                  | String            | Required | The status indicating the job differences between the two          |
|                         |                   |          | revisions. The possible statuses are:                              |
|                         |                   |          |                                                                    |
|                         |                   |          | - *DELETED* - the job existed in the previous revision and has been|
|                         |                   |          |               removed in the newer revision                        |
|                         |                   |          | - *UNCHANGED* - the job did not change between the revisions       |
|                         |                   |          | - *CHANGED* - the job changed between the revisions, see the       |
|                         |                   |          |               *changes* list for more details                      |
|                         |                   |          | - *NEW* - the job did not exist in the previous revision and was   |
|                         |                   |          |           added in the newer revision                              |
|                         |                   |          |                                                                    |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| changes                 | Array             | Required | If *status* is *NEW*, lists the job's changes between the two      |
|                         |                   |          | revisions. Each change is a JSON object with *name* and            |
|                         |                   |          | *description* string fields.                                       |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| job_type                | JSON object       | Required | The job type of the recipe job                                     |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| name                    | String            | Required | The name of the job type                                           |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| version                 | String            | Required | The version of the job type                                        |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| prev_name               | String            | Optional | If the job type name changed between revisions, *prev_name* is the |
|                         |                   |          | name from the previous revision while *name* is the name for the   |
|                         |                   |          | newer revision.                                                    |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| prev_version            | String            | Optional | If the job type version changed between revisions, *prev_version*  |
|                         |                   |          | is the version from the previous revision while *version* is the   |
|                         |                   |          | version for the newer revision.                                    |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| dependencies            | Array             | Required | The list of job dependencies for this recipe job. Each JSON object |
|                         |                   |          | in the list has a single string field called *name* giving the job |
|                         |                   |          | name of the dependency.                                            |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
