
.. _rest_metrics:

Metrics Services
========================================================================================================================

These services provide access to information about processing counts and timings.

.. _rest_metrics_list:

+-------------------------------------------------------------------------------------------------------------------------+
| **Metrics List**                                                                                                        |
+=========================================================================================================================+
| Returns a list of all metrics types.                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /metrics/                                                                                                       |
+-------------------------------------------------------------------------------------------------------------------------+
| **Query Parameters**                                                                                                    |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| page               | Integer           | Optional | The page of the results to return. Defaults to 1.                   |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| page_size          | Integer           | Optional | The size of the page to use for pagination of results.              |
|                    |                   |          | Defaults to 100, and can be anywhere from 1-1000.                   |
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
| .name              | String            | The stable name of the metrics type used for queries.                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .title             | String            | The human readable display name of the metrics type.                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .description       | String            | A longer description of the metrics type.                                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .filters           | Array             | The filter parameters that can be used to query the metrics type.              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..param            | String            | The stable name of the parameter used for queries.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..type             | String            | The data type of the parameter clients can use for validation.                 |
|                    |                   | Example: bool, date, datetime, float, int, string, time, int                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .groups            | Array             | The group definitions that can be used to select the results returned.         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..name             | String            | The stable name of the metrics group used for queries.                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..title            | String            | The human readable display name of the metrics group.                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..description      | String            | A longer description of the metrics group.                                     |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .columns           | Array             | The column definitions that can be used to select the results returned.        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..name             | String            | The stable name of the metrics column used for queries.                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..title            | String            | The human readable display name of the metrics column.                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..description      | String            | A longer description of the metrics column.                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..units            | String            | Each value for the metrics column is converted to this type of unit.           |
|                    |                   | Examples: count, seconds                                                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..group            | String            | Some metric columns are related together, which is indicated by the group name.|
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..aggregate        | String            | The math operation used to aggregate certain types of metrics.                 |
|                    |                   | Examples: avg, max, min, sum                                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "count": 10,                                                                                                     |
|        "next": null,                                                                                                    |
|        "previous": null,                                                                                                |
|        "results": [                                                                                                     |
|            {                                                                                                            |
|                "name": "job-types",                                                                                     |
|                "title": "Job Types",                                                                                    |
|                "description": "Metrics for jobs and executions grouped by job type.",                                   |
|                "filters": [                                                                                             |
|                    {                                                                                                    |
|                        "param": "name",                                                                                 |
|                        "type": "string"                                                                                 |
|                    },                                                                                                   |
|                    ...                                                                                                  |
|                ],                                                                                                       |
|                "groups": [                                                                                              |
|                    {                                                                                                    |
|                        "name": "overview",                                                                              |
|                        "title": "Overview",                                                                             |
|                        "description": "Overall counts based on job status."                                             |
|                    },                                                                                                   |
|                    ...                                                                                                  |
|                ],                                                                                                       |
|                "columns": [                                                                                             |
|                    {                                                                                                    |
|                        "name": "completed_count",                                                                       |
|                        "title": "Completed Count",                                                                      |
|                        "description": "Number of successfully completed jobs.",                                         |
|                        "units": "count",                                                                                |
|                        "group": "overview",                                                                             |
|                        "aggregate": "sum"                                                                               |
|                    },                                                                                                   |
|                    ...                                                                                                  |
|                ]                                                                                                        |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_metrics_details:

+-------------------------------------------------------------------------------------------------------------------------+
| **Metric Details**                                                                                                      |
+=========================================================================================================================+
| Returns a specific metrics type and all its related model information including possible filter choices.                |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /metrics/{name}/                                                                                                |
|         Where {name} is the system name of an existing model.                                                           |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| name               | String            | The stable name of the metrics type used for queries.                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| title              | String            | The human readable display name of the metrics type.                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| description        | String            | A longer description of the metrics type.                                      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| filters            | Array             | The filter parameters that can be used to query the metrics type.              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .param             | String            | The stable name of the parameter used for queries.                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .type              | String            | The data type of the parameter clients can use for validation.                 |
|                    |                   | Example: bool, date, datetime, float, int, string, time, int                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| columns            | Array             | The column definitions that can be used to select the results returned.        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .name              | String            | The stable name of the metrics column used for queries.                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .title             | String            | The human readable display name of the metrics column.                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .description       | String            | A longer description of the metrics column.                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .units             | String            | Each value for the metrics column is converted to this type of unit.           |
|                    |                   | Examples: count, seconds                                                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .group             | String            | Some metric columns are related together, which is indicated by the group name.|
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .aggregate         | String            | The math operation used to aggregate certain types of metrics.                 |
|                    |                   | Examples: avg, max, min, sum                                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| choices            | Array             | The related model choices that can be used to filter the metrics records. All  |
|                    |                   | of the filter parameters described above are fields within the model. The list |
|                    |                   | of choices allow clients to restrict filtering to only valid combinations. Each|
|                    |                   | choice model is specific to a metrics type and so the actual fields vary.      |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "name": "job-types",                                                                                             |
|        "title": "Job Types",                                                                                            |
|        "description": "Metrics for jobs and executions grouped by job type.",                                           |
|        "filters": [                                                                                                     |
|            {                                                                                                            |
|                "param": "name",                                                                                         |
|                "type": "string"                                                                                         |
|            },                                                                                                           |
|            {                                                                                                            |
|                "param": "version",                                                                                      |
|                "type": "string"                                                                                         |
|            }                                                                                                            |
|        ],                                                                                                               |
|        "columns": [                                                                                                     |
|            {                                                                                                            |
|                "name": "completed_count",                                                                               |
|                "title": "Completed Count",                                                                              |
|                "description": "Number of successfully completed jobs.",                                                 |
|                "units": "count",                                                                                        |
|                "group": "overview",                                                                                     |
|                "aggregate": "sum"                                                                                       |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|        "choices": [                                                                                                     |
|            {                                                                                                            |
|                "id": 4,                                                                                                 |
|                "name": "scale-clock",                                                                                   |
|                "version": "1.0",                                                                                        |
|                "title": "Scale Clock",                                                                                  |
|                "description": "Performs Scale system functions that need to be executed on regular time intervals",     | 
|                "category": "system",                                                                                    |
|                "author_name": null,                                                                                     |
|                "author_url": null,                                                                                      |
|                "is_system": true,                                                                                       |
|                "is_long_running": true,                                                                                 |
|                "is_active": true,                                                                                       |
|                "is_operational": true,                                                                                  |
|                "is_paused": false,                                                                                      |
|                "icon_code": "f013"                                                                                      |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_metrics_plot:

+-------------------------------------------------------------------------------------------------------------------------+
| **Metric Plot Data**                                                                                                    |
+=========================================================================================================================+
| Returns all the plot values for a metrics type based on optional query parameters.                                      |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /metrics/{name}/plot-data/                                                                                      |
|         Where {name} is the system name of an existing model.                                                           |
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
| choice_id          | Integer           | Optional | Return only metrics associated with the related model choice. Each  |
|                    |                   |          | of these values must be one of the items in the choices list.       |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
|                    |                   |          | When no choice filters are used, then values are aggregated across  |
|                    |                   |          | all the choices by date.                                            |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| column             | String            | Optional | Include only metrics with the given column name. The column name    |
|                    |                   |          | corresponds with a single statistic, such as completed count.       |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| group              | String            | Optional | Include only metrics with the given group name. The group name      |
|                    |                   |          | corresponds with a collection of related statistics.                |
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
| count              | Integer           | The total number of results that match the query parameters.                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| next               | URL               | A URL to the next page of results.                                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| previous           | URL               | A URL to the previous page of results.                                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| results            | Array             | List of result JSON objects that match the query parameters.                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .column            | Array             | The column definition of the selected plot data values.                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..name             | String            | The stable name of the metrics column used for queries.                        |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..title            | String            | The human readable display name of the metrics column.                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..description      | String            | A longer description of the metrics column.                                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..units            | String            | Each value for the metrics column is converted to this type of unit.           |
|                    |                   | Examples: count, seconds                                                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..group            | String            | Some metric columns are related together, which is indicated by the group name.|
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..aggregate        | String            | The math operation used to aggregate certain types of metrics.                 |
|                    |                   | Examples: avg, max, min, sum                                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .min_x             | ISO-8601 Date     | The minimum value within the x-axis for the metric column. The x-axis will     |
|                    |                   | always be based on time and consist of a single date.                          |
|                    |                   | Supports the ISO-8601 date format, (ex: 2015-01-01).                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .max_x             | ISO-8601 Date     | The maximum value within the x-axis for the metric column. The x-axis will     |
|                    |                   | always be based on time and consist of a single date.                          |
|                    |                   | Supports the ISO-8601 date format, (ex: 2015-12-31).                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .min_y             | Integer           | The minimum value within the y-axis for the metric column. The y-axis will     |
|                    |                   | always be a simple numeric value.                                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .max_y             | Integer           | The maximum value within the y-axis for the metric column. The y-axis will     |
|                    |                   | always be a simple numeric value.                                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .values            | Array             | List of plot value JSON objects for each choice and date in the data series.   |
|                    |                   | Note that the values are sorted oldest to newest.                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..id               | Integer           | The unique identifier of the related choice model for this data value.         |
|                    |                   | This field is omitted when there are no choice filters or only 1 specified.    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..date             | ISO-8601 Date     | The date when the plot value occurred.                                         |
|                    |                   | Uses the ISO-8601 date format, (ex: 2015-12-31).                               |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..value            | Integer           | The statistic value that was calculated for the date.                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "count": 28,                                                                                                     |
|        "next": null,                                                                                                    |
|        "previous": null,                                                                                                |
|        "results": [                                                                                                     |
|            {                                                                                                            |
|                "column": {                                                                                              |
|                    "name": "run_time_min",                                                                              |
|                    "title": "Run Time (Min)",                                                                           |
|                    "description": "Minimum time spent running the pre, job, and post tasks.",                           |
|                    "units": "seconds",                                                                                  |
|                    "group": "run_time",                                                                                 |
|                    "aggregate": "min"                                                                                   |
|                },                                                                                                       |
|                "min_x": "2015-10-05",                                                                                   |
|                "max_x": "2015-10-13",                                                                                   |
|                "min_y": 1,                                                                                              |
|                "max_y": 300,                                                                                            |
|                "values": [                                                                                              |
|                    {                                                                                                    |
|                        "id": 1,                                                                                         |
|                        "date": "2015-10-05",                                                                            |
|                        "value": 1                                                                                       |
|                    },                                                                                                   |
|                    ...                                                                                                  |
|                ]                                                                                                        |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+
