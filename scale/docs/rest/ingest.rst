
.. _rest_ingest:

Ingest Services
===============================================================================

These services provide access to information about ingested files processed by the system.

.. _rest_ingest_list:

+-------------------------------------------------------------------------------------------------------------------------+
| **Ingest List**                                                                                                         |
+=========================================================================================================================+
| Returns a list of all ingests.                                                                                          |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /ingests/                                                                                                       |
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
| order              | String            | Optional | One or more fields to use when ordering the results.                |
|                    |                   |          | Duplicate it to multi-sort, (ex: order=status&order=created).       |
|                    |                   |          | Nested objects require a delimiter (ex: order=source_file__created).|
|                    |                   |          | Prefix fields with a dash to reverse the sort, (ex: order=-status). |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| status             | String            | Optional | Return only ingests with a status matching this string.             |
|                    |                   |          | Choices: [TRANSFERRING, TRANSFERRED, DEFERRED, INGESTING, INGESTED, |
|                    |                   |          | ERRORED, DUPLICATE].                                                |
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
|                    |                   | (See :ref:`Ingest Details <rest_ingest_details>`)                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .file_name         | String            | The name of the file being ingested.                                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .strike            | JSON Object       | The strike process that triggered the ingest.                                  |
|                    |                   | (See :ref:`Strike Details <rest_strike_details>`)                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .status            | String            | The current status of the ingest.                                              |
|                    |                   | Choices: [TRANSFERRING, TRANSFERRED, DEFERRED, INGESTING, INGESTED, ERRORED,   |
|                    |                   | DUPLICATE].                                                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .bytes_transferred | Integer           | The total number of bytes transferred so far.                                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .transfer_started  | ISO-8601 Datetime | When the transfer was started.                                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .transfer_ended    | ISO-8601 Datetime | When the transfer ended.                                                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .media_type        | String            | The IANA media type of the file.                                               |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .file_size         | Integer           | The size of the file in bytes.                                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .data_type         | Array             | A list of string data type "tags" for the file.                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .ingest_started    | ISO-8601 Datetime | When the ingest was started.                                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .ingest_ended      | ISO-8601 Datetime | When the ingest ended.                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .source_file       | JSON Object       | A reference to the source file that was stored by this ingest.                 |
|                    |                   | (See :ref:`Source File Details <rest_source_file_details>`)                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .created           | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .last_modified     | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "count": 42,                                                                                                     |
|        "next": null,                                                                                                    |
|        "previous": null,                                                                                                |
|        "results": [                                                                                                     |
|            {                                                                                                            |
|                "id": 14,                                                                                                |
|                "file_name": "file_name.txt",                                                                            |
|                "strike": {                                                                                              |
|                    "id": 1,                                                                                             |
|                    "job": {                                                                                             |
|                        "id": 2                                                                                          |
|                    }                                                                                                    |
|                },                                                                                                       |
|                "status": "INGESTED",                                                                                    |
|                "bytes_transferred": 1234,                                                                               |
|                "transfer_started": "2015-09-10T14:48:08.920Z",                                                          |
|                "transfer_ended": "2015-09-10T14:48:08.956Z",                                                            |
|                "media_type": "text/plain",                                                                              |
|                "file_size": 1234,                                                                                       |
|                "data_type": [],                                                                                         |
|                "ingest_started": "2015-09-10T15:24:53.503Z",                                                            |
|                "ingest_ended": "2015-09-10T15:24:53.987Z",                                                              |
|                "source_file": {                                                                                         |
|                    "id": 1,                                                                                             |
|                    "workspace": {                                                                                       |
|                        "id": 1,                                                                                         |
|                        "name": "Raw Source"                                                                             |
|                    },                                                                                                   |
|                    "file_name": "file_name.txt",                                                                        |
|                    "media_type": "text/plain",                                                                          |
|                    "file_size": 1234,                                                                                   |
|                    "data_type": [],                                                                                     |
|                    "is_deleted": false,                                                                                 |
|                    "uuid": "c8928d9183fc99122948e7840ec9a0fd",                                                          |
|                    "url": "http://host.com/file_name.txt",                                                              |
|                    "created": "2015-09-10T15:24:53.962Z",                                                               |
|                    "deleted": null,                                                                                     |
|                    "data_started": "2015-09-10T14:36:56Z",                                                              |
|                    "data_ended": "2015-09-10T14:37:01Z",                                                                |
|                    "geometry": null,                                                                                    |
|                    "center_point": null,                                                                                |
|                    "meta_data": {...},                                                                                  |
|                    "last_modified": "2015-09-10T15:25:03.797Z",                                                         |
|                    "is_parsed": true,                                                                                   |
|                    "parsed": "2015-09-10T15:25:03.796Z"                                                                 |
|                },                                                                                                       |
|                "created": "2015-09-10T15:24:47.412Z",                                                                   |
|                "last_modified": "2015-09-10T15:24:53.987Z"                                                              |
|            },                                                                                                           |
|           ...                                                                                                           |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_ingest_details:

+-------------------------------------------------------------------------------------------------------------------------+
| **Ingest Details**                                                                                                      |
+=========================================================================================================================+
| Returns a specific ingest and all its related model information.                                                        |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /ingests/{id}/                                                                                                  |
|         Where {id} is the unique identifier of an existing model.                                                       |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| id                 | Integer           | The unique identifier of the model.                                            |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| file_name          | String            | The name of the file being ingested.                                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| strike             | JSON Object       | The strike process that triggered the ingest.                                  |
|                    |                   | (See :ref:`Strike Details <rest_strike_details>`)                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| status             | String            | The current status of the ingest.                                              |
|                    |                   | Choices: [TRANSFERRING, TRANSFERRED, DEFERRED, INGESTING, INGESTED, ERRORED,   |
|                    |                   | DUPLICATE].                                                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| bytes_transferred  | Integer           | The total number of bytes transferred so far.                                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| transfer_started   | ISO-8601 Datetime | When the transfer was started.                                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| transfer_ended     | ISO-8601 Datetime | When the transfer ended.                                                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| media_type         | String            | The IANA media type of the file.                                               |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| file_size          | Integer           | The size of the file in bytes.                                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| data_type          | Array             | A list of string data type "tags" for the file.                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ingest_started     | ISO-8601 Datetime | When the ingest was started.                                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ingest_ended       | ISO-8601 Datetime | When the ingest ended.                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| source_file        | JSON Object       | A reference to the source file that was stored by this ingest.                 |
|                    |                   | (See :ref:`Source File Details <rest_source_file_details>`)                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| created            | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| last_modified      | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| transfer_path      | String            | The absolute path of the destination where the file is being transferred.      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| file_path          | String            | The relative path for where the file will be stored in the workspace.          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ingest_path        | String            | The absolute path of the file when it is ready to be ingested.                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "id": 14,                                                                                                        |
|        "file_name": "file_name.txt",                                                                                    |
|        "strike": {                                                                                                      |
|            "id": 1,                                                                                                     |
|            "job": {                                                                                                     |
|                "id": 2,                                                                                                 |
|                "job_type": {                                                                                            |
|                    "id": 2,                                                                                             |
|                    "name": "scale-strike",                                                                              |
|                    "version": "1.0",                                                                                    |
|                    "title": "Scale Strike",                                                                             |
|                    "description": "Monitors a directory for incoming files to ingest",                                  |
|                    "category": "system",                                                                                |
|                    "author_name": null,                                                                                 |
|                    "author_url": null,                                                                                  |
|                    "is_system": true,                                                                                   |
|                    "is_long_running": true,                                                                             |
|                    "is_active": true,                                                                                   |
|                    "is_operational": true,                                                                              |
|                    "is_paused": false,                                                                                  |
|                    "icon_code": "f013"                                                                                  |
|                },                                                                                                       |
|                "job_type_rev": {                                                                                        |
|                    "id": 2                                                                                              |
|                },                                                                                                       |
|                "event": {                                                                                               |
|                    "id": 2                                                                                              |
|                },                                                                                                       |
|                "error": null,                                                                                           |
|                "status": "RUNNING",                                                                                     |
|                "priority": 5,                                                                                           |
|                "num_exes": 1                                                                                            |
|            },                                                                                                           |
|            "configuration": {                                                                                           |
|                "transfer_suffix": "_tmp",                                                                               |
|                "mount": "host:/transfer",                                                                               |
|                "version": "1.0",                                                                                        |
|                "mount_on": "/mounts/transfer",                                                                          |
|                "files_to_ingest": [                                                                                     |
|                    {                                                                                                    |
|                        "workspace_path": "/workspace",                                                                  |
|                        "data_types": [],                                                                                |
|                        "filename_regex": "*.txt",                                                                       |
|                        "workspace_name": "rs"                                                                           |
|                    }                                                                                                    |
|                ]                                                                                                        |
|            },                                                                                                           |
|            "created": "2015-09-10T15:24:42.896Z",                                                                       |
|            "last_modified": "2015-09-10T15:24:42.935Z"                                                                  |
|        },                                                                                                               |
|        "status": "INGESTED",                                                                                            |
|        "bytes_transferred": 1234,                                                                                       |
|        "transfer_started": "2015-09-10T14:48:08.920Z",                                                                  |
|        "transfer_ended": "2015-09-10T14:48:08.956Z",                                                                    |
|        "media_type": "text/plain",                                                                                      |
|        "file_size": 1234,                                                                                               |
|        "data_type": [],                                                                                                 |
|        "ingest_started": "2015-09-10T15:24:53.503Z",                                                                    |
|        "ingest_ended": "2015-09-10T15:24:53.987Z",                                                                      |
|        "source_file": {                                                                                                 |
|            "id": 1,                                                                                                     |
|            "workspace": {                                                                                               |
|                "id": 1,                                                                                                 |
|                "name": "Raw Source"                                                                                     |
|            },                                                                                                           |
|            "file_name": "file_name.txt",                                                                                |
|            "media_type": "text/plain",                                                                                  |
|            "file_size": 1234,                                                                                           |
|            "data_type": [],                                                                                             |
|            "is_deleted": false,                                                                                         |
|            "uuid": "c8928d9183fc99122948e7840ec9a0fd",                                                                  |
|            "url": "http://host.com/file_name.txt",                                                                      |
|            "created": "2015-09-10T15:24:53.962Z",                                                                       |
|            "deleted": null,                                                                                             |
|            "data_started": "2015-09-10T14:36:56Z",                                                                      |
|            "data_ended": "2015-09-10T14:37:01Z",                                                                        |
|            "geometry": null,                                                                                            |
|            "center_point": null,                                                                                        |
|            "meta_data": {...},                                                                                          |
|            "last_modified": "2015-09-10T15:25:03.797Z",                                                                 |
|            "is_parsed": true,                                                                                           |
|            "parsed": "2015-09-10T15:25:03.796Z"                                                                         |
|        },                                                                                                               |
|        "created": "2015-09-10T15:24:47.412Z",                                                                           |
|        "last_modified": "2015-09-10T15:24:53.987Z",                                                                     |
|        "transfer_path": "/mounts/transfer/file_name.txt",                                                               |
|        "file_path": "path/file_name.txt",                                                                               |
|        "ingest_path": "/mounts/transfer/ingesting/file_name.txt"                                                        |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_ingest_status:

+-------------------------------------------------------------------------------------------------------------------------+
| **Ingest Status**                                                                                                       |
+=========================================================================================================================+
| Returns status summary information (counts, file sizes) for completed ingests grouped into 1 hour time slots.           |
| NOTE: Time range must be within a one month period (31 days).                                                           |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /ingests/status/                                                                                                |
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
|                    |                   |          | Defaults to the past 1 week.                                        |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| ended              | ISO-8601 Datetime | Optional | End of the time range to query, defaults to the current time.       |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| use_ingest_time    | Boolean           | Optional | Whether to group counts by ingest time or data time.                |
|                    |                   |          | Ingest time is when the strike process registered the file.         |
|                    |                   |          | Data time is the time when the data was collected by a sensor.      |
|                    |                   |          | Defaults to False (data time).                                      |
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
| .strike            | JSON Object       | The strike process that triggered the ingest.                                  |
|                    |                   | (See :ref:`Strike Details <rest_strike_details>`)                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .most_recent       | ISO-8601 Datetime | The date/time when the strike process last completed an ingest.                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .files             | Integer           | The total number of files ingested by the strike process.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .size              | Integer           | The total size of files ingested by the strike process in bytes.               |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .values            | Array             | A list of ingest statistics grouped into 1 hour time slots.                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..time             | ISO-8601 Datetime | The date/time of the 1 hour time slot being counted.                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..files            | Integer           | The number of files ingested by the strike process within the time slot.       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..size             | Integer           | The size of files ingested by the strike process in bytes within the time slot.|
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "count": 2,                                                                                                      |
|        "next": null,                                                                                                    |
|        "previous": null,                                                                                                |
|        "results": [                                                                                                     |
|            {                                                                                                            |
|                "strike": {                                                                                              |
|                    "id": 1,                                                                                             |
|                    "name": "my-strike",                                                                                 |
|                    "title": "My Strike Processor",                                                                      |
|                    "description": "This Strike process handles the data feed",                                          |
|                    "job": {                                                                                             |
|                        "id": 4,                                                                                         |
|                        "job_type": {                                                                                    |
|                            "id": 2,                                                                                     |
|                            "name": "scale-strike",                                                                      |
|                            "version": "1.0",                                                                            |
|                            "title": "Scale Strike",                                                                     |
|                            "description": "Monitors a directory for incoming source files to ingest",                   |
|                            "category": "system",                                                                        |
|                            "author_name": null,                                                                         |
|                            "author_url": null,                                                                          |
|                            "is_system": true,                                                                           |
|                            "is_long_running": true,                                                                     |
|                            "is_active": true,                                                                           |
|                            "is_operational": true,                                                                      |
|                            "is_paused": false,                                                                          |
|                            "icon_code": "f013"                                                                          |
|                        },                                                                                               |
|                        "event": {                                                                                       |
|                            "id": 5                                                                                      |
|                        },                                                                                               |
|                        "error": null,                                                                                   |
|                        "status": "RUNNING",                                                                             |
|                        "priority": 5,                                                                                   |
|                        "num_exes": 36                                                                                   |
|                    },                                                                                                   |
|                    "created": "2015-10-05T17:35:46.690Z",                                                               |
|                    "last_modified": "2015-10-05T17:35:46.740Z"                                                          |
|                },                                                                                                       |
|                "most_recent": "2015-10-21T21:15:56.522Z",                                                               |
|                "files": 1234,                                                                                           |
|                "size": 12345678900000,                                                                                  |
|                "values": [                                                                                              |
|                    {                                                                                                    |
|                        "time": "2015-10-21T00:00:00Z",                                                                  |
|                        "files": 10,                                                                                     |
|                        "size": 123456789                                                                                |
|                    },                                                                                                   |
|                    ...                                                                                                  |
|                ]                                                                                                        |
|            }                                                                                                            |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+
