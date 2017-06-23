
.. _rest_source_file:

Source File Services
========================================================================================================================

These services provide access to information about source files that Scale has ingested.

+-------------------------------------------------------------------------------------------------------------------------+
| **Source File List**                                                                                                    |
+=========================================================================================================================+
| Returns a list of all source files                                                                                      |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /sources/                                                                                                       |
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
| time_field         | String            | Optional | Indicates the time field(s) that *started* and *ended* will use for |
|                    |                   |          | time filtering. Valid values are:                                   |
|                    |                   |          |                                                                     |
|                    |                   |          | - *last_modified* - last modification of source file meta-data      |
|                    |                   |          | - *data* - data time of source file (*data_started*, *data_ended*)  |
|                    |                   |          |                                                                     |
|                    |                   |          | The default value is *last_modified*.                               |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| order              | String            | Optional | One or more fields to use when ordering the results.                |
|                    |                   |          | Duplicate it to multi-sort, (ex: order=file_name&order=created).    |
|                    |                   |          | Nested objects require a delimiter (ex: order=job_type__name).      |
|                    |                   |          | Prefix fields with a dash to reverse the sort, (ex: order=-created).|
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| is_parsed          | Boolean           | Optional | Return only sources flagged as successfully parsed.                 |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| file_name          | String            | Optional | Return only sources with a given file name.                         |
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
|                    |                   | (See :ref:`Source File Details <rest_source_file_details>`)                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .workspace         | JSON Object       | The workspace that has stored the source file.                                 |
|                    |                   | (See :ref:`Workspace Details <rest_workspace_details>`)                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .file_name         | String            | The name of the source file.                                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .media_type        | String            | The IANA media type of the source file.                                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .file_size         | Integer           | The size of the source file in bytes.                                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .data_type         | Array             | List of strings describing the data type of the source.                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .is_deleted        | Boolean           | Whether the source file has been deleted.                                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .uuid              | String            | A unique identifier that stays stable across multiple job execution runs.      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .url               | URL               | The absolute URL to use for downloading the file.                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .created           | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .deleted           | ISO-8601 Datetime | When the source file was deleted.                                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .data_started      | ISO-8601 Datetime | When collection of the underlying data file started.                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .data_ended        | ISO-8601 Datetime | When collection of the underlying data file ended.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .geometry          | WKT String        | The full geospatial geometry footprint of the source.                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .center_point      | WKT String        | The central geospatial location of the source.                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .meta_data         | JSON Object       | A dictionary of key/value pairs that describe source-specific attributes.      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .countries         | Array             | A list of zero or more strings with the ISO3 country codes for countries       |
|                    |                   | contained in the geographic boundary of this file.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .last_modified     | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .is_parsed         | Boolean           | Whether this source was successfully parsed.                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .parsed            | ISO-8601 Datetime | When the source file was originally parsed by Scale.                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "count": 55,                                                                                                     |
|        "next": null,                                                                                                    |
|        "previous": null,                                                                                                |
|        "results": [                                                                                                     |
|            {                                                                                                            |
|                "id": 465,                                                                                               | 
|                "workspace": {                                                                                           |
|                    "id": 1,                                                                                             |
|                    "name": "Raw Source"                                                                                 |
|                },                                                                                                       |
|                "file_name": "my_file.kml",                                                                              | 
|                "media_type": "application/vnd.google-earth.kml+xml",                                                    | 
|                "file_size": 100,                                                                                        | 
|                "data_type": [],                                                                                         |
|                "is_deleted": false,                                                                                     |
|                "uuid": "c8928d9183fc99122948e7840ec9a0fd",                                                              | 
|                "url": "http://host.com/file/path/my_file.kml",                                                          | 
|                "created": "1970-01-01T00:00:00Z",                                                                       | 
|                "deleted": null,                                                                                         | 
|                "data_started": null,                                                                                    | 
|                "data_ended": null,                                                                                      | 
|                "geometry": null,                                                                                        | 
|                "center_point": null,                                                                                    | 
|                "meta_data": {...},                                                                                      | 
|                "countries": ["TCY", "TCT"],                                                                             | 
|                "last_modified": "1970-01-01T00:00:00Z",                                                                 | 
|                "is_parsed": true,                                                                                       | 
|                "parsed": "1970-01-01T00:00:00Z"                                                                         | 
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_source_file_details:

+-------------------------------------------------------------------------------------------------------------------------+
| **Source File Details**                                                                                                 |
+=========================================================================================================================+
| Returns a specific source file and all its related model information including ingests and derived products. Associated |
| products that are superseded are excluded by default.                                                                   |
+-------------------------------------------------------------------------------------------------------------------------+
| **DEPRECATED**                                                                                                          |
|                This table describes the current v4 version of the source file details API, which is now deprecated.     |
|                The new v5 version of this API does not include the *ingests* and *products* arrays in the response.     |
|                The new v5 version also does not support the use of *file_name* in the URL (only source ID supported).   |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /sources/{id}/                                                                                                  |
|         Where {id} is the unique identifier of an existing model.                                                       |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /sources/{file_name}/                                                                                           |
|         Where {file_name} is the unique name of a source file associated with an existing model.                        |
|         *DEPRECATED*: removed in v5                                                                                     |
+-------------------------------------------------------------------------------------------------------------------------+
| **Query Parameters**                                                                                                    |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| include_superseded | Boolean           | Optional | Whether to include superseded products. Defaults to false.          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
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
| workspace          | JSON Object       | The workspace that has stored the source file.                                 |
|                    |                   | (See :ref:`Workspace Details <rest_workspace_details>`)                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| file_name          | String            | The name of the source file.                                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| media_type         | String            | The IANA media type of the source file.                                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| file_size          | Integer           | The size of the source file in bytes.                                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| data_type          | Array             | List of strings describing the data type of the source file.                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| is_deleted         | Boolean           | Whether the source file has been deleted.                                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| uuid               | String            | A unique identifier that stays stable across multiple job execution runs.      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| url                | URL               | The absolute URL to use for downloading the file.                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| created            | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| deleted            | ISO-8601 Datetime | When the source file was deleted.                                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| data_started       | ISO-8601 Datetime | When collection of the underlying data file started.                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| data_ended         | ISO-8601 Datetime | When collection of the underlying data file ended.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| geometry           | WKT String        | The full geospatial geometry footprint of the source file.                     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| center_point       | WKT String        | The central geospatial location of the source file.                            |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| meta_data          | JSON Object       | A dictionary of key/value pairs that describe source-specific attributes.      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| countries          | Array             | A list of zero or more strings with the ISO3 country codes for countries       |
|                    |                   | contained in the geographic boundary of this file.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| last_modified      | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| is_parsed          | Boolean           | Whether this source file was successfully parsed and ingested into the system. |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| parsed             | ISO-8601 Datetime | When the source file was originally parsed by Scale.                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ingests            | Array             | A list of records that represent each attempt to parse and ingest the file.    |
|                    |                   | (See :ref:`Ingest Details <rest_ingest_details>`) (*DEPRECATED*, gone in v5)   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| products           | Array             | A list of all product files derived from this source file during jobs.         |
|                    |                   | (See :ref:`Product Details <rest_product_details>`) (*DEPRECATED*, gone in v5) |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "id": 1,                                                                                                         |
|        "workspace": {                                                                                                   |
|            "id": 1,                                                                                                     |
|            "name": "Raw Source"                                                                                         |
|        },                                                                                                               |
|        "file_name": "my_file.kml",                                                                                      |
|        "media_type": "application/vnd.google-earth.kml+xml",                                                            |
|        "file_size": 100,                                                                                                |
|        "data_type": [],                                                                                                 |
|        "is_deleted": false,                                                                                             |
|        "uuid": "c8928d9183fc99122948e7840ec9a0fd",                                                                      |
|        "url": "http://host.com/file/path/my_file.kml",                                                                  |
|        "created": "1970-01-01T00:00:00Z",                                                                               |
|        "deleted": null,                                                                                                 |
|        "data_started": null,                                                                                            |
|        "data_ended": null,                                                                                              |
|        "geometry": null,                                                                                                |
|        "center_point": null,                                                                                            |
|        "meta_data": {},                                                                                                 |
|        "countries": [],                                                                                                 |
|        "last_modified": "1970-01-01T00:00:00Z",                                                                         |
|        "is_parsed": true,                                                                                               |
|        "parsed": "1970-01-01T00:00:00Z",                                                                                |
|        "ingests": [                                                                                                     |
|            {                                                                                                            |
|                "id": 1,                                                                                                 |
|                "file_name": "my_file.kml",                                                                              |
|                "strike": {                                                                                              |
|                    "id": 1                                                                                              |
|                },                                                                                                       |
|                "status": "INGESTED",                                                                                    |
|                "bytes_transferred": 100,                                                                                |
|                "transfer_started": "1970-01-01T00:00:00Z",                                                              |
|                "transfer_ended": "1970-01-01T00:00:00Z",                                                                |
|                "media_type": "application/vnd.google-earth.kml+xml",                                                    |
|                "file_size": 4806986,                                                                                    |
|                "data_type": [],                                                                                         |
|                "ingest_started": "1970-01-01T00:00:00Z",                                                                |
|                "ingest_ended": "1970-01-01T00:00:00Z",                                                                  |
|                "source_file": {                                                                                         |
|                    "id": 1                                                                                              |
|                },                                                                                                       |
|                "created": "1970-01-01T00:00:00Z",                                                                       |
|                "last_modified": "1970-01-01T00:00:00Z"                                                                  |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ],                                                                                                               |
|        "products": [                                                                                                    |
|            {                                                                                                            |
|                "id": 2,                                                                                                 |
|                "workspace": {                                                                                           |
|                    "id": 2,                                                                                             |
|                    "name": "Products"                                                                                   |
|                },                                                                                                       |
|                "file_name": "my_file.png",                                                                              |
|                "media_type": "image/png",                                                                               |
|                "file_size": 50,                                                                                         |
|                "data_type": [],                                                                                         |
|                "is_deleted": false,                                                                                     |
|                "uuid": "03696f8c30b1757c9108fb9a7d67924f",                                                              |
|                "url": "http://host.com/file/path/my_file.png",                                                          |
|                "created": "1970-01-01T00:00:00Z",                                                                       |
|                "deleted": null,                                                                                         |
|                "data_started": "1970-01-01T00:00:00Z",                                                                  |
|                "data_ended": null,                                                                                      |
|                "geometry": null,                                                                                        |
|                "center_point": null,                                                                                    |
|                "meta_data": null,                                                                                       |
|                "countries": [],                                                                                         |
|                "last_modified": "1970-01-01T00:00:00Z",                                                                 |
|                "is_operational": true,                                                                                  |
|                "is_published": true,                                                                                    |
|                "published": "1970-01-01T00:00:00Z",                                                                     |
|                "unpublished": null,                                                                                     |
|                "is_superseded": false,                                                                                  |
|                "superseded": null,                                                                                      |
|                "job_type": {                                                                                            |
|                    "id": 6,                                                                                             |
|                    "name": "kml-parse",                                                                                 |
|                    "version": "1.0.0",                                                                                  |
|                    "title": "KML Parse",                                                                                |
|                    "description": "Parse KML into a PNG image",                                                         |
|                    "category": null,                                                                                    |
|                    "author_name": null,                                                                                 |
|                    "author_url": null,                                                                                  |
|                    "is_system": false,                                                                                  |
|                    "is_long_running": false,                                                                            |
|                    "is_active": true,                                                                                   |
|                    "is_operational": true,                                                                              |
|                    "is_paused": false,                                                                                  |
|                    "icon_code": null                                                                                    |
|                },                                                                                                       |
|                "job": {                                                                                                 |
|                    "id": 6                                                                                              |
|                },                                                                                                       |
|                "job_exe": {                                                                                             |
|                    "id": 6                                                                                              |
|                }                                                                                                        |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_source_file_ingests:

+-------------------------------------------------------------------------------------------------------------------------+
| **Source File Ingest List**                                                                                             |
+=========================================================================================================================+
| Returns a list of all ingests related to the source file with the given ID.                                             |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /sources/{id}/ingests/                                                                                          |
|         Where {id} is the unique identifier of an existing source file                                                  |
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
|                "scan": null,                                                                                            |
|                "strike": {                                                                                              |
|                    "id": 1,                                                                                             |
|                    "name": "my-strike",                                                                                 |
|                    "title": "My Strike Processor",                                                                      |
|                    "description": "This Strike process handles the data feed",                                          |
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
|                "file_path": "the/current/path/file_name.txt",                                                           |
|                "workspace": {                                                                                           |
|                    "id": 1,                                                                                             |
|                    "name": "my-workspace",                                                                              |
|                    "title": "My Workspace",                                                                             |
|                    "description": "My Workspace",                                                                       |
|                    "base_url": "http://host.com/wk",                                                                    |
|                    "is_active": true,                                                                                   |
|                    "used_size": 0,                                                                                      |
|                    "total_size": 0,                                                                                     |
|                    "created": "2015-10-05T21:26:04.855Z",                                                               |
|                    "archived": null,                                                                                    |
|                    "last_modified": "2015-10-05T21:26:04.855Z"                                                          |
|                },                                                                                                       |
|                "new_file_path": "the/new/path/file_name.txt",                                                           |
|                "new_workspace": {                                                                                       |
|                    "id": 1,                                                                                             |
|                    "name": "my-new-workspace",                                                                          |
|                    "title": "My New Workspace",                                                                         |
|                    "description": "My New Workspace",                                                                   |
|                    "base_url": "http://host.com/new-wk",                                                                |
|                    "is_active": true,                                                                                   |
|                    "used_size": 0,                                                                                      |
|                    "total_size": 0,                                                                                     |
|                    "created": "2015-10-05T21:26:04.855Z",                                                               |
|                    "archived": null,                                                                                    |
|                    "last_modified": "2015-10-05T21:26:04.855Z"                                                          |
|                },                                                                                                       |
|                "job": {                                                                                                 |
|                    "id": 1234                                                                                           |
|                },                                                                                                       |
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
|                "data_started": "2015-09-10T15:24:53.503Z",                                                              |
|                "data_ended": "2015-09-10T15:24:53.987Z",                                                                |
|                "created": "2015-09-10T15:24:47.412Z",                                                                   |
|                "last_modified": "2015-09-10T15:24:53.987Z"                                                              |
|            },                                                                                                           |
|           ...                                                                                                           |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+


.. _rest_source_file_jobs:

+-------------------------------------------------------------------------------------------------------------------------+
| **Source File Job List**                                                                                                |
+=========================================================================================================================+
| Returns a list of all jobs related to the source file with the given ID. Jobs marked as superseded are excluded by      |
| default.                                                                                                                |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /sources/{id}/jobs/                                                                                             |
|         Where {id} is the unique identifier of an existing source file                                                  |
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
|                    |                   |          | Duplicate it to multi-sort, (ex: order=name&order=version).         |
|                    |                   |          | Prefix fields with a dash to reverse the sort, (ex: order=-name).   |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| status             | String            | Optional | Return only jobs with a status matching this string.                |
|                    |                   |          | Choices: [QUEUED, RUNNING, FAILED, COMPLETED, CANCELED].            |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_id             | Integer           | Optional | Return only jobs with a given identifier.                           |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_id        | Integer           | Optional | Return only jobs with a given job type identifier.                  |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_name      | String            | Optional | Return only jobs with a given job type name.                        |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_category  | String            | Optional | Return only jobs with a given job type category.                    |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| error_category     | String            | Optional | Return only jobs that failed due to an error with a given category. |
|                    |                   |          | Choices: [SYSTEM, DATA, ALGORITHM].                                 |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| include_superseded | Boolean           | Optional | Whether to include superseded job instances. Defaults to false.     |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| count               | Integer           | The total number of results that match the query parameters.                  |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| next                | URL               | A URL to the next page of results.                                            |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| previous            | URL               | A URL to the previous page of results.                                        |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| results             | Array             | List of result JSON objects that match the query parameters.                  |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .id                 | Integer           | The unique identifier of the model. Can be passed to the details API call.    |
|                     |                   | (See :ref:`Job Details <rest_job_details>`)                                   |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .job_type           | JSON Object       | The job type that is associated with the job.                                 |
|                     |                   | (See :ref:`Job Type Details <rest_job_type_details>`)                         |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .job_type_rev       | JSON Object       | The job type revision that is associated with the job.                        |
|                     |                   | This represents the definition at the time the job was scheduled.             |
|                     |                   | (See :ref:`Job Type Revision Details <rest_job_type_rev_details>`)            |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .event              | JSON Object       | The trigger event that is associated with the job.                            |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .error              | JSON Object       | The error that is associated with the job.                                    |
|                     |                   | (See :ref:`Error Details <rest_error_details>`)                               |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .status             | String            | The current status of the job.                                                |
|                     |                   | Choices: [QUEUED, RUNNING, FAILED, COMPLETED, CANCELED].                      |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .priority           | Integer           | The priority of the job.                                                      |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .num_exes           | Integer           | The number of executions this job has had.                                    |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .timeout            | Integer           | The maximum amount of time this job can run before being killed (in seconds). |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .max_tries          | Integer           | The maximum number of times to attempt this job when failed (minimum one).    |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .cpus_required      | Decimal           | The number of CPUs needed for a job of this type.                             |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .mem_required       | Decimal           | The amount of RAM in MiB needed for a job of this type.                       |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .disk_in_required   | Decimal           | The amount of disk space in MiB required for input files for this job.        |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .disk_out_required  | Decimal           | The amount of disk space in MiB required for output files for this job.       |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .is_superseded      | Boolean           | Whether this job has been replaced and is now obsolete.                       |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .root_superseded_job| JSON Object       | The first job in the current chain of superseded jobs.                        |
|                     |                   | (See :ref:`Job Details <rest_job_details>`)                                   |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .superseded_job     | JSON Object       | The previous job in the chain that was superseded by this job.                |
|                     |                   | (See :ref:`Job Details <rest_job_details>`)                                   |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .superseded_by_job  | JSON Object       | The next job in the chain that superseded this job.                           |
|                     |                   | (See :ref:`Job Details <rest_job_details>`)                                   |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .delete_superseded  | Boolean           | Whether the products of the previous job should be deleted when superseded.   |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .created            | ISO-8601 Datetime | When the associated database model was initially created.                     |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .queued             | ISO-8601 Datetime | When the job was added to the queue to be run when resources are available.   |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .started            | ISO-8601 Datetime | When the job started running.                                                 |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .ended              | ISO-8601 Datetime | When the job stopped running, which could be due to success or failure.       |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .last_status_change | ISO-8601 Datetime | When the status of the job was last changed.                                  |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .superseded         | ISO-8601 Datetime | When the the job became superseded by another job.                            |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .last_modified      | ISO-8601 Datetime | When the associated database model was last saved.                            |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "count": 68,                                                                                                     |
|        "next": null,                                                                                                    |
|        "previous": null,                                                                                                |
|        "results": [                                                                                                     |
|            {                                                                                                            |
|                "id": 3,                                                                                                 |
|                "job_type": {                                                                                            |
|                    "id": 1,                                                                                             |
|                    "name": "scale-ingest",                                                                              |
|                    "version": "1.0",                                                                                    |
|                    "title": "Scale Ingest",                                                                             |
|                    "description": "Ingests a source file into a workspace",                                             |
|                    "is_system": true,                                                                                   |
|                    "is_long_running": false,                                                                            |
|                    "is_active": true,                                                                                   |
|                    "is_operational": true,                                                                              |
|                    "is_paused": false,                                                                                  |
|                    "icon_code": "f013"                                                                                  |
|                },                                                                                                       |
|                "job_type_rev": {                                                                                        |
|                    "id": 5,                                                                                             |
|                    "job_type": {                                                                                        |
|                        "id": 1                                                                                          |
|                    },                                                                                                   |
|                    "revision_num": 1                                                                                    |
|                },                                                                                                       |
|                "event": {                                                                                               |
|                    "id": 3,                                                                                             |
|                    "type": "STRIKE_TRANSFER",                                                                           |
|                    "rule": null,                                                                                        |
|                    "occurred": "2015-08-28T17:57:24.261Z"                                                               |
|                },                                                                                                       |
|                "error": null,                                                                                           |
|                "status": "COMPLETED",                                                                                   |
|                "priority": 10,                                                                                          |
|                "num_exes": 1,                                                                                           |
|                "timeout": 1800,                                                                                         |
|                "max_tries": 3,                                                                                          |
|                "cpus_required": 1.0,                                                                                    |
|                "mem_required": 64.0,                                                                                    |
|                "disk_in_required": 0.0,                                                                                 |
|                "disk_out_required": 64.0,                                                                               |
|                "is_superseded": false,                                                                                  |
|                "root_superseded_job": null,                                                                             |
|                "superseded_job": null,                                                                                  |
|                "superseded_by_job": null,                                                                               |
|                "delete_superseded": true,                                                                               |
|                "created": "2015-08-28T17:55:41.005Z",                                                                   |
|                "queued": "2015-08-28T17:56:41.005Z",                                                                    |
|                "started": "2015-08-28T17:57:41.005Z",                                                                   |
|                "ended": "2015-08-28T17:58:41.005Z",                                                                     |
|                "last_status_change": "2015-08-28T17:58:45.906Z",                                                        |
|                "superseded": null,                                                                                      |
|                "last_modified": "2015-08-28T17:58:46.001Z"                                                              |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_source_file_products:

+-------------------------------------------------------------------------------------------------------------------------+
| **Source File Product List**                                                                                            |
+=========================================================================================================================+
| Returns a list of all products that were produced by the given source file ID                                           |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /sources/{id}/products/                                                                                         |
|         Where {id} is the unique identifier of an existing source file                                                  |
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
| time_field         | String            | Optional | Indicates the time field(s) that *started* and *ended* will use for |
|                    |                   |          | time filtering. Valid values are:                                   |
|                    |                   |          |                                                                     |
|                    |                   |          | - *last_modified* - last modification of product file meta-data     |
|                    |                   |          | - *data* - data time of product file (*data_started*, *data_ended*) |
|                    |                   |          | - *source* - overall time for all associated source files           |
|                    |                   |          |              (*source_started*, *source_ended*)                     |
|                    |                   |          |                                                                     |
|                    |                   |          | The default value is *last_modified*.                               |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| order              | String            | Optional | One or more fields to use when ordering the results.                |
|                    |                   |          | Duplicate it to multi-sort, (ex: order=file_name&order=created).    |
|                    |                   |          | Nested objects require a delimiter (ex: order=job_type__name).      |
|                    |                   |          | Prefix fields with a dash to reverse the sort, (ex: order=-created).|
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_output         | String            | Optional | Return only products for the given job output.                      |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| recipe_id          | Integer           | Optional | Return only products produced by the given recipe identifier.       |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| recipe_job         | String            | Optional | Return only products produced by the given recipe job.              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| recipe_type_id     | Integer           | Optional | Return only products produced by the given recipe type identifier.  |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| batch_id           | Integer           | Optional | Return only products produced by the given batch identifier.        |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_id        | Integer           | Optional | Return only jobs with a given job type identifier.                  |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_name      | String            | Optional | Return only jobs with a given job type name.                        |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_category  | String            | Optional | Return only jobs with a given job type category.                    |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_id             | Integer           | Optional | Return only products produced by the given job identifier.          |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| is_operational     | Boolean           | Optional | Return only products flagged as operational status versus R&D.      |
|                    |                   |          | Default is include all types of products.                           |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| is_published       | Boolean           | Optional | Return only products flagged as currently exposed for publication.  |
|                    |                   |          | Default is include all products.                                    |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| file_name          | String            | Optional | Return only products with a given file name.                        |
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
|                    |                   | (See :ref:`Product Details <rest_product_details>`)                            |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .workspace         | JSON Object       | The workspace that has stored the product.                                     |
|                    |                   | (See :ref:`Workspace Details <rest_workspace_details>`)                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .file_name         | String            | The name of the product file.                                                  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .media_type        | String            | The IANA media type of the product file.                                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .file_size         | Integer           | The size of the product file in bytes.                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .data_type         | Array             | List of strings describing the data type of the product.                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .is_deleted        | Boolean           | Whether the product file has been deleted.                                     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .uuid              | String            | A unique identifier that stays stable across multiple job execution runs.      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .url               | URL               | The absolute URL to use for downloading the file.                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .created           | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .deleted           | ISO-8601 Datetime | When the product file was deleted.                                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .data_started      | ISO-8601 Datetime | When collection of the underlying data file started.                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .data_ended        | ISO-8601 Datetime | When collection of the underlying data file ended.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .geometry          | WKT String        | The full geospatial geometry footprint of the product.                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .center_point      | WKT String        | The central geospatial location of the product.                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .meta_data         | JSON Object       | A dictionary of key/value pairs that describe product-specific attributes.     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .countries         | Array             | A list of zero or more strings with the ISO3 country codes for countries       |
|                    |                   | contained in the geographic boundary of this file.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .last_modified     | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .is_operational    | Boolean           | Whether this product was produced by an operational job type or a job type     |
|                    |                   | still in research and development.                                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .is_published      | Boolean           | Whether the product file is currently published.                               |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .has_been_published| Boolean           | Whether the product file has ever been published.                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .published         | ISO-8601 Datetime | When the product file was originally published by Scale.                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .unpublished       | ISO-8601 Datetime | When the product file was unpublished by Scale.                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .source_started    | ISO-8601 Datetime | When collection of the underlying source file started.                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .source_ended      | ISO-8601 Datetime | When collection of the underlying source file ended.                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .job_type          | JSON Object       | The type of job that generated the product.                                    |
|                    |                   | (See :ref:`Job Type Details <rest_job_type_details>`)                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .job               | JSON Object       | The job instance that generated the product.                                   |
|                    |                   | (See :ref:`Job Details <rest_job_details>`)                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .job_exe           | JSON Object       | The specific job execution that generated the product.                         |
|                    |                   | (See :ref:`Job Execution Details <rest_job_execution_details>`)                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .recipe_type       | JSON Object       | The type of recipe that generated the product.                                 |
|                    |                   | (See :ref:`Recipe Type Details <rest_recipe_type_details>`)                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .recipe            | JSON Object       | The recipe instance that generated the product.                                |
|                    |                   | (See :ref:`Recipe Details <rest_recipe_details>`)                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .batch             | JSON Object       | The batch instance that generated the product.                                 |
|                    |                   | (See :ref:`Batch Details <rest_batch_details>`)                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "count": 55,                                                                                                     |
|        "next": null,                                                                                                    |
|        "previous": null,                                                                                                |
|        "results": [                                                                                                     |
|            {                                                                                                            |
|                "id": 465,                                                                                               |
|                "workspace": {                                                                                           |
|                    "id": 2,                                                                                             |
|                    "name": "Products"                                                                                   |
|                },                                                                                                       |
|                "file_name": "my_file.kml",                                                                              |
|                "media_type": "application/vnd.google-earth.kml+xml",                                                    |
|                "file_size": 100,                                                                                        |
|                "data_type": [],                                                                                         |
|                "is_deleted": false,                                                                                     |
|                "uuid": "c8928d9183fc99122948e7840ec9a0fd",                                                              |
|                "url": "http://host.com/file/path/my_file.kml",                                                          |
|                "created": "1970-01-01T00:00:00Z",                                                                       |
|                "deleted": null,                                                                                         |
|                "data_started": null,                                                                                    |
|                "data_ended": null,                                                                                      |
|                "geometry": null,                                                                                        |
|                "center_point": null,                                                                                    |
|                "meta_data": {...},                                                                                      |
|                "countries": ["TCY", "TCT"],                                                                             |
|                "last_modified": "1970-01-01T00:00:00Z",                                                                 |
|                "is_operational": true,                                                                                  |
|                "is_published": true,                                                                                    |
|                "has_been_published": true,                                                                              |
|                "published": "1970-01-01T00:00:00Z",                                                                     |
|                "unpublished": null,                                                                                     |
|                "source_started": "1970-01-01T00:00:00Z",                                                                |
|                "source_ended": "1970-01-02T00:00:00Z",                                                                  |
|                "job_type": {                                                                                            |
|                    "id": 8,                                                                                             |
|                    "name": "kml-footprint",                                                                             |
|                    "version": "1.0.0",                                                                                  |
|                    "title": "KML Footprint",                                                                            |
|                    "description": "Creates a KML file.",                                                                |
|                    "category": "footprint",                                                                             |
|                    "author_name": null,                                                                                 |
|                    "author_url": null,                                                                                  |
|                    "is_system": false,                                                                                  |
|                    "is_long_running": false,                                                                            |
|                    "is_active": true,                                                                                   |
|                    "is_operational": true,                                                                              |
|                    "is_paused": false,                                                                                  |
|                    "icon_code": "f0ac"                                                                                  |
|                },                                                                                                       |
|                "job": {                                                                                                 |
|                    "id": 47                                                                                             |
|                },                                                                                                       |
|                "job_exe": {                                                                                             |
|                    "id": 49                                                                                             |
|                },                                                                                                       |
|                "recipe_type": {                                                                                         |
|                    "id": 6,                                                                                             |
|                    "name": "my-recipe",                                                                                 |
|                    "version": "1.0.0",                                                                                  |
|                    "title": "My Recipe",                                                                                |
|                    "description": "Processes some data",                                                                |
|                },                                                                                                       |
|                "recipe": {                                                                                              |
|                    "id": 60                                                                                             |
|                },                                                                                                       |
|                "batch": {                                                                                               |
|                    "id": 15,                                                                                            |
|                    "title": "My Batch",                                                                                 |
|                    "description": "My batch of recipes",                                                                |
|                    "status": "SUBMITTED",                                                                               |
|                    "recipe_type": 6,                                                                                    |
|                    "event": 19,                                                                                         |
|                    "creator_job": 62,                                                                                   |
|                },                                                                                                       |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_source_file_updates:

+-------------------------------------------------------------------------------------------------------------------------+
| **Source File Updates**                                                                                                 |
+=========================================================================================================================+
| Returns the source file updates (created, parsed, and deleted sources) that have occurred in the given time range.      |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /sources/updates/                                                                                               |
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
| time_field         | String            | Optional | Indicates the time field(s) that *started* and *ended* will use for |
|                    |                   |          | time filtering. Valid values are:                                   |
|                    |                   |          |                                                                     |
|                    |                   |          | - *last_modified* - last modification of source file meta-data      |
|                    |                   |          | - *data* - data time of source file (*data_started*, *data_ended*)  |
|                    |                   |          |                                                                     |
|                    |                   |          | The default value is *last_modified*.                               |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| order              | String            | Optional | One or more fields to use when ordering the results.                |
|                    |                   |          | Duplicate it to multi-sort, (ex: order=file_name&order=created).    |
|                    |                   |          | Nested objects require a delimiter (ex: order=job_type__name).      |
|                    |                   |          | Prefix fields with a dash to reverse the sort, (ex: order=-created).|
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| is_parsed          | Boolean           | Optional | Return only sources flagged as successfully parsed.                 |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| file_name          | String            | Optional | Return only sources with a given file name.                         |
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
|                    |                   | (See :ref:`Source File Details <rest_source_file_details>`)                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .workspace         | JSON Object       | The workspace that has stored the source file.                                 |
|                    |                   | (See :ref:`Workspace Details <rest_workspace_details>`)                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .file_name         | String            | The name of the source file.                                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .media_type        | String            | The IANA media type of the source file.                                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .file_size         | Integer           | The size of the source file in bytes.                                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .data_type         | Array             | List of strings describing the data type of the source.                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .is_deleted        | Boolean           | Whether the source file has been deleted.                                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .uuid              | String            | A unique identifier that stays stable across multiple job execution runs.      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .url               | URL               | The absolute URL to use for downloading the file.                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .created           | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .deleted           | ISO-8601 Datetime | When the source file was deleted.                                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .data_started      | ISO-8601 Datetime | When collection of the underlying data file started.                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .data_ended        | ISO-8601 Datetime | When collection of the underlying data file ended.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .geometry          | WKT String        | The full geospatial geometry footprint of the source.                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .center_point      | WKT String        | The central geospatial location of the source.                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .meta_data         | JSON Object       | A dictionary of key/value pairs that describe source-specific attributes.      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .countries         | Array             | A list of zero or more strings with the ISO3 country codes for countries       |
|                    |                   | contained in the geographic boundary of this file.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .last_modified     | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .is_parsed         | Boolean           | Whether this source was successfully parsed.                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .parsed            | ISO-8601 Datetime | When the source file was originally parsed by Scale.                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .update            | JSON Object       | Contains the details of this update.                                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..action           | String            | The source file update that occurred.                                          |
|                    |                   | Choices: [CREATED, PARSED, DELETED].                                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..when             | ISO-8601 Datetime | When the action occurred.                                                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "count": 55,                                                                                                     |
|        "next": null,                                                                                                    |
|        "previous": null,                                                                                                |
|        "results": [                                                                                                     |
|            {                                                                                                            |
|                "id": 465,                                                                                               | 
|                "workspace": {                                                                                           |
|                    "id": 2,                                                                                             |
|                    "name": "Raw Source"                                                                                 |
|                },                                                                                                       |
|                "file_name": "my_file.kml",                                                                              | 
|                "media_type": "application/vnd.google-earth.kml+xml",                                                    | 
|                "file_size": 100,                                                                                        | 
|                "data_type": [],                                                                                         |
|                "is_deleted": false,                                                                                     |
|                "uuid": "c8928d9183fc99122948e7840ec9a0fd",                                                              | 
|                "url": "http://host.com/file/path/my_file.kml",                                                          | 
|                "created": "1970-01-01T00:00:00Z",                                                                       | 
|                "deleted": null,                                                                                         | 
|                "data_started": null,                                                                                    | 
|                "data_ended": null,                                                                                      | 
|                "geometry": null,                                                                                        | 
|                "center_point": null,                                                                                    | 
|                "meta_data": {...},                                                                                      | 
|                "countries": ["TCY", "TCT"],                                                                             | 
|                "last_modified": "1970-01-01T00:00:00Z",                                                                 | 
|                "is_parsed": true,                                                                                       | 
|                "parsed": "1970-01-01T00:00:00Z",                                                                        | 
|                "update": {                                                                                              |
|                    "action": "PUBLISHED",                                                                               | 
|                    "when": "1970-01-01T00:00:00Z"                                                                       |
|                }                                                                                                        |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+
