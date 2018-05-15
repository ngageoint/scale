
.. _rest_v6_scheduler:

v6 Scheduler Services
==================

These services provide access to information about the scheduler.
There should be one and only one scheduler entry in the database and it is used to store global data like paused status.

.. _rest_scheduler_details:

v6 Get Scheduler
----------------------

**Example GET /v6/scheduler/ API call**

Request: GET http://.../v6/scheduler/

Response: 200 OK

 .. code-block:: javascript 
  
   { 
       "is_paused": False, 
       "num_message_handlers": 2, 
       "system_logging_level": 'INFO' 
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
| system_logging_level | String            | The logging level for all scale system components                            |
+----------------------+-------------------+------------------------------------------------------------------------------+


.. _rest_scheduler_update:

v6 Update Scheduler
----------------------

**Example PATCH /v6/scheduler/ API call**

Request: PATCH http://.../v6/scheduler/

Response: 200 OK

 .. code-block:: javascript 
  
   { 
       "is_paused": False, 
       "num_message_handlers": 2, 
       "system_logging_level": 'INFO' 
   }

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
+--------------------------+---------------+------------------------------------------------------------------------------+
| is_paused                | Boolean       | (Optional) True if the scheduler should be paused, false to resume           |
+--------------------------+---------------+------------------------------------------------------------------------------+
| num_message_handlers     | Integer       | (Optional) The number of message handlers to have scheduled                  |
+--------------------------+---------------+------------------------------------------------------------------------------+
| system_logging_level     | String        | (Optional) The logging level sent to all scale system components.            |
|                          |               | Acceptable levels are DEBUG, INFO, WARNING, ERROR and CRITICAL.              |
|                          |               | Anything else will default to INFO                                           |
+--------------------------+---------------+------------------------------------------------------------------------------+
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
| system_logging_level | String            | The logging level for all scale system components                            |
+----------------------+-------------------+------------------------------------------------------------------------------+

