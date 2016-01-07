
.. _rest_port:

Import/Export Services
========================================================================================================================

These services allow administrators to export recipe, job, and error records and safely import them to another system.

.. _rest_port_export:

+-------------------------------------------------------------------------------------------------------------------------+
| **Export**                                                                                                              |
+=========================================================================================================================+
| Exports configuration records for recipe types, job types, and errors.                                                  |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /configuration/                                                                                                 |
+-------------------------------------------------------------------------------------------------------------------------+
| **Query Parameters**                                                                                                    |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| include            | String            | Optional | The types of records to include in the export. Defaults to all.     |
|                    |                   |          | Choices: [recipe_types, job_types, errors].                         |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| recipe_type_id     | Integer           | Optional | Return only recipe types with a given recipe type identifier.       |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| recipe_type_name   | String            | Optional | Return only recipe types with a given recipe type name.             |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_id        | Integer           | Optional | Return only job types with a given job type identifier.             |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_name      | String            | Optional | Return only job types with a given job type name.                   |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| job_type_category  | String            | Optional | Return only job types with a given job type category.               |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| error_id           | Integer           | Optional | Return only errors with a given error identifier.                   |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| error_name         | String            | Optional | Return only errors with a given error name.                         |
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
| version            | String            | The version number of the configuration schema.                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| recipe_types       | Array             | List of exported recipe types.                                                 |
|                    |                   | (See :ref:`Recipe Type Details <rest_recipe_type_details>`)                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| job_types          | Array             | List of exported job types.                                                    |
|                    |                   | (See :ref:`Job Type Details <rest_job_type_details>`)                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| errors             | Array             | List of exported errors.                                                       |
|                    |                   | (See :ref:`Error Details <rest_error_details>`)                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "version": "1.0",                                                                                                |
|        "recipe_types": [                                                                                                |
|            {                                                                                                            |
|                "name": "my-recipe",                                                                                     |
|                "version": "1.0.0",                                                                                      |
|                "title": "My Recipe",                                                                                    |
|                "description": "Runs my recipe",                                                                         |
|                "definition": {...},                                                                                     |
|                "trigger_rule": {...}                                                                                    |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ],                                                                                                               |
|        "job_types": [                                                                                                   |
|            {                                                                                                            |
|                "name": "my-job",                                                                                        |
|                "version": "1.0.0",                                                                                      |
|                "title": "My Job",                                                                                       |
|                "description": "Runs my job",                                                                            |
|                "category": null,                                                                                        |
|                "author_name": null,                                                                                     |
|                "author_url": null,                                                                                      |
|                "is_system": false,                                                                                      |
|                "is_long_running": false,                                                                                |
|                "is_operational": true,                                                                                  |
|                "icon_code": "f013",                                                                                     |
|                "uses_docker": true,                                                                                     |
|                "docker_privileged": false,                                                                              |
|                "docker_image": null,                                                                                    |
|                "priority": 1,                                                                                           |
|                "timeout": 0,                                                                                            |
|                "max_tries": 0,                                                                                          |
|                "cpus_required": 1.0,                                                                                    |
|                "mem_required": 64.0,                                                                                    |
|                "disk_out_const_required": 64.0,                                                                         |
|                "disk_out_mult_required": 0.0,                                                                           |
|                "interface": {...},                                                                                      |
|                "error_mapping": {...},                                                                                  |
|                "trigger_rule": {...}                                                                                    |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ],                                                                                                               |
|        "errors": [                                                                                                      |
|            {                                                                                                            |
|                "name": "bad-data",                                                                                      |
|                "title": "Bad Data",                                                                                     |
|                "description": "Bad data detected",                                                                      |
|                "category": "DATA"                                                                                       |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_port_import:

+-------------------------------------------------------------------------------------------------------------------------+
| **Import**                                                                                                              |
+=========================================================================================================================+
| Imports configuration records for recipe types, job types, and errors.                                                  |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /configuration/                                                                                                |
+-------------------------------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| import             | JSON Object       | Required | The previously exported configuration to load.                      |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| .version           | String            | Optional | The version number of the configuration schema.                     |
|                    |                   |          | Defaults to the latest version.                                     |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| .recipe_types      | Array             | Optional | List of recipe types to import.                                     |
|                    |                   |          | (See :ref:`Recipe Type Details <rest_recipe_type_details>`)         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| .job_types         | Array             | Optional | List of job types to import.                                        |
|                    |                   |          | (See :ref:`Job Type Details <rest_job_type_details>`)               |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| .errors            | Array             | Optional | List of errors to import.                                           |
|                    |                   |          | (See :ref:`Error Details <rest_error_details>`)                     |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| warnings           | Array             | A list of warnings discovered during import.                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .id                | String            | An identifier for the warning.                                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .details           | String            | A human-readable description of the problem.                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "warnings": [                                                                                                    |
|            "id": "media_type",                                                                                          |
|            "details": "Invalid media type for data input: input_file -> image/png"                                      |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_port_validate:

+-------------------------------------------------------------------------------------------------------------------------+
| **Validate Import**                                                                                                     |
+=========================================================================================================================+
| Validate import configuration records for recipe types, job types, and errors.                                          |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /configuration/validation/                                                                                     |
+-------------------------------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| import             | JSON Object       | Required | The previously exported configuration to check.                     |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| warnings           | Array             | A list of warnings discovered during validation.                               |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .id                | String            | An identifier for the warning.                                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .details           | String            | A human-readable description of the problem.                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "warnings": [                                                                                                    |
|            "id": "media_type",                                                                                          |
|            "details": "Invalid media type for data input: input_file -> image/png"                                      |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

+-------------------------------------------------------------------------------------------------------------------------+
| **Export Download**                                                                                                     |
+=========================================================================================================================+
| Exports configuration records for recipe types, job types, and errors as a download attachment response.                |
| All the request parameters and response fields are identical to the normal export.                                      |
| (See :ref:`Export <rest_port_export>`)                                                                                  |
|                                                                                                                         |
| This is purely a convenience API for web applications to provide a *Save As...* download prompt to users.               |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /configuration/download/                                                                                        |
+-------------------------------------------------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    No Response                                                                                                          |
+-------------------------------------------------------------------------------------------------------------------------+

+-------------------------------------------------------------------------------------------------------------------------+
| **Import Upload**                                                                                                       |
+=========================================================================================================================+
| Imports configuration records for recipe types, job types, and errors using a multi-part form encoding.                 |
| All the request parameters and response fields are identical to the normal import.                                      |
| (See :ref:`Import <rest_port_import>`)                                                                                  |
|                                                                                                                         |
| This is purely a convenience API for web applications to provide a *Browse...* file input to users.                     |
| The API supports traditional file uploads using a form element like this:                                               |
|                                                                                                                         |
| .. code-block:: html                                                                                                    |
|                                                                                                                         |
|    <form method="POST" enctype="multipart/form-data" action="SERVER/configuration/upload/">                             |
|       <input type="file" name="import"></input>                                                                         |
|       <button type="submit">Import</button>                                                                             |
|    </form>                                                                                                              |
|                                                                                                                         |
| The API also supports more modern AJAX file uploads by providing the file name in the header: *HTTP_X_FILE_NAME*.       |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /configuration/upload/                                                                                         |
+-------------------------------------------------------------------------------------------------------------------------+
