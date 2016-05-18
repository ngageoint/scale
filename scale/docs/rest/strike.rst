
.. _rest_strike:

Strike Services
===============

These services allow a user to create, view, and manage Strike processes.

.. _rest_strike_list:

+-------------------------------------------------------------------------------------------------------------------------+
| **Strike List**                                                                                                         |
+=========================================================================================================================+
| Returns a list of all Strike processes.                                                                                 |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /strikes/                                                                                                       |
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
| name               | String            | Optional | Return only Strike processes with a given name.                     |
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
|                    |                   | (See :ref:`Strike Details <rest_strike_details>`)                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .name              | String            | The identifying name of the Strike process used for queries.                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .title             | String            | The human readable display name of the Strike process.                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .description       | String            | A longer description of the Strike process.                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .job               | JSON Object       | The job that is associated with the Strike process.                            |
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
|                "name": "my-strike-process",                                                                             |
|                "title": "My Strike Process",                                                                            |
|                "description": "This is my Strike process for detecting my favorite files!",                             |
|                "job": {                                                                                                 |
|                    "id": 7,                                                                                             |
|                    "job_type": {                                                                                        |
|                        "id": 2,                                                                                         |
|                        "name": "scale-strike",                                                                          |
|                        "version": "1.0",                                                                                |
|                        "title": "Scale Strike",                                                                         |
|                        "description": "Monitors a directory for incoming source files to ingest",                       |
|                        "category": "system",                                                                            |
|                        "author_name": null,                                                                             |
|                        "author_url": null,                                                                              |
|                        "is_system": true,                                                                               |
|                        "is_long_running": true,                                                                         |
|                        "is_active": true,                                                                               |
|                        "is_operational": true,                                                                          |
|                        "is_paused": false,                                                                              |
|                        "icon_code": "f0e7"                                                                              |
|                    },                                                                                                   |
|                    "job_type_rev": {                                                                                    |
|                        "id": 2                                                                                          |
|                    },                                                                                                   |
|                    "event": {                                                                                           |
|                        "id": 1                                                                                          |
|                    },                                                                                                   |
|                    "status": "RUNNING",                                                                                 |
|                    "priority": 10,                                                                                      |
|                    "num_exes": 1                                                                                        |
|                }                                                                                                        |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_strike_create:

+-----------------------------------------------------------------------------------------------------------------------+
| **Create Strike Process**                                                                                             |
+=======================================================================================================================+
| Creates a new Strike process and places it onto the queue                                                             |
+-----------------------------------------------------------------------------------------------------------------------+
| **POST** /strike/create/                                                                                              |
+--------------------+--------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                               |
+--------------------+--------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                       |
+--------------------+-------------------+----------+-------------------------------------------------------------------+
| name               | String            | Required | The unique name of the Strike process                             |
+--------------------+-------------------+----------+-------------------------------------------------------------------+
| title              | String            | Optional | A display title for the Strike process                            |
+--------------------+-------------------+----------+-------------------------------------------------------------------+
| description        | String            | Optional | A description for the Strike process                              |
+--------------------+-------------------+----------+-------------------------------------------------------------------+
| configuration      | JSON Object       | Required | JSON defining the Strike configuration,                           |
|                    |                   |          | see :ref:`architecture_strike_spec`                               |
+--------------------+-------------------+----------+-------------------------------------------------------------------+
| .. code-block:: javascript                                                                                            |
|                                                                                                                       |
|    {                                                                                                                  |
|        "name": "my-strike-process",                                                                                   |
|        "title": "My Strike Process",                                                                                  |
|        "description": "This is my Strike process for detecting my favorite files!",                                   |
|        "configuration": {                                                                                             |
|            "version": "1.0",                                                                                          |
|            "mount": "host:/my/path",                                                                                  |
|            "transfer_suffix": "_tmp",                                                                                 |
|            "files_to_ingest": [{                                                                                      |
|                "filename_regex": ".*txt",                                                                             |
|                "workspace_path": "/my/path",                                                                          |
|                "workspace_name": "raw"                                                                                |
|            }]                                                                                                         |
|        }                                                                                                              |
|    }                                                                                                                  |
+-----------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                               |
+--------------------+--------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                           |
+--------------------+--------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                               |
+--------------------+--------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                       |
+--------------------+-------------------+------------------------------------------------------------------------------+
| strike_id          | Integer           | The ID of the new Strike process                                             |
+--------------------+-------------------+------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                            |
|                                                                                                                       |
|    {                                                                                                                  |
|        "strike_id": 5678                                                                                              |
|    }                                                                                                                  |
+-----------------------------------------------------------------------------------------------------------------------+

.. _rest_strike_details:

+-------------------------------------------------------------------------------------------------------------------------+
| **Strike Details**                                                                                                      |
+=========================================================================================================================+
| Returns job type details                                                                                                |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /strikes/{id}/                                                                                                  |
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
|                    |                   | (See :ref:`Strike Details <rest_strike_details>`)                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| name               | String            | The identifying name of the Strike process used for queries.                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| title              | String            | The human readable display name of the Strike process.                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| description        | String            | A longer description of the Strike process.                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| job                | JSON Object       | The job that is associated with the Strike process.                            |
|                    |                   | (See :ref:`Job Details <rest_job_details>`)                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| created            | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| last_modified      | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| configuration      | JSON Object       | JSON defining the Strike configuration.                                        |
|                    |                   | (See :ref:`architecture_strike_spec`)                                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "id": 1,                                                                                                         |
|        "name": "my-strike-process",                                                                                     |
|        "title": "My Strike Process",                                                                                    |
|        "description": "This is my Strike process for detecting my favorite files!",                                     |
|        "job": {                                                                                                         |
|            "id": 7,                                                                                                     |
|            "job_type": {                                                                                                |
|                "id": 2,                                                                                                 |
|                "name": "scale-strike",                                                                                  |
|                "version": "1.0",                                                                                        |
|                "title": "Scale Strike",                                                                                 |
|                "description": "Monitors a directory for incoming source files to ingest",                               |
|                "category": "system",                                                                                    |
|                "author_name": null,                                                                                     |
|                "author_url": null,                                                                                      |
|                "is_system": true,                                                                                       |
|                "is_long_running": true,                                                                                 |
|                "is_active": true,                                                                                       |
|                "is_operational": true,                                                                                  |
|                "is_paused": false,                                                                                      |
|                "icon_code": "f0e7"                                                                                      |
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
|            "version": "1.0",                                                                                            |
|            "mount": "host:/my/path",                                                                                    |
|            "transfer_suffix": "_tmp",                                                                                   |
|            "files_to_ingest": [{                                                                                        |
|                "filename_regex": ".*txt",                                                                               |
|                "workspace_path": "/my/path",                                                                            |
|                "workspace_name": "raw"                                                                                  |
|            }]                                                                                                           |
|        }                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+
