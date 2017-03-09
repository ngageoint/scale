
.. _rest_scan:

Scan Services
===============

These services allow a user to create, view, and manage Scan processes.

.. _rest_scan_list:

+-------------------------------------------------------------------------------------------------------------------------+
| **Scan List**                                                                                                           |
+=========================================================================================================================+
| Returns a list of all Scan processes.                                                                                   |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /scans/                                                                                                         |
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
| name               | String            | Optional | Return only Scan processes with a given name.                       |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| order              | String            | Optional | One or more fields to use when ordering the results.                |
|                    |                   |          | Duplicate it to multi-sort, (ex: order=name&order=description).     |
|                    |                   |          | Prefix fields with a dash to reverse the sort, (ex: order=-name).   |
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
| .id                | Integer           | The unique identifier of the model. Can be passed to the details API.          |
|                    |                   | (See :ref:`Scan Details <rest_scan_details>`)                                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .name              | String            | The identifying name of the Scan process used for queries.                     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .title             | String            | The human readable display name of the Scan process.                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .description       | String            | A longer description of the Scan process.                                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .job               | JSON Object       | The job that is associated with the Scan process.                              |
|                    |                   | (See :ref:`Job Details <rest_job_details>`)                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .dry_run_job       | JSON Object       | The dry run job that is associated with the Scan process.                      |
|                    |                   | (See :ref:`Job Details <rest_job_details>`)                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .created           | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .last_modified     | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "count": 3,                                                                                                      |
|        "next": null,                                                                                                    |
|        "previous": null,                                                                                                |
|        "results": [                                                                                                     |
|            {                                                                                                            |
|                "id": 1,                                                                                                 |
|                "name": "my-scan-process",                                                                               |
|                "title": "My Scan Process",                                                                              |
|                "description": "This is my Scan process for finding my favorite files!",                                 |
|                "job": {                                                                                                 |
|                    "id": 7,                                                                                             |
|                    "job_type": {                                                                                        |
|                        "id": 2,                                                                                         |
|                        "name": "scale-scan",                                                                            |
|                        "version": "1.0",                                                                                |
|                        "title": "Scale Scan",                                                                           |
|                        "description": "Scans a workspace for existing files to ingest",                                 |
|                        "category": "system",                                                                            |
|                        "author_name": null,                                                                             |
|                        "author_url": null,                                                                              |
|                        "is_system": true,                                                                               |
|                        "is_long_running": false,                                                                        |
|                        "is_active": true,                                                                               |
|                        "is_operational": true,                                                                          |
|                        "is_paused": false,                                                                              |
|                        "icon_code": "f02a"                                                                              |
|                    },                                                                                                   |
|                    "job_type_rev": {                                                                                    |
|                        "id": 2                                                                                          |
|                    },                                                                                                   |
|                    "event": {                                                                                           |
|                        "id": 1                                                                                          |
|                    },                                                                                                   |
|                    "status": "RUNNING",                                                                                 |
|                    "priority": 5,                                                                                       |
|                    "num_exes": 1                                                                                        |
|                },                                                                                                       |
|                "dry_run_job": {                                                                                         |
|                    "id": 8,                                                                                             |
|                    "job_type": {                                                                                        |
|                        "id": 2,                                                                                         |
|                        "name": "scale-scan",                                                                            |
|                        "version": "1.0",                                                                                |
|                        "title": "Scale Scan",                                                                           |
|                        "description": "Scans a workspace for existing files to ingest",                                 |
|                        "category": "system",                                                                            |
|                        "author_name": null,                                                                             |
|                        "author_url": null,                                                                              |
|                        "is_system": true,                                                                               |
|                        "is_long_running": false,                                                                        |
|                        "is_active": true,                                                                               |
|                        "is_operational": true,                                                                          |
|                        "is_paused": false,                                                                              |
|                        "icon_code": "f02a"                                                                              |
|                    },                                                                                                   |
|                    "job_type_rev": {                                                                                    |
|                        "id": 2                                                                                          |
|                    },                                                                                                   |
|                    "event": {                                                                                           |
|                        "id": 1                                                                                          |
|                    },                                                                                                   |
|                    "status": "COMPLETED",                                                                               |
|                    "priority": 5,                                                                                       |
|                    "num_exes": 1                                                                                        |
|                }                                                                                                        |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_scan_create:

+-------------------------------------------------------------------------------------------------------------------------+
| **Create Scan**                                                                                                         |
+=========================================================================================================================+
| Creates a new Scan process and places it onto the queue                                                                 |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /scans/                                                                                                        |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| name               | String            | Required | The identifying name of the Scan process used for queries.          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| title              | String            | Optional | The human readable display name of the Scan process.                |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| description        | String            | Optional | A longer description of the Scan process.                           |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| configuration      | JSON Object       | Required | JSON defining the Scan configuration.                               |
|                    |                   |          | (See :ref:`architecture_scan_spec`)                                 |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "name": "my-scan-process",                                                                                       |
|        "title": "My Scan Process",                                                                                      |
|        "description": "This is my Scan process for detecting my favorite files!",                                       |
|        "configuration": {                                                                                               |
|            "version": "1.0",                                                                                            |
|            "workspace": "my-workspace",                                                                                 |
|            "scanner": {                                                                                                 |
|                "type": "dir",                                                                                           |
|            },                                                                                                           |
|            "files_to_ingest": [{                                                                                        |
|                "filename_regex": ".*txt"                                                                                |
|            }]                                                                                                           |
|        }                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 201 CREATED                                                                                        |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Location**       | URL pointing to the details for the newly created scan process                                     |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
|                    | JSON Object       | All fields are the same as the Scan process details model.                     |
|                    |                   | (See :ref:`Scan Details <rest_scan_details>`)                                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "id": 1,                                                                                                         |
|        "name": "my-scan-process",                                                                                       |
|        "title": "My Scan Process",                                                                                      |
|        "description": "This is my Scan process for detecting my favorite files!",                                       |
|        "job": null,                                                                                                     |
|        "dry_run_job": null,                                                                                             |
|        "configuration": {                                                                                               |
|            "version": "1.0",                                                                                            |
|            "workspace": "my-workspace",                                                                                 |
|            "scanner": {                                                                                                 |
|                "type": "dir",                                                                                           |
|            },                                                                                                           |
|            "files_to_ingest": [{                                                                                        |
|                "filename_regex": ".*txt"                                                                                |
|            }]                                                                                                           |
|        }                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_scan_details:

+-------------------------------------------------------------------------------------------------------------------------+
| **Scan Details**                                                                                                        |
+=========================================================================================================================+
| Returns Scan process details                                                                                            |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /scans/{id}/                                                                                                    |
|         Where {id} is the unique identifier of an existing model.                                                       |
+-------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| id                 | Integer           | The unique identifier of the model. Can be passed to the details API.          |
|                    |                   | (See :ref:`Scan Details <rest_scan_details>`)                                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| name               | String            | The identifying name of the Scan process used for queries.                     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| title              | String            | The human readable display name of the Scan process.                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| description        | String            | A longer description of the Scan process.                                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| job                | JSON Object       | The job that is associated with the Scan process.                              |
|                    |                   | (See :ref:`Job Details <rest_job_details>`)                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| created            | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| last_modified      | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| configuration      | JSON Object       | JSON defining the Scan configuration.                                          |
|                    |                   | (See :ref:`architecture_scan_spec`)                                            |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "id": 1,                                                                                                         |
|        "name": "my-scan-process",                                                                                       |
|        "title": "My Scan Process",                                                                                      |
|        "description": "This is my Scan process for detecting my favorite files!",                                       |
|        "file_count": 50,                                                                                                |
|		 "job": {                                                                                                         |
|			 "id": 7,                                                                                                     |
|			 "job_type": {                                                                                                |
|				 "id": 2,                                                                                                 |
|				 "name": "scale-scan",                                                                                    |
|				 "version": "1.0",                                                                                        |
|				 "title": "Scale Scan",                                                                                   |
|				 "description": "Scans a workspace for existing files to ingest",                                         |
|				 "category": "system",                                                                                    |
|				 "author_name": null,                                                                                     |
|				 "author_url": null,                                                                                      |
|				 "is_system": true,                                                                                       |
|				 "is_long_running": false,                                                                                |
|				 "is_active": true,                                                                                       |
|				 "is_operational": true,                                                                                  |
|				 "is_paused": false,                                                                                      |
|				 "icon_code": "f02a"                                                                                      |
|			 },                                                                                                           |
|			 "job_type_rev": {                                                                                            |
|				 "id": 2                                                                                                  |
|			 },                                                                                                           |
|			 "event": {                                                                                                   |
|				 "id": 1                                                                                                  |
|			 },                                                                                                           |
|			 "status": "RUNNING",                                                                                         |
|			 "priority": 5,                                                                                               |
|			 "num_exes": 1                                                                                                |
|		 },                                                                                                               |
|		 "dry_run_job": {                                                                                                 |
|			 "id": 8,                                                                                                     |
|			 "job_type": {                                                                                                |
|				 "id": 2,                                                                                                 |
|				 "name": "scale-scan",                                                                                    |
|				 "version": "1.0",                                                                                        |
|				 "title": "Scale Scan",                                                                                   |
|				 "description": "Scans a workspace for existing files to ingest",                                         |
|				 "category": "system",                                                                                    |
|				 "author_name": null,                                                                                     |
|				 "author_url": null,                                                                                      |
|				 "is_system": true,                                                                                       |
|				 "is_long_running": false,                                                                                |
|				 "is_active": true,                                                                                       |
|				 "is_operational": true,                                                                                  |
|				 "is_paused": false,                                                                                      |
|				 "icon_code": "f02a"                                                                                      |
|			 },                                                                                                           |
|			 "job_type_rev": {                                                                                            |
|			 	"id": 2                                                                                                   |
|			 },                                                                                                           |
|			 "event": {                                                                                                   |
|			 	"id": 1                                                                                                   |
|			 },                                                                                                           |
|			 "status": "COMPLETED",                                                                                       |
|			 "priority": 5,                                                                                               |
|			 "num_exes": 1                                                                                                |
|		 }                                                                                                                |
|        "configuration": {                                                                                               |
|            "version": "1.0",                                                                                            |
|            "workspace": "my-workspace",                                                                                 |
|            "scanner": {                                                                                                 |
|                "type": "dir",                                                                                           |
|            },                                                                                                           |
|            "files_to_ingest": [{                                                                                        |
|                "filename_regex": ".*txt"                                                                                |
|            }]                                                                                                           |
|        }                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_scan_validate:

+-------------------------------------------------------------------------------------------------------------------------+
| **Validate Scan**                                                                                                       |
+=========================================================================================================================+
| Validates a new Scan process configuration without actually saving it                                                   |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /scans/validation/                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| name               | String            | Required | The identifying name of the Scan process used for queries.          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| title              | String            | Optional | The human readable display name of the Scan process.                |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| description        | String            | Optional | A longer description of the Scan process.                           |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| configuration      | JSON Object       | Required | JSON defining the Scan configuration.                               |
|                    |                   |          | (See :ref:`architecture_scan_spec`)                                 |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "name": "my-scan-process",                                                                                       |
|        "title": "My Scan Process",                                                                                      |
|        "description": "This is my Scan process for detecting my favorite files!",                                       |
|        "configuration": {                                                                                               |
|            "version": "1.0",                                                                                            |
|            "workspace": "my-workspace",                                                                                 |
|            "scanner": {                                                                                                 |
|                "type": "dir",                                                                                           |
|            },                                                                                                           |
|            "files_to_ingest": [{                                                                                        |
|                "filename_regex": ".*txt"                                                                                |
|            }]                                                                                                           |
|        }                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+---------------------+------------------------------------------------------------------------------+
| warnings           | Array               | A list of warnings discovered during validation.                             |
+--------------------+---------------------+------------------------------------------------------------------------------+
| .id                | String              | An identifier for the warning.                                               |
+--------------------+---------------------+------------------------------------------------------------------------------+
| .details           | String              | A human-readable description of the problem.                                 |
+--------------------+---------------------+------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "warnings": [                                                                                                    |
|            "id": "mount_change",                                                                                        |
|            "details": "Changing the mount path may disrupt file monitoring."                                            |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_scan_edit:

+-------------------------------------------------------------------------------------------------------------------------+
| **Edit Scan**                                                                                                           |
+=========================================================================================================================+
| Edits an existing Scan process with associated configuration                                                            |
+-------------------------------------------------------------------------------------------------------------------------+
| **PATCH** /scans/{id}/                                                                                                  |
|           Where {id} is the unique identifier of an existing model.                                                     |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| title              | String            | Optional | The human readable display name of the Scan process.                |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| description        | String            | Optional | A longer description of the Scan process.                           |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| configuration      | JSON Object       | Optional | JSON defining the Scan configuration.                               |
|                    |                   |          | (See :ref:`architecture_scan_spec`)                                 |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "title": "My Scan Process",                                                                                      |
|        "description": "This is my Scan process for detecting my favorite files!",                                       |
|        "configuration": {                                                                                               |
|            "version": "1.0",                                                                                            |
|            "workspace": "my-workspace",                                                                                 |
|            "scanner": {                                                                                                 |
|                "type": "dir",                                                                                           |
|            },                                                                                                           |
|            "files_to_ingest": [{                                                                                        |
|                "filename_regex": ".*txt"                                                                                |
|            }]                                                                                                           |
|        }                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
|                    | JSON Object       | All fields are the same as the Scan process details model.                     |
|                    |                   | (See :ref:`Scan Details <rest_scan_details>`)                                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "id": 1,                                                                                                         |
|        "name": "my-scan-process",                                                                                       |
|        "title": "My Scan Process",                                                                                      |
|        "description": "This is my Scan process for detecting my favorite files!",                                       |
|        "job": {                                                                                                         |
|            "id": 7,                                                                                                     |
|            "job_type": {                                                                                                |
|                "id": 2,                                                                                                 |
|                "name": "scale-scan",                                                                                    |
|                "version": "1.0",                                                                                        |
|                "title": "Scale Scan",                                                                                   |
|                "description": "Scans a workspace for existing files to ingest",                                         |
|                "category": "system",                                                                                    |
|                "author_name": null,                                                                                     |
|                "author_url": null,                                                                                      |
|                "is_system": true,                                                                                       |
|                "is_long_running": false,                                                                                |
|                "is_active": true,                                                                                       |
|                "is_operational": true,                                                                                  |
|                "is_paused": false,                                                                                      |
|                "icon_code": "f02a"                                                                                      |
|            },                                                                                                           |
|            "job_type_rev": {                                                                                            |
|                "id": 2                                                                                                  |
|            },                                                                                                           |
|            "event": {                                                                                                   |
|                "id": 1                                                                                                  |
|            },                                                                                                           |
|            "status": "RUNNING",                                                                                         |
|            "priority": 10,                                                                                              |
|            "num_exes": 1                                                                                                |
|        },                                                                                                               |
|        "configuration": {                                                                                               |
|            "version": "2.0",                                                                                            |
|            "workspace": "my-workspace",                                                                                 |
|            "scanner": {                                                                                                 |
|                "type": "dir",                                                                                           |
|            },                                                                                                           |
|            "files_to_ingest": [{                                                                                        |
|                "filename_regex": ".*txt"                                                                                |
|            }]                                                                                                           |
|        }                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_scan_process:

+-------------------------------------------------------------------------------------------------------------------------+
| **Process Scan**                                                                                                        |
+=========================================================================================================================+
| Launches an existing Scan with associated configuration                                                                 |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /scans/process/{id}/                                                                                           |
|           Where {id} is the unique identifier of an existing model.                                                     |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| ingest             | Boolean           | Optional | Whether a dry run or ingest triggering scan should be run.          |
|                    |                   |          | Defaults to false when unset.                                       |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "ingest": true                                                                                                   |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 201 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Location**       | URL pointing to the details of the Scan model used to launch process                               |
+-------------------------------------------------------------------------------------------------------------------------+