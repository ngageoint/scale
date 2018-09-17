
.. _rest_v6_workspace:

V6 Workspace Services
=====================

These services provide access to information about workspaces that Scale uses to manage files.

.. _rest_v6_workspace_list:

v6 Workspace List
-----------------

**Example GET /v6/workspaces/ API call**

Request: GET http://.../v6/workspaces/

Response: 200 OK

 .. code-block:: javascript 
 
    { 
        "count": 5, 
        "next": null, 
        "previous": null, 
        "results": [ 
            { 
                "id": 2, 
                "name": "products", 
                "title": "Products", 
                "description": "Products Workspace", 
                "base_url": "http://host.com/products", 
                "is_active": true,
                "created": "2015-10-05T21:26:04.876Z", 
                "archived": null, 
                "last_modified": "2015-10-05T21:26:04.876Z" 
            }, 
            { 
                "id": 1, 
                "name": "raw", 
                "title": "Raw Source", 
                "description": "Raw Source Workspace", 
                "base_url": "http://host.com/rs", 
                "is_active": true,
                "created": "2015-10-05T21:26:04.855Z", 
                "archived": null, 
                "last_modified": "2015-10-05T21:26:04.855Z" 
            }, 
            ... 
        ] 
    } 

+-------------------------------------------------------------------------------------------------------------------------+
| **Workspace List**                                                                                                      |
+=========================================================================================================================+
| Returns a list of all workspaces.                                                                                       |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/workspaces/                                                                                                 |
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
|                          |                   | (See :ref:`Workspace Details <rest_v6_workspace_details>`)               |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .name                    | String            | The identifying name of the workspace used for queries.                  |
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
| .created                 | ISO-8601 Datetime | When the associated database model was initially created.                |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .archived                | ISO-8601 Datetime | When the workspace was archived (no longer active).                      |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .last_modified           | ISO-8601 Datetime | When the associated database model was last saved.                       |
+--------------------------+-------------------+--------------------------------------------------------------------------+


.. _rest_v6_workspace_create:

v6 Create Workspace
-------------------

**Example POST /v6/workspaces/ API call**

Request: POST http://.../v6/workspaces/

 .. code-block:: javascript  
 
    {
        "title": "Raw Source",
        "description": "Raw Source Workspace",
        "base_url": "http://host.com/rs",
        "is_active": true,
        "configuration": {
            "broker": {
                "type": "host",
                "host_path": "/host/path"
            }
        }
    }
 
Response: 201 Created
Headers:
Location http://.../v6/workspaces/105/

 .. code-block:: javascript  
 
    { 
        "id": 1, 
        "name": "raw-source", 
        "title": "Raw Source", 
        "description": "Raw Source Workspace", 
        "base_url": "http://host.com/rs", 
        "is_active": true,
        "created": "2015-10-05T21:26:04.855Z", 
        "archived": null, 
        "last_modified": "2015-10-05T21:26:04.855Z" 
        "configuration": { 
            "broker": { 
                "type": "host", 
                "host_path": "/host/path" 
            } 
        } 
    } 

+-------------------------------------------------------------------------------------------------------------------------+
| **Create Workspace**                                                                                                    |
+=========================================================================================================================+
| Creates a new workspace with associated configuration                                                                   |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /v6/workspaces/                                                                                                |
+-------------------------+-----------------------------------------------------------------------------------------------+
| **Content Type**        | *application/json*                                                                            |
+-------------------------+-----------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| title                   | String            | Required | The human-readable name of the workspace.                      |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| description             | String            | Optional | An optional description of the workspace.                      |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| base_url                | String            | Optional | The URL prefix used to access all files within the workspace.  |
|                         |                   |          | This field can be null if the workspace is not web-accessible. |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| is_active               | Boolean           | Optional | Whether the workspace is available for use. Defaults to true.  |
|                         |                   |          | Becomes false once a workspace is archived.                    |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| configuration           | JSON Object       | Required | JSON description of the configuration for the workspace.       |
|                         |                   |          | (See :ref:`rest_v6_workspace_configuration`)                   |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 201 CREATED                                                                                        |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Location**       | URL pointing to the details for the newly created workspace                                        |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
|                    | JSON Object       | All fields are the same as the workspace details model.                        |
|                    |                   | (See :ref:`Workspace Details <rest_workspace_details>`)                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+


.. _rest_v6_workspace_details:

v6 Workspace Details
--------------------

**Example GET /v6/workspaces/{id}/ API call**

Request: GET http://.../v6/workspaces/{id}/

Response: 200 OK

 .. code-block:: javascript  
 
    {
        "id": 1,
        "name": "raw",
        "title": "Raw Source",
        "description": "Raw Source Workspace",
        "base_url": "http://host.com/rs",
        "is_active": true,
        "created": "2015-10-05T21:26:04.855Z",
        "archived": null,
        "last_modified": "2015-10-05T21:26:04.855Z"
        "configuration": {
            "broker": {
                "type": "host",
                "host_path": "/host/path"
            }
        }
    }

+-------------------------------------------------------------------------------------------------------------------------+
| **Workspace Details**                                                                                                   |
+=========================================================================================================================+
| Returns workspace details                                                                                               |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/workspaces/{id}/                                                                                            |
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
| name                     | String            | The identifying name of the workspace used for queries.                  |
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
| created                  | ISO-8601 Datetime | When the associated database model was initially created.                |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| archived                 | ISO-8601 Datetime | When the workspace was archived (no longer active).                      |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| last_modified            | ISO-8601 Datetime | When the associated database model was last saved.                       |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| configuration            | JSON Object       | JSON configuration with attributes specific to the type of workspace.    |
|                          |                   | (See :ref:`rest_v6_workspace_configuration`)                             |
+--------------------------+-------------------+--------------------------------------------------------------------------+

.. _rest_v6_workspace_validate:

v6 Validate Workspace
---------------------

**Example POST /v6/workspaces/validation/ API call**

Request: POST http://.../v6/workspaces/validation/

 .. code-block:: javascript 

    {
        "title": "Raw Source",
        "description": "Raw Source Workspace",
        "base_url": "http://host.com/rs",
        "is_active": true,
        "configuration": {
            "broker": {
                "type": "host",
                "host_path": "/host/path"
            }
        }
    }

Response: 200 OK

.. code-block:: javascript 
 
   {
      "is_valid": true,
      "errors": [],
      "warnings": [{"name": "broker_type", "description": "Changing the broker type may disrupt queued/running jobs."}],
   }

+-------------------------------------------------------------------------------------------------------------------------+
| **Validate Workspace**                                                                                                  |
+=========================================================================================================================+
| Validates a new workspace configuration without actually saving it                                                      |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /v6/workspaces/validation/                                                                                     |
+-------------------------+-----------------------------------------------------------------------------------------------+
| **Content Type**        | *application/json*                                                                            |
+-------------------------+-----------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| title                   | String            | Required | The human-readable name of the workspace.                      |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| description             | String            | Optional | An optional description of the workspace.                      |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| base_url                | String            | Optional | The URL prefix used to access all files within the workspace.  |
|                         |                   |          | This field can be null if the workspace is not web-accessible. |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| is_active               | Boolean           | Optional | Whether the workspace is available for use. Defaults to true.  |
|                         |                   |          | Becomes false once a workspace is archived.                    |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| configuration           | JSON Object       | Required | JSON description of the configuration for the workspace.       |
|                         |                   |          | (See :ref:`rest_v6_workspace_configuration`)                   |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+---------------------+------------------------------------------------------------------------------+
| is_valid           | Boolean           | Indicates if the given fields were valid for creating a new workspace. If this |
|                    |                   | is true, then submitting the same fields to the /workspaces/ API will          |
|                    |                   | successfully create a new workspace.                                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| errors             | Array             | Lists any errors causing *is_valid* to be false. The errors are JSON objects   |
|                    |                   | with *name* and *description* string fields.                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| warnings           | Array             | A list of warnings discovered during validation.                               |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .id                | String            | An identifier for the warning.                                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .details           | String            | A human-readable description of the problem.                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+


.. _rest_v6_workspace_edit:

v6 Edit Workspace
-----------------

**Example POST /v6/workspaces/{id}/ API call**

Request: POST http://.../v6/workspaces/{id}/

 .. code-block:: javascript 

    {
        "title": "Raw Source",
        "description": "Raw Source Workspace",
        "base_url": "http://host.com/rs",
        "is_active": true,
        "configuration": {
            "broker": {
                "type": "host",
                "host_path": "/host/path"
            }
        }
    }

Response: 204 NO CONTENT
   
+-------------------------------------------------------------------------------------------------------------------------+
| **Edit Workspace**                                                                                                      |
+=========================================================================================================================+
| Edits an existing workspace with associated configuration                                                               |
+-------------------------------------------------------------------------------------------------------------------------+
| **PATCH** /v6/workspaces/{id}/                                                                                          |
|           Where {id} is the unique identifier of an existing model.                                                     |
+-------------------------+-----------------------------------------------------------------------------------------------+
| **Content Type**        | *application/json*                                                                            |
+-------------------------+-----------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
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
| configuration           | JSON Object       | Optional | JSON description of the configuration for the workspace.       |
|                         |                   |          | (See :ref:`rest_v6_workspace_configuration`)                   |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 204 NO CONTENT                                                                                     |
+--------------------+----------------------------------------------------------------------------------------------------+

.. _rest_v6_workspace_configuration:

Workspace Configuration JSON
----------------------------

A workspace configuration JSON describes a set of configuration settings for a workspace.

**Example host configuration:**

.. code-block:: javascript

    {
       "broker": {
          "type": "host",
          "host_path": "/the/absolute/host/path"
       }
    }
    
**Example NFS configuration:**

.. code-block:: javascript

    {
       "broker": {
          "type": "nfs",
          "nfs_path": "host:/my/path"
       }
    }
    
**Example S3 configuration:**

.. code-block:: javascript

    {
       "broker": {
          "type": "s3",
          "bucket_name": "my_bucket.domain.com",
          "credentials": {
             "access_key_id": "AKIAIOSFODNN7EXAMPLE",
             "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
          },
          "host_path": "/my_bucket",
          "region_name": "us-east-1"
       }
    }

+-----------------------------------------------------------------------------------------------------------------------------+
| **Workspace Configuration**                                                                                                 |
+============================+================+==========+====================================================================+
| workspace                  | String         | Required | String that specifies the name of the workspace that is being      |
|                            |                |          | scanned. The type of the workspace (its broker type) will determine|
|                            |                |          | which types of scanner can be used.                                |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| broker                     | JSON Object    | Required | JSON object representing the type and configuration of the broker  |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| .type                      | String         | Required | The type of the broker. Choices are 'host', 'nfs' or 's3'          |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| .host_path                 | String         | Required | (host) Specifies the absolute path of the host’s local directory   |
|                            |                |          | that should be mounted into a job’s container in order to access   |
|                            |                |          | the workspace’s files.                                             |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| .nfs_path                  | String         | Required | (nfs) Specifies the remote NFS path to use for storing and gettting|
|                            |                |          | the workspace files. It should be in the format host:/path.        |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| .bucket_name               | String         | Required | (s3) Specifies the globally unique name of a storage bucket within |
|                            |                |          | S3. The bucket should be created before attempting to use it here. |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| .credentials               | JSON Object    | Optional | (s3) JSON object that provides the necessary information to access |
|                            |                |          | the bucket. This attribute should be omitted when using IAM        |
|                            |                |          | role-based security. If it is included for key-based security, then|
|                            |                |          | both sub-attributes must be included. An IAM account should be     |
|                            |                |          | created and granted the appropriate permissions to the bucket      |
|                            |                |          | before attempting to use it here.                                  |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| ..access_key_id            | String         | Optional | (s3) Unique identifier for the user account in IAM that will be    |
|                            |                |          | used as a proxy for read and write operations within Scale.        |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| ..secret_access_key        | String         | Required | (s3) Generated token that the system can use to prove it should be |
|                            |                |          | able to make requests on behalf of the associated IAM account      |
|                            |                |          | without requiring the actual password used by that account.        |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| .host_path                 | String         | Optional | Adds S3 workspace support for locally mounted buckets and partial  |   
|                            |                |          | file read-only access. If a FUSE file system (such as s3fs or      |
|                            |                |          | goofys) mounts the S3 bucket at the host_path location on all      | 
|                            |                |          | nodes, an alternative to downloading large files is available to   |
|                            |                |          | jobs that use only portions of a file. The job interface must      |
|                            |                |          | indicate partial equal to true for any input files to take         |
|                            |                |          | advantage of host_path. Only read operations are performed using   |
|                            |                |          | the mount, all write operations will use the S3 REST API.          |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| .region_name               | String         | Optional | (s3) AWS region where the SQS Queue is located. This is not always |
|                            |                |          | required, as environment variables or configuration files could    |
|                            |                |          | set the default region, but it is a highly recommended setting for |
|                            |                |          | explicitly indicating the SQS region.                              |
+----------------------------+----------------+----------+--------------------------------------------------------------------+