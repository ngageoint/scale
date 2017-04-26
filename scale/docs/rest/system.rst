
.. _rest_system:

System Services
===============

These services provide access to general system information.

.. _rest_system_status:

+-------------------------------------------------------------------------------------------------------------------------------+
| **Get Scheduler Status**                                                                                                      |
+===============================================================================================================================+
| Returns the current status of the scheduler, including information about nodes and running jobs.                              |
+-------------------------------------------------------------------------------------------------------------------------------+
| **GET** /status/                                                                                                              |
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
| nodes.job_executions     | JSON Object       | The job executions related to this node. The *running* field describes the     |
|                          |                   | jobs currently running on the node, with a total count, count per job type,    |
|                          |                   | and job IDs per job type. The *completed* field describes job executions that  |
|                          |                   | have completed on the node in the last 3 hours, with a total count, count per  |
|                          |                   | job type, and job IDs per job type. The *failed* field is similar to           |
|                          |                   | *completed*, just with failed executions grouped by error category.            |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                                    |
|                                                                                                                               |
|   {                                                                                                                           |
|      "timestamp": "1970-01-01T00:00:00Z",                                                                                     |
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
|            "job_executions": {                                                                                                |
|               "running": {                                                                                                    |
|                  "total": 3,                                                                                                  |
|                  "by_job_type": [                                                                                             |
|                     {                                                                                                         |
|                        "job_type_id": 1,                                                                                      |
|                        "count": 3,                                                                                            |
|                        "job_ids": [123, 124, 125]                                                                             |
|                     }                                                                                                         |
|                  ]                                                                                                            |
|               },                                                                                                              |
|               "completed": {                                                                                                  |
|                  "total": 3,                                                                                                  |
|                  "by_job_type": [                                                                                             |
|                     {                                                                                                         |
|                        "job_type_id": 1,                                                                                      |
|                        "count": 3,                                                                                            |
|                        "job_ids": [123, 124, 125]                                                                             |
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
|                           "count": 3,                                                                                         |
|                           "job_ids": [123, 124, 125]                                                                          |
|                        }                                                                                                      |
|                     ]                                                                                                         |
|                  },                                                                                                           |
|                  "algorithm": {                                                                                               |
|                     "total": 3,                                                                                               |
|                     "by_job_type": [                                                                                          |
|                        {                                                                                                      |
|                           "job_type_id": 1,                                                                                   |
|                           "count": 3,                                                                                         |
|                           "job_ids": [123, 124, 125]                                                                          |
|                        }                                                                                                      |
|                     ]                                                                                                         |
|                  },                                                                                                           |
|                  "system": {                                                                                                  |
|                     "total": 3,                                                                                               |
|                     "by_job_type": [                                                                                          |
|                        {                                                                                                      |
|                           "job_type_id": 1,                                                                                   |
|                           "count": 3,                                                                                         |
|                           "job_ids": [123, 124, 125]                                                                          |
|                        }                                                                                                      |
|                     ]                                                                                                         |
|                  }                                                                                                            |
|               }                                                                                                               |
|            }                                                                                                                  |
|         }                                                                                                                     |
|      ]                                                                                                                        |
|   }                                                                                                                           |
+-------------------------------------------------------------------------------------------------------------------------------+

.. _rest_system_status_v4:

+-------------------------------------------------------------------------------------------------------------------------------+
| **Get System Status (v4)**                                                                                                    |
+===============================================================================================================================+
| Returns overall master, scheduler, and cluster information, including hardware resources.                                     |
+-------------------------------------------------------------------------------------------------------------------------------+
| **DEPRECATED**                                                                                                                |
|                This table describes the current v4 version of the system status API, which is now deprecated.                 |
|                Please use the new v5 version of this API.                                                                     |
+-------------------------------------------------------------------------------------------------------------------------------+
| **GET** /status/                                                                                                              |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| **Successful Response**                                                                                                       |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| **Status**               | 200 OK                                                                                             |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| **Content Type**         | *application/json*                                                                                 |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                               |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| master                   | JSON Object       | Overall status information for the master host                                 |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| master.hostname          | String            | The network name of the master host                                            |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| master.port              | Integer           | The network port of the master host                                            |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| master.is_online         | Boolean           | Indicates whether or not the master host is running and available              |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| scheduler                | JSON Object       | Overall status information for the scheduler framework                         |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| scheduler.hostname       | String            | The network name of the scheduler host                                         |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| scheduler.is_online      | Boolean           | Indicates whether or not the scheduler host is running and available           |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| scheduler.is_paused      | Boolean           | Indicates whether or not the scheduler framework is currently paused           |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| queue_depth              | Integer           | The number of tasks currently scheduled on the queue                           |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| resources                | JSON Object       | (Optional) Information about the overall hardware resources of the cluster     |
|                          |                   | NOTE: Resource information may not always be available                         |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| resources.total          | JSON Object       | The total hardware resources for all nodes in the cluster                      |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| resources.total.cpus     | Float             | The total number of CPUs for all nodes in the cluster                          |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| resources.total.mem      | Float             | The total amount of RAM in MiB for all nodes in the cluster                    |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| resources.total.disk     | Float             | The total amount of disk space in MiB for all nodes in the cluster             |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| resources.scheduled      | JSON Object       | The scheduled hardware resources for all nodes in the cluster                  |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| resources.scheduled.cpus | Float             | The scheduled number of CPUs for all nodes in the cluster                      |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| resources.scheduled.mem  | Float             | The scheduled amount of RAM in MiB for all nodes in the cluster                |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| resources.scheduled.disk | Float             | The scheduled amount of disk space in MiB for all nodes in the cluster         |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| resources.used           | JSON Object       | The used hardware resources for all nodes in the cluster                       |
|                          |                   | NOTE: Real-time resource usage is not currently available and will be all zero |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| resources.used.cpus      | Float             | The used number of CPUs for all nodes in the cluster                           |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| resources.used.mem       | Float             | The used amount of RAM in MiB for all nodes in the cluster                     |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| resources.used.disk      | Float             | The used amount of disk space in MiB for all nodes in the cluster              |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                                    |
|                                                                                                                               |
|   {                                                                                                                           |
|       "master": {                                                                                                             |
|           "is_online": true,                                                                                                  |
|           "hostname": "localhost",                                                                                            |
|           "port": 5050                                                                                                        |
|       },                                                                                                                      |
|       "scheduler": {                                                                                                          |
|           "is_online": true,                                                                                                  |
|           "is_paused": false,                                                                                                 |
|           "hostname": "localhost"                                                                                             |
|       },                                                                                                                      |
|       "queue_depth": 1234,                                                                                                    |
|       "resources": {                                                                                                          |
|           "total": {                                                                                                          |
|               "cpus": 16.0,                                                                                                   |
|               "mem": 63305.0,                                                                                                 |
|               "disk": 131485.0                                                                                                |
|           },                                                                                                                  |
|           "scheduled": {                                                                                                      |
|               "cpus": 12.0,                                                                                                   |
|               "mem": 35392.0,                                                                                                 |
|               "disk": 131408.0                                                                                                |
|           },                                                                                                                  |
|           "used": {                                                                                                           |
|               "cpus": 16.0,                                                                                                   |
|               "mem": 63305.0,                                                                                                 |
|               "disk": 131485.0                                                                                                |
|           }                                                                                                                   |
|       }                                                                                                                       |
|   }                                                                                                                           |
+-------------------------------------------------------------------------------------------------------------------------------+

.. _rest_system_version:

+-------------------------------------------------------------------------------------------------------------------------------+
| **Get System Version**                                                                                                        |
+===============================================================================================================================+
| Returns version and build information.                                                                                        |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| **GET** /version/                                                                                                             |
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
|       "version": "3.0.0"                                                                                                      |
|   }                                                                                                                           |
+-------------------------------------------------------------------------------------------------------------------------------+
