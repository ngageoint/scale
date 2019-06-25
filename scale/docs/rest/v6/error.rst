
.. _rest_v6_error:

v6 Error Services
=================

These services provide access to information about registered errors and error mappings.

.. _rest_v6_error_list:

v6 List Errors
--------------

**Example GET /v6/errors/ API call**

Request: GET http://.../v6/errors/

Response: 200 OK

 .. code-block:: javascript

    {
        "count": 1,
        "next": null,
        "previous": null,
        "results": [
            {
                "id": 1,
                "name": "unknown",
                "title": "Unknown",
                "description": "The error that caused the failure is unknown.",
                "job_type_name": "job-type",
                "category": "SYSTEM",
                "is_builtin": true,
                "should_be_retried": true,
                "created": "2015-03-11T00:00:00Z",
                "last_modified": "2015-03-11T00:00:00Z"
            }
        ]
    }

+------------------------------------------------------------------------------------------------------------------------------+
| **Error List**                                                                                                               |
+==============================================================================================================================+
| Returns a list of all errors.                                                                                                |
+------------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/errors/                                                                                                          |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| **Query Parameters**                                                                                                         |
+--------------------+-------------------+----------+--------------------------------------------------------------------------+
| page               | Integer           | Optional | The page of the results to return. Defaults to 1.                        |
+--------------------+-------------------+----------+--------------------------------------------------------------------------+
| page_size          | Integer           | Optional | The size of the page to use for pagination of results.                   |
|                    |                   |          | Defaults to 100, and can be anywhere from 1-1000.                        |
+--------------------+-------------------+----------+--------------------------------------------------------------------------+
| started            | ISO-8601 Datetime | Optional | The start of the time range to query.                                    |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z).      |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).                   |
+--------------------+-------------------+----------+--------------------------------------------------------------------------+
| ended              | ISO-8601 Datetime | Optional | End of the time range to query, defaults to the current time.            |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z).      |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).                   |
+--------------------+-------------------+----------+--------------------------------------------------------------------------+
| is_builtin         | Boolean           | Optional | Return only errors matching the is_builtin flag                          |
+--------------------+-------------------+----------+--------------------------------------------------------------------------+
| job_type_name      | String            | Optional | Return only errors for job types with the given name (any version)       |
+--------------------+-------------------+----------+--------------------------------------------------------------------------+
| name               | String            | Optional | Return only errors with the given name                                   |
+--------------------+-------------------+----------+--------------------------------------------------------------------------+
| category           | String            | Optional | Return only errors with the specified category                           |
+--------------------+-------------------+----------+--------------------------------------------------------------------------+
| order              | String            | Optional | One or more fields to use when ordering the results.                     |
|                    |                   |          | Include multiple times to multi-sort, (ex: order=name&order=version).    |
|                    |                   |          | Prefix the field with a dash '-' to reverse the order, (ex: order=-name).|
+--------------------+-------------------+----------+--------------------------------------------------------------------------+
| **Successful Response**                                                                                                      |
+--------------------+---------------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                                  |
+--------------------+---------------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                      |
+--------------------+---------------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                              |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| count              | Integer           | The total number of results that match the query parameters.                        |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| next               | URL               | A URL to the next page of results.                                                  |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| previous           | URL               | A URL to the previous page of results.                                              |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| results            | Array             | List of result JSON objects that match the query parameters.                        |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| .id                | Integer           | The unique identifier of the model. Can be passed to the details API call.          |
|                    |                   | (See :ref:`Error Details <rest_v6_error_details>`)                                  |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| .name              | String            | The identifying name of the error used for queries.                                 |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| .title             | String            | The human readable display name of the error.                                       |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| .description       | String            | A longer description of the error.                                                  |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| .job_type_name     | String            | The name of the job type that relates to this error.                                |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| .category          | String            | The category of the error. Choices: [SYSTEM, ALGORITHM, DATA].                      |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| .is_builtin        | Boolean           | Whether the error was loaded during the installation process.                       |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| .should_be_retried | Boolean           | Whether jobs with this error should be retried automatically. The following builtin |
|                    |                   | errors are retried automatically: Unknown, Database, Database Operation, Filesystem |
|                    |                   | I/O, Ingest Timeout, Task Launch, Docker Launch, Docker Terminated, Node Lost,      |
|                    |                   | Resource Starvation, Launch Timeout, Pull-task Timeout, Pre-task Timeout,           |
|                    |                   | Post-task Timeout, Timeout (System), Docker Pull Failed, Scheduler Restarted        |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| .created           | ISO-8601 Datetime | When the associated database model was initially created.                           |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| .last_modified     | ISO-8601 Datetime | When the associated database model was last saved.                                  |
+--------------------+-------------------+-------------------------------------------------------------------------------------+

.. _rest_v6_error_details:

v6 Error Details
----------------

**Example GET /v6/errors/{id}/ API call**

Request: GET http://.../v6/errors/{id}/

Response: 200 OK

 .. code-block:: javascript

    {
        "id": 1,
        "name": "unknown",
        "title": "Unknown",
        "description": "The error that caused the failure is unknown.",
        "job_type_name": "job-type",
        "category": "SYSTEM",
        "is_builtin": true,
        "should_be_retried": true,
        "created": "2015-03-11T00:00:00Z",
        "last_modified": "2015-03-11T00:00:00Z"
    }

+------------------------------------------------------------------------------------------------------------------------------+
| **Error Details**                                                                                                            |
+==============================================================================================================================+
| Returns the details for an error with the given id.                                                                          |
+------------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/errors/{id}/                                                                                                     |
|         Where {id} is the unique identifier of an existing model.                                                            |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                      |
+--------------------+---------------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                                  |
+--------------------+---------------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                      |
+--------------------+---------------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                              |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| id                 | Integer           | The unique identifier of the model.                                                 |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| name               | String            | The identifying name of the error used for queries.                                 |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| title              | String            | The human readable display name of the error.                                       |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| description        | String            | A longer description of the error.                                                  |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| job_type_name      | String            | The name of the job type that relates to this error.                                |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| category           | String            | The category of the error. Choices: [SYSTEM, ALGORITHM, DATA].                      |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| is_builtin         | Boolean           | Whether the error was loaded during the installation process.                       |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| should_be_retried  | Boolean           | Whether jobs with this error should be retried automatically. The following builtin |
|                    |                   | errors are retried automatically: Unknown, Database, Database Operation, Filesystem |
|                    |                   | I/O, Ingest Timeout, Task Launch, Docker Launch, Docker Terminated, Node Lost,      |
|                    |                   | Resource Starvation, Launch Timeout, Pull-task Timeout, Pre-task Timeout,           |
|                    |                   | Post-task Timeout, Timeout (System), Docker Pull Failed, Scheduler Restarted        |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| created            | ISO-8601 Datetime | When the associated database model was initially created.                           |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| last_modified      | ISO-8601 Datetime | When the associated database model was last saved.                                  |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
