
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
| files                      | Object         | Optional | A JSON object representing every file-based value in the data.     |
|                            |                |          | Each key in the object is the unique name of the data value        |
|                            |                |          | (corresponding to a parameter name) and each value is an array of  |
|                            |                |          | one or more file IDs (integers). Defaults to {}.                   |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| json                       | Object         | Optional | A JSON object representing every JSON value in the data. Each key  |
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
|                            |                |          | characters: [a-zA-Z_-]                                             |
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
