
.. _rest_v6_scan:

v6 Scan Services
================

These services allow a user to create, view, and manage Scan processes.

.. _rest_v6_scan_list:

**Example GET /v6/scans/ API call**

Request: GET http://.../v6/scans/

Response: 200 OK

 .. code-block:: javascript 
 
    { 
        "count": 3, 
        "next": null, 
        "previous": null, 
        "results": [ 
            { 
                "id": 1, 
                "name": "my-scan-process", 
                "title": "My Scan Process", 
                "description": "This is my Scan process for detecting my favorite files!", 
                "file_count": 50,
                "job": { 
                    "id": 7, 
                    "job_type": { 
                        "id": 2, 
                        "name": "scale-scan", 
                        "title": "Scale Scan", 
                        "description": "Scans a workspace for existing source files to ingest", 
                        "revision_num": 1,
                        "icon_code": "f0e7" 
                    }, 
                    "job_type_rev": { 
                        "id": 2 
                    }, 
                    "event": { 
                        "id": 1 
                    }, 
                    "node": { 
                        "id": 1 
                    }, 
                    "error": { 
                        "id": 1 
                    }, 
                    "status": "RUNNING", 
                    "priority": 10, 
                    "num_exes": 1 
                },
                "dry_run_job": { 
                    "id": 6, 
                    "job_type": { 
                        "id": 2, 
                        "name": "scale-scan", 
                        "title": "Scale scan", 
                        "description": "Scans a workspace for existing source files to ingest", 
                        "revision_num": 1,
                        "icon_code": "f0e7" 
                    }, 
                    "job_type_rev": { 
                        "id": 1 
                    }, 
                    "event": { 
                        "id": 1 
                    }, 
                    "node": { 
                        "id": 1 
                    }, 
                    "error": { 
                        "id": 1 
                    }, 
                    "status": "RUNNING", 
                    "priority": 10, 
                    "num_exes": 1 
                },
               "created": "2015-03-11T00:00:00Z",
               "last_modified": "2015-03-11T00:00:00Z"
            }, 
            ... 
        ] 
    } 

+-------------------------------------------------------------------------------------------------------------------------+
| **Scan List**                                                                                                           |
+=========================================================================================================================+
| Returns a list of all Scan processes.                                                                                   |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/scans/                                                                                                      |
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
|                    |                   | (See :ref:`Scan Details <rest_v6_scan_details>`)                               |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .name              | String            | The identifying name of the Scan process used for queries.                     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .title             | String            | The human readable display name of the Scan process.                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .description       | String            | A longer description of the Scan process.                                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .file_count        | Integer           | Count of files identified from last scan operation (either dry run or ingest). |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .job               | JSON Object       | The job that is associated with the Scan process.                              |
|                    |                   | (See :ref:`Job Details <rest_v6_job_details>`)                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .dry_run_job       | JSON Object       | The dry run job that is associated with the Scan process.                      |
|                    |                   | (See :ref:`Job Details <rest_v6_job_details>`)                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .created           | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .last_modified     | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+

.. _rest_v6_scan_create:

**Example POST /v6/scans/ API call**

Request: POST http://.../v6/scans/

 .. code-block:: javascript 
 
    { 
        "title": "My Scan Process", 
        "description": "This is my Scan process for detecting my favorite files!", 
        "configuration": { 
            "workspace": "my-workspace", 
            "scanner": { 
                "type": "dir",
            }, 
            "recursive": true, 
            "files_to_ingest": [{ 
                "filename_regex": ".*txt" 
            }] 
        } 
    } 

Response: 201 Created
Headers:
Location http://.../v6/scans/105/

 .. code-block:: javascript 
 
   { 
       "id": 1, 
       "name": "my-scan-process", 
       "title": "My Scan Process", 
       "description": "This is my Strike process for detecting my favorite files!", 
       "file_count": 50,
       "job": { 
           "id": 7, 
           "job_type": { 
               "id": 2, 
               "name": "scale-scan", 
               "title": "Scale Scan", 
               "description": "Scans a workspace for existing source files to ingest", 
               "revision_num": 1,
               "icon_code": "f0e7" 
           }, 
            "job_type_rev": { 
                "id": 2 
            }, 
            "event": { 
                "id": 1 
            }, 
            "node": { 
                "id": 1 
            }, 
            "error": { 
                "id": 1 
            }, 
           "status": "RUNNING", 
           "priority": 10, 
           "num_exes": 1 
       },
       "dry_run_job": { 
           "id": 6, 
           "job_type": { 
               "id": 2, 
               "name": "scale-scan", 
               "title": "Scale Scan", 
               "description": "Scans a workspace for existing source files to ingest", 
               "revision_num": 1,
               "icon_code": "f0e7" 
           }, 
            "job_type_rev": { 
                "id": 2 
            }, 
            "event": { 
                "id": 1 
            }, 
            "node": { 
                "id": 1 
            }, 
            "error": { 
                "id": 1 
            }, 
           "status": "RUNNING", 
           "priority": 10, 
           "num_exes": 1 
       },
       "created": "2015-03-11T00:00:00Z",
       "last_modified": "2015-03-11T00:00:00Z",
       "configuration": { 
           "workspace": "my-workspace", 
           "monitor": { 
               "type": "dir"
           }, 
           "recursive": true, 
           "files_to_ingest": [{ 
               "filename_regex": ".*txt" 
           }] 
       } 
   } 

+-------------------------------------------------------------------------------------------------------------------------+
| **Create Scan**                                                                                                         |
+=========================================================================================================================+
| Creates a new Scan. To start a dry run or actual scan job, use the */scans/{id}/process/* endpoint.                     |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /v6/scans/                                                                                                     |
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
|                    |                   | (See :ref:`Strike Details <rest_v6_scan_details>`)                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+

.. _rest_v6_scan_details:

**Example GET /v6/scans/{id}/ API call**

Request: GET http://.../v6/scans/{id}/

Response: 200 OK

 .. code-block:: javascript 
 
   { 
       "id": 1, 
       "name": "my-scan-process", 
       "title": "My Scan Process", 
       "description": "This is my Strike process for detecting my favorite files!", 
       "file_count": 50,
       "job": { 
           "id": 7, 
           "job_type": { 
               "id": 2, 
               "name": "scale-scan", 
               "title": "Scale Scan", 
               "description": "Scans a workspace for existing source files to ingest", 
               "revision_num": 1,
               "icon_code": "f0e7" 
           }, 
            "job_type_rev": { 
                "id": 2 
            }, 
            "event": { 
                "id": 1 
            }, 
            "node": { 
                "id": 1 
            }, 
            "error": { 
                "id": 1 
            }, 
           "status": "RUNNING", 
           "priority": 10, 
           "num_exes": 1 
       },
       "dry_run_job": { 
           "id": 6, 
           "job_type": { 
               "id": 2, 
               "name": "scale-scan", 
               "title": "Scale Scan", 
               "description": "Scans a workspace for existing source files to ingest", 
               "revision_num": 1,
               "icon_code": "f0e7" 
           }, 
            "job_type_rev": { 
                "id": 2 
            }, 
            "event": { 
                "id": 1 
            }, 
            "node": { 
                "id": 1 
            }, 
            "error": { 
                "id": 1 
            }, 
           "status": "RUNNING", 
           "priority": 10, 
           "num_exes": 1 
       },
       "created": "2015-03-11T00:00:00Z",
       "last_modified": "2015-03-11T00:00:00Z",
       "configuration": { 
           "workspace": "my-workspace", 
           "monitor": { 
               "type": "dir"
           }, 
           "recursive": true, 
           "files_to_ingest": [{ 
               "filename_regex": ".*txt" 
           }] 
       } 
   } 
   
+-------------------------------------------------------------------------------------------------------------------------+
| **Scan Details**                                                                                                        |
+=========================================================================================================================+
| Returns Scan process details                                                                                            |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/scans/{id}/                                                                                                 |
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
|                    |                   | (See :ref:`Strike Details <rest_v6_scan_details>`)                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| name               | String            | The identifying name of the Scan process used for queries.                     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| title              | String            | The human readable display name of the Scan process.                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| description        | String            | A longer description of the Scan process.                                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| file_count         | Integer           | Count of files identified from last scan operation (either dry run or ingest). |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| job                | JSON Object       | The job that is associated with the Scan process.                              |
|                    |                   | (See :ref:`Job Details <rest_v6_job_details>`)                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| dry_run_job        | JSON Object       | The dry run job that is associated with the Scan process.                      |
|                    |                   | (See :ref:`Job Details <rest_v6_job_details>`)                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| created            | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| last_modified      | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| configuration      | JSON Object       | JSON defining the Scan configuration.                                          |
|                    |                   | (See :ref:`architecture_scan_spec`)                                            |
+--------------------+-------------------+--------------------------------------------------------------------------------+

.. _rest_v6_scan_validate:

**Example POST /v6/scans/validation/ API call**

Request: POST http://.../v6/scans/validation/

.. code-block:: javascript 

    { 
        "title": "My Scan Process", 
        "description": "This is my Scan process for detecting my favorite files!", 
        "configuration": { 
            "workspace": "my-workspace", 
            "monitor": { 
                "type": "dir"
            },
            "recursive": true,
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
| **Validate Scan**                                                                                                       |
+=========================================================================================================================+
| Validates a new Scan process configuration without actually saving it                                                   |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /v6/scans/validation/                                                                                          |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| title              | String            | Required | The human readable display name of the Scan process.                |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| description        | String            | Optional | A longer description of the Scan process.                           |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| configuration      | JSON Object       | Required | JSON defining the Scan configuration.                               |
|                    |                   |          | (See :ref:`architecture_scan_spec`)                                 |
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

.. _rest_v6_scan_edit:

**Example PATCH /v6/scans/{id}/ API call**

Request: PATCH http://.../v6/scans/{id}/

.. code-block:: javascript 
 
    { 
        "title": "My Scan Process", 
        "description": "This is my Scan process for detecting my favorite files!", 
        "configuration": { 
            "workspace": "my-workspace", 
            "monitor": { 
                "type": "dir" 
            }, 
            "recursive": true,
            "files_to_ingest": [{ 
                "filename_regex": ".*txt" 
            }] 
        } 
    }

Response: 204 NO CONTENT
    
+-------------------------------------------------------------------------------------------------------------------------+
| **Edit Scan**                                                                                                           |
+=========================================================================================================================+
| Edits an existing Scan process with associated configuration                                                            |
+-------------------------------------------------------------------------------------------------------------------------+
| **PATCH** /v6/scans/{id}/                                                                                               |
|           Where {id} is the unique identifier of an existing model.                                                     |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| title              | String            | Optional | The human readable display name of the Scan process.                |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| description        | String            | Optional | A longer description of the Scan process.                           |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| configuration      | JSON Object       | Optional | JSON defining the Scan configuration.                               |
|                    |                   |          | (See :ref:`architecture_scan_spec`)                                 |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 204 No Content                                                                                     |
+--------------------+----------------------------------------------------------------------------------------------------+

.. _rest_v6_scan_process:

**Example PATCH /v6/scans/{id}/ API call**

Request: PATCH http://.../v6/scans/{id}/

 .. code-block:: javascript 
 
  { 
    "ingest": true 
  } 

Response: 201 OK
Headers:
Location http://.../v6/scans/105/

 .. code-block:: javascript 
 
   { 
       "id": 1, 
       "name": "my-scan-process", 
       "title": "My Scan Process", 
       "description": "This is my Strike process for detecting my favorite files!", 
       "file_count": 50,
       "job": { 
           "id": 7, 
           "job_type": { 
               "id": 2, 
               "name": "scale-scan", 
               "title": "Scale Scan", 
               "description": "Scans a workspace for existing source files to ingest", 
               "revision_num": 1,
               "icon_code": "f0e7" 
           }, 
            "job_type_rev": { 
                "id": 2 
            }, 
            "event": { 
                "id": 1 
            }, 
            "node": { 
                "id": 1 
            }, 
            "error": { 
                "id": 1 
            }, 
           "status": "RUNNING", 
           "priority": 10, 
           "num_exes": 1 
       },
       "dry_run_job": { 
           "id": 6, 
           "job_type": { 
               "id": 2, 
               "name": "scale-scan", 
               "title": "Scale Scan", 
               "description": "Scans a workspace for existing source files to ingest", 
               "revision_num": 1,
               "icon_code": "f0e7" 
           }, 
            "job_type_rev": { 
                "id": 2 
            }, 
            "event": { 
                "id": 1 
            }, 
            "node": { 
                "id": 1 
            }, 
            "error": { 
                "id": 1 
            }, 
           "status": "RUNNING", 
           "priority": 10, 
           "num_exes": 1 
       },
       "created": "2015-03-11T00:00:00Z",
       "last_modified": "2015-03-11T00:00:00Z",
       "configuration": { 
           "workspace": "my-workspace", 
           "monitor": { 
               "type": "dir"
           }, 
           "recursive": true, 
           "files_to_ingest": [{ 
               "filename_regex": ".*txt" 
           }] 
       } 
   } 

+-------------------------------------------------------------------------------------------------------------------------+
| **Process Scan**                                                                                                        |
+=========================================================================================================================+
| Launches an existing Scan with associated configuration                                                                 |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /scans/{id}/process/                                                                                           |
|           Where {id} is the unique identifier of an existing model.                                                     |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| ingest             | Boolean           | Optional | Whether a dry run or ingest triggering scan should be run.          |
|                    |                   |          | Defaults to false when unset.                                       |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 201 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Location**       | URL pointing to the details of the Scan model used to launch process                               |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| id                 | Integer           | The unique identifier of the model. Can be passed to the details API.          |
|                    |                   | (See :ref:`Scan Details <rest_v6_scan_details>`)                               |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| name               | String            | The identifying name of the Scan process used for queries.                     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| title              | String            | The human readable display name of the Scan process.                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| description        | String            | A longer description of the Scan process.                                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| file_count         | Integer           | Count of files identified from last scan operation (either dry run or ingest). |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| job                | JSON Object       | The job that is associated with the Scan process.                              |
|                    |                   | (See :ref:`Job Details <rest_v6_job_details>`)                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| dry_run_job        | JSON Object       | The dry run job that is associated with the Scan process.                      |
|                    |                   | (See :ref:`Job Details <rest_v6_job_details>`)                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| created            | ISO-8601 Datetime | When the associated database model was initially created.                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| last_modified      | ISO-8601 Datetime | When the associated database model was last saved.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| configuration      | JSON Object       | JSON defining the Scan configuration.                                          |
|                    |                   | (See :ref:`architecture_scan_spec`)                                            |
+--------------------+-------------------+--------------------------------------------------------------------------------+