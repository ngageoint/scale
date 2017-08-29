
.. _architecture_jobs_exe_configuration:

Execution Configuration
========================================================================================================================

The execution configuration is a JSON document that defines the configuration with which a specific job execution will
run. This configuration includes information such as Docker parameters required by the job execution's Docker container.
This JSON schema is used internally by the Scale system and is not exposed through the REST API.

.. _architecture_jobs_exe_configuration_spec:

Execution Configuration Specification Version 2.0
------------------------------------------------------------------------------------------------------------------------

A valid execution configuration is a JSON document with the following structure:

.. code-block:: javascript

   {
      "version": STRING,
      "input_files": [{
         "id": INTEGER,
         "type": STRING,
         "workspace_name": STRING,
         "workspace_path": STRING,
         "local_file_name": STRING,
         "is_deleted": BOOLEAN
      }],
      "output_workspaces": {STRING: STRING},
      "tasks": [{
         "task_id": STRING,
         "type": STRING,
         "resources": {STRING: FLOAT},
         "args": STRING,
         "env_vars": {STRING: STRING},
         "workspaces": {STRING: {"mode": STRING, "volume_name": STRING}},
         "mounts": {STRING: STRING},
         "settings": {STRING: STRING},
         "volumes": {STRING: {"container_path": STRING, "mode": STRING, "type": STRING, "host_path": STRING,
                              "driver": STRING, "driver_opts": {STRING: STRING}}},
         "docker_params": [{"flag": STRING, "value": STRING}]
      }]
   }

**version**: JSON string

    The *version* is an optional string value that defines the version of the configuration specification used. This
    allows updates to be made to the specification while maintaining backwards compatibility by allowing Scale to
    recognize an older version and convert it to the current version. The default value for *version* if it is not
    included is the latest version, which is currently 2.0.

    Scale must recognize the version number as valid for the job to work. Valid execution configuration versions are
    ``"1.0"``, ``"1.1"``, and ``"2.0"``.

**input_files**: JSON array

    The *input_files* field is an optional JSON array of objects that describe each input file for the execution. Each
    input file object has the following fields:

    **id**: JSON number

        The *id* field is a required integer defining the unique Scale ID of the input file.

    **type**: JSON string

        The *type* field is a required string defining the type of the input file and has only two valid values:
        "SOURCE" or "PRODUCT".

    **workspace_name**: JSON string

        The *workspace_name* field is a required string containing the name of the workspace that holds the input file.

    **workspace_path**: JSON string

        The *workspace_path* field is a required string containing the path within the workspace where the input file
        resides.

    **local_file_name**: JSON string

        The *local_file_name* field is an optional string describing an alternate file name to use when passing the
        input file to the executing container. This is used to deconflict identical input file names when multiple files
        with the same name are passed to the same input.

    **is_deleted**: JSON boolean

        The *is_deleted* field is a required boolean indicating whether the input file has been deleted or not.

**output_workspaces**: JSON object

    The *output_workspaces* field is an optional JSON object where the keys are the names of the job's output parameters
    and each corresponding value is the name of the workspace that should be used to store that output's files.

**tasks**: JSON array

    The *tasks* field is an optional JSON array of objects that describe each task in the execution. Each task object
    has the following fields:

    **task_id**: JSON string

        The *task_id* field is an optional string defining the unique Scale ID for the task.

    **type**: JSON string

        The *type* field is a required string defining the type of the task and only has the following valid values:
        "pull", "pre", "main", or "post".

    **resources**: JSON object

        The *resources* field is an optional object where each key is the name of a resource and each corresponding
        value is the floating point amount of that resource that was provided for the task to run.

    **args**: JSON string

        The *args* field is a required string describing the command arguments that will be passed to the task.

    **env_vars**: JSON object

        The *env_vars* field is an optional object where each key is the name of an environment variable and each
        corresponding value is the value passed to that environment variable.

    **workspaces**: JSON object

        The *workspaces* field is an optional object where each key is the name of a workspace needed by the task and
        each corresponding value is an object with the following fields:

        **mode**: JSON string

            The *mode* is a required string describing in what mode the workspace will be used. There are two valid
            values: "ro" for read-only mode and "rw" for read-write mode.

        **volume_name**: JSON string

            The *volume_name* is an optional string containing the name of Docker volume that will be mounted into the
            task's container in order to make the workspace available.

    **mounts**: JSON object

        The *mounts* field is an optional object where each key is the name of a mount and each corresponding value
        is the name of the Docker volume that will be mounted into the task's container. A null value indicates a
        required mount that was not provided.

    **settings**: JSON object

        The *settings* field is an optional object where each key is the name of a setting and each corresponding value
        is the value passed to that setting. A null value indicates a required setting that was not provided.

    **volumes**: JSON object

        The *volumes* field is an optional object where each key is the name of a Docker volume being mounted into the
        task and each corresponding value is an object with the following fields:

        **container_path**: JSON string

            The *container_path* field is a required string describing the path within the container onto which the
            volume will be mounted.

        **mode**: JSON string

            The *mode* field is a required string describing in what mode the volume will be mounted. There are two
            valid values: "ro" for read-only mode and "rw" for read-write mode.

        **type**: JSON string

            The *type* field is a required string specifying the type of the volume and has only two valid values:
            "volume" for normal Docker volume mounts and "host" for Docker host path mounts.

        **host_path**: JSON string

            The *host_path* field is an optional string describing the path on the host machine that should be mounted
            into the container. This field should only be specified when *type* is "host".

        **driver**: JSON string

            The *driver* field is an optional string describing a custom Docker volume driver to use for the volume.
            This field should only be specified when *type* is "volume".

        **driver_opts**: JSON object

            The *driver_opts* field is an optional object where each key/value pair represents the name and value of a
            Docker volume driver argument option that should be passed to the volume driver. This field should only be
            specified when *type* is "volume".

    **docker_params**: JSON array

        The *docker_params* field is an optional JSON array of objects that describe each Docker parameter to pass to
        the container. Each Docker parameter object has the following fields:

        **flag**: JSON string

            The *flag* field is a required string describing the command line flag (long form) to use for passing the
            parameter without the preceding dashes (e.g. use "volume" for passing "--volume=...").

        **value**: JSON string

            The *value* field is a required string describing the value to pass to the parameter on the Docker command
            line.
