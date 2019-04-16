
.. _rest_v6_deprecated:

v6 Removals
======================

All v5 REST API endpoints were removed in Scale v6. Attempting to use v5 with Scale v6 will result in a 404 Error page.

The following APIs were removed from Scale v6:

Import/export REST API
--------------------------------------------
The import/export REST API endpoints were deprecated in Scale v5 and completely removed in Scale v6. This endpoint will now return a 500 Server Error if used. There is no Scale v6 replacement for the import/export REST APIs.

Job REST API
----------------------------------
Specific endpoints under the job and job-type REST API were removed in Scale v6.

- v5/job-types/{id}
    Scale v6 no longer supports retrieving job details through the /job-types/{id} endpoint. Users should use the new Scale v6 /job-types/{name} endpoint instead. See :ref:`_rest_v6_job_type_versions` for more details.

- v5/jobs/executions
    Scale v6 no longer supports retrieving job execution details through the /jobs/executions endpoint. The /jobs/{id}/executions endpoint should be used instead. See :ref:`_rest_v6_job_execution_list` for more details.

- v5/jobs/updates
    Scale v6 no longer supports the /jobs/updates endpoint. Using this endpoint will return a 500 Server Error.

queue REST API
------------------------------------
Specific endpoints under the queue API were deprecated in Scale v5 and completely removed in Scale v6. These endpoints will now return a 500 Server error if used.

- v5/queue/new-job
    The v5/queue/new-job REST endpoint was moved to the v6/jobs/ API. Jobs are now queued by posting to the v6/jobs/ endpoint. See :ref:`rest_v6_job_queue_new_job` for more details.

- v5/queue/new-recipe/
    The v5/queue/new-recipe REST endpoint was moved to the v6/recipes/ API. Recipes are now queued by posting to the v6/recipes/ endpoint. See :ref:`rest_v6_recipe_queue_new_recipe` for more details.

- v5/queue/requeue-jobs/
    The v5/queue/requeue-jobs REST endpoint was moved to the v6/jobs/requeue/ API. Failed/Canceled jobs are now requeued by posting to the v6/job/requeue/ endpoint. See :ref:`_rest_v6_job_requeue` for more details.

products REST API
---------------------------------------
The products REST API endpoint was deprecated in Scale v5 and completely removed in Scale v6. Attempting to use these endpoints will result in a 404 error. The v6 files API should be used to retrieve product details. See :ref:`_rest_v6_scale_file`

recipe REST API
--------------------------------------
Specific endpoints under the recipe API were deprecated in Scale v5 and completely removed in Scale v6. These endpoints will now return a 500 Server Error if used.

- v5/recipe-types/{id}
    Recipe types are no longer accessed via their ids through the Scale v6 API. Recipe type names are used instead. See :ref:`rest_v6_recipe_details` for more details.

source REST API
------------------------------------
The source REST API endpoint was deprecated in Scale v5 and completely removed in Scale v6. Attempting to use these endpoints will result in a 500 Server Error. The v6/files API should be used to retrieve source file details. See :ref:`_rest_v6_scale_file`


v6 Deprecated Messages
======================
The following command messages were removed/replaced in Scale v6:

Recipes
-----------------------------------------------

- reprocess_recipes Message
    This message was deprecated in Scale v5 and removed in Scale v6. The create_recipes message should be used instead.

- update_recipes Message
    This message was deprecated in Scale v5 and removed in Scale v6. The update_recipe message should be used instead.
