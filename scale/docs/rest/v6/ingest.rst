
.. _rest_v6_ingest:

v6 Ingest Services
==================

These services provide access to information about ingested files processed by the system.

.. _rest_v6_ingest_list:

v6 Ingest List
--------------

**Example GET /v6/ingests/ API call**

Request: GET http://.../v6/ingests/?scan_id=1

Response: 200 OK

 .. code-block:: javascript 
 
    { 
        "count": 42, 
        "next": null, 
        "previous": null, 
        "results": [ 
            { 
                "id": 14, 
                "file_name": "file_name.txt", 
                "scan": null, 
                "strike": { 
                    "id": 1, 
                    "name": "my-strike", 
                    "title": "My Strike Processor", 
                    "description": "This Strike process handles the data feed", 
                    "job": { 
                        "id": 2 
                    } 
                }, 
                "status": "INGESTED", 
                "bytes_transferred": 1234, 
                "transfer_started": "2015-09-10T14:48:08.920Z", 
                "transfer_ended": "2015-09-10T14:48:08.956Z", 
                "media_type": "text/plain", 
                "file_size": 1234, 
                "data_type": [], 
                "file_path": "the/current/path/file_name.txt", 
                "workspace": { 
                    "id": 1, 
                    "name": "my-workspace", 
                    "title": "My Workspace", 
                    "description": "My Workspace", 
                    "base_url": "http://host.com/wk", 
                    "is_active": true, 
                    "used_size": 0, 
                    "total_size": 0, 
                    "created": "2015-10-05T21:26:04.855Z", 
                    "archived": null, 
                    "last_modified": "2015-10-05T21:26:04.855Z" 
                }, 
                "new_file_path": "the/new/path/file_name.txt", 
                "new_workspace": { 
                    "id": 1, 
                    "name": "my-new-workspace", 
                    "title": "My New Workspace", 
                    "description": "My New Workspace", 
                    "base_url": "http://host.com/new-wk", 
                    "is_active": true, 
                    "used_size": 0, 
                    "total_size": 0, 
                    "created": "2015-10-05T21:26:04.855Z", 
                    "archived": null, 
                    "last_modified": "2015-10-05T21:26:04.855Z" 
                }, 
                "job": { 
                    "id": 1234 
                }, 
                "ingest_started": "2015-09-10T15:24:53.503Z", 
                "ingest_ended": "2015-09-10T15:24:53.987Z", 
                "source_file": { 
                    "id": 1, 
                    "workspace": { 
                        "id": 1, 
                        "name": "Raw Source" 
                    }, 
                    "file_name": "file_name.txt", 
                    "media_type": "text/plain", 
                    "file_size": 1234, 
                    "data_type": [], 
                    "is_deleted": false, 
                    "uuid": "c8928d9183fc99122948e7840ec9a0fd", 
                    "url": "http://host.com/file_name.txt", 
                    "created": "2015-09-10T15:24:53.962Z", 
                    "deleted": null, 
                    "data_started": "2015-09-10T14:36:56Z", 
                    "data_ended": "2015-09-10T14:37:01Z", 
                    "geometry": null, 
                    "center_point": null, 
                    "meta_data": {...}, 
                    "last_modified": "2015-09-10T15:25:03.797Z", 
                    "is_parsed": true, 
                    "parsed": "2015-09-10T15:25:03.796Z" 
                }, 
                "data_started": "2015-09-10T15:24:53.503Z", 
                "data_ended": "2015-09-10T15:24:53.987Z", 
                "created": "2015-09-10T15:24:47.412Z", 
                "last_modified": "2015-09-10T15:24:53.987Z" 
            }, 
           ... 
        ] 
    } 

+-------------------------------------------------------------------------------------------------------------------------+
| **Ingest List**                                                                                                         |
+=========================================================================================================================+
| Returns a list of all ingests.                                                                                          |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/ingests/                                                                                                    |
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
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| scan_id            | Integer           | Optional | Return only ingests created by a given scan process identifier.     |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| strike_id          | Integer           | Optional | Return only ingests created by a given strike process identifier.   |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| file_name          | String            | Optional | Return only ingests with a specific file name.                      |
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
| .scan              | JSON Object       | The scan process that triggered the ingest.                                    |
|                    |                   | (See :ref:`Scan Details <rest_scan_details>`)                                  |
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
| .file_path         | String            | The relative path of the file in the workspace.                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .workspace         | JSON Object       | The workspace storing the file.                                                |
|                    |                   | (See :ref:`Workspace Details <rest_workspace_details>`)                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .new_file_path     | String            | The relative path for where the file should be moved as part of ingesting.     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .new_workspace     | JSON Object       | The new workspace to move the file into as part of ingesting.                  |
|                    |                   | (See :ref:`Workspace Details <rest_workspace_details>`)                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .job               | JSON Object       | The ID of the ingest job.                                                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .ingest_started    | ISO-8601 Datetime | When the ingest was started.                                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .ingest_ended      | ISO-8601 Datetime | When the ingest ended.                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .source_file       | JSON Object       | A reference to the source file that was stored by this ingest.                 |
|                    |                   | (See :ref:`Source File Details <rest_source_file_details>`)                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .data_started      | ISO-8601 Datetime | The start time of the source data being ingested.                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .data_ended        | ISO-8601 Datetime | The end time of the source data being ingested.                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .created           | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .last_modified     | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+

.. _rest_v6_ingest_details:

v6 Ingest Details
-----------------

**Example GET /v6/ingests/{id}/ API call**

Request: GET http://.../v6/ingests/14/

Response: 200 OK

 .. code-block:: javascript 
 
    { 
        "id": 14, 
        "file_name": "file_name.txt", 
        "scan": null, 
        "strike": { 
            "id": 1, 
            "name": "my-strike", 
            "title": "My Strike Processor", 
            "description": "This Strike process handles the data feed", 
            "job": { 
                "id": 2, 
                "job_type": { 
                    "id": 2, 
                    "name": "scale-strike", 
                    "version": "1.0.0",
                    "title": "Scale Strike", 
                    "description": "Monitors a directory for incoming files to ingest", 
                    "revision_num": 1,
                    "icon_code": "f013" 
                }, 
                "status": "RUNNING"
            }, 
            "configuration": { 
                "transfer_suffix": "_tmp", 
                "mount": "host:/transfer", 
                "mount_on": "/mounts/transfer", 
                "files_to_ingest": [ 
                    { 
                        "workspace_path": "/workspace", 
                        "data_types": [], 
                        "filename_regex": "*.txt", 
                        "workspace_name": "raw" 
                    } 
                ] 
            }, 
            "created": "2015-09-10T15:24:42.896Z", 
            "last_modified": "2015-09-10T15:24:42.935Z" 
        }, 
        "status": "INGESTED", 
        "bytes_transferred": 1234, 
        "transfer_started": "2015-09-10T14:48:08.920Z", 
        "transfer_ended": "2015-09-10T14:48:08.956Z", 
        "media_type": "text/plain", 
        "file_size": 1234, 
        "data_type": [], 
        "file_path": "the/current/path/file_name.txt", 
        "workspace": { 
            "id": 1, 
            "name": "my-workspace", 
            "title": "My Workspace", 
            "description": "My Workspace", 
            "base_url": "http://host.com/wk", 
            "is_active": true, 
            "used_size": 0, 
            "total_size": 0, 
            "created": "2015-10-05T21:26:04.855Z", 
            "archived": null, 
            "last_modified": "2015-10-05T21:26:04.855Z", 
            "json_config": { 
                 "broker": { 
                    "type": "host", 
                    "host_path": "/host/path" 
                } 
            } 
        }, 
        "new_file_path": "the/new/path/file_name.txt", 
        "new_workspace": { 
            "id": 1, 
            "name": "my-new-workspace", 
            "title": "My New Workspace", 
            "description": "My New Workspace", 
            "base_url": "http://host.com/new-wk", 
            "is_active": true, 
            "used_size": 0, 
            "total_size": 0, 
            "created": "2015-10-05T21:26:04.855Z", 
            "archived": null, 
            "last_modified": "2015-10-05T21:26:04.855Z", 
            "json_config": { 
                 "broker": { 
                    "type": "host", 
                    "host_path": "/host/path" 
                } 
            } 
        }, 
        "job": { 
            "id": 1234 
        }, 
        "ingest_started": "2015-09-10T15:24:53.503Z", 
        "ingest_ended": "2015-09-10T15:24:53.987Z", 
        "source_file": { 
            "id": 1, 
            "workspace": { 
                "id": 1, 
                "name": "Raw Source" 
            }, 
            "file_name": "file_name.txt", 
            "media_type": "text/plain", 
            "file_size": 1234, 
            "data_type": [], 
            "is_deleted": false, 
            "uuid": "c8928d9183fc99122948e7840ec9a0fd", 
            "url": "http://host.com/file_name.txt", 
            "created": "2015-09-10T15:24:53.962Z", 
            "deleted": null, 
            "data_started": "2015-09-10T14:36:56Z", 
            "data_ended": "2015-09-10T14:37:01Z", 
            "geometry": null, 
            "center_point": null, 
            "meta_data": {...}, 
            "last_modified": "2015-09-10T15:25:03.797Z", 
            "is_parsed": true, 
            "parsed": "2015-09-10T15:25:03.796Z" 
        }, 
        "data_started": "2015-09-10T15:24:53.503Z", 
        "data_ended": "2015-09-10T15:24:53.987Z", 
        "created": "2015-09-10T15:24:47.412Z", 
        "last_modified": "2015-09-10T15:24:53.987Z", 
    } 

+-------------------------------------------------------------------------------------------------------------------------+
| **Ingest Details**                                                                                                      |
+=========================================================================================================================+
| Returns a specific ingest and all its related model information.                                                        |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/ingests/{id}/                                                                                               |
|         Where {id} is the unique identifier of an existing model.                                                       |
+-------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| id                 | Integer           | The unique identifier of the model. Can be passed to the details API call.     |
|                    |                   | (See :ref:`Ingest Details <rest_ingest_details>`)                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| file_name          | String            | The name of the file being ingested.                                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| scan               | JSON Object       | The scan process that triggered the ingest.                                    |
|                    |                   | (See :ref:`Scan Details <rest_scan_details>`)                                  |
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
| file_path          | String            | The relative path of the file in the workspace.                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| workspace          | JSON Object       | The workspace storing the file.                                                |
|                    |                   | (See :ref:`Workspace Details <rest_workspace_details>`)                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| new_file_path      | String            | The relative path for where the file should be moved as part of ingesting.     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| new_workspace      | JSON Object       | The new workspace to move the file into as part of ingesting.                  |
|                    |                   | (See :ref:`Workspace Details <rest_workspace_details>`)                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| job                | JSON Object       | The ID of the ingest job.                                                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ingest_started     | ISO-8601 Datetime | When the ingest was started.                                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ingest_ended       | ISO-8601 Datetime | When the ingest ended.                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| source_file        | JSON Object       | A reference to the source file that was stored by this ingest.                 |
|                    |                   | (See :ref:`Source File Details <rest_source_file_details>`)                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| data_started       | ISO-8601 Datetime | The start time of the source data being ingested.                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| data_ended         | ISO-8601 Datetime | The end time of the source data being ingested.                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| created            | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| last_modified      | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+

.. _rest_v6_ingest_status:

v6 Ingest Status
----------------

**Example GET /v6/ingests/status/ API call**

Request: GET http://.../v6/ingests/status/

Response: 200 OK

 .. code-block:: javascript  
 
    { 
        "count": 2, 
        "next": null, 
        "previous": null, 
        "results": [ 
            { 
                "strike": { 
                    "id": 1, 
                    "name": "my-strike", 
                    "title": "My Strike Processor", 
                    "description": "This Strike process handles the data feed", 
                    "job": { 
                        "id": 4, 
                        "job_type": { 
                            "id": 2, 
                            "name": "scale-strike",
                            "version": "1.0.0",
                            "title": "Scale Strike", 
                            "description": "Monitors a directory for incoming source files to ingest", 
                            "revision_num": 1,
                            "icon_code": "f013" 
                        }, 
                        "event": { 
                            "id": 5 
                        }, 
                        "error": null, 
                        "status": "RUNNING", 
                        "priority": 5, 
                        "num_exes": 36 
                    }, 
                    "created": "2015-10-05T17:35:46.690Z", 
                    "last_modified": "2015-10-05T17:35:46.740Z" 
                }, 
                "most_recent": "2015-10-21T21:15:56.522Z", 
                "files": 1234, 
                "size": 12345678900000, 
                "values": [ 
                    { 
                        "time": "2015-10-21T00:00:00Z", 
                        "files": 10, 
                        "size": 123456789 
                    }, 
                    ... 
                ] 
            } 
        ] 
    } 

+-------------------------------------------------------------------------------------------------------------------------+
| **Ingest Status**                                                                                                       |
+=========================================================================================================================+
| Returns status summary information (counts, file sizes) for completed ingests grouped into 1 hour time slots.           |
| NOTE: Time range must be within a one month period (31 days).                                                           |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/ingests/status/                                                                                             |
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
