
.. _rest_v6_scale_file:

v6 Scale File Services
========================================================================================================================

These services provide access to information about general files that are being tracked by Scale.

.. _rest_v6_scale_files:

v6 Scale Files
----------------------

**Example GET /v6/files/ API call**

Request: GET http://.../v6/files/

Response: 200 OK

 .. code-block:: javascript  
    { 
        "count": 55, 
        "next": null, 
        "previous": null, 
        "results": [ 
            { 
                "id": 465, 
                "workspace": { 
                    "id": 2, 
                    "name": "Products" 
                }, 
                "file_name": "my_file.kml", 
                "media_type": "application/vnd.google-earth.kml+xml", 
                "file_size": 100, 
                "data_type": [], 
                "is_deleted": false, 
                "url": "http://host.com/file/path/my_file.kml", 
                "created": "1970-01-01T00:00:00Z", 
                "deleted": null, 
                "data_started": null, 
                "data_ended": null, 
                "geometry": null, 
                "center_point": null, 
                "meta_data": {...}, 
                "countries": ["TCY", "TCT"], 
                "last_modified": "1970-01-01T00:00:00Z", 
                "is_operational": true, 
                "is_published": true, 
                "has_been_published": true, 
                "published": "1970-01-01T00:00:00Z", 
                "unpublished": null, 
                "source_started": "1970-01-01T00:00:00Z", 
                "source_ended": "1970-01-02T00:00:00Z", 
                "job_type": { 
                    "id": 8, 
                    "name": "kml-footprint", 
                    "version": "1.0.0", 
                    "title": "KML Footprint", 
                    "description": "Creates a KML file.", 
                    "category": "footprint", 
                    "author_name": null, 
                    "author_url": null, 
                    "is_system": false, 
                    "is_long_running": false, 
                    "is_active": true, 
                    "is_operational": true, 
                    "is_paused": false, 
                    "icon_code": "f0ac" 
                }, 
                "job": { 
                    "id": 47 
                }, 
                "job_exe": { 
                    "id": 49 
                },
                "job_output": "output_name_1",
                "recipe": { 
                    "id": 60 
                }, 
                "recipe_job": "kml-footprint",
                "recipe_type": { 
                    "id": 6, 
                    "name": "my-recipe", 
                    "version": "1.0.0", 
                    "title": "My Recipe", 
                    "description": "Processes some data", 
                }, 
                "batch": { 
                    "id": 15, 
                    "title": "My Batch", 
                    "description": "My batch of recipes", 
                    "status": "SUBMITTED", 
                    "recipe_type": 6, 
                    "event": 19, 
                    "creator_job": 62, 
                }, 
                "is_superseded": true, 
                "superseded": "1970-01-01T00:00:00Z", 
            }, 
            ... 
        ] 
    } 
    
+-------------------------------------------------------------------------------------------------------------------------+
| **Scale Files**                                                                                                         |
+=========================================================================================================================+
| Returns detailed information about files associated with Scale.                                                         |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /files/                                                                                                         |
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
| job_type_id        | Integer           | Optional | Return only products associated with a given job type identifier.   |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_name      | String            | Optional | Return only products with a given job type name.                    |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_id             | Integer           | Optional | Return only products produced by the given job identifier.          |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
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
| is_published       | Boolean           | Optional | Return only products flagged as currently exposed for publication.  |
|                    |                   |          | Default is True, include only published products.                   |
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
| .file_name         | String            | The name of the file.                                                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .media_type        | String            | The IANA media type of the file.                                               |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .file_size         | Integer           | The size of the file in bytes.                                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .data_type         | Array             | List of strings describing the data type of the file.                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .is_deleted        | Boolean           | Whether the file has been deleted.                                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .url               | URL               | The absolute URL to use for downloading the file.                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .created           | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .deleted           | ISO-8601 Datetime | When the file was deleted.                                                     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .data_started      | ISO-8601 Datetime | When collection of the underlying data file started.                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .data_ended        | ISO-8601 Datetime | When collection of the underlying data file ended.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .geometry          | WKT String        | The full geospatial geometry footprint of the file.                            |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .center_point      | WKT String        | The central geospatial location of the file.                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .meta_data         | JSON Object       | A dictionary of key/value pairs that describe product-specific attributes.     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .countries         | Array             | A list of zero or more strings with the ISO3 country codes for countries       |
|                    |                   | contained in the geographic boundary of this file.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .last_modified     | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .source_started    | ISO-8601 Datetime | When collection of the underlying source file started.                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .source_ended      | ISO-8601 Datetime | When collection of the underlying source file ended.                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .job_type          | JSON Object       | The type of job that generated the file.                                       |
|                    |                   | (See :ref:`Job Type Details <rest_job_type_details>`)                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .job               | JSON Object       | The job instance that generated the file.                                      |
|                    |                   | (See :ref:`Job Details <rest_job_details>`)                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .job_exe           | JSON Object       | The specific job execution that generated the product.                         |
|                    |                   | (See :ref:`Job Execution Details <rest_job_execution_details>`)                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .job_output        | String            | The name of the output from the job related to this file.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .recipe            | JSON Object       | The recipe instance that generated the file.                                   |
|                    |                   | (See :ref:`Recipe Details <rest_recipe_details>`)                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .recipe_job        | String            | The recipe job that produced this file.                                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .recipe_type       | JSON Object       | The type of recipe that generated the file.                                    |
|                    |                   | (See :ref:`Recipe Type Details <rest_recipe_type_details>`)                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .batch             | JSON Object       | The batch instance that generated the file.                                    |
|                    |                   | (See :ref:`Batch Details <rest_batch_details>`)                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .is_superseded     | Boolean           | Whether this file has been replaced and is now obsolete.                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .superseded        | ISO-8601 Datetime | When the file became superseded by another file.                               |
+--------------------+-------------------+--------------------------------------------------------------------------------+