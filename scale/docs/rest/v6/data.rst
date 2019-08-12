
.. _rest_v6_data:

v6 Data Services
================

These services allow for the management of data within Scale.

.. _rest_v6_data_data:

Data JSON
---------

A data JSON describes a set of data values that can be passed to an interface.

**Example interface:**

.. code-block:: javascript

   {
      "files": {'foo': [1234, 1235]},
      "json": {'bar': 'hello, this is a string value'}
   }

+-----------------------------------------------------------------------------------------------------------------------------+
| **Data**                                                                                                                    |
+============================+================+==========+====================================================================+
| files                      | JSON Object    | Optional | A JSON object representing every file-based value in the data.     |
|                            |                |          | Each key in the object is the unique name of the data value        |
|                            |                |          | (corresponding to a parameter name) and each value is an array of  |
|                            |                |          | one or more file IDs (integers). Defaults to {}.                   |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| json                       | JSON Object    | Optional | A JSON object representing every JSON value in the data. Each key  |
|                            |                |          | in the object is the unique name of the data value (corresponding  |
|                            |                |          | to a parameter name) and each value is the appropriate JSON        |
|                            |                |          | type/object that matches the parameter. Defaults to {}.            |
+----------------------------+----------------+----------+--------------------------------------------------------------------+

.. _rest_v6_data_interface:

Interface JSON
--------------

An interface JSON describes a set of parameters that can be passed data values to process.

**Example interface:**

.. code-block:: javascript

   {
      "files": [{'name': 'foo', 'media_types': ['image/tiff'], 'required': True, 'multiple': True}],
      "json": [{'name': 'bar', 'type': 'string', 'required': False}]
   }

+-----------------------------------------------------------------------------------------------------------------------------+
| **Interface**                                                                                                               |
+============================+================+==========+====================================================================+
| files                      | Array          | Optional | Lists the parameters that take file(s) as input. Defaults to [].   |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| json                       | Array          | Optional | Lists the parameters that take JSON as input. Defaults to [].      |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| name                       | String         | Required | The unique name of the parameter. Can only contain the following   |
|                            |                |          | characters: \[a-zA-Z_-\]                                           |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| required                   | Boolean        | Optional | Indicates whether the parameter is required. Defaults to True.     |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| media_types                | Array          | Optional | (file parameter) List of strings describing the accepted media     |
|                            |                |          | types for the parameter's file(S)                                  |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| multiple                   | Boolean        | Optional | (file parameter) Indicates whether the parameter takes multiple    |
|                            |                |          | files. Defaults to False.                                          |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| type                       | String         | Required | (JSON parameter) The accepted JSON data type. Must be one of       |
|                            |                |          | 'array', 'boolean', 'integer', 'number', 'object', or 'string'.    |
+----------------------------+----------------+----------+--------------------------------------------------------------------+

.. _rest_v6_data_filter:

Data Filter JSON
----------------

A data filter JSON describes a set of filters that determines whether a set of data is accepted or not.

**Example interface:**

.. code-block:: javascript

   {
     "filters": [
       {
         "name": "input_a",
         "type": "media-type",
         "condition": "==",
         "values": ["application/json"]
       },
       {
         "name": "input_b",
         "type": "string",
         "condition": "contains",
         "values": ["abcde"]
       },
       {
         "name": "input_c",
         "type": "integer",
         "condition": ">",
         "values": [0]
       },
       {
         "name": "input_d",
         "type": "meta-data",
         "condition": "between",
         "values": [[0,100]],
         "fields": [["path", "to", "field"]],
         "all_fields": true
       }
     ],
     "all": true
   }

+-----------------------------------------------------------------------------------------------------------------------------+
| **Data Filter**                                                                                                             |
+============================+================+==========+====================================================================+
| filters                    | Array          | Optional | List of filter definitions. Defaults to []. An empty list will not |
|                            |                |          | accept any data.                                                   |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| name                       | String         | Required | The name of the parameter this filter runs against. Multiple       |
|                            |                |          | filters can run on the same parameter.                             |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| type                       | String         | Required | Type of parameter this filter runs against. Must be one of 'array',|
|                            |                |          | 'boolean', 'integer', 'number', 'object', 'string', 'filename',    |
|                            |                |          | 'media-type', 'data-type', or 'meta-data'                          |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| condition                  | String         | Required | Condition to test data value against. Must be one of '<', '<=',    |
|                            |                |          | '>','>=', '==', '!=', 'between', 'in', 'not in', 'contains',       |
|                            |                |          | 'subset of', or 'superset of'                                      |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| values                     | Array          | Required | List of values to compare data against. May be any type.           |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| fields                     | Array          | Optional | List of lists with each item being a list of keys for a path to a  |
|                            |                |          | field in an object or file meta-data to be tested.                 |
|                            |                |          | e.g. For this data, {'foo': {'bar': 100}}, [['foo','bar']] will    |
|                            |                |          | check the value 100. If provided, this property must be of equal   |
|                            |                |          | length to values                                                   |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| all_fields                 | Boolean        | Optional | Specifies whether all fields need to pass for filter to pass.      |
|                            |                |          | Defaults to true                                                   |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| all_files                  | Boolean        | Optional | Specifies whether all files need to pass for filter to pass.       |
|                            |                |          | Defaults to false                                                  |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| all                        | Boolean        | Optional | Specifies whether all filters need to pass for data to be accepted |
|                            |                |          | Defaults to true                                                   |
+----------------------------+----------------+----------+--------------------------------------------------------------------+

.. _rest_v6_data_dataset:

Dataset JSON
------------

A dataset JSON describes a specification for a bundle of data

**Example interface:**

.. code-block:: javascript

  {
    "global_data": { "files": { "input_a": [1234], "input_b": [1235, 1236] },
                     "json":  { "input_c": 999, { "input_d": {"greeting": "hello"} }
    },
    "global_parameters": { "files": [ { "name": "input_a" },
                                      { "name": "input_b", "media_types": [ "application/json"], "required": False, "multiple": True, ],
                           "json":  [ { "name": "input_c", "type": "integer" }, { "name": "input_d", "type": "object", "required": False } ]
    },
    "parameters": { "files": [ { "name": "input_e" },
                               { "name": "input_f", "media_types": [ "application/json"], "required": False, "multiple": True, ],
                    "json":  [ { "name": "input_g", "type": "integer" },
                               { "name": "input_h", "type": "object", "required": False } ]
    }
  }

+-----------------------------------------------------------------------------------------------------------------------------+
| **Data**                                                                                                                    |
+============================+================+==========+====================================================================+
| global_data                | JSON Object    | Optional | A JSON object representing data to be passed along with each item  |
|                            |                |          | in the dataset. This is useful for doing parameter sweeps where the|
|                            |                |          | same algorithm and data file are run through a set of parameters.  |
|                            |                |          | Must have values for each required parameter in global_parameters. |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| global_parameters          | JSON Object    | Optional | A JSON object representing parameters that are fulfilled by global |
|                            |                |          | values in the dataset not tied to individual members. These are    |
|                            |                |          | combined with regular parameters to define what is passed in to    |
|                            |                |          | algorithms run with this dataset.                                  |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| parameters                 | JSON Object    | Optional | A JSON object representing parameters to be passed to algorithms   |
|                            |                |          | run with this dataset. These are fulfilled by individual members   |
|                            |                |          | of the dataset.                                                    |
+----------------------------+----------------+----------+--------------------------------------------------------------------+

.. _rest_v6_dataset_list:

v6 Retrieve Dataset List
------------------------

**Example GET /v6/datasets/ API call**

Request: GET http://.../v6/datasets/?keyword=abc

Response: 200 OK

.. code-block:: javascript

   {
      "count": 1,
      "next": null,
      "previous": null,
      "results": [{
         "id": 1234,
         "title": "My abc Dataset",
         "description": "My Dataset Description",
         "definition": <:ref:`Dataset JSON <rest_v6_data_dataset>`>,
         "created": "1970-01-01T00:00:00Z"
      }]
   }

+-----------------------------------------------------------------------------------------------------------------------------+
| **Dataset List**                                                                                                            |
+=============================================================================================================================+
| Returns a list of datasets that match the given filter criteria                                                             |
+-----------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/datasets/                                                                                                       |
+-----------------------------------------------------------------------------------------------------------------------------+
| **Query Parameters**                                                                                                        |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| page                    | Integer           | Optional | The page of the results to return. Defaults to 1.                  |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| page_size               | Integer           | Optional | The size of the page to use for pagination of results.             |
|                         |                   |          | Defaults to 100, and can be anywhere from 1-1000.                  |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| started                 | ISO-8601 Datetime | Optional | The start of the time range to query.                              |
|                         |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z).|
|                         |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).             |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| ended                   | ISO-8601 Datetime | Optional | End of the time range to query, defaults to the current time.      |
|                         |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z).|
|                         |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).             |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| dataset_id              | Integer           | Optional | Return only datasets with given ids.                               |
|                         |                   |          | Duplicate it to filter by multiple values.                         |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| keyword                 | String            | Optional | Performs a like search on title and description.                   |
|                         |                   |          | Duplicate to search for multiple keywords.                         |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| order                   | String            | Optional | One or more fields to use when ordering the results.               |
|                         |                   |          | Duplicate it to multi-sort, (ex: order=title&order=created).       |
|                         |                   |          | Prefix fields with a dash to reverse the sort, (ex: order=-title). |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| **Successful Response**                                                                                                     |
+-------------------------+---------------------------------------------------------------------------------------------------+
| **Status**              | 200 OK                                                                                            |
+-------------------------+---------------------------------------------------------------------------------------------------+
| **Content Type**        | *application/json*                                                                                |
+-------------------------+---------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                             |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| count                   | Integer           | The total number of results that match the query parameters                   |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| next                    | URL               | A URL to the next page of results                                             |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| previous                | URL               | A URL to the previous page of results                                         |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| results                 | Array             | List of result JSON objects that match the query parameters                   |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| id                      | Integer           | The unique identifier of the dataset                                          |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| title                   | String            | The human readable display name of the dataset                                |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| description             | String            | A longer description of the dataset                                           |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| definition              | JSON Object       | The definition of the dataset.  (See :ref:`rest_v6_data_dataset`)             |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| created                 | ISO-8601 Datetime | When the dataset was initially created                                        |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| files                   | Integer           | The number of files in the dataset                                            |
+-------------------------+-------------------+-------------------------------------------------------------------------------+

.. _rest_v6_dataset_create:

v6 Create Dataset
-----------------

**Example POST /v6/datasets/ API call**

Request: POST http://.../v6/datasets/

.. code-block:: javascript

   {
      "title": "My Dataset",
      "description": "My Dataset Description",
      "definition": <:ref:`Dataset JSON <rest_v6_data_dataset>`>
   }

Response: 201 Created
Headers:
Location http://.../v6/datasets/105/

.. code-block:: javascript

   {
      "id": 105,
      "title": "My Dataset",
      "description": "My Dataset Description",
      "definition": <:ref:`Dataset JSON <rest_v6_data_dataset>`>,
      "created": "1970-01-01T00:00:00Z",
      "members": [<:ref:`Dataset Member <rest_v6_data_dataset_member>`>],
      "files": [<:ref:`Dataset File <rest_v6_data_dataset_file>`>]
   }

+-------------------------------------------------------------------------------------------------------------------------+
| **Create Dataset*                                                                                                       |
+=========================================================================================================================+
| Creates a new dataset with the given fields                                                                             |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /v6/datasets/                                                                                                  |
+---------------------+---------------------------------------------------------------------------------------------------+
| **Content Type**    | *application/json*                                                                                |
+---------------------+---------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+---------------------+-------------------+----------+--------------------------------------------------------------------+
| title               | String            | Optional | The human-readable name of the dataset                             |
+---------------------+-------------------+----------+--------------------------------------------------------------------+
| description         | String            | Optional | A human-readable description of the dataset                        |
+---------------------+-------------------+----------+--------------------------------------------------------------------+
| definition          | JSON Object       | Required | JSON definition for the dataset                                    |
|                     |                   |          | See :ref:`rest_v6_data_dataset`                                    |
+---------------------+-------------------+----------+--------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 201 Created                                                                                        |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Location**       | URL for retrieving the details of the newly created dataset                                        |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Body**           | JSON containing the details of the newly created batch, see :ref:`rest_v6_dataset_details`         |
+--------------------+----------------------------------------------------------------------------------------------------+

.. _rest_v6_dataset_validation:

v6 Validate Dataset
-------------------

**Example POST /v6/datasets/validation/ API call**

Request: POST http://.../v6/datasets/validation/

.. code-block:: javascript

   {
      "title": "My Dataset",
      "description": "My Dataset Description",
      "definition": <:ref:`Dataset JSON <rest_v6_data_dataset>`>
   }

Response: 200 Ok
Headers:
Location http://.../v6/datasets/validation/

.. code-block:: javascript

   {
      "is_valid": true,
      "errors": [],
      "warnings": [{"name": "EXAMPLE_WARNING", "description": "This is an example warning."}],
   }

+-------------------------------------------------------------------------------------------------------------------------+
| **Validate Dataset*                                                                                                     |
+=========================================================================================================================+
| Validates the given fields for creating a new dataset                                                                   |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /v6/datasets/validation/                                                                                       |
+---------------------+---------------------------------------------------------------------------------------------------+
| **Content Type**    | *application/json*                                                                                |
+---------------------+---------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+---------------------+-------------------+----------+--------------------------------------------------------------------+
| title               | String            | Optional | The human-readable name of the dataset                             |
+---------------------+-------------------+----------+--------------------------------------------------------------------+
| description         | String            | Optional | A human-readable description of the dataset                        |
+---------------------+-------------------+----------+--------------------------------------------------------------------+
| definition          | JSON Object       | Required | JSON definition for the dataset                                    |
|                     |                   |          | See :ref:`rest_v6_data_dataset`                                    |
+---------------------+-------------------+----------+--------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| is_valid           | Boolean           | Indicates if the given fields were valid for creating a new dataset. If this is|
|                    |                   | true, then submitting the same fields to the /datasets/ API will successfully  |
|                    |                   | create a new dataset.                                                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| errors             | Array             | Lists any errors causing *is_valid* to be false. The errors are JSON objects   |
|                    |                   | with *name* and *description* string fields.                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| warnings           | Array             | Lists any warnings found. Warnings are useful to present to the user, but do   |
|                    |                   | not cause *is_valid* to be false. The warnings are JSON objects with *name*    |
|                    |                   | and *description* string fields.                                               |
+--------------------+-------------------+--------------------------------------------------------------------------------+

.. _rest_v6_dataset_details:

v6 Retrieve Dataset Details
---------------------------

**Example GET /v6/datasets/{dataset-id}/ API call**

Request: GET http://.../v6/datasets/105/

Response: 200 OK

.. code-block:: javascript

   {
      "id": 105,
      "title": "My Dataset",
      "description": "My Dataset Description",
      "definition": <:ref:`Dataset JSON <rest_v6_data_dataset>`>,
      "created": "1970-01-01T00:00:00Z",
      "members": [<:ref:`Dataset Member <rest_v6_data_dataset_member>`>],
      "files": [<:ref:`Dataset File <rest_v6_data_dataset_file>`>]
   }

+-----------------------------------------------------------------------------------------------------------------------------+
| **Dataset Details**                                                                                                         |
+=============================================================================================================================+
| Returns the details for a specific dataset                                                                                  |
+-----------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/datasets/{id}/                                                                                                  |
|         Where {id} is the unique ID of the dataset to retrieve                                                              |
+-----------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                     |
+-------------------------+---------------------------------------------------------------------------------------------------+
| **Status**              | 200 OK                                                                                            |
+-------------------------+---------------------------------------------------------------------------------------------------+
| **Content Type**        | *application/json*                                                                                |
+-------------------------+---------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                             |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| id                      | Integer           | The unique identifier of the dataset                                          |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| title                   | String            | The human readable display name of the dataset                                |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| description             | String            | A longer description of the dataset                                           |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| definition              | JSON Object       | The definition of the dataset                                                 |
|                         |                   | See :ref:`rest_v6_data_dataset`                                               |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| created                 | ISO-8601 Datetime | When the dataset was initially created                                        |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| members                 | Array             | List of members belonging to this dataset.                                    |
|                         |                   | See :ref:`rest_v6_data_dataset_member`                                        |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| files                   | Array             | List of files that are part of this dataset.                                  |
|                         |                   | See :ref:`rest_v6_data_dataset_file`                                          |
+-------------------------+-------------------+-------------------------------------------------------------------------------+

.. _rest_v6_dataset_create_member:

v6 Create Dataset Member
------------------------

**Example POST /v6/datasets/ API call**

Request: POST http://.../v6/datasets/100/

.. code-block:: javascript

   {
      "data": <:ref:`Data JSON <rest_v6_data_data>`>
   }

Response: 201 Created
Headers:
Location http://.../v6/datasets/105/

.. code-block:: javascript

   {
      "id": 105,
      "created": "1970-01-01T00:00:00Z",
      "data": <:ref:`Data JSON <rest_v6_data_data>`>
   }

+-------------------------------------------------------------------------------------------------------------------------+
| **Create Dataset Member*                                                                                                |
+=========================================================================================================================+
| Creates a new dataset member with the given fields                                                                      |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /v6/datasets/{id}/                                                                                             |
|         Where {id} is the unique ID of the dataset to add a member to                                                   |
+---------------------+---------------------------------------------------------------------------------------------------+
| **Content Type**    | *application/json*                                                                                |
+---------------------+---------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+---------------------+-------------------+----------+--------------------------------------------------------------------+
| data                | String            | Required | The data for this individual member of the dataset                 |
|                     |                   |          | See :ref:`rest_v6_data_data`                                       |
+---------------------+-------------------+----------+--------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 201 Created                                                                                        |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Location**       | URL for retrieving the details of the newly created dataset                                        |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Body**           | JSON containing the details of the newly created dataset member                                    |
|                    | see :ref:`rest_v6_dataset_member_details`                                                          |
+--------------------+----------------------------------------------------------------------------------------------------+

.. _rest_v6_dataset_member_list:

v6 Retrieve Dataset Member List
-------------------------------

**Example GET /v6/datasets/{dataset_id}/members/ API call**

Request: GET http://.../v6/datasets/100/members/

Response: 200 OK

.. code-block:: javascript

   {
      "count": 1,
      "next": null,
      "previous": null,
      "results": [{
         "id": 1234,
         "data": <:ref:`Data JSON <rest_v6_data_data>`>,
         "created": "1970-01-01T00:00:00Z"
      }]
   }

+-----------------------------------------------------------------------------------------------------------------------------+
| **Dataset Member List**                                                                                                     |
+=============================================================================================================================+
| Returns a list of dataset members for the specified dataset                                                                 |
+-----------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/datasets/{id}/members/                                                                                          |
|         Where {id} is the unique ID of the dataset to retreive members of                                                   |
+-----------------------------------------------------------------------------------------------------------------------------+
| **Query Parameters**                                                                                                        |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| page                    | Integer           | Optional | The page of the results to return. Defaults to 1.                  |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| page_size               | Integer           | Optional | The size of the page to use for pagination of results.             |
|                         |                   |          | Defaults to 100, and can be anywhere from 1-1000.                  |
+-------------------------+-------------------+----------+--------------------------------------------------------------------+
| **Successful Response**                                                                                                     |
+-------------------------+---------------------------------------------------------------------------------------------------+
| **Status**              | 200 OK                                                                                            |
+-------------------------+---------------------------------------------------------------------------------------------------+
| **Content Type**        | *application/json*                                                                                |
+-------------------------+---------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                             |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| count                   | Integer           | The total number of results that match the query parameters                   |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| next                    | URL               | A URL to the next page of results                                             |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| previous                | URL               | A URL to the previous page of results                                         |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| results                 | Array             | List of result JSON objects that match the query parameters                   |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| .id                     | Integer           | The unique identifier of the dataset member                                   |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| .data                   | JSON Object       | The data for this dataset member.  (See :ref:`rest_v6_data_data`)             |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| .created                | ISO-8601 Datetime | When the dataset member was initially created                                 |
+-------------------------+-------------------+-------------------------------------------------------------------------------+

.. _rest_v6_dataset_member_details:

v6 Retrieve Dataset Member Details
----------------------------------

**Example GET /v6/datasets/members/{id} API call**

Request: GET http://.../v6/datasets/members/100/

Response: 200 OK

.. code-block:: javascript

   {
      "id": 1234,
      "data": <:ref:`Data JSON <rest_v6_data_data>`>,
      "created": "1970-01-01T00:00:00Z"
   }

+-----------------------------------------------------------------------------------------------------------------------------+
| **Dataset Member Details**                                                                                                  |
+=============================================================================================================================+
| Returns details for a specific dataset member                                                                               |
+-----------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/datasets/members/{id}/                                                                                          |
|         Where {id} is the unique ID of the dataset member to retrieve                                                       |
+-----------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                     |
+-------------------------+---------------------------------------------------------------------------------------------------+
| **Status**              | 200 OK                                                                                            |
+-------------------------+---------------------------------------------------------------------------------------------------+
| **Content Type**        | *application/json*                                                                                |
+-------------------------+---------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                             |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| id                      | Integer           | The unique identifier of the dataset member                                   |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| data                    | JSON Object       | The data for this dataset member.  (See :ref:`rest_v6_data_data`)             |
+-------------------------+-------------------+-------------------------------------------------------------------------------+
| created                 | ISO-8601 Datetime | When the dataset member was initially created                                 |
+-------------------------+-------------------+-------------------------------------------------------------------------------+