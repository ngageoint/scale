
.. _rest_v6_system:

v6 System Services
==================

These services provide access to general system information.

.. _rest_v6_system_status:

v6 Get Scheduler Status
-----------------------

**Example GET /v6/status/ API call**

Request: GET http://.../v6/status/

Response: 200 OK

.. code-block:: javascript

    {
       "timestamp": "1970-01-01T00:00:00Z",
       "dependencies":{
          "logs":{
            "OK":true,
            "detail": {
              "msg": "Logs are healthy",
              "logging_address": "tcp://localhost:1234",
              "logging_health_address": "http://www.logging.com/health"
            },
            "errors": [],
            "warnings": []
          },
          "msg_queue": {
            "OK":true,
            "detail":{
              "msg": "Message Queue is healthy"
              "num_message_handlers":0,
              "type":"amqp",
              "queue_name":"scale-command-messages",
              "queue_depth":99,
              "region_name":""
            },
            "errors":[],
            "warnings":[]
          },
          "database":{
             "OK":true,
             "detail": {
               "msg": "Database alive and well"
             },
             "errors":[],
             "warnings":[]
          },
          "elasticsearch":{
               "OK":true,
               "detail":{
                  "url":"http://green.host",
                  "msg":"Elasticsearch is healthy",
                  "info":{
                     "tagline":"You know, for X"
                  }
               },
               "errors":[],
               "warnings":[]
          },
          "nodes":{
             "OK": true,
             "detail": {
                "msg": "Enough nodes are online to function."
             }
             "errors":[ {"NODES_OFFLINE":"No nodes reported."} ],
             "warnings":[]
          },
          "idam":{
             "OK":true,
             "detail": {
               "geoaxis_authorization_url": "https://geoaxis.gxaccess.com/ms_oauth/oauth2/endpoints/oauthservice/authorize",
               "scale_vhost": "scale.io",
               "geoaxis_enabled": true,
               "backends": [
                 "django.contrib.auth.backends.ModelBackend",
                 "django_geoaxis.backends.geoaxis.GeoAxisOAuth2"
               ],
               "msg": "Geoaxis is enabled",
               "geoaxis_host": "geoaxis.gxaccess.com"
             },
             "errors":[],
             "warnings":[]
          },
          "silo":{
            "OK":true,
            "detail":{
              "url":"https://en.wikipedia.org/wiki/Silo",
              "msg":"Silo is alive and connected"
            },
            "errors":[],
            "warnings":[]
          }
        },
       "scheduler": {
          "metrics": {
             "task_updates_per_sec": 0.0,
             "new_offers_per_sec": 0.0,
             "jobs_finished_per_sec": 0.0,
             "jobs_launched_per_sec": 0.0,
             "tasks_launched_per_sec": 0.0,
             "offers_launched_per_sec": 0.0,
             "tasks_finished_per_sec": 0.0
          },
          "hostname": "scheduler-host.com",
          "mesos": {
             "framework_id": "framework-1234",
          }, 
          "state": { 
             "name": "READY", 
             "title": "Ready", 
             "description": "Scheduler is ready to run new jobs." 
          },
          "warnings": {[]
          }
       }, 
       "system": { 
          "database_update": { 
             "is_completed": true, 
             "completed": "1970-01-01T00:00:00Z" 
          }, 
          "services": [ 
             { 
                "name": "messaging", 
                "title": "Messaging", 
                "description": "Processes the backend messaging system", 
                "actual_count": 1, 
                "desired_count": 1 
             } 
          ] 
       },
       "vault": {
         "status": "Secrets Improperly Configured",
         "sealed": false,
         "message": "A secrets backend is not properly configured with Scale."
       },
       "num_offers": 4, 
       "resources": { 
          "mem": { 
             "offered": 91445.0, 
             "total": 177501.0, 
             "running": 1024.0, 
             "free": 72744.0, 
             "unavailable": 12288.0 
          }, 
          "gpus": { 
             "offered": 0.0, 
             "total": 0.0, 
             "running": 0.0, 
             "free": 0.0, 
             "unavailable": 0.0 
          }, 
          "disk": { 
             "offered": 383051.0, 
             "total": 676101.0, 
             "running": 0.0, 
             "free": 289722.0, 
             "unavailable": 3328.0 
          }, 
          "cpus": { 
             "offered": 7.3, 
             "total": 28.0, 
             "running": 1.0, 
             "free": 11.0, 
             "unavailable": 8.7 
          } 
       }, 
       "job_types": [ 
          { 
             "id": 1, 
             "name": "my-job", 
             "version": "1.0", 
             "title": "My Job", 
             "description": "My Job Description", 
             "is_system": false, 
             "icon_code": "f186" 
          } 
       ], 
       "nodes": [ 
          { 
             "id": 1, 
             "hostname": "my-host", 
             "agent_id": "my-agent", 
             "is_active": true, 
             "state": { 
                "name": "READY", 
                "title": "Ready", 
                "description": "Node is ready to run new jobs." 
             }, 
             "errors": [ 
                { 
                   "name": "my-error", 
                   "title": "My Error", 
                   "description": "My Error Description", 
                   "started": "1970-01-01T00:00:00Z", 
                   "last_updated": "1970-01-01T00:00:00Z" 
                } 
             ], 
             "warnings": [ 
                { 
                   "name": "my-warning", 
                   "title": "My Warning", 
                   "description": "My Warning Description", 
                   "started": "1970-01-01T00:00:00Z", 
                   "last_updated": "1970-01-01T00:00:00Z" 
                } 
             ], 
             "node_tasks": [ 
                { 
                   "type": "cleanup", 
                   "title": "Node Cleanup", 
                   "description": "Performs Docker container and volume cleanup on the node", 
                   "count": 1 
                } 
             ], 
             "system_tasks": [ 
                { 
                   "type": "message-handler", 
                   "title": "Message Handler", 
                   "description": "Processes messages from Scale's backend messaging system", 
                   "count": 1 
                } 
             ], 
             "num_offers": 1, 
             "resources": { 
                "mem": { 
                   "offered": 26893.0, 
                   "total": 29965.0, 
                   "running": 0.0, 
                   "free": 0.0, 
                   "unavailable": 3072.0 
                }, 
                "gpus": { 
                   "offered": 0.0, 
                   "total": 0.0, 
                   "running": 0.0, 
                   "free": 0.0, 
                   "unavailable": 0.0 
                }, 
                "disk": { 
                   "offered": 95553.0, 
                   "total": 96577.0, 
                   "running": 0.0, 
                   "free": 0.0, 
                   "unavailable": 1024.0 
                }, 
                "cpus": { 
                   "offered": 1.0, 
                   "total": 4.0, 
                   "running": 0.0, 
                   "free": 0.0, 
                   "unavailable": 3.0 
                } 
             }, 
             "job_executions": { 
                "running": { 
                   "total": 3, 
                   "by_job_type": [ 
                      { 
                         "job_type_id": 1, 
                         "count": 3 
                      } 
                   ] 
                }, 
                "completed": { 
                   "total": 3, 
                   "by_job_type": [ 
                      { 
                         "job_type_id": 1, 
                         "count": 3 
                      } 
                   ] 
                }, 
                "failed": { 
                   "total": 9, 
                   "data": { 
                      "total": 3, 
                      "by_job_type": [ 
                         { 
                            "job_type_id": 1, 
                            "count": 3 
                         } 
                      ] 
                   }, 
                   "algorithm": { 
                      "total": 3, 
                      "by_job_type": [ 
                         { 
                            "job_type_id": 1, 
                            "count": 3 
                         } 
                      ] 
                   }, 
                   "system": { 
                      "total": 3, 
                      "by_job_type": [ 
                         { 
                            "job_type_id": 1, 
                            "count": 3 
                         } 
                      ] 
                   } 
                } 
             } 
          } 
       ] 
    } 

+---------------------------------------------------------------------------------------------------------------------------------+
| **Get Scheduler Status**                                                                                                        |
+=================================================================================================================================+
| Returns the current status of the scheduler, including information about nodes and running jobs.                                |
+---------------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/status/                                                                                                             |
+---------------------------------------------------------------------------------------------------------------------------------+
| **Successful Responses**                                                                                                        |
+----------------------------+----------------------------------------------------------------------------------------------------+
| **Status**                 | 503 SERVICE UNAVAILABLE                                                                            |
+----------------------------+----------------------------------------------------------------------------------------------------+
| The 503 SERVICE UNAVAILABLE response indicates that the Scale scheduler is either currently offline, so there is no status      |
| provide, or the something is causing the scheduler status update to be slow and the status is stale.                            |
+----------------------------+----------------------------------------------------------------------------------------------------+
| **Status**                 | 200 OK                                                                                             |
+----------------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**           | *application/json*                                                                                 |
+----------------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                                 |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| timestamp                  | ISO-8601 Datetime | When the status information was generated                                      |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| dependencies               | JSON Object       | Status of Scale's dependencies                                                 |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| dependencies.logs          | JSON Object       | Status of the logging service used by Scale                                    |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| dependencies.msg_queue     | JSON Object       | Status of Scale's message queue                                                |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| dependencies.database      | JSON Object       | Status of Scale's database                                                     |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| dependencies.elasticsearch | JSON Object       | Status of configured elasticsearch service                                     |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| dependencies.nodes         | JSON Object       | Status of nodes in Scale. Warns if too many are offline/degraded               |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| dependencies.idam          | JSON Object       | Status of IdAM service (GEOAxIS)                                               |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| dependencies.silo          | JSON Object       | Status of Silo service used for discovering and importing Seed images          |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| scheduler                  | JSON Object       | Scheduler configuration and metrics information                                |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| scheduler.metrics          | JSON Object       | Contains various near real-time metrics related to scheudling tasks and jobs   |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| scheduler.mesos            | JSON Object       | Contains Scale's framework ID and hostname and port of the Mesos master        |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| scheduler.state            | JSON Object       | The current scheduler state, with a title and description                      |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| scheduler.warnings         | Array             | List of scheduler warning objects, with a title, description, and when the     |
|                            |                   | warning began and was last updated                                             |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| system                     | JSON Object       | System information                                                             |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| system.database_update     | JSON Object       | Information on if and when the current Scale database update completed         |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| system.services            | Array             | List of services, with name, title, description, and task counts               |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| vault                      | JSON Object       | Secrets Vault information                                                      |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| vault.status               | String            | The status of the secrets vault                                                |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| vault.sealed               | Boolean           | Whether the secrets vault is currently sealed                                  |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| vault.message              | String            | Description of error reading the secrets vault, if any                         |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| num_offers                 | Integer           | Number of resource offers currently held by Scale                              |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| resources                  | JSON Object       | Describes the resource totals across all of Scale's nodes. Each resource name  |
|                            |                   | is a key and its corresponding object breaks down the resource into several    |
|                            |                   | categories: *running* resources are used by current Scale tasks, *offered*     |
|                            |                   | resources are currently offered to Scale, *free* resources are available on    |
|                            |                   | the node and may be offered to Scale soon, *unavailable* resources are used by |
|                            |                   | other tasks and cannot be used by Scale, and *total* resources are the total   |
|                            |                   | amounts for the node.                                                          |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| job_types                  | Array             | List of job type objects, with a few basic fields                              |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| nodes                      | Array             | List of node objects, with a few basic fields including the current node state |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| nodes.state                | JSON Object       | The current node state, with a title and description                           |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| nodes.errors               | Array             | List of node error objects, with a title, description, and when the error      |
|                            |                   | began and was last updated                                                     |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| nodes.warnings             | Array             | List of node warning objects, with a title, description, and when the warning  |
|                            |                   | began and was last updated                                                     |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| nodes.node_tasks           | Array             | List of node tasks running on the node, with a type, title, description, and   |
|                            |                   | count                                                                          |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| nodes.system_tasks         | Array             | List of system tasks running on the node, with a type, title, description, and |
|                            |                   | count                                                                          |
+----------------------------+-------------------+--------------------------------------------------------------------------------+
| nodes.job_executions       | JSON Object       | The job executions related to this node. The *running* field describes the     |
|                            |                   | jobs currently running on the node, with a total count and count per job type. |
|                            |                   | The *completed* field describes job executions that have completed on the node |
|                            |                   | in the last 3 hours, with a total count and count per job type. The *failed*   |
|                            |                   | field is similar to *completed*, just with failed executions grouped by error  |
|                            |                   | category.                                                                      |
+----------------------------+-------------------+--------------------------------------------------------------------------------+


.. _rest_v6_system_version:

v6 Get System Version
---------------------

**Example GET /v6/version/ API call**

Request: GET http://.../v6/version/

Response: 200 OK

.. code-block:: javascript

   { 
       "version": "6.0.0" 
   }

+-------------------------------------------------------------------------------------------------------------------------------+
| **Get System Version**                                                                                                        |
+===============================================================================================================================+
| Returns version and build information.                                                                                        |
+--------------------------+-------------------+--------------------------------------------------------------------------------+
| **GET** /v6/version/                                                                                                          |
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
