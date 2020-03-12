
.. _rest_v6_timeline:

v6 Timeline Services
====================

These services provide access to information about the timeline functionality.

.. _rest_v6_timeline_recipes:

v6 Recipe Types
--------------

**Example GET /v6/timeline/recipe-types API call**

Request: GET http://.../v6/timeline/recipe-types/

Response: 200 OK

 .. code-block:: javascript

    {
        "count": 1,
        "next": null,
        "previous": null,
        "results": [
            {
                "recipe_type_id": 1,
                "name": "recipe-type-name",
                "title": "Recipe Type Title",
                "revision_num": 1,
                "results": [{
                    "date": "2015-03-11T00:00:00Z",
                    "count": 457
                }]
            }
        ]
    }

+------------------------------------------------------------------------------------------------------------------------------+
| **Timeline Recipe Types List**                                                                                               |
+==============================================================================================================================+
| Returns a list of recipe types that were started between the given dates                                                     |
+------------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/timeline/recipe-types/                                                                                                          |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| **Query Parameters**                                                                                                         |
+--------------------+-------------------+----------+--------------------------------------------------------------------------+
| page               | Integer           | Optional | The page of the results to return. Defaults to 1.                        |
+--------------------+-------------------+----------+--------------------------------------------------------------------------+
| page_size          | Integer           | Optional | The size of the page to use for pagination of results.                   |
|                    |                   |          | Defaults to 100, and can be anywhere from 1-1000.                        |
+--------------------+-------------------+----------+--------------------------------------------------------------------------+
| started            | ISO-8601 Datetime | Required | The start of the time range to query.                                    |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z).      |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).                   |
+--------------------+-------------------+----------+--------------------------------------------------------------------------+
| ended              | ISO-8601 Datetime | Optional | End of the time range to query, defaults to the current time.            |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z).      |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).                   |
+--------------------+-------------------+----------+--------------------------------------------------------------------------+
| recipe_type_id     | Integer           | Optional | Return timeline information matching only the given id(s). Duplicate for |
|                    |                   |          | multiple.                                                                |
+--------------------+-------------------+----------+--------------------------------------------------------------------------+
| recipe_type_name   | String            | Optional | Return timeline information matching only the given name(s). Duplicate   |
|                    |                   |          | for multiple.                                                            |
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
| .recipe_type_id    | Integer           | The unique identifier of the recipe type.                                           |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| .name              | String            | The name (key) of the recipe type.                                                  |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| .title             | String            | The title of the recipe type.                                                       |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| .revision_num      | Integer           | The revision number of the recipe type.                                             |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| .results           | Array             | Lists the dates and counts of recipe types.                                         |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| .date              | ISO-8601 Datetime | The date of the count.                                                              |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| .count             | Integer           | Number of recipe types that were started on that date.                              |
+--------------------+-------------------+-------------------------------------------------------------------------------------+

.. _rest_v6_timeline_jobs:

v6 Job Types
--------------

**Example GET /v6/timeline/job-types API call**

Request: GET http://.../v6/timeline/job-types/

Response: 200 OK

 .. code-block:: javascript

    {
        "count": 1,
        "next": null,
        "previous": null,
        "results": [
            {
                "job_type_id": 1,
                "name": "job-type-name",
                "version": "1.0.0,
                "title": "Job Type Title",
                "revision_num": 1,
                "results": [{
                    "date": "2015-03-11T00:00:00Z",
                    "count": 338
                }]
            }
        ]
    }

+------------------------------------------------------------------------------------------------------------------------------+
| **Timeline Job Types List**                                                                                                  |
+==============================================================================================================================+
| Returns a  list of job types that were started between the given dates                                                       |
+------------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/timeline/job-types/                                                                                              |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| **Query Parameters**                                                                                                         |
+--------------------+-------------------+----------+--------------------------------------------------------------------------+
| page               | Integer           | Optional | The page of the results to return. Defaults to 1.                        |
+--------------------+-------------------+----------+--------------------------------------------------------------------------+
| page_size          | Integer           | Optional | The size of the page to use for pagination of results.                   |
|                    |                   |          | Defaults to 100, and can be anywhere from 1-1000.                        |
+--------------------+-------------------+----------+--------------------------------------------------------------------------+
| started            | ISO-8601 Datetime | Required | The start of the time range to query.                                    |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z).      |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).                   |
+--------------------+-------------------+----------+--------------------------------------------------------------------------+
| ended              | ISO-8601 Datetime | Optional | End of the time range to query, defaults to the current time.            |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z).      |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).                   |
+--------------------+-------------------+----------+--------------------------------------------------------------------------+
| job_type_id        | Integer           | Optional | Return timeline information matching only the given id(s). Duplicate for |
|                    |                   |          | multiple.                                                                |
+--------------------+-------------------+----------+--------------------------------------------------------------------------+
| job_type_name      | String            | Optional | Return timeline information matching only the given name(s). Duplicate   |
|                    |                   |          | for multiple.                                                            |
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
| .job_type_id       | Integer           | The unique identifier of the job type.                                              |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| .name              | String            | The name (key) of the job type.                                                     |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| .version           | String            | The job type version.                                                               |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| .title             | String            | The title of the job type.                                                          |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| .revision_num      | Integer           | The revision number of the job type.                                                |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| .results           | Array             | Lists the dates and counts of job types.                                            |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| .date              | ISO-8601 Datetime | The date of the count.                                                              |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
| .count             | Integer           | Number of job types that were started on that date.                                 |
+--------------------+-------------------+-------------------------------------------------------------------------------------+
