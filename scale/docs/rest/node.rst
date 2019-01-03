
.. _rest_node:

Node Services
========================================================================================================================

These services provide access to information about the nodes.

.. _rest_node_list:

+-------------------------------------------------------------------------------------------------------------------------+
| **Node List**                                                                                                           |
+=========================================================================================================================+
| Returns a list of nodes.                                                                                                |
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
| .pause_reason      | String            | The reason this node is paused if is_paused is true. This is a descriptive     |
|                    |                   | field for presentation to the user.                                            |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .is_paused         | Boolean           | True if the node is paused and will not accept new jobs for execution.         |
|                    |                   | Remaining tasks for a previously executing job will complete.                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .is_active         | Boolean           | True if the node is actively participating in the cluster.                     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .deprecated        | ISO-8601 Datetime | When the node was removed (is_active == False) from the cluster.               |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .created           | ISO-8601 Datetime | When the associated database model was initially created.                      |
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
|                "is_paused": false,                                                                                      |
|                "is_active": true,                                                                                       |
|                "deprecated": null,                                                                                      |
|                "created": "2015-08-28T18:32:33.954Z",                                                                   |
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
| pause_reason       | String            | The reason this node is paused if is_paused is true. This is a descriptive     |
|                    |                   | field for presentation to the user.                                            |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| is_paused          | Boolean           | True if the node is paused and will not accept new jobs for execution.         |
|                    |                   | Remaining tasks for a previously executing job will complete.                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| is_active          | Boolean           | True if the node is actively participating in the cluster.                     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| deprecated         | ISO-8601 Datetime | When the node was removed (is_active == False) from the cluster.               |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| created            | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| last_modified      | ISO-8601 Datetime | When the associated database model was last saved.                             |
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
+--------------------+-------------------+--------------------------------------------------------------------------------+
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
|                    |                   | (*DEPRECATED*, gone in v5)                                                     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|   {                                                                                                                     |
|       "id": 4,                                                                                                          |
|       "hostname": "host.com",                                                                                           |
|       "is_paused": false,                                                                                               |
|       "is_paused_errors": false,                                                                                        |
|       "is_active": true,                                                                                                |
|       "deprecated": null,                                                                                               |
|       "created": "2015-06-15T17:18:52.414Z",                                                                            |
|       "last_modified": "2015-06-17T20:05:16.041Z",                                                                      |
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

.. _rest_node_update:

+-------------------------------------------------------------------------------------------------------------------------+
| **Update Node**                                                                                                         |
+=========================================================================================================================+
| Update one or more fields in an existing node.                                                                          |
+-------------------------------------------------------------------------------------------------------------------------+
| **PATCH** /nodes/{id}/                                                                                                  |
|           Where {id} is the unique identifier of an existing model.                                                     |
|           All fields are optional and additional fields are not accepted.                                               |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| pause_reason       | String            | (Optional) The reason this node is paused if is_paused is true. If is_paused   |
|                    |                   | is false, this field will be set to null. This should provide a brief          |
|                    |                   | description for user display.                                                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| is_paused          | Boolean           | (Optional) True if the node is paused and will not accept new jobs             |
|                    |                   | for execution. Remaining tasks for a previously executing job will complete.   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| is_active          | Boolean           | (Optional) True if the node is active and Scale should use it for scheduling   |
|                    |                   | jobs.                                                                          |
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
| pause_reason       | String            | The reason this node is paused if is_paused is true. This is a descriptive     |
|                    |                   | field for presentation to the user.                                            |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| is_paused          | Boolean           | True if the node is paused and will not accept new jobs for execution.         |
|                    |                   | Remaining tasks for a previously executing job will complete.                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| is_active          | Boolean           | True if the node is actively participating in the cluster.                     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| deprecated         | ISO-8601 Datetime | When the node was removed (is_active == False) from the cluster.               |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| created            | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| last_modified      | ISO-8601 Datetime | When the associated database model was last saved.                             |
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
+--------------------+-------------------+--------------------------------------------------------------------------------+
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
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|   {                                                                                                                     |
|       "id": 4,                                                                                                          |
|       "hostname": "host.com",                                                                                           |
|       "is_paused": false,                                                                                               |
|       "is_paused_errors": false,                                                                                        |
|       "is_active": true,                                                                                                |
|       "created": "2015-06-15T17:18:52.414Z",                                                                            |
|       "last_modified": "2015-06-17T20:05:16.041Z",                                                                      |
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
