
.. _rest_v6_batch:

v6 Batch Services
=================

These services allow for the creation and management of batches. A batch is a user-created collection of recipes of a
single recipe type. Batches can be used for running recipes over a given data set or for performing iterative test runs
for algorithm development and validation.

.. _rest_v6_batch_json_definition:

Batch Definition JSON
=====================

A batch definition JSON defines what a batch is going to run. Currently the v6 batch definition only supports running a
batch that re-processes the same set of recipes that ran in a previous batch.

**Example batch definition:**

.. code-block:: javascript

   {
      "previous_batch": {
         "batch_id": 1234,
         "job_names": ['job_a', 'job_b'],
         "all_jobs": false
      }
   }

+-----------------------------------------------------------------------------------------------------------------------------+
| **Batch Definition**                                                                                                        |
+=============================================+==========+====================================================================+
| previous_batch          | JSON object       | Optional | Indicates that the batch should re-process the recipes from a      |
|                         |                   |          | previous batch. This will link the previous and new batch together |
|                         |                   |          | so that their metrics can be easily compared.                      |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| batch_id                | Integer           | Required | The ID of the previous batch                                       |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| job_names               | String            | Optional | A list of strings that define specific jobs within the recipes     |
|                         |                   |          | that will be re-processed. Any job that has changed between the    |
|                         |                   |          | previously run recipe revision and the current revision will       |
|                         |                   |          | automatically be included in the batch, however this parameter can |
|                         |                   |          | be used to include additional jobs that did not have a revision    |
|                         |                   |          | change. If a job is selected to be re-processed, all of its        |
|                         |                   |          | dependent jobs will automatically be re-processed as well.         |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| all_jobs                | Boolean           | Optional | If true, then *job_names* is ignored and ALL jobs within the batch |
|                         |                   |          | recipes will be re-processed.                                      |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
