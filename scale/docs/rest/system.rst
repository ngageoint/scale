
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
| scheduler                | JSON Object       | Scheduler configuration and metrics information                                |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| scheduler.metrics        | JSON Object       | Contains various near real-time metrics related to scheudling tasks and jobs   |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| scheduler.hostname       | String            | The name of the host where the scheduler is running                            |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| scheduler.mesos          | JSON Object       | Contains Scale's framework ID and hostname and port of the Mesos master        |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| num_offers               | Integer           | Number of resource offers currently held by Scale                              |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| resources                | JSON Object       | Describes the resource totals across all of Scale's nodes. Each resource name  |
|                          |                   | is a key and its corresponding object breaks down the resource into several    |
|                          |                   | categories: *running* resources are used by current Scale tasks, *offered*     |
|                          |                   | resources are currently offered to Scale, *free* resources are available on    |
|                          |                   | the node and may be offered to Scale soon, *unavailable* resources are used by |
|                          |                   | other tasks and cnnot be used by Scale, and *total* resources are the total    |
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
|         "hostname": "scheduler-host.domain.com",                                                                              |
|         "mesos": {                                                                                                            |
|            "framework_id": "1234",                                                                                            |
|            "master_hostname": "192.168.1.1",                                                                                  |
|            "master_port": 5050                                                                                                |
|         }                                                                                                                     |
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
