
.. _rest_scale_file:

Scale File Services
========================================================================================================================

These services provide access to information about general files that are being tracked by Scale.

.. _rest_scale_files:

+-------------------------------------------------------------------------------------------------------------------------+
| **Scale Files**                                                                                                         |
+=========================================================================================================================+
| Returns detailed information about files associated with Scale.                                                         |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /files/                                                                                                         |
+-------------------------------------------------------------------------------------------------------------------------+
| **Query Parameters**                                                                                                    |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| started            | ISO-8601 Datetime | Optional | The start of the time range to query.                               |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| ended              | ISO-8601 Datetime | Optional | The end of the time range to query.                                 |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| time_field         | String            | Optional | Indicates the time field(s) that *started* and *ended* will use for |
|                    |                   |          | time filtering. Valid values are:                                   |
|                    |                   |          |                                                                     |
|                    |                   |          | - *last_modified* - last modification of source file meta-data      |
|                    |                   |          | - *data* - data time of Scale file (*data_started*, *data_ended*)   |
|                    |                   |          | - *source* - collection time of source file (*source_started*,      |
|                    |                   |          |              *source_ended*)                                        |
|                    |                   |          |                                                                     |
|                    |                   |          | The default value is *last_modified*.                               |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| file_name          | String            | Optional | Returns only input files with this file name.                       |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| id                 | Integer           | The unique identifier of the file.                                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| file_name          | String            | The name of the file                                                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| file_path          | String            | The relative path of the file in the workspace.                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| file_type          | String            | The type of Scale file, either 'SOURCE' or 'PRODUCT'                           |
+---------------------+-------------------+-------------------------------------------------------------------------------+
| file_size          | Integer           | The size of the file in bytes.                                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| media_type         | String            | The IANA media type of the file.                                               |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| data_type          | String            | A list of string data type "tags" for the file.                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| meta_data          | JSON Object       | A dictionary of key/value pairs that describe file-specific attributes.        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| url                | String            | A hyperlink to the file.                                                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| source_started     | ISO-8601 Datetime | When collection of the source file started.                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| source_ended       | ISO-8601 Datetime | When collection of the source file ended.                                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| data_started       | ISO-8601 Datetime | The start time of the source data being ingested.                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| data_ended         | ISO-8601 Datetime | The ended time of the source data being ingested.                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| created            | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| deleted            | ISO-8601 Datetime | When the file was deleted from storage.                                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| last_modified      | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| uuid               | String            | A unique string of characters that help determine if files are identical.      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| is_deleted         | Boolean           | A flag that will indicate if the file was deleted.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| workspace          | JSON Object       | The workspace storing the file.                                                |
|                    |                   | (See :ref:`Workspace Details <rest_workspace_details>`)                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .id                | Integer           | The unique identifier of the workspace.                                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .name              | String            | The name of the workspace                                                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| countries          | Array             | A list of zero or more strings with the ISO3 country codes for countries       |
|                    |                   | contained in the geographic boundary of this file.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| geometry           | Array             | The geo-spatial footprint of the file.                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| center_point       | Array             | The center point of the file in Lat/Lon Decimal Degree.                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|         "count": 68,                                                                                                    |
|         "next": null,                                                                                                   |
|         "previous": null,                                                                                               |
|         "results": [                                                                                                    |
|             {                                                                                                           |
|                 "id": 7,                                                                                                |
|                 "file_name": "foo.bar",                                                                                 |
|                 "file_path": "file/path/foo.bar",                                                                       |
|                 "file_type": "SOURCE",                                                                                  |
|                 "file_size": 100,                                                                                       |
|                 "media_type": "text/plain",                                                                             |
|                 "data_type": "",                                                                                        |
|                 "meta_data": {...},                                                                                     |
|                 "url": null,                                                                                            |
|                 "source_started": "2016-01-10T00:00:00Z",                                                               |
|                 "source_ended": "2016-01-11T00:00:00Z",                                                                 |
|                 "data_started": "2016-01-10T00:00:00Z",                                                                 |
|                 "data_ended": "2016-01-11T00:00:00Z",                                                                   |
|                 "created": "2017-10-12T18:59:24.398334Z",                                                               |
|                 "deleted": null,                                                                                        |
|                 "last_modified": "2017-10-12T18:59:24.398379Z",                                                         |
|                 "uuid": "",                                                                                             |
|                 "is_deleted": false,                                                                                    |
|                 "workspace": {                                                                                          |
|                     "id": 19,                                                                                           |
|                     "name": "workspace-19"                                                                              |
|                 },                                                                                                      |
|                 "countries": ["TCY", "TCT"],                                                                            |
|                 "geometry" :null,                                                                                       |
|                 "center_point": null                                                                                    |
|             }                                                                                                           |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+
