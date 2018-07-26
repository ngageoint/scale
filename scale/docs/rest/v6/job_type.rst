
.. _rest_v6_job_type:

v6 Job Type Services
====================

These services allow for the management of job types within Scale.

.. _rest_v6_job_type_configuration:

Job Configuration JSON
----------------------

A job configuration JSON describes a set of configuration settings that affect how a job executes.

**Example interface:**

.. code-block:: javascript

   {
      "mounts": {
         "mount_1": {"type": "host", "host_path": "/the/host/path"},
         "mount_2": {"type": "volume", "driver": "docker-driver", "driver_opts": {"opt_1": "foo"}}
      },
      "output_workspaces": {
         "default": "workspace_1",
         "outputs": {"output_1": "workspace_2"}
      },
      "priority": 100,
      "settings": {"setting_1": "foo", "setting_2": "bar"}
   }

+-----------------------------------------------------------------------------------------------------------------------------+
| **Job Configuration**                                                                                                       |
+============================+================+==========+====================================================================+
| mounts                     | JSON Object    | Optional | A JSON object representing the configuration for each mount to     |
|                            |                |          | provide to the job. Each key is the name of a mount defined in the |
|                            |                |          | job's Seed manifest and each value is the configuration for that   |
|                            |                |          | mount.                                                             |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| type                       | String         | Required | The type of the mount configuration. Must be either 'host' or      |
|                            |                |          | 'volume'.                                                          |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| host_path                  | String         | Required | (host mount) The absolute file-system path on the host to mount    |
|                            |                |          | into the job's container.                                          |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| driver                     | String         | Optional | (volume mount) The Docker driver to use for creating the Docker    |
|                            |                |          | volume that will be mounted into the job's container.              |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| driver_opts                | JSON Object    | Optional | (volume mount) An object of key-value strings specifying the name  |
|                            |                |          | and value of the Docker driver options to use for creating the     |
|                            |                |          | Docker volume that will be mounted into the job's container.       |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| output_workspaces          | JSON Object    | Optional | A JSON object representing the workspaces to use for storing the   |
|                            |                |          | job's output files for each defined file output in the job's Seed  |
|                            |                |          | manifest.                                                          |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| default                    | String         | Optional | The unique name of the default workspace to use for storing any    |
|                            |                |          | output files that don't belong to an output configured in          |
|                            |                |          | *outputs*.                                                         |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| outputs                    | JSON Object    | Optional | A JSON object representing the workspaces to use for storing the   |
|                            |                |          | job's output files for specific job file outputs. Each key is the  |
|                            |                |          | name of a file output defined in the job's Seed manifest and each  |
|                            |                |          | value is the unique name of the workspace to use.                  |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| priority                   | Integer        | Optional | The priority to use for scheduling the job off of the queue.       |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| settings                   | JSON Object    | Optional | A JSON object representing the configuration for each setting to   |
|                            |                |          | provide to the job. Each key is the name of a setting defined in   |
|                            |                |          | the job's Seed manifest and each value is the value to provide for |
|                            |                |          | that setting.                                                      |
+----------------------------+----------------+----------+--------------------------------------------------------------------+



The services will be replaced as the new v6 job type services are created:

.. _rest_v6_job_type_list:

v6 Job Type Names
-----------------

**Example GET /v6/job-types/ API call**

Request: GET http://.../v6/job-types/

Response: 200 OK

 .. code-block:: javascript  
    { 
        "count": 1, 
        "next": null, 
        "previous": null, 
        "results": [ 
            { 
                "name": "my-job",
                "title": "My Job", 
                "description": "A simple job type", 
                "icon_code": "f013", 
                "num_versions": 1, 
                "latest_version": "1.0.0" 
            }
        ] 
    } 
    
+-------------------------------------------------------------------------------------------------------------------------+
| **Job Type Names**                                                                                                      |
+=========================================================================================================================+
| Returns a list of all job type names                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/job-types/                                                                                                  |
+-------------------------------------------------------------------------------------------------------------------------+
| **Query Parameters**                                                                                                    |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| page               | Integer           | Optional | The page of the results to return. Defaults to 1.                   |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| page_size          | Integer           | Optional | The size of the page to use for pagination of results.              |
|                    |                   |          | Defaults to 100, and can be anywhere from 1-1000.                   |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| keyword            | String            | Optional | Performs a like search on name, title, description and tags         |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| is_active          | Boolean           | Optional | Return only job types with one version that matches is_active flag. |
|                    |                   |          | Defaults to True.                                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| is_system          | Boolean           | Optional | Return only job types that are system (True) or user (False).       |
|                    |                   |          | Defaults to all job types.                                          |
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
| .name                    | String            | The name of the job type.                                                |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .title                   | String            | The human readable display name for the latest version of the job type.  |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .description             | String            | A longer description of the latest version of the job type.              |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .icon_code               | String            | A font-awesome icon code for the latest version of this job type.        |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .num_versions            | Ingeger           | The number of versions of this job type.                                 |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .latest_version          | String            | The latest version of this job type.                                     |
+--------------------------+-------------------+--------------------------------------------------------------------------+

.. _rest_v6_job_type_versions:

v6 Job Type Versions
--------------------

**Example GET /v6/job-types/{name}/ API call**

Request: GET http://.../v6/job-types/{name}/

Response: 200 OK

 .. code-block:: javascript  
    { 
        "count": 2, 
        "next": null, 
        "previous": null, 
        "results": [ 
            { 
                "id": 3, 
                "name": "my-job",
                "version": "1.0.0" 
                "title": "My Job", 
                "description": "A simple job type", 
                "icon_code": "f013", 
                "is_active": true, 
                "is_paused": false, 
                "is_system": true, 
                "max_scheduled": 1, 
                "revision_num": 1, 
                "docker_image": null, 
                "created": "2015-03-11T00:00:00Z", 
                "deprecated": null, 
                "paused": null, 
                "last_modified": "2015-03-11T00:00:00Z" 
            }, 
            ... 
        ] 
    } 
    
+-------------------------------------------------------------------------------------------------------------------------+
| **Retrieve Job Type Versions**                                                                                          |
+=========================================================================================================================+
| Returns versions of a given job type.                                                                                   |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/job-types/{name}                                                                                            |
+-------------------------------------------------------------------------------------------------------------------------+
| **Query Parameters**                                                                                                    |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| page               | Integer           | Optional | The page of the results to return. Defaults to 1.                   |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| page_size          | Integer           | Optional | The size of the page to use for pagination of results.              |
|                    |                   |          | Defaults to 100, and can be anywhere from 1-1000.                   |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| is_active          | Boolean           | Optional | Return only job types with one version that matches is_active flag. |
|                    |                   |          | Defaults to all job types.                                          |
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
| .name                    | String            | The name of the job type.                                                |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .version                 | String            | The version number for this version of the job type.                     |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .title                   | String            | The human readable display name for this version of the job type.        |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .description             | String            | A longer description of this version of the job type.                    |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .icon_code               | String            | A font-awesome icon code to use when representing this job type version. |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .is_active               | Boolean           | Whether this job type is active or deprecated.                           |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .is_paused               | Boolean           | Whether the job type is paused (while paused no jobs of this type will   |
|                          |                   | be scheduled off of the queue).                                          |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .is_system               | Boolean           | Whether this is a system type.                                           |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .max_scheduled           | Ingeger           | Maximum  number of jobs of this type that may be scheduled to run at the |
|                          |                   | same time. May be null.                                                  |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .revision_num            | Ingeger           | The number of versions of this job type.                                 |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .docker_image            | String            | The Docker image containing the code to run for this job.                |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .created                 | ISO-8601 Datetime | When the associated database model was initially created.                |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .deprecated              | ISO-8601 Datetime | When the job type was last deprecated (archived).                        |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .paused                  | ISO-8601 Datetime | When the job type was last paused.                                       |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .last_modified           | ISO-8601 Datetime | When the associated database model was last saved.                       |
+--------------------------+-------------------+--------------------------------------------------------------------------+

.. _rest_v6_job_type_details:

v6 Job Type Details
-------------------

**Example GET /v6/job-types/{name}/{version}/ API call**

Request: GET http://.../v6/job-types/{name}/{version}/

Response: 200 OK

 .. code-block:: javascript  
    { 
		"id": 3, 
		"name": "my-job", 
		"version": "1.0.0" 
		"title": "My Job", 
		"description": "A simple job type", 
		"icon_code": "f013", 
		"is_active": true, 
		"is_paused": false, 
		"is_system": true, 
		"max_scheduled": 1, 
		"revision_num": 1, 
		"docker_image": null, 
		"manifest": { ... }, 
		"configuration": { ... },
		"created": "2015-03-11T00:00:00Z", 
		"deprecated": null, 
		"paused": null, 
		"last_modified": "2015-03-11T00:00:00Z" 
    } 
    
+-------------------------------------------------------------------------------------------------------------------------+
| **Retrieve Job Type Details**                                                                                           |
+=========================================================================================================================+
| Returns job type details.                                                                                               |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/job-types/{name}/{version}/                                                                                 |
+-------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------------+----------------------------------------------------------------------------------------------+
| **Status**               | 200 OK                                                                                       |
+--------------------------+----------------------------------------------------------------------------------------------+
| **Content Type**         | *application/json*                                                                           |
+--------------------------+----------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| id                       | Integer           | The unique identifier of the model.                                      |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| name                     | String            | The name of the job type.                                                |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| version                  | String            | The version number for this version of the job type.                     |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| title                    | String            | The human readable display name for this version of the job type.        |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| description              | String            | A longer description of this version of the job type.                    |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| icon_code                | String            | A font-awesome icon code to use when representing this job type version. |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| is_active                | Boolean           | Whether this job type is active or deprecated.                           |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| is_paused                | Boolean           | Whether the job type is paused (while paused no jobs of this type will   |
|                          |                   | be scheduled off of the queue).                                          |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| is_system                | Boolean           | Whether this is a system type.                                           |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| max_scheduled            | Ingeger           | Maximum  number of jobs of this type that may be scheduled to run at the |
|                          |                   | same time. May be null.                                                  |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| revision_num             | Ingeger           | The number of versions of this job type.                                 |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| docker_image             | String            | The Docker image containing the code to run for this job.                |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| manifest                 | String            | Seed manifest describing Job, interface and requirements.                |
|                          |                   | (See :ref:`architecture_seed_manifest_spec`)                             | 
+--------------------------+-------------------+--------------------------------------------------------------------------+
| configuration            | JSON Object       | JSON description of the configuration for running the job                |
|                          |                   | (See :ref:`architecture_jobs_job_configuration_spec`)  		          |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| created                  | ISO-8601 Datetime | When the associated database model was initially created.                |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| deprecated               | ISO-8601 Datetime | When the job type was last deprecated (archived).                        |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| paused                   | ISO-8601 Datetime | When the job type was last paused.                                       |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| last_modified            | ISO-8601 Datetime | When the associated database model was last saved.                       |
+--------------------------+-------------------+--------------------------------------------------------------------------+

.. _rest_v6_job_type_revisions:

v6 Job Type Revisions
---------------------

**Example GET /v6/job-types/{name}/{version}/revisions/ API call**

Request: GET http://.../v6/job-types/{name}/{version}/revisions/

Response: 200 OK

 .. code-block:: javascript  
    { 
        "count": 1, 
        "next": null, 
        "previous": null, 
        "results": [ 
            { 
        		"id": 3, 
        		"job_type": { 
                    "id": 1,
                    "name": "my-job",
                    "title": "My first job",
                    "description": "My very first job",
                    "icon_code": 012F
        		},
        		"revision_num": 1, 
        		"docker_image": "my-job-1.0.0-seed:1.0.0", 
        		"created": "2015-03-11T00:00:00Z"
		    }
	    }
    } 
    
+-------------------------------------------------------------------------------------------------------------------------+
| **Retrieve Job Type Revisions**                                                                                         |
+=========================================================================================================================+
| Returns revisions for a job type.                                                                                       |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/job-types/{name}/{version}/revisions/                                                                       |
+-------------------------------------------------------------------------------------------------------------------------+
| **Query Parameters**                                                                                                    |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| page               | Integer           | Optional | The page of the results to return. Defaults to 1.                   |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| page_size          | Integer           | Optional | The size of the page to use for pagination of results.              |
|                    |                   |          | Defaults to 100, and can be anywhere from 1-1000.                   |
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
| .id                      | Integer           | The unique identifier of the model.                                      |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .job_type                | JSON Object       | The job type object this is a revision of.                               |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .revision_num            | Ingeger           | The number for this revision of the job type.                            |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .docker_image            | String            | The Docker image containing the code to run for this job.                |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .created                 | ISO-8601 Datetime | When the associated database model was initially created.                |
+--------------------------+-------------------+--------------------------------------------------------------------------+

.. _rest_v6_job_type_revision_details:

v6 Job Type Revision Details
----------------------------

**Example GET /v6/job-types/{name}/{version}/revisions/{revision_num}/ API call**

Request: GET http://.../v6/job-types/{name}/{version}/revisions/{revision_num}/

Response: 200 OK

 .. code-block:: javascript  
    { 
		"id": 3, 
		"job_type": { 
            "id": 1,
            "name": "my-job",
            "title": "My first job",
            "description": "My very first job",
            "icon_code": 012F,
            "num_versions": 1,
            "latest_version": "1.0.0"
		},
		"revision_num": 1, 
		"docker_image": "my-job-1.0.0-seed:1.0.0", 
		"manifest": { ... }, 
		"created": "2015-03-11T00:00:00Z"
    } 
    
+-------------------------------------------------------------------------------------------------------------------------+
| **Retrieve Job Type Revision Details**                                                                                  |
+=========================================================================================================================+
| Returns job type revision details.                                                                                      |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/job-types/{name}/{version}/revisions/{revision_num}/                                                        |
+-------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------------+----------------------------------------------------------------------------------------------+
| **Status**               | 200 OK                                                                                       |
+--------------------------+----------------------------------------------------------------------------------------------+
| **Content Type**         | *application/json*                                                                           |
+--------------------------+----------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| id                       | Integer           | The unique identifier of the model.                                      |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| job_type                 | JSON Object       | The job type object this is a revision of.                               |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| revision_num             | Ingeger           | The number for this revision of the job type.                            |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| docker_image             | String            | The Docker image containing the code to run for this job.                |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| manifest                 | String            | Seed manifest describing Job, interface and requirements.                |
|                          |                   | (See :ref:`architecture_seed_manifest_spec`)                             | 
+--------------------------+-------------------+--------------------------------------------------------------------------+
| created                  | ISO-8601 Datetime | When the associated database model was initially created.                |
+--------------------------+-------------------+--------------------------------------------------------------------------+

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
| manifest                | String            | Required | Seed manifest describing Job, interface and requirements.      |
|                         |                   |          | (See :ref:`architecture_seed_manifest_spec`)                   |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| is_operational          | Boolean           | Optional | Whether this job type is operational (True) or is still in a   |
|                         |                   |          | research & development (R&D) phase (False).                    |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| is_paused               | Boolean           | Optional | Whether the job type is paused (while paused no jobs of this   |
|                         |                   |          | type will be scheduled off of the queue).                      |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| icon_code               | String            | Optional | A font-awesome icon code to use when displaying this job type. |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| docker_image            | String            | Required | The Docker image containing the code to run for this job.      |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| priority                | Integer           | Optional | The priority of the job type (lower number is higher priority).|
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| max_scheduled           | Integer           | Optional | Indicates the maximum number of jobs of this type that may be  |
|                         |                   |          | scheduled to run at the same time.                             |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| max_tries               | Integer           | Optional | The maximum number of times to try executing a job when failed.|
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| configuration           | JSON Object       | Optional | JSON description of the configuration for running the job      |
|                         |                   |          | (See :ref:`architecture_jobs_job_configuration_spec`)          |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| trigger_rule            | JSON Object       | Optional | A linked trigger rule that automatically invokes the job type. |
|                         |                   |          | Type and configuration fields are required if setting a rule.  |
|                         |                   |          | The is_active field is optional and can be used to pause.      |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "manifest": {                                                                                                    |
|            "seedVersion": "1.0.0",                                                                                      |
|            "job": {                                                                                                     |
|                "jobVersion": "1.0.0",                                                                                   |
|                "packageVersion": "1.0.0",                                                                               |
|                "name": "test",                                                                                          |
|                "title": "Job to demonstrate job type APIs"                                                              |
|                "description": "Reads input file and spit out specified number of bytes as output",                      |
|                "tags": [                                                                                                |
|                    "sample",                                                                                            |
|                    "job"                                                                                                |
|                ],                                                                                                       |
|                "timeout": 3600,                                                                                         |
|                "maintainer": {                                                                                          |
|                    "email": "jdoe@example.com",                                                                         |
|                    "name": "John Doe",                                                                                  |
|                    "organization": "E-corp",                                                                            |
|                    "phone": "666-555-4321",                                                                             |
|                    "url": "http://www.example.com"                                                                      |
|                },                                                                                                       |
|                "errors": [                                                                                              |
|                    {                                                                                                    |
|                        "category": "data",                                                                              |
|                        "code": 1,                                                                                       |
|                        "description": "There was a problem with input data",                                            |
|                        "title": "Data Issue discovered"                                                                 |
|                    },                                                                                                   |
|                    {                                                                                                    |
|                        "code": 2,                                                                                       |
|                        "category": "job",                                                                               |
|                        "description": "Expected environment not provided",                                              |
|                        "title": "Missing environment"                                                                   |
|                    }                                                                                                    |
|                ],                                                                                                       |
|                "interface": {                                                                                           |
|                    "command": "${INPUT_TEXT} ${INPUT_FILES} ${READ_LENGTH}",                                            |
|                    "inputs": {                                                                                          |
|                        "files": [                                                                                       |
|                            {                                                                                            |
|                                "mediaTypes": [                                                                          |
|                                    "text/plain"                                                                         |
|                                ],                                                                                       |
|                                "name": "INPUT_TEXT",                                                                    |
|                                "partial": true                                                                          |
|                            }                                                                                            |
|                        ],                                                                                               |
|                        "json": [                                                                                        |
|                            {                                                                                            |
|                                "name": "READ_LENGTH",                                                                   |
|                                "type": "integer"                                                                        |
|                            }                                                                                            |
|                        ]                                                                                                |
|                    },                                                                                                   |
|                    "mounts": [                                                                                          |
|                        {                                                                                                |
|                            "mode": "ro",                                                                                |
|                            "name": "MOUNT_PATH",                                                                        |
|                            "path": "/the/container/path"                                                                |
|                        }                                                                                                |
|                    ],                                                                                                   |
|                    "outputs": {                                                                                         |
|                        "files": [                                                                                       |
|                            {                                                                                            |
|                                "mediaType": "text/plain",                                                               |
|                                "name": "OUTPUT_TEXT",                                                                   |
|                                "pattern": "output_text.txt"                                                             |
|                            }                                                                                            |
|                        ],                                                                                               |
|                        "json": [                                                                                        |
|                            {                                                                                            |
|                                "key": "TOTAL_INPUT",                                                                    |
|                                "name": "total_input",                                                                   |
|                                "type": "integer"                                                                        |
|                            }                                                                                            |
|                        ]                                                                                                |
|                    },                                                                                                   |
|                    "settings": [                                                                                        |
|                        {                                                                                                |
|                            "name": "DB_HOST",                                                                           |
|                            "secret": false                                                                              |
|                        },                                                                                               |
|                        {                                                                                                |
|                            "name": "DB_PASS",                                                                           |
|                            "secret": true                                                                               |
|                        }                                                                                                |
|                    ]                                                                                                    |
|                },                                                                                                       |
|                "resources": {                                                                                           |
|                    "scalar": [                                                                                          |
|                        {                                                                                                |
|                            "name": "cpus",                                                                              |
|                            "value": 1.5                                                                                 |
|                        },                                                                                               |
|                        {                                                                                                |
|                            "name": "mem",                                                                               |
|                            "value": 244.0                                                                               |
|                        },                                                                                               |
|                        {                                                                                                |
|                            "name": "sharedMem",                                                                         |
|                            "value": 1.0                                                                                 |
|                        },                                                                                               |
|                        {                                                                                                |
|                            "inputMultiplier": 4.0,                                                                      |
|                            "name": "disk",                                                                              |
|                            "value": 11.0                                                                                |
|                        }                                                                                                |
|                    ]                                                                                                    |
|                },                                                                                                       |
|            }                                                                                                            |
|        },                                                                                                               |
|        "is_long_running": false,                                                                                        |
|        "is_operational": true,                                                                                          |
|        "is_paused": false,                                                                                              |
|        "icon_code": "f1c5",                                                                                             |
|        "docker_image": "test-1.0.0-seed:1.0.0",                                                                         |
|        "priority": 1,                                                                                                   |
|        "max_tries": 0,                                                                                                  |
|        "configuration": {                                                                                               |
|            "version": "2.0",                                                                                            |
|            "mounts": {                                                                                                  |
|                "MOUNT_PATH": {"type": "host", "host_path": "/path/on/host"}                                             |
|            },                                                                                                           |
|            "settings": {                                                                                                |
|                "DB_HOST": "som.host.name",                                                                              |
|                "DB_PASS": "secret_password"                                                                             |
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
|                    "workspace_name": "raw"                                                                              |
|                }                                                                                                        |
|            }                                                                                                            |
|        }                                                                                                                |
|    }                                                                                                                    |
+-------------------------------------------------------------------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 201 CREATED                                                                                        |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Location**       | URL pointing to the details for the newly created job type                                         |
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
|        "manifest": {...},                                                                                               |
|        "is_system": false,                                                                                              |
|        "is_long_running": false,                                                                                        |
|        "is_active": true,                                                                                               |
|        "is_operational": true,                                                                                          |
|        "is_paused": false,                                                                                              |
|        "icon_code": "f1c5",                                                                                             |
|        "docker_image": null,                                                                                            |
|        "revision_num": 1,                                                                                               |
|        "priority": 1,                                                                                                   |
|        "max_scheduled": null,                                                                                           |
|        "max_tries": 0,                                                                                                  |
|        "created": "2015-03-11T00:00:00Z",                                                                               |
|        "archived": null,                                                                                                |
|        "paused": null,                                                                                                  |
|        "last_modified": "2015-03-11T00:00:00Z",                                                                         |
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
| **POST** /job-types/validate/                                                                                           |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| manifest                | String            | Required | Seed manifest describing Job, interface and requirements.      |
|                         |                   |          | (See :ref:`architecture_seed_manifest_spec`)                   |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| is_operational          | Boolean           | Optional | Whether this job type is operational (True) or is still in a   |
|                         |                   |          | research & development (R&D) phase (False).                    |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| is_paused               | Boolean           | Optional | Whether the job type is paused (while paused no jobs of this   |
|                         |                   |          | type will be scheduled off of the queue).                      |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| icon_code               | String            | Optional | A font-awesome icon code to use when displaying this job type. |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| docker_image            | String            | Required | The Docker image containing the code to run for this job.      |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| priority                | Integer           | Optional | The priority of the job type (lower number is higher priority).|
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| max_scheduled           | Integer           | Optional | Indicates the maximum number of jobs of this type that may be  |
|                         |                   |          | scheduled to run at the same time.                             |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| max_tries               | Integer           | Optional | The maximum number of times to try executing a job when failed.|
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| configuration           | JSON Object       | Optional | JSON description of the configuration for running the job      |
|                         |                   |          | (See :ref:`architecture_jobs_job_configuration_spec`)          |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| trigger_rule            | JSON Object       | Optional | A linked trigger rule that automatically invokes the job type. |
|                         |                   |          | Type and configuration fields are required if setting a rule.  |
|                         |                   |          | The is_active field is optional and can be used to pause.      |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "manifest": {                                                                                                    |
|            "seedVersion": "1.0.0",                                                                                      |
|            "job": {                                                                                                     |
|                "jobVersion": "1.0.0",                                                                                   |
|                "packageVersion": "1.0.0",                                                                               |
|                "name": "test",                                                                                          |
|                "title": "Job to demonstrate job type APIs"                                                              |
|                "description": "Reads input file and spit out specified number of bytes as output",                      |
|                "tags": [                                                                                                |
|                    "sample",                                                                                            |
|                    "job"                                                                                                |
|                ],                                                                                                       |
|                "timeout": 3600,                                                                                         |
|                "maintainer": {                                                                                          |
|                    "email": "jdoe@example.com",                                                                         |
|                    "name": "John Doe",                                                                                  |
|                    "organization": "E-corp",                                                                            |
|                    "phone": "666-555-4321",                                                                             |
|                    "url": "http://www.example.com"                                                                      |
|                },                                                                                                       |
|                "errors": [                                                                                              |
|                    {                                                                                                    |
|                        "category": "data",                                                                              |
|                        "code": 1,                                                                                       |
|                        "description": "There was a problem with input data",                                            |
|                        "title": "Data Issue discovered"                                                                 |
|                    },                                                                                                   |
|                    {                                                                                                    |
|                        "code": 2,                                                                                       |
|                        "category": "job",                                                                               |
|                        "description": "Expected environment not provided",                                              |
|                        "title": "Missing environment"                                                                   |
|                    }                                                                                                    |
|                ],                                                                                                       |
|                "interface": {                                                                                           |
|                    "command": "${INPUT_TEXT} ${INPUT_FILES} ${READ_LENGTH}",                                            |
|                    "inputs": {                                                                                          |
|                        "files": [                                                                                       |
|                            {                                                                                            |
|                                "mediaTypes": [                                                                          |
|                                    "text/plain"                                                                         |
|                                ],                                                                                       |
|                                "name": "INPUT_TEXT",                                                                    |
|                                "partial": true                                                                          |
|                            }                                                                                            |
|                        ],                                                                                               |
|                        "json": [                                                                                        |
|                            {                                                                                            |
|                                "name": "READ_LENGTH",                                                                   |
|                                "type": "integer"                                                                        |
|                            }                                                                                            |
|                        ]                                                                                                |
|                    },                                                                                                   |
|                    "mounts": [                                                                                          |
|                        {                                                                                                |
|                            "mode": "ro",                                                                                |
|                            "name": "MOUNT_PATH",                                                                        |
|                            "path": "/the/container/path"                                                                |
|                        }                                                                                                |
|                    ],                                                                                                   |
|                    "outputs": {                                                                                         |
|                        "files": [                                                                                       |
|                            {                                                                                            |
|                                "mediaType": "text/plain",                                                               |
|                                "name": "OUTPUT_TEXT",                                                                   |
|                                "pattern": "output_text.txt"                                                             |
|                            }                                                                                            |
|                        ],                                                                                               |
|                        "json": [                                                                                        |
|                            {                                                                                            |
|                                "key": "TOTAL_INPUT",                                                                    |
|                                "name": "total_input",                                                                   |
|                                "type": "integer"                                                                        |
|                            }                                                                                            |
|                        ]                                                                                                |
|                    },                                                                                                   |
|                    "settings": [                                                                                        |
|                        {                                                                                                |
|                            "name": "DB_HOST",                                                                           |
|                            "secret": false                                                                              |
|                        },                                                                                               |
|                        {                                                                                                |
|                            "name": "DB_PASS",                                                                           |
|                            "secret": true                                                                               |
|                        }                                                                                                |
|                    ]                                                                                                    |
|                },                                                                                                       |
|                "resources": {                                                                                           |
|                    "scalar": [                                                                                          |
|                        {                                                                                                |
|                            "name": "cpus",                                                                              |
|                            "value": 1.5                                                                                 |
|                        },                                                                                               |
|                        {                                                                                                |
|                            "name": "mem",                                                                               |
|                            "value": 244.0                                                                               |
|                        },                                                                                               |
|                        {                                                                                                |
|                            "name": "sharedMem",                                                                         |
|                            "value": 1.0                                                                                 |
|                        },                                                                                               |
|                        {                                                                                                |
|                            "inputMultiplier": 4.0,                                                                      |
|                            "name": "disk",                                                                              |
|                            "value": 11.0                                                                                |
|                        }                                                                                                |
|                    ]                                                                                                    |
|                },                                                                                                       |
|            }                                                                                                            |
|        },                                                                                                               |
|        "is_long_running": false,                                                                                        |
|        "is_operational": true,                                                                                          |
|        "is_paused": false,                                                                                              |
|        "icon_code": "f1c5",                                                                                             |
|        "docker_image": "test-1.0.0-seed:1.0.0",                                                                         |
|        "priority": 1,                                                                                                   |
|        "max_tries": 0,                                                                                                  |
|        "configuration": {                                                                                               |
|            "version": "2.0",                                                                                            |
|            "mounts": {                                                                                                  |
|                "MOUNT_PATH": {"type": "host", "host_path": "/path/on/host"}                                             |
|            },                                                                                                           |
|            "settings": {                                                                                                |
|                "DB_HOST": "som.host.name",                                                                              |
|                "DB_PASS": "secret_password"                                                                             |
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
|                    "workspace_name": "raw"                                                                              |
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
|            "id": "settings",                                                                                            |
|            "details": "Missing configuration for interface required setting"                                            |
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
| manifest                 | String            | Seed manifest describing Job, interface and requirements.                |
|                          |                   | (See :ref:`architecture_seed_manifest_spec`)                             |
+--------------------------+-------------------+----------+---------------------------------------------------------------+
| is_operational           | Boolean           | Whether this job type is operational (True) or is still in a research &  |
|                          |                   | development (R&D) phase (False).                                         |
+--------------------------+-------------------+----------+---------------------------------------------------------------+
| is_paused                | Boolean           | Whether the job type is paused (while paused no jobs of this type will   |
|                          |                   | be scheduled off of the queue).                                          |
+--------------------------+-------------------+----------+---------------------------------------------------------------+
| icon_code                | String            | A font-awesome icon code to use when displaying this job type.           |
+--------------------------+-------------------+----------+---------------------------------------------------------------+
| docker_image             | String            | The Docker image containing the code to run for this job.                |
+--------------------------+-------------------+----------+---------------------------------------------------------------+
| priority                 | Integer           | The priority of the job type (lower number is higher priority).          |
+--------------------------+-------------------+----------+---------------------------------------------------------------+
| max_scheduled            | Integer           | Indicates the maximum number of jobs of this type that may be scheduled  |
|                          |                   | to run at the same time.                                                 |
+--------------------------+-------------------+----------+---------------------------------------------------------------+
| max_tries                | Integer           | The maximum number of times to try executing a job when failed.          |
+--------------------------+-------------------+----------+---------------------------------------------------------------+
| configuration            | JSON Object       | SON description of the configuration for running the job                 |
|                          |                   | See :ref:`architecture_jobs_job_configuration_spec`)                     |
+--------------------------+-------------------+----------+---------------------------------------------------------------+
| trigger_rule             | JSON Object       | linked trigger rule that automatically invokes the job type.             |
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
|        "manifest": {                                                                                                    |
|            "seedVersion": "1.0.0",                                                                                      |
|            "job": {                                                                                                     |
|                "jobVersion": "1.0.0",                                                                                   |
|                "packageVersion": "1.0.0",                                                                               |
|                "name": "test",                                                                                          |
|                "title": "Job to demonstrate job type APIs"                                                              |
|                "description": "Reads input file and spit out specified number of bytes as output",                      |
|                "tags": [                                                                                                |
|                    "sample",                                                                                            |
|                    "job"                                                                                                |
|                ],                                                                                                       |
|                "timeout": 3600,                                                                                         |
|                "maintainer": {                                                                                          |
|                    "email": "jdoe@example.com",                                                                         |
|                    "name": "John Doe",                                                                                  |
|                    "organization": "E-corp",                                                                            |
|                    "phone": "666-555-4321",                                                                             |
|                    "url": "http://www.example.com"                                                                      |
|                },                                                                                                       |
|                "errors": [                                                                                              |
|                    {                                                                                                    |
|                        "category": "data",                                                                              |
|                        "code": 1,                                                                                       |
|                        "description": "There was a problem with input data",                                            |
|                        "title": "Data Issue discovered"                                                                 |
|                    },                                                                                                   |
|                    {                                                                                                    |
|                        "code": 2,                                                                                       |
|                        "category": "job",                                                                               |
|                        "description": "Expected environment not provided",                                              |
|                        "title": "Missing environment"                                                                   |
|                    }                                                                                                    |
|                ],                                                                                                       |
|                "interface": {                                                                                           |
|                    "command": "${INPUT_TEXT} ${INPUT_FILES} ${READ_LENGTH}",                                            |
|                    "inputs": {                                                                                          |
|                        "files": [                                                                                       |
|                            {                                                                                            |
|                                "mediaTypes": [                                                                          |
|                                    "text/plain"                                                                         |
|                                ],                                                                                       |
|                                "name": "INPUT_TEXT",                                                                    |
|                                "partial": true                                                                          |
|                            }                                                                                            |
|                        ],                                                                                               |
|                        "json": [                                                                                        |
|                            {                                                                                            |
|                                "name": "READ_LENGTH",                                                                   |
|                                "type": "integer"                                                                        |
|                            }                                                                                            |
|                        ]                                                                                                |
|                    },                                                                                                   |
|                    "mounts": [                                                                                          |
|                        {                                                                                                |
|                            "mode": "ro",                                                                                |
|                            "name": "MOUNT_PATH",                                                                        |
|                            "path": "/the/container/path"                                                                |
|                        }                                                                                                |
|                    ],                                                                                                   |
|                    "outputs": {                                                                                         |
|                        "files": [                                                                                       |
|                            {                                                                                            |
|                                "mediaType": "text/plain",                                                               |
|                                "name": "OUTPUT_TEXT",                                                                   |
|                                "pattern": "output_text.txt"                                                             |
|                            }                                                                                            |
|                        ],                                                                                               |
|                        "json": [                                                                                        |
|                            {                                                                                            |
|                                "key": "TOTAL_INPUT",                                                                    |
|                                "name": "total_input",                                                                   |
|                                "type": "integer"                                                                        |
|                            }                                                                                            |
|                        ]                                                                                                |
|                    },                                                                                                   |
|                    "settings": [                                                                                        |
|                        {                                                                                                |
|                            "name": "DB_HOST",                                                                           |
|                            "secret": false                                                                              |
|                        },                                                                                               |
|                        {                                                                                                |
|                            "name": "DB_PASS",                                                                           |
|                            "secret": true                                                                               |
|                        }                                                                                                |
|                    ]                                                                                                    |
|                },                                                                                                       |
|                "resources": {                                                                                           |
|                    "scalar": [                                                                                          |
|                        {                                                                                                |
|                            "name": "cpus",                                                                              |
|                            "value": 1.5                                                                                 |
|                        },                                                                                               |
|                        {                                                                                                |
|                            "name": "mem",                                                                               |
|                            "value": 244.0                                                                               |
|                        },                                                                                               |
|                        {                                                                                                |
|                            "name": "sharedMem",                                                                         |
|                            "value": 1.0                                                                                 |
|                        },                                                                                               |
|                        {                                                                                                |
|                            "inputMultiplier": 4.0,                                                                      |
|                            "name": "disk",                                                                              |
|                            "value": 11.0                                                                                |
|                        }                                                                                                |
|                    ]                                                                                                    |
|                },                                                                                                       |
|            }                                                                                                            |
|        },                                                                                                               |
|        "is_long_running": false,                                                                                        |
|        "is_operational": true,                                                                                          |
|        "is_paused": false,                                                                                              |
|        "icon_code": "f1c5",                                                                                             |
|        "docker_image": "test-1.0.0-seed:1.0.0",                                                                         |
|        "priority": 1,                                                                                                   |
|        "max_tries": 0,                                                                                                  |
|        "configuration": {                                                                                               |
|            "version": "2.0",                                                                                            |
|            "mounts": {                                                                                                  |
|                "MOUNT_PATH": {"type": "host", "host_path": "/path/on/host"}                                             |
|            },                                                                                                           |
|            "settings": {                                                                                                |
|                "DB_HOST": "som.host.name",                                                                              |
|                "DB_PASS": "secret_password"                                                                             |
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
|                    "workspace_name": "raw"                                                                              |
|                }                                                                                                        |
|            }                                                                                                            |
|        },                                                                                                               |
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
| manifest                | String            | Required | Seed manifest describing Job, interface and requirements.      |
|                         |                   |          | (See :ref:`architecture_seed_manifest_spec`)                   |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| is_operational          | Boolean           | Optional | Whether this job type is operational (True) or is still in a   |
|                         |                   |          | research & development (R&D) phase (False).                    |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| is_paused               | Boolean           | Optional | Whether the job type is paused (while paused no jobs of this   |
|                         |                   |          | type will be scheduled off of the queue).                      |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| icon_code               | String            | Optional | A font-awesome icon code to use when displaying this job type. |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| docker_image            | String            | Required | The Docker image containing the code to run for this job.      |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| priority                | Integer           | Optional | The priority of the job type (lower number is higher priority).|
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| max_scheduled           | Integer           | Optional | Indicates the maximum number of jobs of this type that may be  |
|                         |                   |          | scheduled to run at the same time.                             |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| max_tries               | Integer           | Optional | The maximum number of times to try executing a job when failed.|
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| configuration           | JSON Object       | Optional | JSON description of the configuration for running the job      |
|                         |                   |          | (See :ref:`architecture_jobs_job_configuration_spec`)          |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| trigger_rule            | JSON Object       | Optional | A linked trigger rule that automatically invokes the job type. |
|                         |                   |          | Type and configuration fields are required if setting a rule.  |
|                         |                   |          | The is_active field is optional and can be used to pause.      |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| .. code-block:: javascript                                                                                              |
|                                                                                                                         |
|    {                                                                                                                    |
|        "manifest": {                                                                                                    |
|            "seedVersion": "1.0.0",                                                                                      |
|            "job": {                                                                                                     |
|                "jobVersion": "1.0.0",                                                                                   |
|                "packageVersion": "1.0.0",                                                                               |
|                "name": "test",                                                                                          |
|                "title": "Job to demonstrate job type APIs"                                                              |
|                "description": "Reads input file and spit out specified number of bytes as output",                      |
|                "tags": [                                                                                                |
|                    "sample",                                                                                            |
|                    "job"                                                                                                |
|                ],                                                                                                       |
|                "timeout": 3600,                                                                                         |
|                "maintainer": {                                                                                          |
|                    "email": "jdoe@example.com",                                                                         |
|                    "name": "John Doe",                                                                                  |
|                    "organization": "E-corp",                                                                            |
|                    "phone": "666-555-4321",                                                                             |
|                    "url": "http://www.example.com"                                                                      |
|                },                                                                                                       |
|                "errors": [                                                                                              |
|                    {                                                                                                    |
|                        "category": "data",                                                                              |
|                        "code": 1,                                                                                       |
|                        "description": "There was a problem with input data",                                            |
|                        "title": "Data Issue discovered"                                                                 |
|                    },                                                                                                   |
|                    {                                                                                                    |
|                        "code": 2,                                                                                       |
|                        "category": "job",                                                                               |
|                        "description": "Expected environment not provided",                                              |
|                        "title": "Missing environment"                                                                   |
|                    }                                                                                                    |
|                ],                                                                                                       |
|                "interface": {                                                                                           |
|                    "command": "${INPUT_TEXT} ${INPUT_FILES} ${READ_LENGTH}",                                            |
|                    "inputs": {                                                                                          |
|                        "files": [                                                                                       |
|                            {                                                                                            |
|                                "mediaTypes": [                                                                          |
|                                    "text/plain"                                                                         |
|                                ],                                                                                       |
|                                "name": "INPUT_TEXT",                                                                    |
|                                "partial": true                                                                          |
|                            }                                                                                            |
|                        ],                                                                                               |
|                        "json": [                                                                                        |
|                            {                                                                                            |
|                                "name": "READ_LENGTH",                                                                   |
|                                "type": "integer"                                                                        |
|                            }                                                                                            |
|                        ]                                                                                                |
|                    },                                                                                                   |
|                    "mounts": [                                                                                          |
|                        {                                                                                                |
|                            "mode": "ro",                                                                                |
|                            "name": "MOUNT_PATH",                                                                        |
|                            "path": "/the/container/path"                                                                |
|                        }                                                                                                |
|                    ],                                                                                                   |
|                    "outputs": {                                                                                         |
|                        "files": [                                                                                       |
|                            {                                                                                            |
|                                "mediaType": "text/plain",                                                               |
|                                "name": "OUTPUT_TEXT",                                                                   |
|                                "pattern": "output_text.txt"                                                             |
|                            }                                                                                            |
|                        ],                                                                                               |
|                        "json": [                                                                                        |
|                            {                                                                                            |
|                                "key": "TOTAL_INPUT",                                                                    |
|                                "name": "total_input",                                                                   |
|                                "type": "integer"                                                                        |
|                            }                                                                                            |
|                        ]                                                                                                |
|                    },                                                                                                   |
|                    "settings": [                                                                                        |
|                        {                                                                                                |
|                            "name": "DB_HOST",                                                                           |
|                            "secret": false                                                                              |
|                        },                                                                                               |
|                        {                                                                                                |
|                            "name": "DB_PASS",                                                                           |
|                            "secret": true                                                                               |
|                        }                                                                                                |
|                    ]                                                                                                    |
|                },                                                                                                       |
|                "resources": {                                                                                           |
|                    "scalar": [                                                                                          |
|                        {                                                                                                |
|                            "name": "cpus",                                                                              |
|                            "value": 1.5                                                                                 |
|                        },                                                                                               |
|                        {                                                                                                |
|                            "name": "mem",                                                                               |
|                            "value": 244.0                                                                               |
|                        },                                                                                               |
|                        {                                                                                                |
|                            "name": "sharedMem",                                                                         |
|                            "value": 1.0                                                                                 |
|                        },                                                                                               |
|                        {                                                                                                |
|                            "inputMultiplier": 4.0,                                                                      |
|                            "name": "disk",                                                                              |
|                            "value": 11.0                                                                                |
|                        }                                                                                                |
|                    ]                                                                                                    |
|                },                                                                                                       |
|            }                                                                                                            |
|        },                                                                                                               |
|        "is_long_running": false,                                                                                        |
|        "is_operational": true,                                                                                          |
|        "is_paused": false,                                                                                              |
|        "icon_code": "f1c5",                                                                                             |
|        "docker_image": "test-1.0.0-seed:1.0.0",                                                                         |
|        "priority": 1,                                                                                                   |
|        "max_tries": 0,                                                                                                  |
|        "configuration": {                                                                                               |
|            "version": "2.0",                                                                                            |
|            "mounts": {                                                                                                  |
|                "MOUNT_PATH": {"type": "host", "host_path": "/path/on/host"}                                             |
|            },                                                                                                           |
|            "settings": {                                                                                                |
|                "DB_HOST": "som.host.name",                                                                              |
|                "DB_PASS": "secret_password"                                                                             |
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
|                    "workspace_name": "raw"                                                                              |
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
|    {                                                                                                                    ||    {                                                                                                                    |
|        "id": 100,                                                                                                       |
|        "manifest": {...},                                                                                               |
|        "is_system": false,                                                                                              |
|        "is_long_running": false,                                                                                        |
|        "is_active": true,                                                                                               |
|        "is_operational": true,                                                                                          |
|        "is_paused": false,                                                                                              |
|        "icon_code": "f1c5",                                                                                             |
|        "docker_image": null,                                                                                            |
|        "revision_num": 1,                                                                                               |
|        "priority": 1,                                                                                                   |
|        "max_scheduled": null,                                                                                           |
|        "max_tries": 0,                                                                                                  |
|        "created": "2015-03-11T00:00:00Z",                                                                               |
|        "archived": null,                                                                                                |
|        "paused": null,                                                                                                  |
|        "last_modified": "2015-03-11T00:00:00Z",                                                                         |
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
| is_operational     | String            | Optional | Return only job types that are operational (True) or still in a     |
|                    |                   |          | research & development (R&D) phase (False).                         |
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

.. _rest_job_type_pending:

+-------------------------------------------------------------------------------------------------------------------------+
| **Job Types Pending**                                                                                                   |
+=========================================================================================================================+
| Returns counts of job types that are pending, ordered by the longest pending job.                                       |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /job-types/pending/                                                                                             |
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
| .count             | Integer           | The number of jobs of this type that are currently pending.                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .longest_pending   | ISO-8601 Datetime | The queue start time of the job of this type that has been pending the longest.|
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
|                "longest_pending": "2015-09-08T15:43:15.681Z"                                                            |
|            },                                                                                                           |
|            ...                                                                                                          |
|        ]                                                                                                                |
|    }                                                                                                                    |
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
|                    "is_builtin": true,                                                                                  |
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
