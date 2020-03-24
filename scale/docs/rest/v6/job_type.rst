
.. _rest_v6_job_type:

v6 Job Type Services
====================

These services allow for the management of job types within Scale.


The services will be replaced as the new v6 job type services are created:

.. _rest_v6_job_type_name_list:

v6 Job Type Names
-----------------

**Example GET /v6/job-type-names/ API call**

Request: GET http://.../v6/job-type-names/

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
                "versions": ["1.0.0"],
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
| keyword            | String            | Optional | Performs a like search on name and tags                             |
|                    |                   |          | Duplicate to search for multiple keywords.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| id                 | Integer           | Optional | Return only job types with one version has a matching id.           |
|                    |                   |          | Duplicate to search for multiple ids.                               |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| is_active          | Boolean           | Optional | Return only job types with one version that matches is_active flag. |
|                    |                   |          | Defaults to all job types.                                          |
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
| .is_published            | Boolean           | Whether this job type publishes its output.                              |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .versions                | Array             | List of versions of this job type.                                       |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .latest_version          | String            | The latest version of this job type.                                     |
+--------------------------+-------------------+--------------------------------------------------------------------------+

.. _rest_v6_job_type_list:

v6 Job Type List
----------------

**Example GET /v6/job-types/ API call**

Request: GET http://.../v6/job-types/

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
                "is_published": true,
                "is_active": true,
                "is_paused": false,
                "is_system": false,
                "max_scheduled": 1,
                "revision_num": 1,
                "docker_image": "my-job-1.0.0-seed:1.0.0",
                "created": "2015-03-11T00:00:00Z",
                "deprecated": null,
                "paused": null,
                "last_modified": "2015-03-11T00:00:00Z"
            },
            ...
        ]
    }

+-------------------------------------------------------------------------------------------------------------------------+
| **Retrieve Job Types**                                                                                                  |
+=========================================================================================================================+
| Returns a list of job types                                                                                             |
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
| keyword            | String            | Optional | Performs a like search on name and tags                             |
|                    |                   |          | Duplicate to search for multiple keywords.                          |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| id                 | Integer           | Optional | Return only job types with a matching id.                           |
|                    |                   |          | Duplicate to search for multiple ids.                               |
+--------------------+-------------------+----------+---------------------------------------------------------------------+
| is_active          | Boolean           | Optional | Return only job types that match the is_active flag.                |
|                    |                   |          | Defaults to all job types.                                          |
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
| .version                 | String            | The version number for this version of the job type.                     |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .title                   | String            | The human readable display name for this version of the job type.        |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .description             | String            | A longer description of this version of the job type.                    |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .icon_code               | String            | A font-awesome icon code to use when representing this job type version. |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .is_published            | Boolean           | Whether this job type publishes its output.                              |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .is_active               | Boolean           | Whether this job type is active or deprecated.                           |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .is_paused               | Boolean           | Whether the job type is paused (while paused no jobs of this type will   |
|                          |                   | be scheduled off of the queue).                                          |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .is_system               | Boolean           | Whether this is a system type.                                           |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .max_scheduled           | Integer           | Maximum  number of jobs of this type that may be scheduled to run at the |
|                          |                   | same time. May be null.                                                  |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .revision_num            | Integer           | The number of versions of this job type.                                 |
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
                "is_published": true,
                "is_active": true,
                "is_paused": false,
                "is_system": false,
                "max_scheduled": 1,
                "revision_num": 1,
                "docker_image": "my-job-1.0.0-seed:1.0.0",
                "unmet_resources": "chocolate,vanilla",
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
|           Where {name} is the name of the job type                                                                      |
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
| .is_published            | Boolean           | Whether this job type publishes its output.                              |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .is_active               | Boolean           | Whether this job type is active or deprecated.                           |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .is_paused               | Boolean           | Whether the job type is paused (while paused no jobs of this type will   |
|                          |                   | be scheduled off of the queue).                                          |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .is_system               | Boolean           | Whether this is a system type.                                           |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .max_scheduled           | Integer           | Maximum  number of jobs of this type that may be scheduled to run at the |
|                          |                   | same time. May be null.                                                  |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .revision_num            | Integer           | The number of versions of this job type.                                 |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .docker_image            | String            | The Docker image containing the code to run for this job.                |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .unmet_resources         | String            | Resources required by this job type that are not present.                |
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
    "is_published", true,
    "is_active": true,
    "is_paused": false,
    "is_system": false,
    "max_scheduled": 1,
    "max_tries": 3,
    "revision_num": 1,
    "docker_image": "my-job-1.0.0-seed:1.0.0",
    "unmet_resources": "chocolate,vanilla",
    "manifest": { ... },
    "configuration": { ... },
    "recipe_types": [:ref:`Recipe Type Details <rest_v6_recipe_type_details>`],
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
|           Where {name} is the name of the job type and {version} is its version                                         |
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
| is_published             | Boolean           | Whether this job type publishes its output.                              |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| is_active                | Boolean           | Whether this job type is active or deprecated.                           |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| is_paused                | Boolean           | Whether the job type is paused (while paused no jobs of this type will   |
|                          |                   | be scheduled off of the queue).                                          |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| is_system                | Boolean           | Whether this is a system type.                                           |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| max_scheduled            | Integer           | Maximum  number of jobs of this type that may be scheduled to run at the |
|                          |                   | same time. May be null.                                                  |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| max_tries                | Integer           | Number of times a job will be automatically retried afer an error.       |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| revision_num             | Integer           | The number of versions of this job type.                                 |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| docker_image             | String            | The Docker image containing the code to run for this job.                |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| unmet_resources          | String            | Resources required by this job type that are not present.                |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| manifest                 | String            | Seed manifest describing Job, interface and requirements.                |
|                          |                   | (See :ref:`architecture_seed_manifest_spec`)                             |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| configuration            | JSON Object       | JSON description of the configuration for running the job                |
|                          |                   | (See :ref:`rest_v6_job_type_configuration`)                              |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| recipe_types             | JSON Object       | List of all recipe_types that this job type is a member of               |
|                          |                   | (See :ref:`rest_v6_recipe_type_configuration`)                           |
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
            "name": "my-job",
            "version": "1.0.0",
            "title": "My first job",
            "description": "My very first job",
            "is_active": true,
            "is_paused": false,
            "is_published": false,
            "icon_code": "f013",
            "unmet_resources": "chocolate,vanilla"
          },
          "revision_num": 1,
          "docker_image": "my-job-1.0.0-seed:1.0.0",
          "created": "2015-03-11T00:00:00Z"
        }
      ]
    }

+-------------------------------------------------------------------------------------------------------------------------+
| **Retrieve Job Type Revisions**                                                                                         |
+=========================================================================================================================+
| Returns revisions for a job type.                                                                                       |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/job-types/{name}/{version}/revisions/                                                                       |
|           Where {name} is the name of the job type and {version} is its version                                         |
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
| .job_type                | JSON Object       | The job type                                                             |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| .revision_num            | Integer           | The number for this revision of the job type.                            |
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
        "name": "my-job",
        "version": "1.0.0",
        "title": "My first job",
        "description": "My very first job",
        "is_active": true,
        "is_paused": false,
        "is_published": false,
        "icon_code": "f013",
        "unmet_resources": "chocolate,vanilla"
      },
      "revision_num": 1,
      "docker_image": "my-job-1.0.0-seed:1.0.0",
      "manifest": "",
      "created": "2015-03-11T00:00:00Z"
    }

+-------------------------------------------------------------------------------------------------------------------------+
| **Retrieve Job Type Revision Details**                                                                                  |
+=========================================================================================================================+
| Returns job type revision details.                                                                                      |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/job-types/{name}/{version}/revisions/{revision_num}/                                                        |
|           Where {name} is the name of the job type, {version} is its version and {revision_num} is the revision         |
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
| .job_type                | JSON Object       | The job type                                                             |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| revision_num             | Integer           | The number for this revision of the job type.                            |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| docker_image             | String            | The Docker image containing the code to run for this job.                |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| manifest                 | String            | Seed manifest describing Job, interface and requirements.                |
|                          |                   | (See :ref:`architecture_seed_manifest_spec`)                             |
+--------------------------+-------------------+--------------------------------------------------------------------------+
| created                  | ISO-8601 Datetime | When the associated database model was initially created.                |
+--------------------------+-------------------+--------------------------------------------------------------------------+

.. _rest_v6_add_seed_image:

v6 Add Seed Image
-----------------

**Example POST /v6/job-types/ API call**

Request: POST http://.../v6/job-types/

 .. code-block:: javascript

     {
      "icon_code": "f1c5",
      "max_scheduled": 1,
      "docker_image": "test-1.0.0-seed:1.0.0",
      "configuration": {
        "mounts": {
          "MOUNT_PATH": {
            "type": "host",
            "host_path": "/path/on/host"
          }
        },
        "output_workspaces": {
         "default": "workspace_1",
         "outputs": {"output_1": "workspace_2"}
        },
        "settings": {
          "DB_HOST": "som.host.name",
          "DB_PASS": "secret_password"
        }
      },
      "manifest": {
        "seedVersion": "1.0.0",
        "job": {
          "jobVersion": "1.0.0",
          "packageVersion": "1.0.0",
          "name": "test",
          "title": "Job to demonstrate job type APIs",
          "description": "Reads input file and spit out specified number of bytes as output",
          "tags": [
            "sample",
            "job"
          ],
          "timeout": 3600,
          "maintainer": {
            "email": "jdoe@example.com",
            "name": "John Doe",
            "organization": "E-corp",
            "phone": "666-555-4321",
            "url": "http://www.example.com"
          },
          "errors": [
            {
              "category": "data",
              "code": 1,
              "description": "There was a problem with input data",
              "title": "Data Issue discovered"
            },
            {
              "code": 2,
              "category": "job",
              "description": "Expected environment not provided",
              "title": "Missing environment"
            }
          ],
          "interface": {
            "command": "${INPUT_TEXT} ${INPUT_FILES} ${READ_LENGTH}",
            "inputs": {
              "files": [
                {
                  "mediaTypes": [
                    "text/plain"
                  ],
                  "name": "INPUT_TEXT",
                  "partial": true
                }
              ],
              "json": [
                {
                  "name": "READ_LENGTH",
                  "type": "integer"
                }
              ]
            },
            "mounts": [
              {
                "mode": "ro",
                "name": "MOUNT_PATH",
                "path": "/the/container/path"
              }
            ],
            "outputs": {
              "files": [
                {
                  "mediaType": "text/plain",
                  "name": "OUTPUT_TEXT",
                  "pattern": "output_text.txt"
                }
              ],
              "json": [
                {
                  "key": "TOTAL_INPUT",
                  "name": "total_input",
                  "type": "integer"
                }
              ]
            },
            "settings": [
              {
                "name": "DB_HOST",
                "secret": false
              },
              {
                "name": "DB_PASS",
                "secret": true
              }
            ]
          },
          "resources": {
            "scalar": [
              {
                "name": "cpus",
                "value": 1.5
              },
              {
                "name": "mem",
                "value": 244
              },
              {
                "name": "sharedMem",
                "value": 1
              },
              {
                "inputMultiplier": 4,
                "name": "disk",
                "value": 11
              }
            ]
          }
        }
      },
      "auto_update": true
    }

Response: 201 CREATED
Headers:
Location http://.../v6/job-types/test/1.0.0/

 .. code-block:: javascript

    {
    "id": 3,
    "name": "test",
    "version": "1.0.0"
    "title": "Job to demonstrate job type APIs",
    "description": "Reads input file and spit out specified number of bytes as output",
    "icon_code": "f1c5",
    "is_published": true,
    "is_active": true,
    "is_paused": false,
    "is_system": false,
    "max_scheduled": 1,
    "max_tries": 3,
    "revision_num": 1,
    "docker_image": "test-1.0.0-seed:1.0.0",
    "unmet_resources": "chocolate,vanilla",
    "manifest": { ... },
    "configuration": { ... },
    "created": "2015-03-11T00:00:00Z",
    "deprecated": null,
    "paused": null,
    "last_modified": "2015-03-11T00:00:00Z"
    }

+-------------------------------------------------------------------------------------------------------------------------+
| **Add Seed Image**                                                                                                      |
+=========================================================================================================================+
| Adds a new job type or creates a new version of an existing job type for the supplied Seed image                        |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /job-types/                                                                                                    |
+-------------------------+-----------------------------------------------------------------------------------------------+
| **Content Type**        | *application/json*                                                                            |
+-------------------------+-----------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| icon_code               | String            | Optional | A font-awesome icon code to use when displaying this job type. |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| is_published            | Boolean           | Optional | Whether this job type publishes its output. Defaults to False. |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| max_scheduled           | Integer           | Optional | Indicates the maximum number of jobs of this type that may be  |
|                         |                   |          | scheduled to run at the same time.                             |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| docker_image            | String            | Required | The Docker image containing the code to run for this job.      |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| configuration           | JSON Object       | Optional | JSON description of the configuration for running the job      |
|                         |                   |          | (See :ref:`rest_v6_job_type_configuration`)                    |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| manifest                | String            | Required | Seed manifest describing Job, interface and requirements.      |
|                         |                   |          | (See :ref:`architecture_seed_manifest_spec`)                   |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| auto_update             | Boolean           | Optional | Whether to automatically update recipes containing this type.  |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| is_active               | Boolean           | Optional | Whether this job type is active or deprecated.                 |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| is_paused               | Boolean           | Optional | Whether the job type is paused (while paused no jobs of this   |
|                         |                   |          | type will be scheduled off of the queue).                      |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 201 CREATED                                                                                        |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Location**       | URL pointing to the details for the newly created job type                                         |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Body**           | JSON containing the details of the newly created job type, see :ref:`rest_v6_job_type_details`     |
+--------------------+----------------------------------------------------------------------------------------------------+

.. _rest_v6_job_type_validate:

v6 Validate Job Type
--------------------

**Example POST /v6/job-types/validation/ API call**

Request: POST http://.../v6/job-types/validation/

 .. code-block:: javascript

     {
      "configuration": {
        "mounts": {
          "MOUNT_PATH": {
            "type": "host",
            "host_path": "/path/on/host"
          }
        },
        "output_workspaces": {
         "default": "workspace_1",
         "outputs": {"output_1": "workspace_2"}
        },
        "settings": {
          "DB_HOST": "som.host.name",
          "DB_PASS": "secret_password"
        }
      },
      "manifest": {
        "seedVersion": "1.0.0",
        "job": {
          "jobVersion": "1.0.0",
          "packageVersion": "1.0.0",
          "name": "test",
          "title": "Job to demonstrate job type APIs",
          "description": "Reads input file and spit out specified number of bytes as output",
          "tags": [
            "sample",
            "job"
          ],
          "timeout": 3600,
          "maintainer": {
            "email": "jdoe@example.com",
            "name": "John Doe",
            "organization": "E-corp",
            "phone": "666-555-4321",
            "url": "http://www.example.com"
          },
          "errors": [
            {
              "category": "data",
              "code": 1,
              "description": "There was a problem with input data",
              "title": "Data Issue discovered"
            },
            {
              "code": 2,
              "category": "job",
              "description": "Expected environment not provided",
              "title": "Missing environment"
            }
          ],
          "interface": {
            "command": "${INPUT_TEXT} ${INPUT_FILES} ${READ_LENGTH}",
            "inputs": {
              "files": [
                {
                  "mediaTypes": [
                    "text/plain"
                  ],
                  "name": "INPUT_TEXT",
                  "partial": true
                }
              ],
              "json": [
                {
                  "name": "READ_LENGTH",
                  "type": "integer"
                }
              ]
            },
            "mounts": [
              {
                "mode": "ro",
                "name": "MOUNT_PATH",
                "path": "/the/container/path"
              }
            ],
            "outputs": {
              "files": [
                {
                  "mediaType": "text/plain",
                  "name": "OUTPUT_TEXT",
                  "pattern": "output_text.txt"
                }
              ],
              "json": [
                {
                  "key": "TOTAL_INPUT",
                  "name": "total_input",
                  "type": "integer"
                }
              ]
            },
            "settings": [
              {
                "name": "DB_HOST",
                "secret": false
              },
              {
                "name": "DB_PASS",
                "secret": true
              }
            ]
          },
          "resources": {
            "scalar": [
              {
                "name": "cpus",
                "value": 1.5
              },
              {
                "name": "mem",
                "value": 244
              },
              {
                "name": "sharedMem",
                "value": 1
              },
              {
                "inputMultiplier": 4,
                "name": "disk",
                "value": 11
              }
            ]
          }
        }
      }
    }

Response: 200 OK

.. code-block:: javascript

   {
      "is_valid": true,
      "errors": [],
      "warnings": [{"name": "EXAMPLE_WARNING", "description": "This is an example warning."}]
   }

+-------------------------------------------------------------------------------------------------------------------------+
| **Validate Job Type**                                                                                                   |
+=========================================================================================================================+
| Validates a new job type without actually saving it                                                                     |
+-------------------------------------------------------------------------------------------------------------------------+
| **POST** /v6/job-types/validation/                                                                                      |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| manifest                | String            | Required | Seed manifest describing Job, interface and requirements.      |
|                         |                   |          | (See :ref:`architecture_seed_manifest_spec`)                   |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| configuration           | JSON Object       | Optional | JSON description of the configuration for running the job      |
|                         |                   |          | (See :ref:`rest_v6_job_type_configuration`)                    |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+---------------------+------------------------------------------------------------------------------+
| is_valid           | Boolean           | Indicates if the given fields were valid for creating a new job type. If this  |
|                    |                   | is true, then submitting the same fields to the /job-types/ API will           |
|                    |                   | successfully create a new job type.                                            |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| errors             | Array             | Lists any errors causing *is_valid* to be false. The errors are JSON objects   |
|                    |                   | with *name* and *description* string fields.                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| warnings           | Array             | Lists any warnings found. Warnings are useful to present to the user, but do   |
|                    |                   | not cause *is_valid* to be false. The warnings are JSON objects with *name*    |
|                    |                   | and *description* string fields.                                               |
+--------------------+-------------------+--------------------------------------------------------------------------------+

.. _rest_v6_job_type_edit:

v6 Edit Job Type
----------------

**Example PATCH /v6/job-types/{name}/{version}/ API call**

Request: PATCH http://.../v6/job-types/test/1.0.0/

 .. code-block:: javascript

    {
      "icon_code": "012F",
      "is_published": true,
      "is_active": true,
      "is_paused": false,
      "max_scheduled": 1,
      "configuration": {
        "mounts": {
          "MOUNT_PATH": {
            "type": "host",
            "host_path": "/path/on/host"
          }
        },
        "output_workspaces": {
         "default": "workspace_1",
         "outputs": {"output_1": "workspace_2"}
        },
        "settings": {
          "DB_HOST": "som.host.name",
          "DB_PASS": "secret_password"
        }
      }
    }

Response: 200 OK

.. code-block:: javascript

   {
      "is_valid": true,
      "errors": [],
      "warnings": [{"name": "EXAMPLE_WARNING", "description": "This is an example warning."}]
   }

+-------------------------------------------------------------------------------------------------------------------------+
| **Edit Job Type**                                                                                                       |
+=========================================================================================================================+
| Edits an existing job type with the associated fields                                                                   |
+-------------------------------------------------------------------------------------------------------------------------+
| **PATCH** /v6/job-types/{name}/{version}/                                                                               |
|           Where {name} is the name of the job type and {version} is its version                                         |
+-------------------------+-----------------------------------------------------------------------------------------------+
| **Content Type**        | *application/json*                                                                            |
+-------------------------+-----------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| icon_code               | String            | Optional | A font-awesome icon code to use when displaying this job type. |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| is_published            | Boolean           | Optional | Whether this job type publishes its output. Defaults to False. |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| is_active               | Boolean           | Optional | Whether this job type is active or deprecated.                 |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| is_paused               | Boolean           | Optional | Whether the job type is paused (while paused no jobs of this   |
|                         |                   |          | type will be scheduled off of the queue).                      |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| max_scheduled           | Integer           | Optional | Indicates the maximum number of jobs of this type that may be  |
|                         |                   |          | scheduled to run at the same time.                             |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| docker_image            | String            | Optional | The Docker image containing the code to run for this job.      |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| manifest                | String            | Optional | Seed manifest describing Job, interface and requirements.      |
|                         |                   |          | (See :ref:`architecture_seed_manifest_spec`)                   |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| configuration           | JSON Object       | Optional | JSON description of the configuration for running the job      |
|                         |                   |          | (See :ref:`rest_v6_job_type_configuration`)                    |
+-------------------------+-------------------+----------+----------------------------------------------------------------+
| **Successful Response**                                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Status**         | 200 OK                                                                                             |
+--------------------+----------------------------------------------------------------------------------------------------+
| **Content Type**   | *application/json*                                                                                 |
+--------------------+----------------------------------------------------------------------------------------------------+
| **JSON Fields**                                                                                                         |
+--------------------+---------------------+------------------------------------------------------------------------------+
| is_valid           | Boolean           | Indicates if the given fields were valid for editing the job type. If this     |
|                    |                   | is true, then the job type was successfully edited.                            |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| errors             | Array             | Lists any errors causing *is_valid* to be false. The errors are JSON objects   |
|                    |                   | with *name* and *description* string fields.                                   |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| warnings           | Array             | Lists any warnings found. Warnings are useful to present to the user, but do   |
|                    |                   | not cause *is_valid* to be false. The warnings are JSON objects with *name*    |
|                    |                   | and *description* string fields.                                               |
+--------------------+-------------------+--------------------------------------------------------------------------------+


.. _rest_v6_job_type_configuration:

Job Type Configuration JSON
---------------------------

A job type configuration JSON describes a set of configuration settings that affect how a job executes.

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
| mounts                     | JSON Object    | Required | A JSON object representing the configuration for each mount to     |
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
| output_workspaces          | JSON Object    | Required | A JSON object representing the workspaces to use for storing the   |
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
| priority                   | Integer        | Required | The priority to use for scheduling the job off of the queue.       |
+----------------------------+----------------+----------+--------------------------------------------------------------------+
| settings                   | JSON Object    | Required | A JSON object representing the configuration for each setting to   |
|                            |                |          | provide to the job. Each key is the name of a setting defined in   |
|                            |                |          | the job's Seed manifest and each value is the value to provide for |
|                            |                |          | that setting.                                                      |
+----------------------------+----------------+----------+--------------------------------------------------------------------+

.. _rest_v6_job_type_status:

v6 Job Type Status
------------------

**Example GET /v6/job-types/status/ API call**

Request: GET http://.../v6/job-types/status/

.. code-block:: javascript

  {
    "count": 1,
    "next": null,
    "previous": null,
    "results": [{
        "job_type": {
          "id": 1,
          "name": "scale-ingest",
          "version": "1.0",
          "title": "Scale Ingest",
          "description": "Ingests a source file into a workspace",
          "is_active": true,
          "is_paused": false,
          "is_published": true,
          "icon_code": "f013",
          "unmet_resources": "chocolate,vanilla"
        },
        "job_counts": [{
            "status": "RUNNING",
            "count": 1,
            "most_recent": "2015-08-31T22:09:12.674Z",
            "category": null
          },
          {
            "status": "FAILED",
            "count": 2,
            "most_recent": "2015-08-31T19:28:30.799Z",
            "category": "SYSTEM"
          },
          {
            "status": "COMPLETED",
            "count": 57,
            "most_recent": "2015-08-31T21:51:40.900Z",
            "category": null
          }
        ],
      },
      {
        "job_type": {
          "id": 3,
          "name": "scale-clock",
          "version": "1.0",
          "title": "Scale Clock",
          "description": "Monitors a directory for incoming files to ingest",
          "is_active": true,
          "is_paused": false,
          "is_published": true,
          "icon_code": "f013",
          "unmet_resources": "chocolate,vanilla"
        },
        "job_counts": []
      }
    ]
  }

+-------------------------------------------------------------------------------------------------------------------------+
| **Job Types Status**                                                                                                    |
+=========================================================================================================================+
| Returns a list of overall job type statistics, based on counts of jobs organized by status.                             |
| Note that all jobs with a status of RUNNING are included regardless of date/time filters.                               |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/job-types/status/                                                                                           |
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
|                    |                   | (See :ref:`Job Type Details <rest_v6_job_type_details>`)                       |
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

.. _rest_v6_job_type_pending:

v6 Job Types Pending
--------------------

**Example GET /v6/job-types/pending/ API call**

Request: GET http://.../v6/job-types/pending/

.. code-block:: javascript

  {
    "count": 1,
    "next": null,
    "previous": null,
    "results": [{
      "job_type": {
        "id": 3,
        "name": "scale-clock",
        "version": "1.0",
        "title": "Scale Clock",
        "description": "",
        "is_active": true,
        "is_paused": false,
        "is_published": true,
        "icon_code": "f013",
        "unmet_resources": "chocolate,vanilla"
      },
      "count": 1,
      "longest_pending": "2015-09-08T15:43:15.681Z"
    }]
  }

+-------------------------------------------------------------------------------------------------------------------------+
| **Job Types Pending**                                                                                                   |
+=========================================================================================================================+
| Returns counts of job types that are pending, ordered by the longest pending job.                                       |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/job-types/pending/                                                                                          |
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
|                    |                   | (See :ref:`Job Type Details <rest_v6_job_type_details>`)                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .count             | Integer           | The number of jobs of this type that are currently pending.                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .longest_pending   | ISO-8601 Datetime | The queue start time of the job of this type that has been pending the longest.|
+--------------------+-------------------+--------------------------------------------------------------------------------+


.. _rest_v6_job_type_running:

v6 Job Types Running
--------------------

**Example GET /v6/job-types/running/ API call**

Request: GET http://.../v6/job-types/status/

.. code-block:: javascript

  {
    "count": 1,
    "next": null,
    "previous": null,
    "results": [{
      "job_type": {
        "id": 3,
        "name": "scale-clock",
        "version": "1.0",
        "title": "Scale Clock",
        "description": "",
        "is_active": true,
        "is_paused": false,
        "is_published": true,
        "icon_code": "f013",
        "unmet_resources": "chocolate,vanilla"
      },
      "count": 1,
      "longest_running": "2015-09-08T15:43:15.681Z"
    }]
  }

+-------------------------------------------------------------------------------------------------------------------------+
| **Job Types Running**                                                                                                   |
+=========================================================================================================================+
| Returns counts of job types that are running, ordered by the longest running job.                                       |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/job-types/running/                                                                                          |
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
|                    |                   | (See :ref:`Job Type Details <rest_v6_job_type_details>`)                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .count             | Integer           | The number of jobs of this type that are currently running.                    |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .longest_running   | ISO-8601 Datetime | The run start time of the job of this type that has been running the longest.  |
+--------------------+-------------------+--------------------------------------------------------------------------------+

.. _rest_v6_job_type_system_failures:

v6 Job Type System Failures
---------------------------

**Example GET /v6/job-types/system-failures/ API call**

Request: GET http://.../v6/job-types/system-failures/

.. code-block:: javascript

  {
    "count": 1,
    "next": null,
    "previous": null,
    "results": [{
      "job_type": {
        "id": 3,
        "name": "scale-clock",
        "version": "1.0",
        "title": "Scale Clock",
        "description": "",
        "is_active": true,
        "is_paused": false,
        "is_published": true,
        "icon_code": "f013",
        "unmet_resources": "chocolate,vanilla"
      },
      "error": {
        "id": 1,
        "name": "Unknown",
        "description": "The error that caused the failure is unknown.",
        "category": "SYSTEM",
        "is_builtin": true,
        "should_be_retried": true,
        "created": "2015-03-11T00:00:00Z",
        "last_modified": "2015-03-11T00:00:00Z"
      },
      "count": 38,
      "first_error": "2015-08-28T23:29:28.719Z",
      "last_error": "2015-09-08T16:27:42.243Z"
    }]
  }

+-------------------------------------------------------------------------------------------------------------------------+
| **Job Type System Failures**                                                                                            |
+=========================================================================================================================+
| Returns counts of job types that have a critical system failure error, ordered by last error.                           |
+-------------------------------------------------------------------------------------------------------------------------+
| **GET** /v6/job-types/system-failures/                                                                                  |
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
|                    |                   | (See :ref:`Job Type Details <rest_v6_job_type_details>`)                       |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .count             | Integer           | The number of jobs of this type that have an error.                            |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .error             | JSON Object       | The error that is associated with the count.                                   |
|                    |                   | (See :ref:`Error Details <rest_v6_error_details>`)                             |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .first_error       | ISO-8601 Datetime | When this error first occurred for a job of this type.                         |
+--------------------+-------------------+--------------------------------------------------------------------------------+
| .last_error        | ISO-8601 Datetime | When this error most recently occurred for a job of this type.                 |
+--------------------+-------------------+--------------------------------------------------------------------------------+