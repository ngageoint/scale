
.. _rest_product:

Product Services
========================================================================================================================

These services provide access to information about products that Scale has produced.

+-------------------------------------------------------------------------------------------------------------------------+
| **Product List**                                                                                                        |
+=========================================================================================================================+
| Returns a list of all products                                                                                          |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /products/                                                                                                      |
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
| job_type_id        | Integer           | Optional | Return only jobs with a given job type identifier.                  |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_name      | String            | Optional | Return only jobs with a given job type name.                        |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_category  | String            | Optional | Return only jobs with a given job type category.                    |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| is_operational     | Boolean           | Optional | Return only products flagged as operational status versus R&D.      |
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
| .published         | ISO-8601 Datetime | When the product file was originally published by Scale.                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .unpublished       | ISO-8601 Datetime | When the product file was unpublished by Scale.                                |
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
|                "published": "1970-01-01T00:00:00Z",                                                                     | 
|                "unpublished": null,                                                                                     | 
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
|                }                                                                                                        |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_product_updates:

+-------------------------------------------------------------------------------------------------------------------------+
| **Product Updates**                                                                                                     |
+=========================================================================================================================+
| Returns the product updates (published, unpublished, and deleted products) that have occurred in the given time range.  |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /products/updates/                                                                                              |
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
| job_type_id        | Integer           | Optional | Return only jobs with a given job type identifier.                  |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_name      | String            | Optional | Return only jobs with a given job type name.                        |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_category  | String            | Optional | Return only jobs with a given job type category.                    |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| is_operational     | Boolean           | Optional | Return only products flagged as operational status versus R&D.      |
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
| .published         | ISO-8601 Datetime | When the product file was originally published by Scale.                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .unpublished       | ISO-8601 Datetime | When the product file was unpublished by Scale.                                |
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
| .update            | JSON Object       | Contains the details of this update.                                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..action           | String            | The product update that occurred.                                              |
|                    |                   | Choices: [PUBLISHED, UNPUBLISHED, DELETED].                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..when             | ISO-8601 Datetime | When the action occurred.                                                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .source_files      | Array             | List of source files involved in the creation of this product.                 |
|                    |                   | (See :ref:`Source File Details <rest_source_file_details>`)                    |
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
|                "published": "1970-01-01T00:00:00Z",                                                                     | 
|                "unpublished": null,                                                                                     | 
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
|                "update": {                                                                                              |
|                    "action": "PUBLISHED",                                                                               | 
|                    "when": "1970-01-01T00:00:00Z"                                                                       |
|                },                                                                                                       |
|                "source_files": [                                                                                        |
|                    {                                                                                                    |
|                        "id": 464,                                                                                       | 
|                        "workspace": {                                                                                   |
|                            "id": 2,                                                                                     |
|                            "name": "Raw Source"                                                                         |
|                        },                                                                                               |
|                        "file_name": "my_file.h5",                                                                       |
|                        "media_type": "image/x-hdf5-image",                                                              | 
|                        "file_size": 100,                                                                                | 
|                        "data_type": [],                                                                                 |
|                        "is_deleted": false,                                                                             | 
|                        "uuid": "3d8e577bddb17db339eae0b3d9bcf180",                                                      | 
|                        "url": "http://host.com/file/path/my_file.h5",                                                   | 
|                        "created": "1970-01-01T00:00:00Z",                                                               |
|                        "deleted": null,                                                                                 | 
|                        "data_started": null,                                                                            | 
|                        "data_ended": null,                                                                              | 
|                        "geometry": null,                                                                                | 
|                        "center_point": null,                                                                            | 
|                        "meta_data": {...},                                                                              | 
|                        "countries": ["TCY", "TCT"],                                                                     | 
|                        "last_modified": "1970-01-01T00:00:00Z",                                                         |
|                        "is_parsed": true,                                                                               | 
|                        "parsed": "1970-01-01T00:00:00Z"                                                                 |
|                    }                                                                                                    |
|                ]                                                                                                        |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_product_details:
