
.. _rest_v6_strike:

v6 Strike Services
==================

These services allow a user to create, view, and manage Strike processes.

.. _rest_v6_strike_list:

**Example GET /v6/strikes/ API call**

Request: GET http://.../v6/strikes/

Response: 200 OK

 .. code-block:: javascript 
 
    { 
        "count": 3, 
        "next": null, 
        "previous": null, 
        "results": [ 
            { 
                "id": 1, 
                "name": "my-strike-process", 
                "title": "My Strike Process", 
                "description": "This is my Strike process for detecting my favorite files!", 
                "job": { 
                    "id": 7, 
                    "job_type": { 
                        "id": 2, 
                        "name": "scale-strike", 
                        "title": "Scale Strike", 
                        "description": "Monitors a directory for incoming source files to ingest", 
                        "revision_num": 1,
                        "icon_code": "f0e7" 
                    }, 
                    "status": "RUNNING"
                },
                "created": "2015-03-11T00:00:00Z",
                "last_modified": "2015-03-11T00:00:00Z"
            }, 
            ... 
        ] 
    } 

+-------------------------------------------------------------------------------------------------------------------------+
| **Strike List**                                                                                                         |
+=========================================================================================================================+
| Returns a list of all Strike processes.                                                                                 |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/strikes/                                                                                                    |
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
| name               | String            | Optional | Return only Strike processes with a given name.                     |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| order              | String            | Optional | One or more fields to use when ordering the results.                |
|                    |                   |          | Duplicate it to multi-sort, (ex: order=name&order=description).     |
|                    |                   |          | Prefix fields with a dash to reverse the sort, (ex: order=-name).   |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| count              | Integer           | The total number of results that match the query parameters.                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| next               | URL               | A URL to the next page of results.                                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| previous           | URL               | A URL to the previous page of results.                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| results            | Array             | List of result JSON objects that match the query parameters.                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .id                | Integer           | The unique identifier of the model. Can be passed to the details API.          |
|                    |                   | (See :ref:`Strike Details <rest_v6_strike_details>`)                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .name              | String            | The identifying name of the Strike process used for queries.                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .title             | String            | The human readable display name of the Strike process.                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .description       | String            | A longer description of the Strike process.                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .job               | JSON Object       | The job that is associated with the Strike process.                            |
|                    |                   | (See :ref:`Job Details <rest_v6_job_details>`)                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .created           | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .last_modified     | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+

.. _rest_v6_strike_create:

**Example POST /v6/strikes/ API call**

Request: POST http://.../v6/strikes/

 .. code-block:: javascript 
 
    { 
        "title": "My Strike Process", 
        "description": "This is my Strike process for detecting my favorite files!", 
        "configuration": { 
            "workspace": "my-workspace", 
            "monitor": { 
                "type": "dir-watcher", 
                "transfer_suffix": "_tmp" 
            }, 
            "files_to_ingest": [{ 
                "filename_regex": ".*txt" 
            }] 
        } 
    } 

Response: 201 Created
Headers:
Location http://.../v6/strikes/105/

 .. code-block:: javascript 
 
    { 
        "id": 1, 
        "name": "my-strike-process", 
        "title": "My Strike Process", 
        "description": "This is my Strike process for detecting my favorite files!", 
        "job": { 
            "id": 7, 
            "job_type": { 
                "id": 2, 
                "name": "scale-strike", 
                "title": "Scale Strike", 
                "description": "Monitors a directory for incoming source files to ingest", 
                "revision_num": 1,
                "icon_code": "f0e7" 
            }, 
            "status": "RUNNING"
        }, 
        "created": "2015-03-11T00:00:00Z",
        "last_modified": "2015-03-11T00:00:00Z",
        "configuration": { 
            "workspace": "my-workspace", 
            "monitor": { 
                "type": "dir-watcher", 
                "transfer_suffix": "_tmp" 
            }, 
            "files_to_ingest": [{ 
                "filename_regex": ".*txt" 
            }] 
        }
    } 

+-------------------------------------------------------------------------------------------------------------------------+
| **Create Strike**                                                                                                       |
+=========================================================================================================================+
| Creates a new Strike process and places it onto the queue                                                               |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /v6/strikes/                                                                                                   |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| title              | String            | Required | The human readable display name of the Strike process.              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| description        | String            | Optional | A longer description of the Strike process.                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| configuration      | JSON Object       | Required | JSON defining the Strike configuration.                             |
|                    |                   |          | (See :ref:`rest_v6_strike_configuration`)                           |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 201 CREATED                                                                                        |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Location**       | URL pointing to the details for the newly created strike process                                   |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
|                    | JSON Object       | All fields are the same as the Strike process details model.                   |
|                    |                   | (See :ref:`Strike Details <rest_strike_details>`)                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+

.. _rest_v6_strike_details:

**Example GET /v6/strikes/{id}/ API call**

Request: GET http://.../v6/strikes/{id}/

Response: 200 OK

 .. code-block:: javascript 
 
   { 
       "id": 1, 
       "name": "my-strike-process", 
       "title": "My Strike Process", 
       "description": "This is my Strike process for detecting my favorite files!", 
       "job": { 
           "id": 7, 
           "job_type": { 
               "id": 2, 
               "name": "scale-strike", 
               "title": "Scale Strike", 
               "description": "Monitors a directory for incoming source files to ingest", 
               "revision_num": 1,
               "icon_code": "f0e7" 
           }, 
           "status": "RUNNING"
       },
       "created": "2015-03-11T00:00:00Z",
       "last_modified": "2015-03-11T00:00:00Z",
       "configuration": { 
           "workspace": "my-workspace", 
           "monitor": { 
               "type": "dir-watcher", 
               "transfer_suffix": "_tmp" 
           }, 
           "files_to_ingest": [{ 
               "filename_regex": ".*txt" 
           }] 
       } 
   } 
   
+-------------------------------------------------------------------------------------------------------------------------+
| **Strike Details**                                                                                                      |
+=========================================================================================================================+
| Returns Strike process details                                                                                          |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/strikes/{id}/                                                                                               |
|         Where {id} is the unique identifier of an existing model.                                                       |
+-------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| id                 | Integer           | The unique identifier of the model. Can be passed to the details API.          |
|                    |                   | (See :ref:`Strike Details <rest_strike_details>`)                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| name               | String            | The identifying name of the Strike process used for queries.                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| title              | String            | The human readable display name of the Strike process.                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| description        | String            | A longer description of the Strike process.                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| job                | JSON Object       | The job that is associated with the Strike process.                            |
|                    |                   | (See :ref:`Job Details <rest_job_details>`)                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| created            | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| last_modified      | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| configuration      | JSON Object       | JSON defining the Strike configuration.                                        |
|                    |                   | (See :ref:`rest_v6_strike_configuration`)                                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+

.. _rest_v6_strike_validate:

**Example POST /v6/strikes/validation/ API call**

Request: POST http://.../v6/strikes/validation/

.. code-block:: javascript 

    { 
        "name": "my-strike-process", 
        "title": "My Strike Process", 
        "description": "This is my Strike process for detecting my favorite files!", 
        "configuration": { 
            "workspace": "my-workspace", 
            "monitor": { 
                "type": "dir-watcher", 
                "transfer_suffix": "_tmp" 
            }, 
            "files_to_ingest": [{ 
                "filename_regex": ".*txt" 
            }] 
        } 
    } 

Response: 200 OK

.. code-block:: javascript 
 
   {
      "is_valid": true,
      "errors": [],
      "warnings": [{"name": "EXAMPLE_WARNING", "description": "This is an example warning."}],
   }

+-------------------------------------------------------------------------------------------------------------------------+
| **Validate Strike**                                                                                                     |
+=========================================================================================================================+
| Validates a new Strike process configuration without actually saving it                                                 |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /v6/strikes/validation/                                                                                        |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| title              | String            | Required | The human readable display name of the Strike process.              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| description        | String            | Optional | A longer description of the Strike process.                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| configuration      | JSON Object       | Required | JSON defining the Strike configuration.                             |
|                    |                   |          | (See :ref:`rest_v6_strike_configuration`)                           |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| is_valid           | Boolean           | Indicates if the given fields were valid for creating a new batch. If this is  |
|                    |                   | true, then submitting the same fields to the /batches/ API will successfully   |
|                    |                   | create a new batch.                                                            |
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

.. _rest_v6_strike_edit:

**Example PATCH /v6/strikes/{id}/ API call**

Request: PATCH http://.../v6/strikes/{id}/

.. code-block:: javascript 
 
    { 
        "title": "My Strike Process", 
        "description": "This is my Strike process for detecting my favorite files!", 
        "configuration": { 
            "workspace": "my-workspace", 
            "monitor": { 
                "type": "dir-watcher", 
                "transfer_suffix": "_tmp" 
            }, 
            "files_to_ingest": [{ 
                "filename_regex": ".*txt" 
            }] 
        } 
    }

Response: 204 NO CONTENT
    
+-------------------------------------------------------------------------------------------------------------------------+
| **Edit Strike**                                                                                                         |
+=========================================================================================================================+
| Edits an existing Strike process with associated configuration                                                          |
+-------------------------------------------------------------------------------------------------------------------------+
| **PATCH** /v6/strikes/{id}/                                                                                             |
|           Where {id} is the unique identifier of an existing model.                                                     |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| title              | String            | Optional | The human readable display name of the Strike process.              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| description        | String            | Optional | A longer description of the Strike process.                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| configuration      | JSON Object       | Optional | JSON defining the Strike configuration.                             |
|                    |                   |          | (See :ref:`rest_v6_strike_configuration`)                           |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 204 No Content                                                                                     |
+--------------------+----------------------------------------------------------------------------------------------------+

.. _rest_v6_strike_configuration:

Strike Configuration JSON
-------------------------

A strike configuration JSON describes a set of configuration settings that affect how a strike job executes.

**Example dir-watcher interface:**

.. code-block:: javascript

    {
      "workspace" : "workspace_name",
      "monitor" : {
        "type" : "dir-watcher",
        "transfer_suffix" : "_tmp"
      },
      "files_to_ingest":[
        {
          "filename_regex" : ".*txt",
          "data_types": [ "type1", "type2" ],
          "new_workspace" : "workspace_name",
          "new_file_path" : "wksp/path"
        }
      ]
    }
    
**Example S3 interface:**

.. code-block:: javascript

    {
        "workspace": "my-host-workspace",
        "monitor": {
            "type": "s3",
            "sqs_name": "my-sqs"
            "credentials": {
                "access_key_id": "AKIAIOSFODNN7EXAMPLE",
                "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
            },
            "region_name": "us-east-1"
        },
        "files_to_ingest": [
            {
                "filename_regex": "*.h5",
                "data_types": [
                    "data type 1",
                    "data type 2"
                ],
                "new_workspace": "my-new-workspace",
                "new_file_path": "/new/file/path"
            }
        ]
    }

+-----------------------------------------------------------------------------------------------------------------------------+
| **Strike Configuration**                                                                                                    |
+============================+================+==========+====================================================================+
| workspace                  | String         | Required | String that specifies the name of the workspace that is being      |
|                            |                |          | scanned. The type of the workspace (its broker type) will determine|
|                            |                |          | which types of scanner can be used.                                |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| monitor                    | JSON Object    | Required | JSON object representing the type and configuration of the monitor |
|                            |                |          | that will watch *workspace* for new files.                         |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| .type                      | String         | Required | The type of the monitor. Must be either 'dir-watcher' or 's3'      |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| .transfer_suffix           | String         | Required | (dir-watcher)Defines a suffix that is used on the file names to    |
|                            |                |          | indicate that files are still transferring and have not yet        |
|                            |                |          | finished being copied into the monitored directory                 |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| .sqs_name                  | String         | Required | (s3) Name of the SQS queue that should be polled for object        |
|                            |                |          | creation notifications that describe new files in the S3 bucket.   |
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
| .region_name               | String         | Optional | (s3) AWS region where the SQS Queue is located. This is not always |
|                            |                |          | required, as environment variables or configuration files could set|
|                            |                |          | the default region, but it is a highly recommended setting for     |
|                            |                |          | explicitly indicating the SQS region.                              |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| files_to_ingest            | Array          | Required | List of JSON objects that define the rules for how to handle files |
|                            |                |          | that appear in the scanned workspace. The array must contain at    |
|                            |                |          | least one item.                                                    |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| .filename_regex            | String         | Required | Regular expression to check against the names of new files in the  |   
|                            |                |          | scanned workspace. When a new file appears in the workspace, the   |
|                            |                |          | file’s name is checked against each expression in order of the     | 
|                            |                |          | files_to_ingest array. If an expression matches the new file name  |
|                            |                |          | in the workspace, that file is ingested according to the other     |
|                            |                |          | fields in the JSON object and all subsequent rules in the list are |
|                            |                |          | ignored (first rule matched is applied).                           |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| .data_types                | Array          | Optional | Any file that matches the corresponding file name regular          |
|                            |                |          | expression will have these data type strings “tagged” with the     |
|                            |                |          | file. If not provided, data_types defaults to an empty array.      |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| .new_workspace             | String         | Optional | Specifies the name of a new workspace to which the file should be  |
|                            |                |          | copied. This allows the ingest process to move files to a different|
|                            |                |          | workspace after they appear in the scanned workspace.              |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| .new_file_path             | String         | Optional | Specifies a new relative path for storing new files. If            |
|                            |                |          | new_workspace is also specified, the file is moved to the new      |
|                            |                |          | workspace at this new path location (instead of using the current  |
|                            |                |          | path the new file originally came in on). If new_workspace is not  |
|                            |                |          | specified, the file is moved to this new path location within the  |
|                            |                |          | original scanned workspace. In either of these cases, three        |
|                            |                |          | additional and dynamically named directories, for the current year,|
|                            |                |          | month, and day, will be appended to the new_file_path value        |
|                            |                |          | automatically by the Scale system (i.e. workspace_path/YYYY/MM/DD).|
+----------------------------+----------------+----------+--------------------------------------------------------------------+