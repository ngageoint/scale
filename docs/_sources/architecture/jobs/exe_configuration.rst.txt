
.. _architecture_jobs_exe_configuration:

Execution Configuration
========================================================================================================================

The execution configuration is a JSON document that defines the environment and configuration on which a specific job
execution will run. This configuration includes information such as Docker parameters required by the job execution's
container. This JSON schema is used internally by the Scale system and is not exposed through the REST API.

.. _architecture_jobs_exe_configuration_spec:

Execution Configuration Specification Version 1.1
------------------------------------------------------------------------------------------------------------------------

A valid execution configuration is a JSON document with the following structure:

.. code-block:: javascript

   {
      "version": STRING,
      "pre_task": {
         "docker_params": [{"flag": STRING, "value": STRING}],
         "settings": [{"name": STRING, "value": STRING}],
         "workspaces": [{"name": STRING, "mode": STRING}]
      },
      "job_task": {
         "docker_params": [{"flag": STRING, "value": STRING}],
         "settings": [{"name": STRING, "value": STRING}],
         "workspaces": [{"name": STRING, "mode": STRING}]
      },
      "post_task": {
         "docker_params": [{"flag": STRING, "value": STRING}],
         "settings": [{"name": STRING, "value": STRING}],
         "workspaces": [{"name": STRING, "mode": STRING}]
      }
   }

**version**: JSON string

    The *version* is an optional string value that defines the version of the configuration specification used. This
    allows updates to be made to the specification while maintaining backwards compatibility by allowing Scale to
    recognize an older version and convert it to the current version. The default value for *version* if it is not
    included is the latest version, which is currently 1.1.

    Scale must recognize the version number as valid for the job to work. Valid execution configuration versions are
    ``"1.0"`` and ``"1.1"``.

**pre_task**: JSON object

    The *pre_task* is a JSON object that defines the workspaces and Docker parameters to use for the pre task. It has
    the following fields:

    **docker_params**: JSON array

        The *docker_params* field is a required list of JSON objects that define the parameters to pass to Docker. Each
        JSON object has the following fields:

        **flag**: JSON string

            The *flag* is a required string describing the command line flag (long form) to use for passing the
            parameter without the preceding dashes (e.g. use "volume" for passing "--volume=...").

        **value**: JSON string

            The *value* is a required string describing the value to pass to the parameter on the Docker command line.

    **settings**: JSON array

        The *settings* field is an optional list of JSON objects that define the settings to pass to the pre task
        portion of a job. Each JSON object has the following fields:

        **name**: JSON string

            The *name* is a required string describing the name of the setting. The name is used to identify the setting
            within command line arguments or environment variables that should receive the setting's value.

        **value**: JSON string

            The *value* is a required string describing the value to pass to the setting.

    **workspaces**: JSON array

        The *workspaces* field is a required list of JSON objects that define the workspaces used by the task. Each JSON
        object has the following fields:

        **name**: JSON string

            The *name* is a required string defining the unique name of the workspace.

        **mode**: JSON string

            The *mode* is a required string describing in what mode the workspace will be used. There are two valid
            values: "ro" for read-only mode and "rw" for read-write mode.

**job_task**: JSON object

    The *job_task* is a JSON object that defines the workspaces and Docker parameters to use for the job task (which
    performs the primary job/algorithm). It is identical in structure to *pre_task*.

    The *job_task* *settings* values will be inserted into the job's *command_arguments* string if a matching settings
    *name* appears in the *command_arguments*.

**post_task**: JSON object

    The *post_task* is a JSON object that defines the workspaces and Docker parameters to use for the post task. It is
    identical in structure to *pre_task*.
