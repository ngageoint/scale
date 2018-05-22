
.. _rest_v6_data:

v6 Data Services
================

These services allow for the management of data within Scale.

.. _rest_v6_data_interface:

Interface JSON
--------------

An interface JSON describes a set of parameters that can be passed data values to process.

**Example interface:**

.. code-block:: javascript

   {
      "files": [{'name': 'foo', 'media_types': ['image/tiff'], 'required': True, 'multiple': True}],
      "json": [{'name': 'bar', 'type': 'integer', 'required': False}]
   }

+-----------------------------------------------------------------------------------------------------------------------------+
| **Interface**                                                                                                               |
+============================+================+==========+====================================================================+
| files                      | Array          | Required | Lists the parameters that take file(s) as input                    |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| json                       | Array          | Required | Lists the parameters that take JSON as input                       |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| name                       | String         | Required | The unique name of the parameter                                   |
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
