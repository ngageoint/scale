
.. _rest_v6_node:

v6 Node Services
========================================================================================================================

These services provide access to information about the nodes.

.. _rest_v6_node_list:

v6 Node List
----------------------

**Example GET /v6/nodes/ API call**

Request: GET http://.../v6/nodes/

Response: 200 OK

 .. code-block:: javascript  
 
    { 
        "count": 9, 
        "next": null, 
        "previous": null, 
        "results": [ 
            { 
                "id": 4, 
                "hostname": "host.com", 
                "is_paused": false, 
                "is_active": true, 
                "deprecated": null, 
                "created": "2015-08-28T18:32:33.954Z", 
                "last_modified": "2015-09-04T13:53:46.670Z" 
            }, 
           ... 
        ] 
    } 

+-------------------------------------------------------------------------------------------------------------------------+
| **Node List**                                                                                                           |
+=========================================================================================================================+
| Returns a list of nodes.                                                                                                |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/nodes/                                                                                                      |
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
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_v6_node_details:

v6 Node Details
----------------------

**Example GET /v6/nodes/{id} API call**

Request: GET http://.../v6/nodes/{id}/

Response: 200 OK

 .. code-block:: javascript  
 
   { 
       "id": 4, 
       "hostname": "host.com", 
       "is_paused": false, 
       "is_active": true, 
       "deprecated": null, 
       "created": "2015-06-15T17:18:52.414Z", 
       "last_modified": "2015-06-17T20:05:16.041Z", 
       } 
   } 

+-------------------------------------------------------------------------------------------------------------------------+
| **Node Details**                                                                                                        |
+=========================================================================================================================+
|  Returns a specific node and all its related model information.                                                         |
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

.. _rest_v6_node_update:

v6 Node Update
----------------------

**Example GET /v6/nodes/{id} API call**

Request: PATCH http://.../v6/nodes/{id}/

Response: 200 OK

 .. code-block:: javascript  
 
   { 
       "id": 4, 
       "hostname": "host.com", 
       "is_paused": false, 
       "is_active": true, 
       "deprecated": null, 
       "created": "2015-06-15T17:18:52.414Z", 
       "last_modified": "2015-06-17T20:05:16.041Z", 
       } 
   } 

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
