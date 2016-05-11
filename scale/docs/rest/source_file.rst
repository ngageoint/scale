
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
| Returns a specific source file and all its related model information including ingests and derived products.            |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /sources/{id}/                                                                                                  |
|         Where {id} is the unique identifier of an existing model.                                                       |
+--------------------+----------------------------------------------------------------------------------------------------+
| **GET** /sources/{file_name}/                                                                                           |
|         Where {file_name} is the unique name of a source file associated with an existing model.                        |
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
|                    |                   | (See :ref:`Ingest Details <rest_ingest_details>`)                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| products           | Array             | A list of all product files derived from this source file during jobs.         |
|                    |                   | (See :ref:`Product Details <rest_product_details>`)                            |
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
