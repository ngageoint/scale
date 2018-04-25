
.. _rest_system:

v6 System Services
===============

These services provide access to general system information.

.. _rest_v6_system_status:

+-------------------------------------------------------------------------------------------------------------------------------+
| **Get Scheduler Status**                                                                                                      |
+===============================================================================================================================+
| Returns the current status of the scheduler, including information about nodes and running jobs.                              |
+-------------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/status/                                                                                                              |
+-------------------------------------------------------------------------------------------------------------------------------+
| **Successful Responses**                                                                                                      |
+--------------------------+----------------------------------------------------------------------------------------------------+
| **Status**               | 204 NO CONTENT                                                                                     |
+--------------------------+----------------------------------------------------------------------------------------------------+
| The 204 NO CONTENT response indicates that the Scale scheduler is currently offline, so there is no status content to         |
| provide.                                                                                                                      |
+--------------------------+----------------------------------------------------------------------------------------------------+
| **Status**               | 200 OK                                                                                             |
+--------------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**         | *application/json*                                                                                 |
+--------------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                               |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| timestamp                | ISO-8601 Datetime | When the status information was generated                                      |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| scheduler                | JSON Object       | Scheduler configuration and metrics information                                |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| scheduler.metrics        | JSON Object       | Contains various near real-time metrics related to scheudling tasks and jobs   |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| scheduler.hostname       | String            | The name of the host where the scheduler is running                            |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| scheduler.mesos          | JSON Object       | Contains Scale's framework ID and hostname and port of the Mesos master        |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| scheduler.state          | JSON Object       | The current scheduler state, with a title and description                      |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| system                   | JSON Object       | System information                                                             |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| system.database_update   | JSON Object       | Information on if and when the current Scale database update completed         |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| system.services          | Array             | List of services, with name, title, description, and task counts               |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| num_offers               | Integer           | Number of resource offers currently held by Scale                              |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| resources                | JSON Object       | Describes the resource totals across all of Scale's nodes. Each resource name  |
|                          |                   | is a key and its corresponding object breaks down the resource into several    |
|                          |                   | categories: *running* resources are used by current Scale tasks, *offered*     |
|                          |                   | resources are currently offered to Scale, *free* resources are available on    |
|                          |                   | the node and may be offered to Scale soon, *unavailable* resources are used by |
|                          |                   | other tasks and cannot be used by Scale, and *total* resources are the total   |
|                          |                   | amounts for the node.                                                          |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| job_types                | Array             | List of job type objects, with a few basic fields                              |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| nodes                    | Array             | List of node objects, with a few basic fields including the current node state |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| nodes.state              | JSON Object       | The current node state, with a title and description                           |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| nodes.errors             | Array             | List of node error objects, with a title, description, and when the error      |
|                          |                   | began and was last updated                                                     |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| nodes.warnings           | Array             | List of node warning objects, with a title, description, and when the warning  |
|                          |                   | began and was last updated                                                     |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| nodes.node_tasks         | Array             | List of node tasks running on the node, with a type, title, description, and   |
|                          |                   | count                                                                          |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| nodes.system_tasks       | Array             | List of system tasks running on the node, with a type, title, description, and |
|                          |                   | count                                                                          |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| nodes.job_executions     | JSON Object       | The job executions related to this node. The *running* field describes the     |
|                          |                   | jobs currently running on the node, with a total count and count per job type. |
|                          |                   | The *completed* field describes job executions that have completed on the node |
|                          |                   | in the last 3 hours, with a total count and count per job type. The *failed*   |
|                          |                   | field is similar to *completed*, just with failed executions grouped by error  |
|                          |                   | category.                                                                      |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                                    |
|                                                                                                                               |
|   {                                                                                                                           |
|      "timestamp": "1970-01-01T00:00:00Z",                                                                                     |
|      "scheduler": {                                                                                                           |
|         "metrics": {                                                                                                          |
|            "task_updates_per_sec": 0.0,                                                                                       |
|            "new_offers_per_sec": 0.0,                                                                                         |
|            "jobs_finished_per_sec": 0.0,                                                                                      |
|            "jobs_launched_per_sec": 0.0,                                                                                      |
|            "tasks_launched_per_sec": 0.0,                                                                                     |
|            "offers_launched_per_sec": 0.0,                                                                                    |
|            "tasks_finished_per_sec": 0.0                                                                                      |
|         },                                                                                                                    |
|         "hostname": "scheduler-host.com",                                                                                     |
|         "mesos": {                                                                                                            |
|            "framework_id": "framework-1234",                                                                                  |
|            "master_hostname": "192.168.1.1",                                                                                  |
|            "master_port": 5050                                                                                                |
|         },                                                                                                                    |
|         "state": {                                                                                                            |
|            "name": "READY",                                                                                                   |
|            "title": "Ready",                                                                                                  |
|            "description": "Scheduler is ready to run new jobs."                                                               |
|         }                                                                                                                     |
|      },                                                                                                                       |
|      "system": {                                                                                                              |
|         "database_update": {                                                                                                  |
|            "is_completed": true,                                                                                              |
|            "completed": "1970-01-01T00:00:00Z"                                                                                |
|         },                                                                                                                    |
|         "services": [                                                                                                         |
|            {                                                                                                                  |
|               "name": "messaging",                                                                                            |
|               "title": "Messaging",                                                                                           |
|               "description": "Processes the backend messaging system",                                                        |
|               "actual_count": 1,                                                                                              |
|               "desired_count": 1                                                                                              |
|            }                                                                                                                  |
|         ]                                                                                                                     |
|      },                                                                                                                       |
|      "num_offers": 4,                                                                                                         |
|      "resources": {                                                                                                           |
|         "mem": {                                                                                                              |
|            "offered": 91445.0,                                                                                                |
|            "total": 177501.0,                                                                                                 |
|            "running": 1024.0,                                                                                                 |
|            "free": 72744.0,                                                                                                   |
|            "unavailable": 12288.0                                                                                             |
|         },                                                                                                                    |
|         "gpus": {                                                                                                             |
|            "offered": 0.0,                                                                                                    |
|            "total": 0.0,                                                                                                      |
|            "running": 0.0,                                                                                                    |
|            "free": 0.0,                                                                                                       |
|            "unavailable": 0.0                                                                                                 |
|         },                                                                                                                    |
|         "disk": {                                                                                                             |
|            "offered": 383051.0,                                                                                               |
|            "total": 676101.0,                                                                                                 |
|            "running": 0.0,                                                                                                    |
|            "free": 289722.0,                                                                                                  |
|            "unavailable": 3328.0                                                                                              |
|         },                                                                                                                    |
|         "cpus": {                                                                                                             |
|            "offered": 7.3,                                                                                                    |
|            "total": 28.0,                                                                                                     |
|            "running": 1.0,                                                                                                    |
|            "free": 11.0,                                                                                                      |
|            "unavailable": 8.7                                                                                                 |
|         }                                                                                                                     |
|      },                                                                                                                       |
|      "job_types": [                                                                                                           |
|         {                                                                                                                     |
|            "id": 1,                                                                                                           |
|            "name": "my-job",                                                                                                  |
|            "version": "1.0",                                                                                                  |
|            "title": "My Job",                                                                                                 |
|            "description": "My Job Description",                                                                               |
|            "is_system": false,                                                                                                |
|            "icon_code": "f186"                                                                                                |
|         }                                                                                                                     |
|      ],                                                                                                                       |
|      "nodes": [                                                                                                               |
|         {                                                                                                                     |
|            "id": 1,                                                                                                           |
|            "hostname": "my-host",                                                                                             |
|            "agent_id": "my-agent",                                                                                            |
|            "is_active": true,                                                                                                 |
|            "state": {                                                                                                         |
|               "name": "READY",                                                                                                |
|               "title": "Ready",                                                                                               |
|               "description": "Node is ready to run new jobs."                                                                 |
|            },                                                                                                                 |
|            "errors": [                                                                                                        |
|               {                                                                                                               |
|                  "name": "my-error",                                                                                          |
|                  "title": "My Error",                                                                                         |
|                  "description": "My Error Description",                                                                       |
|                  "started": "1970-01-01T00:00:00Z",                                                                           |
|                  "last_updated": "1970-01-01T00:00:00Z"                                                                       |
|               }                                                                                                               |
|            ],                                                                                                                 |
|            "warnings": [                                                                                                      |
|               {                                                                                                               |
|                  "name": "my-warning",                                                                                        |
|                  "title": "My Warning",                                                                                       |
|                  "description": "My Warning Description",                                                                     |
|                  "started": "1970-01-01T00:00:00Z",                                                                           |
|                  "last_updated": "1970-01-01T00:00:00Z"                                                                       |
|               }                                                                                                               |
|            ],                                                                                                                 |
|            "node_tasks": [                                                                                                    |
|               {                                                                                                               |
|                  "type": "cleanup",                                                                                           |
|                  "title": "Node Cleanup",                                                                                     |
|                  "description": "Performs Docker container and volume cleanup on the node",                                   |
|                  "count": 1                                                                                                   |
|               }                                                                                                               |
|            ],                                                                                                                 |
|            "system_tasks": [                                                                                                  |
|               {                                                                                                               |
|                  "type": "message-handler",                                                                                   |
|                  "title": "Message Handler",                                                                                  |
|                  "description": "Processes messages from Scale's backend messaging system",                                   |
|                  "count": 1                                                                                                   |
|               }                                                                                                               |
|            ],                                                                                                                 |
|            "num_offers": 1,                                                                                                   |
|            "resources": {                                                                                                     |
|               "mem": {                                                                                                        |
|                  "offered": 26893.0,                                                                                          |
|                  "total": 29965.0,                                                                                            |
|                  "running": 0.0,                                                                                              |
|                  "free": 0.0,                                                                                                 |
|                  "unavailable": 3072.0                                                                                        |
|               },                                                                                                              |
|               "gpus": {                                                                                                       |
|                  "offered": 0.0,                                                                                              |
|                  "total": 0.0,                                                                                                |
|                  "running": 0.0,                                                                                              |
|                  "free": 0.0,                                                                                                 |
|                  "unavailable": 0.0                                                                                           |
|               },                                                                                                              |
|               "disk": {                                                                                                       |
|                  "offered": 95553.0,                                                                                          |
|                  "total": 96577.0,                                                                                            |
|                  "running": 0.0,                                                                                              |
|                  "free": 0.0,                                                                                                 |
|                  "unavailable": 1024.0                                                                                        |
|               },                                                                                                              |
|               "cpus": {                                                                                                       |
|                  "offered": 1.0,                                                                                              |
|                  "total": 4.0,                                                                                                |
|                  "running": 0.0,                                                                                              |
|                  "free": 0.0,                                                                                                 |
|                  "unavailable": 3.0                                                                                           |
|               }                                                                                                               |
|            },                                                                                                                 |
|            "job_executions": {                                                                                                |
|               "running": {                                                                                                    |
|                  "total": 3,                                                                                                  |
|                  "by_job_type": [                                                                                             |
|                     {                                                                                                         |
|                        "job_type_id": 1,                                                                                      |
|                        "count": 3                                                                                             |
|                     }                                                                                                         |
|                  ]                                                                                                            |
|               },                                                                                                              |
|               "completed": {                                                                                                  |
|                  "total": 3,                                                                                                  |
|                  "by_job_type": [                                                                                             |
|                     {                                                                                                         |
|                        "job_type_id": 1,                                                                                      |
|                        "count": 3                                                                                             |
|                     }                                                                                                         |
|                  ]                                                                                                            |
|               },                                                                                                              |
|               "failed": {                                                                                                     |
|                  "total": 9,                                                                                                  |
|                  "data": {                                                                                                    |
|                     "total": 3,                                                                                               |
|                     "by_job_type": [                                                                                          |
|                        {                                                                                                      |
|                           "job_type_id": 1,                                                                                   |
|                           "count": 3                                                                                          |
|                        }                                                                                                      |
|                     ]                                                                                                         |
|                  },                                                                                                           |
|                  "algorithm": {                                                                                               |
|                     "total": 3,                                                                                               |
|                     "by_job_type": [                                                                                          |
|                        {                                                                                                      |
|                           "job_type_id": 1,                                                                                   |
|                           "count": 3                                                                                          |
|                        }                                                                                                      |
|                     ]                                                                                                         |
|                  },                                                                                                           |
|                  "system": {                                                                                                  |
|                     "total": 3,                                                                                               |
|                     "by_job_type": [                                                                                          |
|                        {                                                                                                      |
|                           "job_type_id": 1,                                                                                   |
|                           "count": 3                                                                                          |
|                        }                                                                                                      |
|                     ]                                                                                                         |
|                  }                                                                                                            |
|               }                                                                                                               |
|            }                                                                                                                  |
|         }                                                                                                                     |
|      ]                                                                                                                        |
|   }                                                                                                                           |
+-------------------------------------------------------------------------------------------------------------------------------+


.. _rest_v6_system_version:

+-------------------------------------------------------------------------------------------------------------------------------+
| **Get System Version**                                                                                                        |
+===============================================================================================================================+
| Returns version and build information.                                                                                        |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| **GET** /v6/version/                                                                                                             |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| **Successful Response**                                                                                                       |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| **Status**               | 200 OK                                                                                             |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| **Content Type**         | *application/json*                                                                                 |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                               |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| version                  | String            | The full version identifier of Scale.                                          |
|                          |                   | The format follows the Semantic scheme: http://semver.org/                     |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                                    |
|                                                                                                                               |
|   {                                                                                                                           |
|       "version": "6.0.0"                                                                                                      |
|   }                                                                                                                           |
+-------------------------------------------------------------------------------------------------------------------------------+
