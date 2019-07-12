
.. _rest_v6_queue:

v6 Queue Services
==================

.. _rest_v6_queue_load:

v6 Queue Load
-------------

**Example GET /v6/load/ API call**

Request: GET http://.../v6/load

Response: 200 OK

.. code-block:: javascript

    {
      "count": 1,
      "next": null,
      "previous": null,
      "results": [{
          "time": "2015-10-21T00:00:00Z",
          "pending_count": 1,
          "queued_count": 0,
          "running_count": 0
        }
      ]
    }

+-------------------------------------------------------------------------------------------------------------------------+
| **Job Load**                                                                                                            |
+=========================================================================================================================+
| Returns statistics about the current job load organized by job type. Jobs are counted when they are in the PENDING,     |
| QUEUED, and RUNNING states. NOTE: Time range must be within a one month period (31 days).                               |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/load/                                                                                                       |
+-------------------------------------------------------------------------------------------------------------------------+
| **Query Parameters**                                                                                                    |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| started            | ISO-8601 Datetime | Required | The start of the time range to query.                               |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
|                    |                   |          | Defaults to the past 1 week.                                        |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| ended              | ISO-8601 Datetime | Required | End of the time range to query, defaults to the current time.       |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_id        | Integer           | Optional | Count only jobs with a given job type identifier.                   |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_name      | String            | Optional | Count only jobs with a given job type name.                         |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_category  | String            | Optional | Count only jobs with a given job type category.                     |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_priority  | Integer           | Optional | Count only jobs with a given job type priority.                     |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
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
| .time              | ISO-8601 Datetime | When the counts were actually recorded.                                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .pending_count     | Integer           | The number of jobs in the pending state at the measured time.                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .queued_count      | Integer           | The number of jobs in the queued state at the measured time.                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .running_count     | Integer           | The number of jobs in the running state at the measured time.                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+

.. _rest_v6_queue_status:

v6 Queue Status
---------------

**Example GET /v6/queue/status/ API call**

Request: GET http://.../v6/queue/status/

Response: 200 OK

.. code-block:: javascript                                                                                              
                                                                                                                         
 {
   "count": 1,
   "next": null,
   "previous": null,
   "results": [{
       "job_type": {
         "id": 1,
         "name": "scale-ingest",
         "version": "1.0",
         "title": "Scale Ingest",
         "description": "Ingests a source file into a workspace",
         "is_active": true,
         "is_paused": false,
         "is_published": true,
         "icon_code": "f013",
         "unmet_resources": "chocolate,vanilla"
       },
       "count": 19,
       "longest_queued": "1970-01-01T00:00:00.000Z",
       "highest_priority": 1
     }
   ]
 } 
        
+-------------------------------------------------------------------------------------------------------------------------+
| **Get Queue Status**                                                                                                    |
+=========================================================================================================================+
| Returns the current status of the queue by grouping the queued jobs by their types.                                     |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/queue/status/                                                                                               |
+-------------------------------------------------------------------------------------------------------------------------+
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
| .job_type          | JSON Object       | The job type being summarized within the queue.                                |
|                    |                   | (See :ref:`Job Type Details <rest_v6_job_type_details>`)                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .count             | Integer           | The total number of jobs of the type in the queue.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .longest_queued    | ISO-8601 Datetime | When the job that has been queued the longest of the type was queued.          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .highest_priority  | Integer           | The highest priority of any job of the type in the queue.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+

v6 Queue New-Job
----------------------

see v6 job :ref:`Queue New Job <rest_v6_job_queue_new_job>`

v6 Queue New-Recipe
----------------------

see v6 Recipe :ref:`Queue New Recipe <rest_v6_recipe_queue_new_recipe>`
