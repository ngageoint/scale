
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
                        "version": "1.0", 
                        "title": "Scale Strike", 
                        "description": "Monitors a directory for incoming source files to ingest", 
                        "category": "system", 
                        "author_name": null, 
                        "author_url": null, 
                        "is_system": true, 
                        "is_long_running": true, 
                        "is_active": true, 
                        "is_operational": true, 
                        "is_paused": false, 
                        "icon_code": "f0e7" 
                    }, 
                    "job_type_rev": { 
                        "id": 2 
                    }, 
                    "event": { 
                        "id": 1 
                    }, 
                    "status": "RUNNING", 
                    "priority": 10, 
                    "num_exes": 1 
                } 
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
|                    |                   | (See :ref:`Strike Details <rest_strike_details>`)                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .name              | String            | The identifying name of the Strike process used for queries.                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .title             | String            | The human readable display name of the Strike process.                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .description       | String            | A longer description of the Strike process.                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .job               | JSON Object       | The job that is associated with the Strike process.                            |
|                    |                   | (See :ref:`Job Details <rest_job_details>`)                                    |
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
            "version": "2.0", 
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
                "version": "1.0", 
                "title": "Scale Strike", 
                "description": "Monitors a directory for incoming source files to ingest", 
                "category": "system", 
                "author_name": null, 
                "author_url": null, 
                "is_system": true, 
                "is_long_running": true, 
                "is_active": true, 
                "is_operational": true, 
                "is_paused": false, 
                "icon_code": "f0e7" 
            }, 
            "job_type_rev": { 
                "id": 2 
            }, 
            "event": { 
                "id": 1 
            }, 
            "status": "RUNNING", 
            "priority": 10, 
            "num_exes": 1 
        }, 
        "configuration": { 
            "version": "2.0", 
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
|                    |                   |          | (See :ref:`architecture_strike_spec`)                               |
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
               "version": "1.0", 
               "title": "Scale Strike", 
               "description": "Monitors a directory for incoming source files to ingest", 
               "category": "system", 
               "author_name": null, 
               "author_url": null, 
               "is_system": true, 
               "is_long_running": true, 
               "is_active": true, 
               "is_operational": true, 
               "is_paused": false, 
               "icon_code": "f0e7" 
           }, 
           "job_type_rev": { 
               "id": 2 
           }, 
           "event": { 
               "id": 1 
           }, 
           "status": "RUNNING", 
           "priority": 10, 
           "num_exes": 1 
       }, 
       "configuration": { 
           "version": "2.0", 
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
|                    |                   | (See :ref:`architecture_strike_spec`)                                          |
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
            "version": "2.0", 
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
|                    |                   |          | (See :ref:`architecture_strike_spec`)                               |
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
            "version": "2.0", 
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
        "id": 1, 
        "name": "my-strike-process", 
        "title": "My Strike Process", 
        "description": "This is my Strike process for detecting my favorite files!", 
        "job": { 
            "id": 7, 
            "job_type": { 
                "id": 2, 
                "name": "scale-strike", 
                "version": "1.0", 
                "title": "Scale Strike", 
                "description": "Monitors a directory for incoming source files to ingest", 
                "category": "system", 
                "author_name": null, 
                "author_url": null, 
                "is_system": true, 
                "is_long_running": true, 
                "is_active": true, 
                "is_operational": true, 
                "is_paused": false, 
                "icon_code": "f0e7" 
            }, 
            "job_type_rev": { 
                "id": 2 
            }, 
            "event": { 
                "id": 1 
            }, 
            "status": "RUNNING", 
            "priority": 10, 
            "num_exes": 1 
        }, 
        "configuration": { 
            "version": "2.0", 
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
|                    |                   |          | (See :ref:`architecture_strike_spec`)                               |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
|                    | JSON Object       | All fields are the same as the Strike process details model.                   |
|                    |                   | (See :ref:`Strike Details <rest_strike_details>`)                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
