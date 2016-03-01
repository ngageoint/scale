
.. _rest_job_type:

Job Type Services
=================

These services provide access to information about job types.

.. _rest_job_type_list:

+-------------------------------------------------------------------------------------------------------------------------+
| **Job Type List**                                                                                                       |
+=========================================================================================================================+
| Returns a list of all job types.                                                                                        |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /job-types/                                                                                                     |
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
| name               | String            | Optional | Return only job types with a given name.                            |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| category           | String            | Optional | Return only job types with a given category.                        |
|                    |                   |          | Duplicate it to filter by multiple values.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| order              | String            | Optional | One or more fields to use when ordering the results.                |
|                    |                   |          | Duplicate it to multi-sort, (ex: order=name&order=version).         |
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
|                          |                   | (See :ref:`Job Type Details <rest_job_type_details>`)                    |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .name                    | String            | The stable name of the job type used for queries.                        |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .version                 | String            | The version of the job type.                                             |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .title                   | String            | The human readable display name of the job type.                         |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .description             | String            | A longer description of the job type.                                    |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .category                | String            | An optional overall category of the job type.                            |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .author_name             | String            | The name of the person or organization that created the job algorithm.   |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .author_url              | String            | The address to a home page about the author or associated algorithm.     |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .is_system               | Boolean           | Whether this is a system type.                                           |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .is_long_running         | Boolean           | Whether this type is long running. A job of this type is intended to run |
|                          |                   | for a long time, potentially indefinitely, without timing out and always |
|                          |                   | being re-queued after a failure.                                         |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .is_active               | Boolean           | Whether the job type is active (false once job type is archived).        |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .is_paused               | Boolean           | Whether the job type is paused (while paused no jobs of this type will be|
|                          |                   | scheduled off of the queue).                                             |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .icon_code               | String            | A font-awesome icon code to use when representing this job type.         |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .uses_docker             | Boolean           | Whether the job type uses Docker.                                        |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .docker_image            | String            | The Docker image containing the code to run for this job.                |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .revision_num            | Integer           | The current revision number of the job type, incremented for each edit.  |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .priority                | Integer           | The priority of the job type (lower number is higher priority).          |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .timeout                 | Integer           | The maximum amount of time to allow a job of this type to run            |
|                          |                   | before being killed (in seconds).                                        |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .max_scheduled           | Integer           | An optional number indicating the maximum number of jobs of this type    |
|                          |                   | that may be scheduled to run at the same time. May be 'null'.            |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .max_tries               | Integer           | The maximum number of times to try executing a job in case of errors.    |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .cpus_required           | Decimal           | The number of CPUs needed for a job of this type.                        |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .mem_required            | Decimal           | The amount of RAM in MiB needed for a job of this type.                  |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .disk_out_const_required | Decimal           | A constant amount of disk space in MiB required for job output.          |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .disk_out_mult_required  | Decimal           | A multiplier (2x = 2.0) applied to the size of the input files to        |
|                          |                   | determine additional disk space in MiB required for job output.          |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .created                 | ISO-8601 Datetime | When the associated database model was initially created.                |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .archived                | ISO-8601 Datetime | When the job type was archived (no longer active).                       |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .paused                  | ISO-8601 Datetime | When the job type was paused.                                            |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .last_modified           | ISO-8601 Datetime | When the associated database model was last saved.                       |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "count": 23,                                                                                                     |
|        "next": null,                                                                                                    |
|        "previous": null,                                                                                                |
|        "results": [                                                                                                     |
|            {                                                                                                            |
|                "id": 3,                                                                                                 |
|                "name": "scale-clock",                                                                                   |
|                "version": "1.0",                                                                                        |
|                "title": "Scale Clock",                                                                                  |
|                "description": "Monitors a directory for incoming files to ingest",                                      |
|                "category": "system",                                                                                    |
|                "author_name": null,                                                                                     |
|                "author_url": null,                                                                                      |
|                "is_system": true,                                                                                       |
|                "is_long_running": true,                                                                                 |
|                "is_active": true,                                                                                       |
|                "is_operational": true,                                                                                  |
|                "is_paused": false,                                                                                      |
|                "icon_code": "f013",                                                                                     |
|                "uses_docker": false,                                                                                    |
|                "docker_privileged": false,                                                                              |
|                "docker_image": null,                                                                                    |
|                "revision_num": 1,                                                                                       |
|                "priority": 1,                                                                                           |
|                "timeout": 0,                                                                                            |
|                "max_scheduled": 1,                                                                                      |
|                "max_tries": 0,                                                                                          |
|                "cpus_required": 0.5,                                                                                    |
|                "mem_required": 64.0,                                                                                    |
|                "disk_out_const_required": 64.0,                                                                         |
|                "disk_out_mult_required": 0.0,                                                                           |
|                "created": "2015-03-11T00:00:00Z",                                                                       |
|                "archived": null,                                                                                        |
|                "paused": null,                                                                                          |
|                "last_modified": "2015-03-11T00:00:00Z"                                                                  |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_job_type_create:

+-------------------------------------------------------------------------------------------------------------------------+
| **Create Job Type**                                                                                                     |
+=========================================================================================================================+
| Creates a new job type with associated interface and error mapping                                                      |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /job-types/                                                                                                    |
+-------------------------+-----------------------------------------------------------------------------------------------+
| **Content Type**        | *application/json*                                                                            |
+-------------------------+-----------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| name                    | String            | Required | The stable name of job type used for queries.                  |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| version                 | String            | Required | The version of the job type.                                   |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| title                   | String            | Optional | The human-readable name of the job type.                       |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| description             | String            | Optional | An optional description of the job type.                       |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| category                | String            | Optional | An optional overall category of the job type.                  |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| author_name             | String            | Optional | The name of the person or organization that created the        |
|                         |                   |          | algorithm associated with the job type.                        |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| author_url              | String            | Optional | The address to a home page about the author or associated      |
|                         |                   |          | algorithm run by the job type.                                 |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| is_long_running         | Boolean           | Optional | Whether this type is long running. A job of this type is       |
|                         |                   |          | intended to run for a long time, potentially indefinitely,     |
|                         |                   |          | without timing out and always being re-queued after a failure. |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| is_paused               | Boolean           | Optional | Whether the job type is paused (while paused no jobs of this   |
|                         |                   |          | type will be scheduled off of the queue).                      |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| icon_code               | String            | Optional | A font-awesome icon code to use when displaying this job type. |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| docker_image            | String            | Optional | The Docker image containing the code to run for this job.      |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| priority                | Integer           | Optional | The priority of the job type (lower number is higher priority).|
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| timeout                 | Integer           | Optional | The maximum amount of time to allow a job of this type to run  |
|                         |                   |          | before being killed (in seconds).                              |
+-------------------------+-------------------+---------------------------------------------------------------------------+
| max_scheduled           | Integer           | Optional | Indicates the maximum number of jobs of this type that may be  |
|                         |                   |          | scheduled to run at the same time.                             |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| max_tries               | Integer           | Optional | The maximum number of times to try executing a job when failed.|
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| cpus_required           | Decimal           | Optional | The number of CPUs needed for a job of this type.              |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| mem_required            | Decimal           | Optional | The amount of RAM in MiB needed for a job of this type.        |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| disk_out_const_required | Decimal           | Optional | A constant amount of disk space in MiB required for job output.|
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| disk_out_mult_required  | Decimal           | Optional | A multiplier (2x = 2.0) applied to the size of input files to  |
|                         |                   |          | determine additional disk space in MiB required for job output.|
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| interface               | JSON Object       | Required | JSON description of the interface for running the job.         |
|                         |                   |          | (See :ref:`architecture_jobs_interface_spec`)                  |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| error_mapping           | JSON Object       | Optional | JSON description that maps exit codes to known error models.   |
|                         |                   |          | (See :ref:`architecture_errors_interface_spec`)                |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| trigger_rule            | JSON Object       | Optional | A linked trigger rule that automatically invokes the job type. |
|                         |                   |          | Type and configuration fields are required if setting a rule.  |
|                         |                   |          | The is_active field is optional and can be used to pause.      |
|                         |                   |          | (See :ref:`Trigger Rule Details <rest_trigger_rule_details>`   |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "name": "my-job",                                                                                                |
|        "version": "1.0",                                                                                                |
|        "title": "My Job",                                                                                               |
|        "description": "This is a description of the job",                                                               |
|        "category": "test",                                                                                              |
|        "author_name": null,                                                                                             |
|        "author_url": null,                                                                                              |
|        "is_long_running": false,                                                                                        |
|        "is_operational": true,                                                                                          |
|        "is_paused": false,                                                                                              |
|        "icon_code": "f1c5",                                                                                             |
|        "docker_privileged": false,                                                                                      |
|        "docker_image": null,                                                                                            |
|        "priority": 1,                                                                                                   |
|        "timeout": 0,                                                                                                    |
|        "max_tries": 0,                                                                                                  |
|        "cpus_required": 0.5,                                                                                            |
|        "mem_required": 64.0,                                                                                            |
|        "disk_out_const_required": 64.0,                                                                                 |
|        "disk_out_mult_required": 0.0,                                                                                   |
|        "interface": {                                                                                                   |
|            "version": "1.0",                                                                                            |
|            "command": "test_cmd",                                                                                       |
|            "command_arguments": "test_arg",                                                                             |
|            "input_data": [                                                                                              |
|                {                                                                                                        |
|                    "media_types": ["image/png"],                                                                        |
|                    "type": "file",                                                                                      |
|                    "name": "input_file"                                                                                 |
|                }                                                                                                        |
|            ],                                                                                                           |
|            "output_data": [],                                                                                           |
|            "shared_resources": []                                                                                       |
|        },                                                                                                               |
|        "error_mapping": {                                                                                               |
|            "version": "1.0",                                                                                            |
|            "exit_codes": {                                                                                              |
|                "1": "unknown"                                                                                           |
|            }                                                                                                            |
|        },                                                                                                               |
|        "trigger_rule": {                                                                                                |
|            "type": "PARSE",                                                                                             |
|            "is_active": true,                                                                                           |
|            "configuration": {                                                                                           |
|                "version": "1.0",                                                                                        |
|                "condition": {                                                                                           |
|                    "media_type": "image/png",                                                                           |
|                    "data_types": []                                                                                     |
|                },                                                                                                       |
|                "data": {                                                                                                |
|                    "input_data_name": "input_file",                                                                     |
|                    "workspace_name": "rs"                                                                               |
|                }                                                                                                        |
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
|                    | JSON Object       | All fields are the same as the job type details model.                         |
|                    |                   | (See :ref:`Job Type Details <rest_job_type_details>`)                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "id": 100,                                                                                                       |
|        "name": "my-job",                                                                                                |
|        "version": "1.0",                                                                                                |
|        "title": "My Job",                                                                                               |
|        "description": "This is a description of the job",                                                               |
|        "category": "test",                                                                                              |
|        "author_name": null,                                                                                             |
|        "author_url": null,                                                                                              |
|        "is_system": false,                                                                                              |
|        "is_long_running": false,                                                                                        |
|        "is_active": true,                                                                                               |
|        "is_operational": true,                                                                                          |
|        "is_paused": false,                                                                                              |
|        "icon_code": "f1c5",                                                                                             |
|        "uses_docker": true,                                                                                             |
|        "docker_privileged": false,                                                                                      |
|        "docker_image": null,                                                                                            |
|        "revision_num": 1,                                                                                               |
|        "priority": 1,                                                                                                   |
|        "timeout": 0,                                                                                                    |
|        "max_scheduled": null,                                                                                           |
|        "max_tries": 0,                                                                                                  |
|        "cpus_required": 0.5,                                                                                            |
|        "mem_required": 64.0,                                                                                            |
|        "disk_out_const_required": 64.0,                                                                                 |
|        "disk_out_mult_required": 0.0,                                                                                   |
|        "created": "2015-03-11T00:00:00Z",                                                                               |
|        "archived": null,                                                                                                |
|        "paused": null,                                                                                                  |
|        "last_modified": "2015-03-11T00:00:00Z",                                                                         |
|        "interface": {...},                                                                                              |
|        "error_mapping": {...},                                                                                          |
|        "errors": [...],                                                                                                 |
|        "job_counts_6h": [...],                                                                                          |
|        "job_counts_12h": [...],                                                                                         |
|        "job_counts_24h": [...]                                                                                          |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_job_type_validate:

+-------------------------------------------------------------------------------------------------------------------------+
| **Validate Job Type**                                                                                                   |
+=========================================================================================================================+
| Validates a new job type without actually saving it                                                                     |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /job-types/validation/                                                                                         |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| name                    | String            | Required | The stable name of job type used for queries.                  |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| version                 | String            | Required | The version of the job type.                                   |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| title                   | String            | Optional | The human-readable name of the job type.                       |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| description             | String            | Optional | An optional description of the job type.                       |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| category                | String            | Optional | An optional overall category of the job type.                  |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| author_name             | String            | Optional | The name of the person or organization that created the        |
|                         |                   |          | algorithm associated with the job type.                        |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| author_url              | String            | Optional | The address to a home page about the author or associated      |
|                         |                   |          | algorithm run by the job type.                                 |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| is_long_running         | Boolean           | Optional | Whether this type is long running. A job of this type is       |
|                         |                   |          | intended to run for a long time, potentially indefinitely,     |
|                         |                   |          | without timing out and always being re-queued after a failure. |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| is_paused               | Boolean           | Optional | Whether the job type is paused (while paused no jobs of this   |
|                         |                   |          | type will be scheduled off of the queue).                      |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| icon_code               | String            | Optional | A font-awesome icon code to use when displaying this job type. |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| docker_image            | String            | Optional | The Docker image containing the code to run for this job.      |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| priority                | Integer           | Optional | The priority of the job type (lower number is higher priority).|
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| timeout                 | Integer           | Optional | The maximum amount of time to allow a job of this type to run  |
|                         |                   |          | before being killed (in seconds).                              |
+-------------------------+-------------------+---------------------------------------------------------------------------+
| max_scheduled           | Integer           | Optional | Indicates the maximum number of jobs of this type that may be  |
|                         |                   |          | scheduled to run at the same time.                             |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| max_tries               | Integer           | Optional | The maximum number of times to try executing a job when failed.|
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| cpus_required           | Decimal           | Optional | The number of CPUs needed for a job of this type.              |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| mem_required            | Decimal           | Optional | The amount of RAM in MiB needed for a job of this type.        |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| disk_out_const_required | Decimal           | Optional | A constant amount of disk space in MiB required for job output.|
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| disk_out_mult_required  | Decimal           | Optional | A multiplier (2x = 2.0) applied to the size of input files to  |
|                         |                   |          | determine additional disk space in MiB required for job output.|
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| interface               | JSON Object       | Required | JSON description of the interface for running the job.         |
|                         |                   |          | (See :ref:`architecture_jobs_interface_spec`)                  |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| error_mapping           | JSON Object       | Optional | JSON description that maps exit codes to known error models.   |
|                         |                   |          | (See :ref:`architecture_errors_interface_spec`)                |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| trigger_rule            | JSON Object       | Optional | A linked trigger rule that automatically invokes the job type. |
|                         |                   |          | Type and configuration fields are required if setting a rule.  |
|                         |                   |          | The is_active field is optional and can be used to pause.      |
|                         |                   |          | (See :ref:`Trigger Rule Details <rest_trigger_rule_details>`   |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "name": "my-job",                                                                                                |
|        "version": "1.0",                                                                                                |
|        "title": "My Job",                                                                                               |
|        "description": "This is a description of the job",                                                               |
|        "category": "test",                                                                                              |
|        "author_name": null,                                                                                             |
|        "author_url": null,                                                                                              |
|        "is_long_running": false,                                                                                        |
|        "is_operational": true,                                                                                          |
|        "is_paused": false,                                                                                              |
|        "icon_code": "f1c5",                                                                                             |
|        "docker_privileged": false,                                                                                      |
|        "docker_image": null,                                                                                            |
|        "priority": 1,                                                                                                   |
|        "timeout": 0,                                                                                                    |
|        "max_tries": 0,                                                                                                  |
|        "cpus_required": 0.5,                                                                                            |
|        "mem_required": 64.0,                                                                                            |
|        "disk_out_const_required": 64.0,                                                                                 |
|        "disk_out_mult_required": 0.0,                                                                                   |
|        "interface": {                                                                                                   |
|            "version": "1.0",                                                                                            |
|            "command": "test_cmd",                                                                                       |
|            "command_arguments": "test_arg",                                                                             |
|            "input_data": [                                                                                              |
|                {                                                                                                        |
|                    "media_types": ["image/png"],                                                                        |
|                    "type": "file",                                                                                      |
|                    "name": "input_file"                                                                                 |
|                }                                                                                                        |
|            ],                                                                                                           |
|            "output_data": [],                                                                                           |
|            "shared_resources": []                                                                                       |
|        },                                                                                                               |
|        "error_mapping": {                                                                                               |
|            "version": "1.0",                                                                                            |
|            "exit_codes": {                                                                                              |
|                "1": "unknown"                                                                                           |
|            }                                                                                                            |
|        },                                                                                                               |
|        "trigger_rule": {                                                                                                |
|            "type": "PARSE",                                                                                             |
|            "is_active": true,                                                                                           |
|            "configuration": {                                                                                           |
|                "version": "1.0",                                                                                        |
|                "condition": {                                                                                           |
|                    "media_type": "image/png",                                                                           |
|                    "data_types": []                                                                                     |
|                },                                                                                                       |
|                "data": {                                                                                                |
|                    "input_data_name": "input_file",                                                                     |
|                    "workspace_name": "rs"                                                                               |
|                }                                                                                                        |
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
|            "id": "media_type",                                                                                          |
|            "details": "Invalid media type for data input: input_file -> image/png"                                      |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_job_type_details:

+-------------------------------------------------------------------------------------------------------------------------+
| **Job Type Details**                                                                                                    |
+=========================================================================================================================+
| Returns job type details                                                                                                |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /job-types/{id}/                                                                                                |
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
| name                     | String            | The stable name of the job type used for queries.                        |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| version                  | String            | The version of the job type.                                             |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| title                    | String            | The human readable display name of the job type.                         |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| description              | String            | A longer description of the job type.                                    |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| category                 | String            | An optional overall category of the job type.                            |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| author_name              | String            | The name of the person or organization that created the job algorithm.   |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| author_url               | String            | The address to a home page about the author or associated algorithm.     |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| is_system                | Boolean           | Whether this is a system type.                                           |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| is_long_running          | Boolean           | Whether this type is long running. A job of this type is intended to run |
|                          |                   | for a long time, potentially indefinitely, without timing out and always |
|                          |                   | being re-queued after a failure.                                         |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| is_active                | Boolean           | Whether the job type is active (false once job type is archived).        |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| is_operational           | Boolean           | Whether this job type is operational (True) or is still in a research &  |
|                          |                   | development (R&D) phase (False).                                         |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| is_paused                | Boolean           | Whether the job type is paused (while paused no jobs of this type will be|
|                          |                   | scheduled off of the queue).                                             |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| icon_code                | String            | A font-awesome icon code to use when representing this job type.         |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| uses_docker              | Boolean           | Whether the job type uses Docker.                                        |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| docker_image             | String            | The Docker image containing the code to run for this job.                |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| revision_num             | Integer           | The current revision number of the job type, incremented for each edit.  |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| priority                 | Integer           | The priority of the job type (lower number is higher priority).          |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| timeout                  | Integer           | The maximum amount of time to allow a job of this type to run            |
|                          |                   | before being killed (in seconds).                                        |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| max_scheduled            | Integer           | An optional number indicating the maximum number of jobs of this type    |
|                          |                   | that may be scheduled to run at the same time. May be 'null'.            |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| max_tries                | Integer           | The maximum number of times to try executing a job in case of errors.    |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| cpus_required            | Decimal           | The number of CPUs needed for a job of this type.                        |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| mem_required             | Decimal           | The amount of RAM in MiB needed for a job of this type.                  |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| disk_out_const_required  | Decimal           | A constant amount of disk space in MiB required for job output.          |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| disk_out_mult_required   | Decimal           | A multiplier (2x = 2.0) applied to the size of the input files to        |
|                          |                   | determine additional disk space in MiB required for job output.          |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| created                  | ISO-8601 Datetime | When the associated database model was initially created.                |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| archived                 | ISO-8601 Datetime | When the job type was archived (no longer active).                       |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| paused                   | ISO-8601 Datetime | When the job type was paused.                                            |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| last_modified            | ISO-8601 Datetime | When the associated database model was last saved.                       |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| interface                | JSON Object       | JSON description defining the interface for running a job of this type.  |
|                          |                   | (See :ref:`architecture_jobs_interface_spec`)                            |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| error_mapping            | JSON Object       | JSON description defining the error mappings for a job of this type.     |
|                          |                   | (See :ref:`architecture_errors_interface_spec`)                          |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| trigger_rule             | JSON Object       | A linked trigger rule that automatically invokes the job type.           |
|                          |                   | Type and configuration fields are required if setting a rule.            |
|                          |                   | The is_active field is optional and can be used to pause.                |
|                          |                   | (See :ref:`Trigger Rule Details <rest_trigger_rule_details>`             |
+--------------------------+-------------------+----------+---------------------------------------------------------------+
| errors                   | Array             | List of all errors that are referenced by this job type's error mapping. |
|                          |                   | (See :ref:`Error Details <rest_error_details>`)                          |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .job_counts_6h           | Array             | List of job counts for the job type, grouped by status the past 6 hours. |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| ..status                 | String            | The type of job status the count represents.                             |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| ..count                  | Integer           | The number of jobs with that status.                                     |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| ..most_recent            | ISO-8601 Datetime | The date/time when a job was last in that status.                        |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| ..category               | String            | The category of the status, which is only used by a FAILED status.       |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .job_counts_12h          | Array             | List of job counts for the job type, grouped by status the past 12 hours.|
+--------------------------+-------------------+--------------------------------------------------------------------------+
| ..status                 | String            | The type of job status the count represents.                             |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| ..count                  | Integer           | The number of jobs with that status.                                     |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| ..most_recent            | ISO-8601 Datetime | The date/time when a job was last in that status.                        |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| ..category               | String            | The category of the status, which is only used by a FAILED status.       |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .job_counts_24h          | Array             | List of job counts for the job type, grouped by status the past 24 hours.|
+--------------------------+-------------------+--------------------------------------------------------------------------+
| ..status                 | String            | The type of job status the count represents.                             |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| ..count                  | Integer           | The number of jobs with that status.                                     |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| ..most_recent            | ISO-8601 Datetime | The date/time when a job was last in that status.                        |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| ..category               | String            | The category of the status, which is only used by a FAILED status.       |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "id": 3,                                                                                                         |
|        "name": "scale-clock",                                                                                           |
|        "version": "1.0",                                                                                                |
|        "title": "Scale Clock",                                                                                          |
|        "description": "Monitors a directory for incoming files to ingest",                                              |
|        "category": "system",                                                                                            |
|        "author_name": null,                                                                                             |
|        "author_url": null,                                                                                              |
|        "is_system": true,                                                                                               |
|        "is_long_running": true,                                                                                         |
|        "is_active": true,                                                                                               |
|        "is_operational": true,                                                                                          |
|        "is_paused": false,                                                                                              |
|        "icon_code": "f013",                                                                                             |
|        "uses_docker": false,                                                                                            |
|        "docker_privileged": false,                                                                                      |
|        "docker_image": null,                                                                                            |
|        "revision_num": 1,                                                                                               |
|        "priority": 1,                                                                                                   |
|        "timeout": 0,                                                                                                    |
|        "max_scheduled": null,                                                                                           |
|        "max_tries": 0,                                                                                                  |
|        "cpus_required": 0.5,                                                                                            |
|        "mem_required": 64.0,                                                                                            |
|        "disk_out_const_required": 64.0,                                                                                 |
|        "disk_out_mult_required": 0.0,                                                                                   |
|        "created": "2015-03-11T00:00:00Z",                                                                               |
|        "archived": null,                                                                                                |
|        "paused": null,                                                                                                  |
|        "last_modified": "2015-03-11T00:00:00Z"                                                                          |
|        "interface": {...},                                                                                              |
|        "error_mapping": {...},                                                                                          |
|        "trigger_rule": {...},                                                                                           |
|        "errors": [...],                                                                                                 |
|        "job_counts_6h": [                                                                                               |
|            {                                                                                                            |
|                "status": "QUEUED",                                                                                      |
|                "count": 3,                                                                                              |
|                "most_recent": "2015-09-16T18:36:12.278Z",                                                               |
|                "category": null                                                                                         |
|            }                                                                                                            |
|        ],                                                                                                               |
|        "job_counts_12h": [                                                                                              |
|            {                                                                                                            |
|                "status": "QUEUED",                                                                                      |
|                "count": 3,                                                                                              |
|                "most_recent": "2015-09-16T18:36:12.278Z",                                                               |
|                "category": null                                                                                         |
|            },                                                                                                           |
|            {                                                                                                            |
|                "status": "COMPLETED",                                                                                   |
|                "count": 225,                                                                                            |
|                "most_recent": "2015-09-16T18:40:01.101Z",                                                               |
|                "category": null                                                                                         |
|            }                                                                                                            |
|        ],                                                                                                               |
|        "job_counts_24h": [                                                                                              |
|            {                                                                                                            |
|                "status": "QUEUED",                                                                                      |
|                "count": 3,                                                                                              |
|                "most_recent": "2015-09-16T18:36:12.278Z",                                                               |
|                "category": null                                                                                         |
|            },                                                                                                           |
|            {                                                                                                            |
|                "status": "COMPLETED",                                                                                   |
|                "count": 419,                                                                                            |
|                "most_recent": "2015-09-16T18:40:01.101Z",                                                               |
|                "category": null                                                                                         |
|            },                                                                                                           |
|            {                                                                                                            |
|                "status": "FAILED",                                                                                      |
|                "count": 1,                                                                                              |
|                "most_recent": "2015-09-16T10:01:34.308Z",                                                               |
|                "category": "SYSTEM"                                                                                     |
|            }                                                                                                            |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_job_type_edit:

+-------------------------------------------------------------------------------------------------------------------------+
| **Edit Job Type**                                                                                                       |
+=========================================================================================================================+
| Edits an existing job type with associated interface and error mapping                                                  |
+-------------------------------------------------------------------------------------------------------------------------+
| **PATCH** /job-types/{id}/                                                                                              |
|           Where {id} is the unique identifier of an existing model.                                                     |
+-------------------------+-----------------------------------------------------------------------------------------------+
| **Content Type**        | *application/json*                                                                            |
+-------------------------+-----------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| title                   | String            | Optional | The human-readable name of the job type.                       |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| description             | String            | Optional | An optional description of the job type.                       |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| category                | String            | Optional | An optional overall category of the job type.                  |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| author_name             | String            | Optional | The name of the person or organization that created the        |
|                         |                   |          | algorithm associated with the job type.                        |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| author_url              | String            | Optional | The address to a home page about the author or associated      |
|                         |                   |          | algorithm run by the job type.                                 |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| is_long_running         | Boolean           | Optional | Whether this type is long running. A job of this type is       |
|                         |                   |          | intended to run for a long time, potentially indefinitely,     |
|                         |                   |          | without timing out and always being re-queued after a failure. |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| is_paused               | Boolean           | Optional | Whether the job type is paused (while paused no jobs of this   |
|                         |                   |          | type will be scheduled off of the queue).                      |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| icon_code               | String            | Optional | A font-awesome icon code to use when displaying this job type. |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| docker_image            | String            | Optional | The Docker image containing the code to run for this job.      |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| priority                | Integer           | Optional | The priority of the job type (lower number is higher priority).|
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| timeout                 | Integer           | Optional | The maximum amount of time to allow a job of this type to run  |
|                         |                   |          | before being killed (in seconds).                              |
+-------------------------+-------------------+---------------------------------------------------------------------------+
| max_scheduled           | Integer           | Optional | Indicates the maximum number of jobs of this type that may be  |
|                         |                   |          | scheduled to run at the same time.                             |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| max_tries               | Integer           | Optional | The maximum number of times to try executing a job when failed.|
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| cpus_required           | Decimal           | Optional | The number of CPUs needed for a job of this type.              |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| mem_required            | Decimal           | Optional | The amount of RAM in MiB needed for a job of this type.        |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| disk_out_const_required | Decimal           | Optional | A constant amount of disk space in MiB required for job output.|
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| disk_out_mult_required  | Decimal           | Optional | A multiplier (2x = 2.0) applied to the size of input files to  |
|                         |                   |          | determine additional disk space in MiB required for job output.|
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| interface               | JSON Object       | Optional | JSON description of the interface for running the job.         |
|                         |                   |          | (See :ref:`architecture_jobs_interface_spec`)                  |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| error_mapping           | JSON Object       | Optional | JSON description that maps exit codes to known error models.   |
|                         |                   |          | (See :ref:`architecture_errors_interface_spec`)                |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| trigger_rule            | JSON Object       | Optional | A linked trigger rule that automatically invokes the job type. |
|                         |                   |          | Type and configuration fields are required if setting a rule.  |
|                         |                   |          | The is_active field is optional and can be used to pause.      |
|                         |                   |          | (See :ref:`Trigger Rule Details <rest_trigger_rule_details>`   |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "title": "My Job",                                                                                               |
|        "description": "This is a description of the job",                                                               |
|        "category": "test",                                                                                              |
|        "author_name": null,                                                                                             |
|        "author_url": null,                                                                                              |
|        "is_long_running": false,                                                                                        |
|        "is_operational": true,                                                                                          |
|        "is_paused": false,                                                                                              |
|        "icon_code": "f1c5",                                                                                             |
|        "docker_privileged": false,                                                                                      |
|        "docker_image": null,                                                                                            |
|        "priority": 1,                                                                                                   |
|        "timeout": 0,                                                                                                    |
|        "max_scheduled": 2,                                                                                              |
|        "max_tries": 0,                                                                                                  |
|        "cpus_required": 0.5,                                                                                            |
|        "mem_required": 64.0,                                                                                            |
|        "disk_out_const_required": 64.0,                                                                                 |
|        "disk_out_mult_required": 0.0,                                                                                   |
|        "interface": {                                                                                                   |
|            "version": "1.0",                                                                                            |
|            "command": "test_cmd",                                                                                       |
|            "command_arguments": "test_arg",                                                                             |
|            "input_data": [                                                                                              |
|                {                                                                                                        |
|                    "media_types": ["image/png"],                                                                        |
|                    "type": "file",                                                                                      |
|                    "name": "input_file"                                                                                 |
|                }                                                                                                        |
|            ],                                                                                                           |
|            "output_data": [],                                                                                           |
|            "shared_resources": []                                                                                       |
|        },                                                                                                               |
|        "error_mapping": {                                                                                               |
|            "version": "1.0",                                                                                            |
|            "exit_codes": {                                                                                              |
|                "1": "unknown"                                                                                           |
|            }                                                                                                            |
|        },                                                                                                               |
|        "trigger_rule": {                                                                                                |
|            "type": "PARSE",                                                                                             |
|            "is_active": true,                                                                                           |
|            "configuration": {                                                                                           |
|                "version": "1.0",                                                                                        |
|                "condition": {                                                                                           |
|                    "media_type": "image/png",                                                                           |
|                    "data_types": []                                                                                     |
|                },                                                                                                       |
|                "data": {                                                                                                |
|                    "input_data_name": "input_file",                                                                     |
|                    "workspace_name": "rs"                                                                               |
|                }                                                                                                        |
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
+--------------------+-------------------+--------------------------------------------------------------------------------+
|                    | JSON Object       | All fields are the same as the job type details model.                         |
|                    |                   | (See :ref:`Job Type Details <rest_job_type_details>`)                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "id": 100,                                                                                                       |
|        "name": "my-job",                                                                                                |
|        "version": "1.0",                                                                                                |
|        "title": "My Job",                                                                                               |
|        "description": "This is a description of the job",                                                               |
|        "category": "test",                                                                                              |
|        "author_name": null,                                                                                             |
|        "author_url": null,                                                                                              |
|        "is_system": false,                                                                                              |
|        "is_long_running": false,                                                                                        |
|        "is_active": true,                                                                                               |
|        "is_operational": true,                                                                                          |
|        "is_paused": false,                                                                                              |
|        "icon_code": "f1c5",                                                                                             |
|        "uses_docker": true,                                                                                             |
|        "docker_privileged": false,                                                                                      |
|        "docker_image": null,                                                                                            |
|        "revision_num": 1,                                                                                               |
|        "priority": 1,                                                                                                   |
|        "timeout": 0,                                                                                                    |
|        "max_scheduled": 1,                                                                                              |
|        "max_tries": 0,                                                                                                  |
|        "cpus_required": 0.5,                                                                                            |
|        "mem_required": 64.0,                                                                                            |
|        "disk_out_const_required": 64.0,                                                                                 |
|        "disk_out_mult_required": 0.0,                                                                                   |
|        "created": "2015-03-11T00:00:00Z",                                                                               |
|        "archived": null,                                                                                                |
|        "paused": null,                                                                                                  |
|        "last_modified": "2015-03-11T00:00:00Z",                                                                         |
|        "interface": {...},                                                                                              |
|        "error_mapping": {...},                                                                                          |
|        "errors": [...],                                                                                                 |
|        "job_counts_6h": [...],                                                                                          |
|        "job_counts_12h": [...],                                                                                         |
|        "job_counts_24h": [...]                                                                                          |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_job_type_status:

+-------------------------------------------------------------------------------------------------------------------------+
| **Job Types Status**                                                                                                    |
+=========================================================================================================================+
| Returns a list of overall job type statistics, based on counts of jobs organized by status.                             |
| Note that all jobs with a status of RUNNING are included regardless of date/time filters.                               |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /job-types/status/                                                                                              |
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
|                    |                   |          | Defaults to the past 3 hours.                                       |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| ended              | ISO-8601 Datetime | Optional | End of the time range to query, defaults to the current time.       |
|                    |                   |          | Supports the ISO-8601 date/time format, (ex: 2015-01-01T00:00:00Z). |
|                    |                   |          | Supports the ISO-8601 duration format, (ex: PT3H0M0S).              |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
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
| .job_type          | JSON Object       | The job type that is associated with the statistics.                           |
|                    |                   | (See :ref:`Job Type Details <rest_job_type_details>`)                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .job_counts        | Array             | A list of recent job counts for the job type, grouped by status.               |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..status           | String            | The type of job status the count represents.                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..count            | Integer           | The number of jobs with that status.                                           |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..most_recent      | ISO-8601 Datetime | The date/time when a job was last in that status.                              |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| ..category         | String            | The category of the status, which is only used by a FAILED status.             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|   "count": 2,                                                                                                           | 
|   "next": null,                                                                                                         |
|   "previous": null,                                                                                                     |
|   "results": [                                                                                                          |
|        {                                                                                                                |
|            "job_type": {                                                                                                |
|                "id": 1,                                                                                                 |
|                "name": "scale-ingest",                                                                                  |
|                "version": "1.0",                                                                                        |
|                "title": "Scale Ingest",                                                                                 |
|                "description": "Ingests a source file into a workspace",                                                 |
|                "category": "system",                                                                                    |
|                "author_name": null,                                                                                     |
|                "author_url": null,                                                                                      |
|                "is_system": true,                                                                                       |
|                "is_long_running": false,                                                                                |
|                "is_active": true,                                                                                       |
|                "is_operational": true,                                                                                  |
|                "is_paused": false,                                                                                      |
|                "icon_code": "f013"                                                                                      |
|            },                                                                                                           |
|            "job_counts": [                                                                                              |
|                {                                                                                                        |
|                    "status": "RUNNING",                                                                                 |
|                    "count": 1,                                                                                          |
|                    "most_recent": "2015-08-31T22:09:12.674Z",                                                           |
|                    "category": null                                                                                     |
|                },                                                                                                       |
|                {                                                                                                        |
|                    "status": "FAILED",                                                                                  |
|                    "count": 2,                                                                                          |
|                    "most_recent": "2015-08-31T19:28:30.799Z",                                                           |
|                    "category": "SYSTEM"                                                                                 |
|                },                                                                                                       |
|                {                                                                                                        |
|                    "status": "COMPLETED",                                                                               |
|                    "count": 57,                                                                                         |
|                    "most_recent": "2015-08-31T21:51:40.900Z",                                                           |
|                    "category": null                                                                                     |
|                }                                                                                                        |
|            ],                                                                                                           |
|        },                                                                                                               |
|        {                                                                                                                |
|            "job_type": {                                                                                                |
|                "id": 3,                                                                                                 |
|                "name": "scale-clock",                                                                                   |
|                "version": "1.0",                                                                                        |
|                "title": "Scale Clock",                                                                                  |
|                "description": "Monitors a directory for incoming files to ingest",                                      |
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
|            "job_counts": []                                                                                             |
|        },                                                                                                               |
|        ...                                                                                                              |
|    ]                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_job_type_running:

+-------------------------------------------------------------------------------------------------------------------------+
| **Job Types Running**                                                                                                   |
+=========================================================================================================================+
| Returns counts of job types that are running, ordered by the longest running job.                                       |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /job-types/running/                                                                                             |
+-------------------------------------------------------------------------------------------------------------------------+
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
| .job_type          | JSON Object       | The job type that is associated with the count.                                |
|                    |                   | (See :ref:`Job Type Details <rest_job_type_details>`)                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .count             | Integer           | The number of jobs of this type that are currently running.                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .longest_running   | ISO-8601 Datetime | The run start time of the job of this type that has been running the longest.  |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "count": 5,                                                                                                      |
|        "next": null,                                                                                                    |
|        "previous": null,                                                                                                |
|        "results": [                                                                                                     |
|            {                                                                                                            |
|                "job_type": {                                                                                            |
|                    "id": 3,                                                                                             |
|                    "name": "scale-clock",                                                                               |
|                    "version": "1.0",                                                                                    |
|                    "title": "Scale Clock",                                                                              |
|                    "description": "",                                                                                   |
|                    "category": "system",                                                                                |
|                    "author_name": null,                                                                                 |
|                    "author_url": null,                                                                                  |
|                    "is_system": true,                                                                                   |
|                    "is_long_running": true,                                                                             |
|                    "is_active": true,                                                                                   |
|                    "is_operational": true,                                                                              |
|                    "is_paused": false,                                                                                  |
|                    "icon_code": "f013"                                                                                  |
|                },                                                                                                       |
|                "count": 1,                                                                                              |
|                "longest_running": "2015-09-08T15:43:15.681Z"                                                            |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_job_type_system_failures:

+-------------------------------------------------------------------------------------------------------------------------+
| **Job Type System Failures**                                                                                            |
+=========================================================================================================================+
| Returns counts of job types that have a critical system failure error, ordered by last error.                           |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /job-types/system-failures/                                                                                     |
+-------------------------------------------------------------------------------------------------------------------------+
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
| .job_type          | JSON Object       | The job type that is associated with the count.                                |
|                    |                   | (See :ref:`Job Type Details <rest_job_type_details>`)                          |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .count             | Integer           | The number of jobs of this type that are currently running.                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .error             | JSON Object       | The error that is associated with the count.                                   |
|                    |                   | (See :ref:`Error Details <rest_error_details>`)                                |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .first_error       | ISO-8601 Datetime | When this error first occurred for a job of this type.                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .last_error        | ISO-8601 Datetime | When this error most recently occurred for a job of this type.                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "count": 5,                                                                                                      |
|        "next": null,                                                                                                    |
|        "previous": null,                                                                                                |
|        "results": [                                                                                                     |
|            {                                                                                                            |
|                "job_type": {                                                                                            |
|                    "id": 3,                                                                                             |
|                    "name": "scale-clock",                                                                               |
|                    "version": "1.0",                                                                                    |
|                    "title": "Scale Clock",                                                                              |
|                    "description": "",                                                                                   |
|                    "category": "system",                                                                                |
|                    "author_name": null,                                                                                 |
|                    "author_url": null,                                                                                  |
|                    "is_system": true,                                                                                   |
|                    "is_long_running": true,                                                                             |
|                    "is_active": true,                                                                                   |
|                    "is_operational": true,                                                                              |
|                    "is_paused": false,                                                                                  |
|                    "icon_code": "f013"                                                                                  |
|                },                                                                                                       |
|               "error": {                                                                                                |
|                    "id": 1,                                                                                             |
|                    "name": "Unknown",                                                                                   |
|                    "description": "The error that caused the failure is unknown.",                                      |
|                    "category": "SYSTEM",                                                                                |
|                    "created": "2015-03-11T00:00:00Z",                                                                   |
|                    "last_modified": "2015-03-11T00:00:00Z"                                                              |
|                },                                                                                                       |
|                "count": 38,                                                                                             |
|                "first_error": "2015-08-28T23:29:28.719Z",                                                               | 
|                "last_error": "2015-09-08T16:27:42.243Z"                                                                 |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+

.. _rest_job_type_rev_details:
