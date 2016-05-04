
.. _rest_node:

Node Services
========================================================================================================================

These services provide access to information about the nodes.

.. _rest_node_list:

+-------------------------------------------------------------------------------------------------------------------------+
| **Node List**                                                                                                           |
+=========================================================================================================================+
| Returns a list of all nodes.                                                                                            |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /nodes/                                                                                                         |
+-------------------------------------------------------------------------------------------------------------------------+
| **Query Parameters**                                                                                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
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
|                    |                   |          | Duplicate it to multi-sort, (ex: order=host_name&order=created).    |
|                    |                   |          | Prefix fields with a dash to reverse the sort, (ex: order=-created).|
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| include_inactive   | Boolean           | Optional | If true, all nodes in the database are returned including those     |
|                    |                   |          | marked inactive. These are typically removed from the cluster.      |
|                    |                   |          | The default is False.                                               |
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
|                    |                   | (See :ref:`Node Details <rest_node_details>`)                                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .hostname          | String            | The full domain-qualified hostname of the node.                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .port              | Integer           | The port being used by the executor on this node.                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .slave_id          | String            | The slave ID used by Mesos for the node.                                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .pause_reason      | String            | The reason this node is paused if is_paused is true. This is a descriptive     |
|                    |                   | field for presentation to the user.                                            |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .is_paused         | Boolean           | True if the node is paused and will not accept new jobs for execution.         |
|                    |                   | Remaining tasks for a previously executing job will complete.                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .is_paused_errors  |                   | True if the node was automatically paused due to a high error rate.            |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .is_active         | Boolean           | True if the node is actively participating in the cluster.                     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .archived          | ISO-8601 Datetime | (Optional) When the node was removed (is_active == False) from the cluster.    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .created           | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .last_offer        | ISO-8601 Datetime | When the node last received an offer from Mesos.                               |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .last_modified     | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "count": 9,                                                                                                      |
|        "next": null,                                                                                                    |
|        "previous": null,                                                                                                |
|        "results": [                                                                                                     |
|            {                                                                                                            |
|                "id": 4,                                                                                                 |
|                "hostname": "host.com",                                                                                  |
|                "port": 5051,                                                                                            |
|                "slave_id": "20150828-143216-659603848-5050-13473-S9",                                                   |
|                "is_paused": false,                                                                                      |
|                "is_paused_errors": false,                                                                               |
|                "is_active": true,                                                                                       |
|                "archived": null,                                                                                        |
|                "created": "2015-08-28T18:32:33.954Z",                                                                   |
|                "last_offer": null,                                                                                      |
|                "last_modified": "2015-09-04T13:53:46.670Z"                                                              |
|            },                                                                                                           |
|           ...                                                                                                           |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_node_details:

+-------------------------------------------------------------------------------------------------------------------------+
| **Node Details**                                                                                                        |
+=========================================================================================================================+
|  Returns a specific job and all its related model information including resource usage.                                 |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /nodes/{id}/                                                                                                    |
|         Where {id} is the unique identifier of an existing model.                                                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| id                 | Integer           | The unique identifier of the model. Can be passed to the details API call.     |
|                    |                   | (See :ref:`Node Details <rest_node_details>`)                                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| hostname           | String            | The full domain-qualified hostname of the node.                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| port               | Integer           | The port being used by the executor on this node.                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| slave_id           | String            | The slave ID used by Mesos for the node.                                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| pause_reason       | String            | The reason this node is paused if is_paused is true. This is a descriptive     |
|                    |                   | field for presentation to the user.                                            |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| is_paused          | Boolean           | True if the node is paused and will not accept new jobs for execution.         |
|                    |                   | Remaining tasks for a previously executing job will complete.                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .is_paused_errors  |                   | True if the node was automatically paused due to a high error rate.            |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| is_active          | Boolean           | True if the node is actively participating in the cluster.                     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| archived           | ISO-8601 Datetime | (Optional) When the node was removed (is_active == False) from the cluster.    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| created            | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| last_offer         | ISO-8601 Datetime | When the node last received an offer from Mesos.                               |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| last_modified      | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| resources          | JSON Object       | (Optional) Information about the hardware resources of the node                |
|                    |                   | NOTE: Resource information may not always be available                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .total             | JSON Object       | The total hardware resources for the node                                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..cpus             | Float             | The total number of CPUs at this node                                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..mem              | Float             | The total amount of RAM in MiB at this node                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..disk             | Float             | The total amount of disk space in MiB at this node                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .scheduled         | JSON Object       | The scheduled hardware resources for the node                                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..cpus             | Float             | The scheduled number of CPUs at this node                                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..mem              | Float             | The scheduled amount of RAM in MiB at this node                                |
+--------------------------+-------------+--------------------------------------------------------------------------------+
| ..disk             | Float             | The scheduled amount of disk space in MiB at this node                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .used              | JSON Object       | The used hardware resources for all nodes in the cluster                       |
|                    |                   | NOTE: Real-time resource usage is not currently available and will be all zero |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..cpus             | Float             | The used number of CPUs at this node                                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..mem              | Float             | The used amount of RAM in MiB at this node                                     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..disk             | Float             | The used amount of disk space in MiB at this node                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| disconnected       | Boolean           | (Optional) If present and true, there is an active Node entry in the scale     |     
|                    |                   | database but mesos does not have a corresponding active slave.                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .job_exes_running  | Array             | A list of job executions currently running on the node.                        |
|                    |                   | (See :ref:`Job Execution Details <rest_job_execution_details>`)                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|   {                                                                                                                     |
|       "id": 4,                                                                                                          |
|       "hostname": "host.com",                                                                                           |
|       "port": 5051,                                                                                                     |
|       "slave_id": "20150616-103057-1800454536-5050-6193-S2",                                                            | 
|       "is_paused": false,                                                                                               |
|       "is_paused_errors": false,                                                                                        |
|       "is_active": true,                                                                                                |
|       "archived": null,                                                                                                 |
|       "created": "2015-06-15T17:18:52.414Z",                                                                            |
|       "last_offer": null,                                                                                               |
|       "last_modified": "2015-06-17T20:05:16.041Z",                                                                      |
|       "job_exes_running": [                                                                                             |
|           {                                                                                                             |
|               "id": 1,                                                                                                  |
|               "status": "RUNNING",                                                                                      |
|               "command_arguments": "",                                                                                  |
|               "timeout": 0,                                                                                             |
|               "pre_started": null,                                                                                      |
|               "pre_completed": null,                                                                                    |
|               "pre_exit_code": null,                                                                                    |
|               "job_started": "2015-08-28T18:32:34.295Z",                                                                |
|               "job_completed": null,                                                                                    |
|               "job_exit_code": null,                                                                                    |
|               "post_started": null,                                                                                     |
|               "post_completed": null,                                                                                   |
|               "post_exit_code": null,                                                                                   |
|               "created": "2015-08-28T18:32:33.862Z",                                                                    |
|               "queued": "2015-08-28T18:32:33.833Z",                                                                     |
|               "started": "2015-08-28T18:32:34.040Z",                                                                    |
|               "ended": null,                                                                                            |
|               "last_modified": "2015-08-28T18:32:34.389Z",                                                              |
|               "job": {                                                                                                  |
|                   "id": 1,                                                                                              |
|                   "job_type": {                                                                                         |
|                       "id": 3,                                                                                          |
|                       "name": "scale-clock",                                                                            |
|                       "version": "1.0",                                                                                 |
|                       "title": "Scale Clock",                                                                           |
|                       "description": "Performs Scale system functions that need to be executed periodically",           | 
|                       "category": "system",                                                                             |
|                       "author_name": null,                                                                              |
|                       "author_url": null,                                                                               |
|                       "is_system": true,                                                                                |
|                       "is_long_running": true,                                                                          |
|                       "is_active": true,                                                                                |
|                       "is_operational": true,                                                                           |
|                       "is_paused": false,                                                                               |
|                       "icon_code": "f013"                                                                               |
|                   },                                                                                                    |
|                   "job_type_rev": {                                                                                     |
|                       "id": 5,                                                                                          |
|                   },                                                                                                    |
|                   "event": {                                                                                            |
|                       "id": 1                                                                                           |
|                   },                                                                                                    |
|                   "error": null,                                                                                        |
|                   "status": "RUNNING",                                                                                  |
|                   "priority": 1,                                                                                        |
|                   "num_exes": 19                                                                                        |
|               },                                                                                                        |
|               "node": {                                                                                                 |
|                   "id": 7                                                                                               |
|               },                                                                                                        |
|               "error": null,                                                                                            |
|               "cpus_scheduled": 1.0,                                                                                    |
|               "mem_scheduled": 1024.0,                                                                                  |
|               "disk_in_scheduled": 0.0,                                                                                 |
|               "disk_out_scheduled": 0.0,                                                                                |
|               "disk_total_scheduled": 0.0                                                                               |
|           }                                                                                                             |
|       ],                                                                                                                |
|       "resources": {                                                                                                    | 
|           "total": {                                                                                                    | 
|               "cpus": 16.0,                                                                                             |
|               "mem": 63305.0,                                                                                           | 
|               "disk": 131485.0                                                                                          |
|           },                                                                                                            |
|           "scheduled": {                                                                                                | 
|               "cpus": 12.0,                                                                                             |
|               "mem": 35392.0,                                                                                           | 
|               "disk": 131408.0                                                                                          |
|           },                                                                                                            |
|           "used": {                                                                                                     | 
|               "cpus": 16.0,                                                                                             |
|               "mem": 63305.0,                                                                                           | 
|               "disk": 131485.0                                                                                          |
|           }                                                                                                             |
|       }                                                                                                                 |
|   }                                                                                                                     |
+-------------------------------------------------------------------------------------------------------------------------+
| **Error Responses**                                                                                                     |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 404 NOT FOUND                                                                                      |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *text/plain*                                                                                       |
+--------------------+----------------------------------------------------------------------------------------------------+
| The specified slave_id does not exist in the database.                                                                  |
+--------------------+----------------------------------------------------------------------------------------------------+

+-------------------------------------------------------------------------------------------------------------------------+
| **Replace Node**                                                                                                        |
+=========================================================================================================================+
| Replaces node data with specified data                                                                                  |
+-------------------------------------------------------------------------------------------------------------------------+
| **PUT** /nodes/{id}/                                                                                                    |
|         Where {id} is the unique identifier of an existing model.                                                       |
|         All fields are required and additional fields are not tolerated.                                                |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| hostname           | String            | The full domain-qualified hostname of the node.                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| port               | Integer           | The port being used by the executor on this node.                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| pause_reason       | String            | The reason this node is paused if is_paused is true. If is_paused is false     |
|                    |                   | this field will be set to null. This should provide a brief description        |
|                    |                   | for user display.                                                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| is_paused          | Boolean           | True if the node is paused and will not accept new jobs for execution.         |
|                    |                   | Remaining tasks for a previously executing job will complete.                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 201 CREATED                                                                                        |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Location**       | URL pointing to the details for the node (should be the same as the request URL)                   |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| Response format is identical to GET but contains the updated data.                                                      |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| hostname           | String            | The full domain-qualified hostname of the node.                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| port               | Integer           | The port being used by the executor on this node.                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| slave_id           | String            | The slave ID used by Mesos for the node.                                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| pause_reason       | String            | The reason this node is paused if is_paused is true. This is a descriptive     |
|                    |                   | field for presentation to the user.                                            |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| is_paused          | Boolean           | True if the node is paused and will not accept new jobs for execution.         |
|                    |                   | Remaining tasks for a previously executing job will complete.                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .is_paused_errors  |                   | True if the node was automatically paused due to a high error rate.            |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| created            | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| last_modified      | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| **Error Responses**                                                                                                     |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 400 BAD REQUEST                                                                                    |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *text/plain*                                                                                       |
+--------------------+----------------------------------------------------------------------------------------------------+
| Bad update fields were specified, either unexpected fields or there were missing fields. An error message lists them.   |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 404 NOT FOUND                                                                                      |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *text/plain*                                                                                       |
+--------------------+----------------------------------------------------------------------------------------------------+
| The specified slave_id does not exist in the database.                                                                  |
+--------------------+----------------------------------------------------------------------------------------------------+

+-------------------------------------------------------------------------------------------------------------------------+
| **Update Node**                                                                                                         |
+=========================================================================================================================+
| Update one or more fields in an existing node.                                                                          |
+-------------------------------------------------------------------------------------------------------------------------+
| **PATCH** /nodes/{id}/                                                                                                  |
|           Where {id} is the unique identifier of an existing model.                                                     |
|           All fields are optional and additional fields are not tolerated.                                              |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| hostname           | String            | (Optional) The full domain-qualified hostname of the node.                     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| port               | Integer           | (Optional) The port being used by the executor on this node.                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| pause_reason       | String            | (Optional) The reason this node is paused if is_paused is true. If is_paused   |
|                    |                   | is false, this field will be set to null. This should provide a brief          |
|                    |                   | description for user display.                                                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| is_paused          | Boolean           | (Optional) True if the node is paused and will not accept new jobs             |
|                    |                   | for execution. Remaining tasks for a previously executing job will complete.   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 201 CREATED                                                                                        |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Location**       | URL pointing to the details for the node (should be the same as the request URL).                  |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| Response format is identical to GET but contains the updated data.                                                      |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| hostname           | String            | The full domain-qualified hostname of the node.                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| port               | Integer           | The port being used by the executor on this node.                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| slave_id           | String            | The slave ID used by Mesos for the node.                                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| is_paused          | Boolean           | True if the node is paused and will not accept new jobs for execution.         |
|                    |                   | Remaining tasks for a previously executing job will complete.                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .is_paused_errors  |                   | True if the node was automatically paused due to a high error rate.            |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| created            | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| last_modified      | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| **Error Responses**                                                                                                     |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 400 BAD REQUEST                                                                                    |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *text/plain*                                                                                       |
+--------------------+----------------------------------------------------------------------------------------------------+
| Unexpected fields were specified. An error message lists them. Or no fields were specified.                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 404 NOT FOUND                                                                                      |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *text/plain*                                                                                       |
+--------------------+----------------------------------------------------------------------------------------------------+
| The specified slave_id does not exist in the database.                                                                  |
+--------------------+----------------------------------------------------------------------------------------------------+

+-------------------------------------------------------------------------------------------------------------------------+
| **Nodes Status**                                                                                                        |
+=========================================================================================================================+
| Returns a list of overall node statistics, based on counts of job executions organized by status.                       |
| This only returns data for nodes marked as active in the database. For status information on nodes which are no         |
| longer in the cluseter (is_active is false), request node details for that specific node ID.                            |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /nodes/status/                                                                                                  |
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
| **Successful Response**                                                                                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
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
| .node              | JSON Object       | The node that is associated with the statistics.                               |
|                    |                   | (See :ref:`Node Details <rest_node_details>`)                                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .is_online         | Boolean           | (Optional) Whether or not the node is running and available.                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .job_exe_counts    | Array             | A list of recent job execution counts for the node, grouped by status.         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..status           | String            | The type of job execution status the count represents.                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..count            | Integer           | The number of job executions for the status attempted by the node.             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..most_recent      | ISO-8601 Datetime | The date/time when the node last ran a job execution with the status.          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..category         | String            | The category of the status, which is only used by a FAILED status.             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .job_exes_running  | Array             | A list of job executions currently running on the node.                        |
|                    |                   | (See :ref:`Job Execution Details <rest_job_execution_details>`)                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|   "count": 2,                                                                                                           | 
|   "next": null,                                                                                                         |
|   "previous": null,                                                                                                     |
|   "results": [                                                                                                          |
|        {                                                                                                                |
|            "node": {                                                                                                    |
|                "id": 2                                                                                                  |
|                "hostname": "host1.com",                                                                                 |
|                "port": 5051,                                                                                            |
|                "slave_id": "20150821-144617-659603848-5050-22035-S2",                                                   |
|                "is_paused": false,                                                                                      |
|                "is_paused_errors": false,                                                                               |
|                "is_active": true,                                                                                       |
|                "archived": null,                                                                                        |
|                "created": "2015-07-08T17:49:21.771Z",                                                                   |
|                "last_modified": "2015-07-08T17:49:21.771Z",                                                             |
|            },                                                                                                           |
|            "is_online": true,                                                                                           |
|            "job_exe_counts": [                                                                                          |
|                {                                                                                                        |
|                    "status": "RUNNING",                                                                                 |
|                    "count": 1,                                                                                          |
|                    "most_recent": "2015-08-31T22:09:12.674Z",                                                           |
|                    "category": null                                                                                     |
|                },                                                                                                       |
|                {                                                                                                        |
|                    "status": "FAILED",                                                                                  |
|                    "count": 2,                                                                                          |
|                    "most_recent": "2015-08-31T19:28:30.799Z",                                                           |
|                    "category": "SYSTEM"                                                                                 |
|                },                                                                                                       |
|                {                                                                                                        |
|                    "status": "COMPLETED",                                                                               |
|                    "count": 57,                                                                                         |
|                    "most_recent": "2015-08-31T21:51:40.900Z",                                                           |
|                    "category": null                                                                                     |
|                }                                                                                                        |
|            ],                                                                                                           |
|            "job_exes_running": [                                                                                        |
|                {                                                                                                        |
|                   "id": 1,                                                                                              |
|                   "status": "RUNNING",                                                                                  |
|                   "command_arguments": "",                                                                              |
|                   "timeout": 0,                                                                                         |
|                   "pre_started": null,                                                                                  |
|                   "pre_completed": null,                                                                                |
|                   "pre_exit_code": null,                                                                                |
|                   "job_started": "2015-08-28T18:32:34.295Z",                                                            |
|                   "job_completed": null,                                                                                |
|                   "job_exit_code": null,                                                                                |
|                   "post_started": null,                                                                                 |
|                   "post_completed": null,                                                                               |
|                   "post_exit_code": null,                                                                               |
|                   "created": "2015-08-28T18:32:33.862Z",                                                                |
|                   "queued": "2015-08-28T18:32:33.833Z",                                                                 |
|                   "started": "2015-08-28T18:32:34.040Z",                                                                |
|                   "ended": null,                                                                                        |
|                   "last_modified": "2015-08-28T18:32:34.389Z",                                                          |
|                   "job": {                                                                                              |
|                       "id": 1,                                                                                          |
|                       "job_type": {                                                                                     |
|                           "id": 3,                                                                                      |
|                           "name": "scale-clock",                                                                        |
|                           "version": "1.0",                                                                             |
|                           "title": "Scale Clock",                                                                       |
|                           "description": "Performs Scale system functions that need to be executed periodically",       | 
|                           "category": "system",                                                                         |
|                           "author_name": null,                                                                          |
|                           "author_url": null,                                                                           |
|                           "is_system": true,                                                                            |
|                           "is_long_running": true,                                                                      |
|                           "is_active": true,                                                                            |
|                           "is_operational": true,                                                                       |
|                           "is_paused": false,                                                                           |
|                           "icon_code": "f013"                                                                           |
|                       },                                                                                                |
|                       "job_type_rev": {                                                                                 |
|                           "id": 5,                                                                                      |
|                       },                                                                                                |
|                       "event": {                                                                                        |
|                           "id": 1                                                                                       |
|                       },                                                                                                |
|                       "error": null,                                                                                    |
|                       "status": "RUNNING",                                                                              |
|                       "priority": 1,                                                                                    |
|                       "num_exes": 19                                                                                    |
|                   },                                                                                                    |
|                   "node": {                                                                                             |
|                       "id": 7                                                                                           |
|                   },                                                                                                    |
|                   "error": null,                                                                                        |
|                   "cpus_scheduled": 1.0,                                                                                |
|                   "mem_scheduled": 1024.0,                                                                              |
|                   "disk_in_scheduled": 0.0,                                                                             |
|                   "disk_out_scheduled": 0.0,                                                                            |
|                   "disk_total_scheduled": 0.0                                                                           |
|                }                                                                                                        |
|            ]                                                                                                            |
|        },                                                                                                               |
|        {                                                                                                                |
|            "node": {                                                                                                    |
|                "id": 1                                                                                                  |
|                "hostname": "host2.com",                                                                                 |
|                "port": 5051,                                                                                            |
|                "slave_id": "20150821-144617-659603848-5050-22035-S1",                                                   |
|                "is_paused": false,                                                                                      |
|                "is_paused_errors": false,                                                                               |
|                "is_active": true,                                                                                       |
|                "archived": null,                                                                                        |
|                "created": "2015-07-08T17:49:21.771Z",                                                                   |
|                "last_modified": "2015-07-08T17:49:21.771Z"                                                              |
|            },                                                                                                           |
|            "is_online": false,                                                                                          |
|            "job_exe_counts": [],                                                                                        |
|            "job_exes_running": []                                                                                       |
|        },                                                                                                               |
|        ...                                                                                                              |
|    ]                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+
