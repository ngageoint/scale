
.. _rest_workspace:

Workspace Services
==================

These services provide access to information about workspaces that Scale uses to manage files.

.. _rest_workspace_list:

+-------------------------------------------------------------------------------------------------------------------------+
| **Workspace List**                                                                                                      |
+=========================================================================================================================+
| Returns a list of all workspaces.                                                                                       |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /workspaces/                                                                                                    |
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
| name               | String            | Optional | Return only workspaces with a given name.                           |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| order              | String            | Optional | One or more fields to use when ordering the results.                |
|                    |                   |          | Duplicate it to multi-sort, (ex: order=name&order=title).           |
|                    |                   |          | Prefix fields with a dash to reverse the sort, (ex: order=-name).   |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------------+----------------------------------------------------------------------------------------------+
| **Status**               | 200 OK                                                                                       |
+--------------------------+----------------------------------------------------------------------------------------------+
| **Content Type**         | *application/json*                                                                           |
+--------------------------+----------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| count                    | Integer           | The total number of results that match the query parameters.             |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| next                     | URL               | A URL to the next page of results.                                       |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| previous                 | URL               | A URL to the previous page of results.                                   |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| results                  | Array             | List of result JSON objects that match the query parameters.             |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .id                      | Integer           | The unique identifier of the model. Can be passed to the details API.    |
|                          |                   | (See :ref:`Workspace Details <rest_workspace_details>`)                  |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .name                    | String            | The stable name of the workspace used for queries.                       |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .title                   | String            | The human readable display name of the workspace.                        |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .description             | String            | A longer description of the workspace.                                   |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .base_url                | String            | The URL prefix used to access all files within the workspace.            |
|                          |                   | This field can be null if the workspace is not web-accessible.           |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .is_active               | Boolean           | Whether the workspace is active (false once workspace is archived).      |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .used_size               | Decimal           | The amount of disk space currently being used by the workspace in bytes. |
|                          |                   | This field can be null if the disk space is unknown.                     |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .total_size              | Decimal           | The total amount of disk space provided by the workspace in bytes.       |
|                          |                   | This field can be null if the disk space is unknown.                     |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .created                 | ISO-8601 Datetime | When the associated database model was initially created.                |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .archived                | ISO-8601 Datetime | When the workspace was archived (no longer active).                      |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .last_modified           | ISO-8601 Datetime | When the associated database model was last saved.                       |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "count": 5,                                                                                                      |
|        "next": null,                                                                                                    |
|        "previous": null,                                                                                                |
|        "results": [                                                                                                     |
|            {                                                                                                            |
|                "id": 2,                                                                                                 |
|                "name": "products",                                                                                      |
|                "title": "Products",                                                                                     |
|                "description": "Products Workspace",                                                                     |
|                "base_url": "http://host.com/products",                                                                  |
|                "is_active": true,                                                                                       |
|                "used_size": 0,                                                                                          |
|                "total_size": 0,                                                                                         |
|                "created": "2015-10-05T21:26:04.876Z",                                                                   |
|                "archived": null,                                                                                        |
|                "last_modified": "2015-10-05T21:26:04.876Z"                                                              |
|            },                                                                                                           |
|            {                                                                                                            |
|                "id": 1,                                                                                                 |
|                "name": "raw",                                                                                           |
|                "title": "Raw Source",                                                                                   |
|                "description": "Raw Source Workspace",                                                                   |
|                "base_url": "http://host.com/rs",                                                                        |
|                "is_active": true,                                                                                       |
|                "used_size": 0,                                                                                          |
|                "total_size": 0,                                                                                         |
|                "created": "2015-10-05T21:26:04.855Z",                                                                   |
|                "archived": null,                                                                                        |
|                "last_modified": "2015-10-05T21:26:04.855Z"                                                              |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_workspace_create:

+-------------------------------------------------------------------------------------------------------------------------+
| **Create Workspace**                                                                                                    |
+=========================================================================================================================+
| Creates a new workspace with associated configuration                                                                   |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /workspaces/                                                                                                   |
+-------------------------+-----------------------------------------------------------------------------------------------+
| **Content Type**        | *application/json*                                                                            |
+-------------------------+-----------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| name                    | String            | Required | The stable name of the workspace used for queries.             |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| title                   | String            | Optional | The human-readable name of the workspace.                      |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| description             | String            | Optional | An optional description of the workspace.                      |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| base_url                | String            | Optional | The URL prefix used to access all files within the workspace.  |
|                         |                   |          | This field can be null if the workspace is not web-accessible. |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| is_active               | Boolean           | Optional | Whether the workspace is available for use. Defaults to true.  |
|                         |                   |          | Becomes false once a workspace is archived.                    |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| json_config             | JSON Object       | Required | JSON description of the configuration for the workspace.       |
|                         |                   |          | (See :ref:`architecture_workspaces_spec`)                      |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "name": "raw",                                                                                                   |
|        "title": "Raw Source",                                                                                           |
|        "description": "Raw Source Workspace",                                                                           |
|        "base_url": "http://host.com/rs",                                                                                |
|        "is_active": true,                                                                                               |
|        "json_config": {                                                                                                 |
|            "broker": {                                                                                                  |
|                "type": "host"                                                                                           |
|            }                                                                                                            |
|        }                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 201 CREATED                                                                                        |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
|                    | JSON Object       | All fields are the same as the workspace details model.                        |
|                    |                   | (See :ref:`Workspace Details <rest_workspace_details>`)                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "id": 1,                                                                                                         |
|        "name": "raw",                                                                                                   |
|        "title": "Raw Source",                                                                                           |
|        "description": "Raw Source Workspace",                                                                           |
|        "base_url": "http://host.com/rs",                                                                                |
|        "is_active": true,                                                                                               |
|        "used_size": 0,                                                                                                  |
|        "total_size": 0,                                                                                                 |
|        "created": "2015-10-05T21:26:04.855Z",                                                                           |
|        "archived": null,                                                                                                |
|        "last_modified": "2015-10-05T21:26:04.855Z"                                                                      |
|        "json_config": {                                                                                                 |
|            "broker": {                                                                                                  |
|                "type": "host"                                                                                           |
|            }                                                                                                            |
|        }                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_workspace_details:

+-------------------------------------------------------------------------------------------------------------------------+
| **Workspace Details**                                                                                                   |
+=========================================================================================================================+
| Returns workspace details                                                                                               |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /workspaces/{id}/                                                                                               |
|         Where {id} is the unique identifier of an existing model.                                                       |
+-------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| **Status**               | 200 OK                                                                                       |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| **Content Type**         | *application/json*                                                                           |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| id                       | Integer           | The unique identifier of the model.                                      |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| name                     | String            | The stable name of the workspace used for queries.                       |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| title                    | String            | The human readable display name of the workspace.                        |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| description              | String            | A longer description of the workspace.                                   |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| base_url                 | String            | The URL prefix used to access all files within the workspace.            |
|                          |                   | This field can be null if the workspace is not web-accessible.           |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| is_active                | Boolean           | Whether the workspace is active (false once workspace is archived).      |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| used_size                | Decimal           | The amount of disk space currently being used by the workspace in bytes. |
|                          |                   | This field can be null if the disk space is unknown.                     |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| total_size               | Decimal           | The total amount of disk space provided by the workspace in bytes.       |
|                          |                   | This field can be null if the disk space is unknown.                     |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| created                  | ISO-8601 Datetime | When the associated database model was initially created.                |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| archived                 | ISO-8601 Datetime | When the workspace was archived (no longer active).                      |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| last_modified            | ISO-8601 Datetime | When the associated database model was last saved.                       |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| json_config              | JSON Object       | JSON configuration with attributes specific to the type of workspace.    |
|                          |                   | (See :ref:`architecture_workspaces`)                                     |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "id": 1,                                                                                                         |
|        "name": "raw",                                                                                                   |
|        "title": "Raw Source",                                                                                           |
|        "description": "Raw Source Workspace",                                                                           |
|        "base_url": "http://host.com/rs",                                                                                |
|        "is_active": true,                                                                                               |
|        "used_size": 0,                                                                                                  |
|        "total_size": 0,                                                                                                 |
|        "created": "2015-10-05T21:26:04.855Z",                                                                           |
|        "archived": null,                                                                                                |
|        "last_modified": "2015-10-05T21:26:04.855Z"                                                                      |
|        "json_config": {                                                                                                 |
|            "broker": {                                                                                                  |
|                "type": "host"                                                                                           |
|            }                                                                                                            |
|        }                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_workspace_validate:

+-------------------------------------------------------------------------------------------------------------------------+
| **Validate Workspace**                                                                                                  |
+=========================================================================================================================+
| Validates a new workspace configuration without actually saving it                                                      |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /workspaces/validatation/                                                                                      |
+-------------------------+-----------------------------------------------------------------------------------------------+
| **Content Type**        | *application/json*                                                                            |
+-------------------------+-----------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| name                    | String            | Required | The stable name of the workspace used for queries.             |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| title                   | String            | Optional | The human-readable name of the workspace.                      |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| description             | String            | Optional | An optional description of the workspace.                      |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| base_url                | String            | Optional | The URL prefix used to access all files within the workspace.  |
|                         |                   |          | This field can be null if the workspace is not web-accessible. |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| is_active               | Boolean           | Optional | Whether the workspace is available for use. Defaults to true.  |
|                         |                   |          | Becomes false once a workspace is archived.                    |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| json_config             | JSON Object       | Required | JSON description of the configuration for the workspace.       |
|                         |                   |          | (See :ref:`architecture_workspaces_spec`)                      |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "name": "raw",                                                                                                   |
|        "title": "Raw Source",                                                                                           |
|        "description": "Raw Source Workspace",                                                                           |
|        "base_url": "http://host.com/rs",                                                                                |
|        "is_active": true,                                                                                               |
|        "json_config": {                                                                                                 |
|            "broker": {                                                                                                  |
|                "type": "host"                                                                                           |
|            }                                                                                                            |
|        }                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+---------------------+------------------------------------------------------------------------------+
| warnings           | Array               | A list of warnings discovered during validation.                             |
+--------------------+---------------------+------------------------------------------------------------------------------+
| .id                | String              | An identifier for the warning.                                               |
+--------------------+---------------------+------------------------------------------------------------------------------+
| .details           | String              | A human-readable description of the problem.                                 |
+--------------------+---------------------+------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "warnings": [                                                                                                    |
|            "id": "broker_type",                                                                                         |
|            "details": "Changing the broker type may disrupt queued/running jobs."                                       |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+
