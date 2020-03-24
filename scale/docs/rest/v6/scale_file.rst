
.. _rest_v6_scale_file:

v6 Scale File Services
======================

These services provide access to information about general files that are being tracked by Scale.

.. _rest_v6_scale_file_list:

v6 Scale Files
--------------

**Example GET /v6/files/ API call**

Request: GET http://.../v6/files/

Response: 200 OK

 .. code-block:: javascript  
 
    { 
        "count": 1, 
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
                "data_type_tags": [],
                "media_type": "application/vnd.google-earth.kml+xml", 
                "file_size": 100, 
                "is_deleted": false, 
                "url": "http://host.com/file/path/my_file.kml", 
                "created": "1970-01-01T00:00:00Z", 
                "deleted": null, 
                "data_started": "1970-01-01T00:00:00Z", 
                "data_ended": "1970-01-01T00:00:00Z", 
                "geometry": null, 
                "center_point": null, 
                "countries": ["TCY", "TCT"], 
                "last_modified": "1970-01-01T00:00:00Z", 
                "file_path": "path/to/the/file.png",
                "source_started": "1970-01-01T00:00:00Z", 
                "source_ended": "1970-01-02T00:00:00Z", 
                "source_sensor_class": "classA", 
                "source_sensor": "1", 
                "source_collection": "12345", 
                "source_task": "my-task", 
                "job": { 
                    "id": 47 
                }, 
                "job_exe": { 
                    "id": 49 
                },
                "job_output": "output_name_1",
                "job_type": { 
                    "id": 8, 
                    "name": "kml-footprint", 
                    "version": "1.0.0",
                    "title": "KML Footprint", 
                    "description": "Creates a KML file.",
                    "is_active": true,
                    "is_paused": false,
                    "is_published": true,
                    "icon_code": "f013",
                    "unmet_resources": "chocolate,vanilla"
                }, 
                "recipe": { 
                    "id": 60 
                }, 
                "recipe_node": "kml-footprint",
                "recipe_type": { 
                    "id": 6, 
                    "name": "my-recipe", 
                    "title": "My Recipe", 
                    "description": "Processes some data", 
                    "revision_num": 1
                }, 
                "batch": { 
                    "id": 15, 
                    "title": "My Batch", 
                    "description": "My batch of recipes", 
                    "created": "1970-01-01T00:00:00Z" 
                }, 
                "is_superseded": true, 
                "superseded": "1970-01-01T00:00:00Z"
            } 
        ] 
    } 

+---------------------------------------------------------------------------------------------------------------------------+
| **Scale Files**                                                                                                           |
+===========================================================================================================================+
| Returns detailed information about files associated with Scale.                                                           |
+---------------------------------------------------------------------------------------------------------------------------+
| **GET** /files/                                                                                                           |
+---------------------------------------------------------------------------------------------------------------------------+
| **Query Parameters**                                                                                                      |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| page                 | Integer           | Optional | The page of the results to return. Defaults to 1.                   |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| page_size            | Integer           | Optional | The size of the page to use for pagination of results.              |
|                      |                   |          | Defaults to 100, and can be anywhere from 1-1000.                   |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| data_started         | ISO-8601 Datetime | Optional | The start of the data time range to query.                          |
|                      |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                      |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| data_ended           | ISO-8601 Datetime | Optional | End of the data time range to query, defaults to the current time.  |
|                      |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                      |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| source_started       | ISO-8601 Datetime | Optional | The start of the source file time range to query.                   |
|                      |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                      |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| source_ended         | ISO-8601 Datetime | Optional | End of the source file time range to query, default is current time.|
|                      |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                      |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| source_sensor_class  | String            | Optional | Return only files for the given source sensor class                 |
|                      |                   |          | Duplicate it to filter by multiple values.                          |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| source_sensor        | String            | Optional | Return only files for the given source sensor                       |
|                      |                   |          | Duplicate it to filter by multiple values.                          |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| source_collection    | String            | Optional | Return only files for the given source collection                   |
|                      |                   |          | Duplicate it to filter by multiple values.                          |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| source_task          | String            | Optional | Return only files for the given source task                         |
|                      |                   |          | Duplicate it to filter by multiple values.                          |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| modified_started     | ISO-8601 Datetime | Optional | The start of the last modified time range to query.                 |
|                      |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                      |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| modified_ended       | ISO-8601 Datetime | Optional | End of the last modified time range to query (default current time) |
|                      |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                      |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| order                | String            | Optional | One or more fields to use when ordering the results.                |
|                      |                   |          | Duplicate it to multi-sort, (ex: order=file_name&order=created).    |
|                      |                   |          | Nested objects require a delimiter (ex: order=job_type__name).      |
|                      |                   |          | Prefix fields with a dash to reverse the sort, (ex: order=-created).|
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| job_output           | String            | Optional | Return only files for the given job output.                         |
|                      |                   |          | Duplicate it to filter by multiple values.                          |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_id          | Integer           | Optional | Return only files associated with a given job type identifier.      |
|                      |                   |          | Duplicate it to filter by multiple values.                          |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_name        | String            | Optional | Return only files with a given job type name.                       |
|                      |                   |          | Duplicate it to filter by multiple values.                          |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| job_id               | Integer           | Optional | Return only files produced by the given job identifier.             |
|                      |                   |          | Duplicate it to filter by multiple values.                          |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| recipe_id            | Integer           | Optional | Return only files produced by the given recipe identifier.          |
|                      |                   |          | Duplicate it to filter by multiple values.                          |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| recipe_node          | String            | Optional | Return only files produced by the given recipe node.                |
|                      |                   |          | Duplicate it to filter by multiple values.                          |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| recipe_type_id       | Integer           | Optional | Return only files produced by the given recipe type identifier.     |
|                      |                   |          | Duplicate it to filter by multiple values.                          |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| batch_id             | Integer           | Optional | Return only files produced by the given batch identifier.           |
|                      |                   |          | Duplicate it to filter by multiple values.                          |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| countries            | String            | Optional | Return only files associated with a given country.                  |
|                      |                   |          | Use country code style ISO3.                                        |
|                      |                   |          | Duplicate it to filter by multiple values.                          |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| file_name            | String            | Optional | Return only files with a given file name.                           |
|                      |                   |          | Duplicate it to filter by multiple values.                          |
+----------------------+-------------------+----------+---------------------------------------------------------------------+
| **Successful Response**                                                                                                   |
+--------------------+------------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                               |
+--------------------+------------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                   |
+--------------------+------------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                           |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| count                | Integer           | The total number of results that match the query parameters.                   |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| next                 | URL               | A URL to the next page of results.                                             |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| previous             | URL               | A URL to the previous page of results.                                         |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| results              | Array             | List of result JSON objects that match the query parameters.                   |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .id                  | Integer           | The unique identifier of the model. Can be passed to the details API call.     |
|                      |                   | (See :ref:`File Details <rest_v6_file_details>`)                               |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .workspace           | JSON Object       | The workspace that has stored the product.                                     |
|                      |                   | (See :ref:`Workspace Details <rest_v6_workspace_details>`)                     |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .file_name           | String            | The name of the file.                                                          |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .data_type_tags      | Array             | A list of string data type "tags" for the file.                                |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .media_type          | String            | The IANA media type of the file.                                               |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .file_size           | Integer           | The size of the file in bytes.                                                 |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .file_path           | String            | The relative path of the file in the workspace.                                |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .is_deleted          | Boolean           | Whether the file has been deleted.                                             |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .url                 | URL               | The absolute URL to use for downloading the file.                              |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .created             | ISO-8601 Datetime | When the associated database model was initially created.                      |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .deleted             | ISO-8601 Datetime | When the file was deleted.                                                     |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .data_started        | ISO-8601 Datetime | The start time of the source data being ingested.                              |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .data_ended          | ISO-8601 Datetime | The ended time of the source data being ingested.                              |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .geometry            | WKT String        | The full geospatial geometry footprint of the file.                            |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .center_point        | WKT String        | The central geospatial location of the file.                                   |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .countries           | Array             | A list of zero or more strings with the ISO3 country codes for countries       |
|                      |                   | contained in the geographic boundary of this file.                             |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .last_modified       | ISO-8601 Datetime | When the associated database model was last saved.                             |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .file_path           | String            | The relative path of the file in the workspace.                                |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .source_started      | ISO-8601 Datetime | When collection of the underlying source file started.                         |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .source_ended        | ISO-8601 Datetime | When collection of the underlying source file ended.                           |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .source_sensor_class | String            | The class of sensor used to produce the source file.                           |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .source_sensor       | String            | The specific identifier of the sensor used to produce the source file.         |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .source_collection   | String            | The collection of the source file.                                             |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .source_task         | String            | The task that produced the source file.                                        |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .job                 | JSON Object       | The job instance that generated the file.                                      |
|                      |                   | (See :ref:`Job Details <rest_v6_job_details>`)                                 |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .job_exe             | JSON Object       | The specific job execution that generated the file.                            |
|                      |                   | (See :ref:`Job Execution Details <rest_v6_job_execution_details>`)             |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .job_output          | String            | The name of the output from the job related to this file.                      |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .job_type            | JSON Object       | The type of job that generated the file.                                       |
|                      |                   | (See :ref:`Job Type Details <rest_v6_job_type_details>`)                       |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .recipe              | JSON Object       | The recipe instance that generated the file.                                   |
|                      |                   | (See :ref:`Recipe Details <rest_v6_recipe_details>`)                           |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .recipe_node         | String            | The recipe node that produced this file.                                       |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .recipe_type         | JSON Object       | The type of recipe that generated the file.                                    |
|                      |                   | (See :ref:`Recipe Type Details <rest_v6_recipe_type_details>`)                 |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .batch               | JSON Object       | The batch instance that generated the file.                                    |
|                      |                   | (See :ref:`Batch Details <rest_v6_batch_details>`)                             |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .is_superseded       | Boolean           | Whether this file has been replaced and is now obsolete.                       |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| .superseded          | ISO-8601 Datetime | When the file became superseded by another file.                               |
+----------------------+-------------------+--------------------------------------------------------------------------------+

.. _rest_v6_file_details:

v6 Scale File Details
---------------------

**Example GET /v6/files/{id}/ API call**

Request: GET http://.../v6/files/{id}/

Response: 200 OK

 .. code-block:: javascript 
 
    { 
        "id": 2, 
        "workspace": { 
            "id": 2, 
            "name": "Products" 
        }, 
        "file_name": "my_file2.png", 
        "data_type_tags": [],
        "media_type": "image/png", 
        "file_size": 50, 
        "is_deleted": false, 
        "url": "http://host.com/file/path/my_file2.png", 
        "created": "1970-01-01T00:00:00Z", 
        "deleted": null, 
        "data_started": "1970-01-01T00:00:00Z", 
        "data_ended": null, 
        "geometry": null, 
        "center_point": null, 
        "meta_data": null, 
        "countries": [], 
        "last_modified": "1970-01-01T00:00:00Z", 
        "file_path": "path/to/the/file.png",
        "source_started": "1970-01-01T00:00:00Z", 
        "source_ended": "1970-01-02T00:00:00Z", 
        "source_sensor_class": "classA", 
        "source_sensor": "1", 
        "source_collection": "12345", 
        "source_task": "my-task", 
        "job": { 
            "id": 4 
        }, 
        "job_exe": { 
            "id": 4 
        }, 
        "job_output": "output_name_1",
        "job_type": { 
            "id": 4, 
            "name": "png-filter", 
            "version": "1.0.0",
            "title": "PNG Filter", 
            "description": "Filters PNG images into a new PNG image", 
            "is_active": true,
            "is_paused": false,
            "is_published": true,
            "icon_code": "f013",
            "unmet_resources": "chocolate,vanilla"
        }, 
        "recipe": { 
            "id": 60 
        }, 
        "recipe_node": "kml-footprint",
        "recipe_type": { 
            "id": 6, 
            "name": "my-recipe", 
            "title": "My Recipe", 
            "description": "Processes some data", 
            "revision_num": 1
        }, 
        "batch": { 
            "id": 15, 
            "title": "My Batch", 
            "description": "My batch of recipes", 
            "created": "1970-01-01T00:00:00Z" 
        },
        "is_superseded": true, 
        "superseded": "1970-01-01T00:00:00Z"
    } 
    
+---------------------------------------------------------------------------------------------------------------------------+
| **File Details**                                                                                                          |
+===========================================================================================================================+
| Returns a specific file and all its related model information.                                                            |
+---------------------------------------------------------------------------------------------------------------------------+
| **GET** /files/{id}/                                                                                                      |
|         Where {id} is the unique identifier of an existing model.                                                         |
+---------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                   |
+--------------------+------------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                               |
+--------------------+------------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                   |
+--------------------+------------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                           |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| id                   | Integer           | The unique identifier of the model.                                            |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| workspace            | JSON Object       | The workspace that has stored the product file.                                |
|                      |                   | (See :ref:`Workspace Details <rest_v6_workspace_details>`)                     |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| file_name            | String            | The name of the file.                                                          |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| data_type_tags       | Array             | A list of string data type "tags" for the file.                                |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| media_type           | String            | The IANA media type of the file.                                               |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| file_size            | Integer           | The size of the file in bytes.                                                 |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| file_path            | String            | The relative path of the file in the workspace.                                |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| is_deleted           | Boolean           | Whether the file has been deleted.                                             |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| url                  | URL               | The absolute URL to use for downloading the file.                              |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| created              | ISO-8601 Datetime | When the associated database model was initially created.                      |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| deleted              | ISO-8601 Datetime | When the file was deleted.                                                     |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| data_started         | ISO-8601 Datetime | The start time of the source data being ingested.                              |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| data_ended           | ISO-8601 Datetime | The ended time of the source data being ingested.                              |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| geometry             | WKT String        | The full geospatial geometry footprint of the file.                            |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| center_point         | WKT String        | The central geospatial location of the file.                                   |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| meta_data            | JSON Object       | A dictionary of key/value pairs that describe product-specific attributes.     |
|                      |                   | When provided, meta_data is GeoJSON compliant.                                 |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| countries            | Array             | A list of zero or more strings with the ISO3 country codes for countries       |
|                      |                   | contained in the geographic boundary of this file.                             |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| last_modified        | ISO-8601 Datetime | When the associated database model was last saved.                             |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| file_path            | String            | The relative path of the file in the workspace.                                |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| source_started       | ISO-8601 Datetime | When collection of the underlying source file started.                         |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| source_ended         | ISO-8601 Datetime | When collection of the underlying source file ended.                           |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| source_sensor_class  | String            | The class of sensor used to produce the source file.                           |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| source_sensor        | String            | The specific identifier of the sensor used to produce the source file.         |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| source_collection    | String            | The collection of the source file.                                             |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| source_task          | String            | The task that produced the source file.                                        |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| job                  | JSON Object       | The job that created the file.                                                 |
|                      |                   | (See :ref:`Job Details <rest_v6_job_details>`)                                 |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| job_exe              | JSON Object       | The job execution that created the file.                                       |
|                      |                   | (See :ref:`Job Execution Details <rest_v6_job_execution_details>`)             |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| job_output           | String            | The name of the output from the job related to this file.                      |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| job_type             | JSON Object       | The type of job that created the file.                                         |
|                      |                   | (See :ref:`Job Type Details <rest_v6_job_type_details>`)                       |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| recipe               | JSON Object       | The recipe instance that generated the file.                                   |
|                      |                   | (See :ref:`Recipe Details <rest_v6_recipe_details>`)                           |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| recipe_node          | String            | The recipe node that produced this file.                                       |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| recipe_type          | JSON Object       | The type of recipe that generated the file.                                    |
|                      |                   | (See :ref:`Recipe Type Details <rest_v6_recipe_type_details>`)                 |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| batch                | JSON Object       | The batch instance that generated the file.                                    |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| is_superseded        | Boolean           | Whether this file has been replaced and is now obsolete.                       |
+----------------------+-------------------+--------------------------------------------------------------------------------+
| superseded           | ISO-8601 Datetime | When the file became superseded by another file.                               |
+----------------------+-------------------+--------------------------------------------------------------------------------+

.. _rest_v6_purge_source:

v6 Purge Source File
---------------------

**Example POST /v6/files/purge-source/ API call**

Request: POST http://.../v6/files/purge-source/

Data:

.. code-block:: javascript 
 
    { 
        "file_id": 123, 
    }

Response: 204 NO CONTENT
    
+---------------------------------------------------------------------------------------------------------------------------+
| **Purge Source File**                                                                                                     |
+===========================================================================================================================+
| Removes all records related to the given source file.  This includes records for the following models: FileAncestryLink,  |
| Ingest, Job, JobExecution, JobExecutionEnd, JobExecutionOutput, JobInputFile, Queue, Recipe, RecipeInputFile, RecipeNode, |
| ScaleFile, and TaskUpdate. **This will also delete any product files from their respective workspace.**                   |
+---------------------------------------------------------------------------------------------------------------------------+
| **POST** /files/purge-source/                                                                                             |
+---------------------------------------------------------------------------------------------------------------------------+
| **Content Type**    | *application/json*                                                                                  |
+---------------------+-----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                           |
+---------------------+---------------+-----------+-------------------------------------------------------------------------+
| file_id             | Integer       | Required  | The file id of the ScaleFile SOURCE file to purge.                      |
+---------------------+---------------+-----------+-------------------------------------------------------------------------+
| **Successful Response**                                                                                                   |
+---------------------+-----------------------------------------------------------------------------------------------------+
| **Status**          | 204 NO CONTENT                                                                                      |
+---------------------+-----------------------------------------------------------------------------------------------------+