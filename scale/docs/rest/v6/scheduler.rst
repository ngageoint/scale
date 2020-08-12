
.. _rest_v6_scheduler:

v6 Scheduler Services
=====================

These services provide access to information about the scheduler.

.. _rest_v6_scheduler_details:

v6 Get Scheduler
----------------

**Example GET /v6/scheduler/ API call**

Request: GET http://.../v6/scheduler/

Response: 200 OK

 .. code-block:: javascript 
  
   { 
       "is_paused": False, 
       "num_message_handlers": 2, 
       "system_logging_level": 'INFO',
       "queue_mode": 'FIFO'
   }

+-------------------------------------------------------------------------------------------------------------------------+
| **Get Scheduler**                                                                                                       |
+=========================================================================================================================+
| Returns data for the scheduler                                                                                          |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/scheduler/                                                                                                  |
+-------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+----------------------+-------------------+------------------------------------------------------------------------------+
| is_paused            | Boolean           | True if the scheduler is paused. This functions like individually pausing    |
|                      |                   | all nodes but maintains separated state so toggling this back to unpaused    |
|                      |                   | results in the previous individual node pause state.                         |
+----------------------+-------------------+------------------------------------------------------------------------------+
| num_message_handlers | Integer           | The number of message handlers to have scheduled                             |
+----------------------+-------------------+------------------------------------------------------------------------------+
| queue_mode           | String            | The mode the queue operates in (LIFO or FIFO); the default mode is FIFO.     |
+----------------------+-------------------+------------------------------------------------------------------------------+
| system_logging_level | String            | The logging level for all scale system components                            |
+----------------------+-------------------+------------------------------------------------------------------------------+


.. _rest_v6_scheduler_update:

v6 Update Scheduler
-------------------

**Example PATCH /v6/scheduler/ API call**

Request: PATCH http://.../v6/scheduler/

Response: 204 No content

+-------------------------------------------------------------------------------------------------------------------------+
| **Update Scheduler**                                                                                                    |
+=========================================================================================================================+
| Update one or more fields for the scheduler.                                                                            |
+-------------------------------------------------------------------------------------------------------------------------+
| **PATCH** /v6/scheduler/                                                                                                |
|           All fields are optional and additional fields are not tolerated.                                              |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+----------------------+-------------------+------------------------------------------------------------------------------+
| is_paused            | Boolean           | (Optional) True if the scheduler should be paused, false to resume           |
+----------------------+-------------------+------------------------------------------------------------------------------+
| num_message_handlers | Integer           | (Optional) The number of message handlers to have scheduled                  |
+----------------------+-------------------+------------------------------------------------------------------------------+
| queue_mode           | String            | (Optional) The mode the queue should operate in: last in first out vs first  |
|                      |                   | in last out. Valid values are LIFO or FIFO.                                  |
+----------------------+-------------------+------------------------------------------------------------------------------+
| system_logging_level | String            | (Optional) The logging level sent to all scale system components.            |
|                      |                   | Acceptable levels are DEBUG, INFO, WARNING, ERROR and CRITICAL.              |
|                      |                   | Anything else will default to INFO                                           |
+----------------------+-------------------+------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 204 No content                                                                                     |
+--------------------+----------------------------------------------------------------------------------------------------+


.. _rest_v6_scheduler_details:

v6 Get Queued Resources
----------------

**Example GET /v6/scheduler/queued-resources/ API call**

Request: GET http://.../v6/scheduler/queued-resources/

Response: 200 OK

 .. code-block:: javascript 

   {
        "cluster_resources": {
            'cpus': 252.0,
            'disk': 25120.0,
            'gpus': 0.0,
            'mem': 25120.0
        },
        "queue_lengths": {
            'PENDING': 0,
            'QUEUED': 3,
            'RUNNING': 0
        },
        "total_resources": {
            'PENDING': {},
            'QUEUED': {'cpus': 3.0, 'mem': 384.0},
            'RUNNING': {}
        }
    }

+-------------------------------------------------------------------------------------------------------------------------+
| **Get Queued Resources**                                                                                                |
+=========================================================================================================================+
| Returns resource information about all pending, queued, and running jobs.                                               |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/scheduler/queued-resources/                                                                                 |
+-------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+----------------------+-------------------+------------------------------------------------------------------------------+
| cluster_resources    | Dictionary        | The total available resources for the entire cluster.                        |
+----------------------+-------------------+------------------------------------------------------------------------------+
| queue_lengths        | Dictionary        | The number of current pending, queued, and running jobs                      |
+----------------------+-------------------+------------------------------------------------------------------------------+
| total_resources      | Dictionary        | The amount of total resources the pending, queued, and running jobs are      |
|                      |                   | using.                                                                       |
+----------------------+-------------------+------------------------------------------------------------------------------+
