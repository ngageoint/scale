
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

A data filter JSON describes a set of filters that determines whether a set of data is accepted or not.  A filter consists of a name, type,
condition and a set of values.

The name determines which condition input parameter is examined. A condition node's input parameters are defined when it is created as part of a recipe type definition and the values for the parameters are fed from recipe inputs or job outputs that the condition node depends on.  The value 'input_a' means the filter will look at the value of the 'input_a' parameter if it exists.
If a parameter with the given name does not exist, the filter will automatically fail. This can be useful for determining whether to continue
when a previous job did not supply an optional output.  

The type describes the form of data to be used in the condition.  Valid types are 'boolean', 'integer', 'number', 'object', 'string', 
'filename', 'media-type', 'data-type', or 'meta-data'.  The type for a filter must be compatible with the parameter being tested.  File
parameters should have a type of 'filename', 'media-type', 'data-type', or 'meta-data'.  Otherwise the type of the json parameter should
match the condition type.  

The condition describes how the incoming data (usually from a previous job) should be compared.  Valid conditions are '<', '<=', 
'>','>=', '==', '!=', 'between', 'in', 'not in', 'contains', 'subset of', or 'superset of'.  The list of conditions which are valid
changes depending on the type. Here are the valid conditions for each group of types:

String Types: {'filename', 'media-type', 'data-type', 'meta-data'}
String conditions: {'==', '!=', 'in', 'not in', 'contains'}

Number Types: {'integer', 'number'}
Number Conditions: {'<', '<=', '>','>=', '==', '!=', 'between', 'in', 'not in'}

Bool Types: {'boolean'}
Bool Conditions: {'==', '!='}

Object Types: {'meta-data', 'object'}
Object Conditions: {'subset of', 'superset of'}

Here is a description of what each condition tests:

'<'
***
Tests whether the first item in the list of values is less than the incoming data. The following will test parameter 'input_a' to see if it is less than 100. The 0 is ignored.

.. code-block:: javascript

    {
        "name": "input_a",
        "type": "integer",
        "condition": "<",
        "values": [100,0]
    }

'<='
****
Tests whether the first item in the list of values is less than or equal to the incoming data. The following will test parameter 'input_a' to see if the meta-data for that file has an attribute at foo/bar less than or equal to 100. The 0 is ignored.

.. code-block:: javascript

    {
        "name": "input_a",
        "type": "meta-data",
        "condition": "<=",
        "values": [[100,0]],
        "fields": [["foo", "bar"]
    }


'>'
***
Tests whether the first item in the list of values is greater than the incoming data. The following will test parameter 'input_a' to see if it is greater than 100. The 0 is ignored.

.. code-block:: javascript

    {
        "name": "input_a",
        "type": "number",
        "condition": ">",
        "values": [100,0]
    }

'>='
****
Tests whether the first item in the list of values is greater than or equal to the incoming data. The following will test parameter 'input_a' to see if it has an attribute at foo/bar greater than or equal to 100. The 0 is ignored.

.. code-block:: javascript

    {
        "name": "input_a",
        "type": "object",
        "condition": ">=",
        "values": [[100,0]],
        "fields": [["foo", "bar"]
    }

'=='
****
Tests whether the first item in the list of values is equal to the incoming data. The following will test parameter 'input_a' to see if the parsed data-type is 'ABC'.

.. code-block:: javascript

    {
        "name": "input_a",
        "type": "data-type",
        "condition": "==",
        "values": ["ABC"]
    }

'!='
****
Tests whether the first item in the list of values is not equal to the incoming data. The following will test parameter 'input_a' to see if the filename is not 'bad_file.txt'.

.. code-block:: javascript

    {
        "name": "input_a",
        "type": "filename",
        "condition": "!=",
        "values": ["bad_file.txt"]
    }

'between'
*********
Tests whether the incoming data is between the first two values in the list of values.  Note the first value must be smaller than the second or this will never be true. The following will test parameter 'input_a' to see if it is >= 0 and <= 100.  

.. code-block:: javascript

    {
        "name": "input_a",
        "type": "integer",
        "condition": "between",
        "values": [0,100]
    }

'in'
****
Tests whether the incoming data is in the list of values (e.g. a job outputs "apple" and your values are ["orange", "apple"] succeeds, an output of "pineapple" will fail).  The following will test parameter 'input_a' to see if it's media-type is either javascript or plain text.

.. code-block:: javascript

    {
        "name": "input_a",
        "type": "media-type",
        "condition": "in",
        "values": ["application/javascript","text/plain"]
    }

'not in'
********
Reverse of the previous condition. Will succeed if the input is not in the list of values. The following will test parameter 'input_a' to see if it's media-type is neither javascript nor plain text.

.. code-block:: javascript

    {
        "name": "input_a",
        "type": "media-type",
        "condition": "not in",
        "values": ["application/javascript","text/plain"]
    }

'contains'
**********
Iterates over each value and checks if it exists in the input.  Succeeds if one value is present in the input. The following will check if either 'abc' or 'def' exists as a substring in the filename of 'input_a'

.. code-block:: javascript

    {
        "name": "input_a",
        "type": "filename",
        "condition": "contains",
        "values": ["abc","def"]
    }

'subset of'
***********
Only applicable for objects, this condition tests whether each item in the input object exists in the object defined in the first item in the list of values. This will inspect the meta-data for the file passed into 'input_a' to see if it contains any of the parameters 'foo' or 'bar' with values of 10 and 100 respectively and nothing else. Note that if the file's meta-data is empty this will return true and this may need to be coupled with a filter that specifies the meta-data is not equal to an empty object.

.. code-block:: javascript

    {
        "name": "input_a",
        "type": "meta-data",
        "condition": "subset of",
        "values": [{"foo": 10, "bar": 100}]
    }

'superset of'
*************
Only applicable for objects, this condition tests whether each item in the object defined in the first item in the list of values exists in the input object. This will inspect 'input_a' to see if it contains all of the parameters 'foo' or 'bar' with values of 10 and 100 respectively.  Additional fields present in 'input_a' are ignored.

.. code-block:: javascript

    {
        "name": "input_a",
        "type": "object",
        "condition": "superset of",
        "values": [{"foo": 10, "bar": 100}]
    }

The list of values is used by the filter to compare against the input from the preceding job (specified by the name).  For most conditions, only the first entry in the list is used
but this must always be a list.  The values should correspond to the type but there is no type checking performed on values when validating the filter, only when the filter is run.

The optional fields parameter specifies paths of fields to compare when testing json objects or file meta-data.  If a job returns the following json for an output: 

.. code-block:: javascript

   {
      "foo": {
         "bar": 100
      }
   }

then a fields value of [['foo','bar']] will check the value 100 against the condition and first value specified in the filter.  Multiple paths can be specified but the length
of the fields array must equal the length of the values array and each entry in the values array must be an array itself. The nth entry in the paths array will be compared 
against the nth entry in the values array.  By default all fields must pass for the condition to pass. If 'all_fields' is set to false then a single path succeeding will
pass the filter.

When multiple files are passed to a parameter, the all_files field determines if all files must pass the condition for the filter to pass. By
default only a single file must pass.

Finally, by default all filters must pass for a condition node to accept the data but setting the 'all' flag to false will accept the data if any filter passes.

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

.. _rest_v6_data_dataset_member:

Dataset Member JSON
-------------------

**Example interface:**

.. code-block:: javascript

  {
    "id": 65,
    "created": "",
    "file_ids": [421]
  }

+----------------------------------------------------------------------------------------------------------+
| **Dataset Member**                                                                                       |
+============================+===================+=========================================================+
| id                         | int               | The id of the dataset member.                           |
+----------------------------+-------------------+---------------------------------------------------------+
| created                    | ISO-8601 Datetime | The date the dataset member was created.                |
+----------------------------+-------------------+---------------------------------------------------------+
| file_ids                   | Array             | The list of Scale File ids associated with this member  |
+----------------------------+-------------------+---------------------------------------------------------+

.. _rest_v6_data_dataset_file:

Dataset File JSON
-----------------

**Example interface:**
.. code-block:: javascript

  {
    "id": 65,
    "parameter_name": "INPUT_FILE",
    "scale_file": {
        "id": 3002,
        "file_name": "the-scale-file.txt",
        "countries": ["USA"]
  }

+-------------------------------------------------------------------------------------------------------------+
| **Dataset File**                                                                                            |
+============================+===================+============================================================+
| id                         | int               | The id of the dataset file.                                |
+----------------------------+-------------------+------------------------------------------------------------+
| parameter_name             | string            | The parameter the Scale File is associated to.             |
+----------------------------+-------------------+------------------------------------------------------------+
| scale_file                 | JSON Object       |                                                            |
+----------------------------+-------------------+------------------------------------------------------------+
| .id                        | int               |  The id of the Scale File.                                 |
+----------------------------+-------------------+------------------------------------------------------------+
| .file_name                 | string            |  The file name of the Scale File.                          |
+----------------------------+-------------------+------------------------------------------------------------+
| .countries                 | Array             |  The list of country codes associated with the Scale File. |
+----------------------------+-------------------+------------------------------------------------------------+


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
| **Create Dataset**                                                                                                      |
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


.. _rest_v6_dataset_with_members:

v6 Create Dataset with Members
------------------------------

**Example POST /v6/datasets API call**

Request: POST http://.../v6/datasets/

.. code-block:: javascript

    {
        "title": "My Dataset",
        "description": "My Dataset Description",
        "definition": <:ref:`Dataset JSON <rest_v6_data_dataset>`>,
        "data": <:ref:`Data JSON <rest_v6_data_data>`>
    }

Response: 201 Ok
Headers:
Location http://.../v6/datasets/106

.. code-block:: javascript

   {
      "id": 106,
      "title": "My Dataset",
      "description": "My Dataset Description",
      "created": "1970-01-01T00:00:00Z",
      "definition": <:ref:`Dataset JSON <rest_v6_data_dataset>`>,
      "files": 42
   }

+-------------------------------------------------------------------------------------------------------------------------+
| **Create Dataset**                                                                                                      |
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
| data                | JSON Object       | Optional | JSON definition for the dataset members                            |
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
| **Validate Dataset**                                                                                                    |
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

v6 Create Dataset Members
-------------------------

**Example POST /v6/datasets/ API calls**

Request: POST http://.../v6/datasets/100/

.. code-block:: javascript

   {
      "data": [<:ref:`Data JSON <rest_v6_data_data>`>]
   }

Response: 201 Created
Headers:
Location http://.../v6/datasets/105/

.. code-block:: javascript

   [{
      "id": 105,
      "created": "1970-01-01T00:00:00Z",
      "data": <:ref:`Data JSON <rest_v6_data_data>`>
   }]
   
Request: POST http://.../v6/datasets/100/

.. code-block:: javascript

   {
      "data_template": {
            "files": {"input_a": "FILE_VALUE"},
            "json": {}
      },
      "source_collection": ['12345', '123456'],
      "dry_run": True
   }
   
Response: 200 Ok

.. code-block:: javascript

   [ <:ref:`Data JSON <rest_v6_data_data>`> ]
   
+-------------------------------------------------------------------------------------------------------------------------+
| **Create Dataset Members**                                                                                              |
+=========================================================================================================================+
| Creates new dataset members with the given fields                                                                       |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /v6/datasets/{id}/                                                                                             |
|         Where {id} is the unique ID of the dataset to add a member to                                                   |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| data               | Array             | Optional | The data for the dataset members to be created                      |
|                    |                   |          | See :ref:`rest_v6_data_data`                                        |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| data_template      | JSON Object       | Optional | JSON defining the data template for each member. Each member will   |
|                    |                   |          | make a copy of this template and replace FILE_VALUE with one of the |
|                    |                   |          | files returned by the given filters.                                |
|                    |                   |          | See :ref:`Data JSON <rest_v6_data_data>`                            |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| dry_run            | Boolean           | Optional | If true, only validate the data and return the list of data objects |
|                    |                   |          | that would have been created and turned into dataset members. Useful|
|                    |                   |          | to validate a template and set of filters and determine how many    |
|                    |                   |          | members would be added to the dataset.                              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| data_started       | ISO-8601 Datetime | Optional | The start of the data time range to query.                          |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| data_ended         | ISO-8601 Datetime | Optional | End of the data time range to query, defaults to the current time.  |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| source_started     | ISO-8601 Datetime | Optional | The start of the source file time range to query.                   |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| source_ended       | ISO-8601 Datetime | Optional | End of the source file time range to query, default is current time.|
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| source_sensor_class| String            | Optional | Return only files for the given source sensor class                 |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| source_sensor      | String            | Optional | Return only files for the given source sensor                       |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| source_collection  | String            | Optional | Return only files for the given source collection                   |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| source_task        | String            | Optional | Return only files for the given source task                         |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| modified_started   | ISO-8601 Datetime | Optional | The start of the last modified time range to query.                 |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| modified_ended     | ISO-8601 Datetime | Optional | End of the last modified time range to query (default current time) |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| order              | String            | Optional | One or more fields to use when ordering the results.                |
|                    |                   |          | Duplicate it to multi-sort, (ex: order=file_name&order=created).    |
|                    |                   |          | Nested objects require a delimiter (ex: order=job_type__name).      |
|                    |                   |          | Prefix fields with a dash to reverse the sort, (ex: order=-created).|
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_output         | String            | Optional | Return only files for the given job output.                         |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_id        | Integer           | Optional | Return only files associated with a given job type identifier.      |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_name      | String            | Optional | Return only files with a given job type name.                       |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_id             | Integer           | Optional | Return only files produced by the given job identifier.             |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| recipe_id          | Integer           | Optional | Return only files produced by the given recipe identifier.          |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| recipe_node        | String            | Optional | Return only files produced by the given recipe node.                |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| recipe_type_id     | Integer           | Optional | Return only files produced by the given recipe type identifier.     |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| batch_id           | Integer           | Optional | Return only files produced by the given batch identifier.           |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| file_name          | String            | Optional | Return only files with a given file name.                           |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
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
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Body**           | JSON array containing the data for dataset members that would be created if not a dry run          |
|                    | see :ref:`rest_v6_data_data`                                                                       |
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
