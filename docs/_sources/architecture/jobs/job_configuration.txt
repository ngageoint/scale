
.. _architecture_jobs_job_configuration:

Job Configuration
========================================================================================================================

The job configuration is a JSON document that provides a user-defined configuration for running a job.

**Example job configuration:**

.. code-block:: javascript

  {
     "version": "2.0",
     "mounts": {
        "dted": {"type": "host", "host_path": "/path/to/dted"}
     },
     "settings": {
        "DB_HOST": "scale"
     }
  }

In this example a host mount is defined to provide a needed directory for the job's algorithm (called "dted" in the
job's interface). *DB_HOST* is the name for a setting that will be added to the job_task of the
:ref:`architecture_jobs_exe_configuration` as a setting when a job is scheduled, along with the value that follows.

.. _architecture_jobs_job_configuration_spec:

Job Configuration Specification Version 2.0
------------------------------------------------------------------------------------------------------------------------

A valid job configuration is a JSON document with the following structure:

.. code-block:: javascript

   {
      "version": STRING,
      "mounts": {STRING: {"type": "host", "host_path": STRING},
                 STRING: {"type": "volume", "driver": STRING, "driver_opts": {STRING: STRING}}},
      "settings": {STRING: STRING}
   }

**version**: JSON string

    The *version* is an optional string value that defines the version of the configuration specification used. This
    allows updates to be made to the specification while maintaining backwards compatibility by allowing Scale to
    recognize an older version and convert it to the current version. The default value for *version* if it is not
    included is the latest version, which is currently 2.0.

    Scale must recognize the version number as valid for the job type to work. Currently, the only valid job
    configuration versions are ``"1.0"`` and ``"2.0"``.

**mounts**: JSON object

    The *mounts* field is a JSON object that contains the mount names and their configuration as key/value pairs. Each
    mount configuration is its own JSON object with the following fields:

    **type**: JSON string

        The *type* is a required string that specifies the type of mount to use. The other fields that configure
        the mount are based upon the *type* field. The valid mount types are:

        **host**

            A "host" mount mounts a local directory from the host into the job's container. Usually this local directory
            is a shared file system that has been mounted onto the host.

        **volume**

            A "volume" mount uses a created Docker volume to mount into the job's container, typically specifying a
            driver that provides access to some type of shared network file system.

        Additional mount fields may be required depending on the type of mount selected. See below for more
        information on each mount type.

**settings**: JSON object

    The *settings* is a JSON object that contains the setting names and their values as key/value pairs.

Host Mount
------------------------------------------------------------------------------------------------------------------------

The host mount mounts a local directory from the host into the job's container. This local directory should be a shared
file system that has been mounted onto all hosts in the cluster. All hosts must have the same shared file system mounted
at the same location for this mount to work properly.

**Security**

There are potential security risks involved with mounting a host directory into a Docker container. Please consult the
Docker documentation for more information.

Example host mount configuration:

.. code-block:: javascript

   {
      "version": "2.0",
      "mounts": {"my-mount": {"type": "host", "host_path": "/the/host/path"}}
   }

The host mount requires one additional field in its configuration:

**host_path**: JSON string

    The *host_path* is a required string that specifies the absolute path of the host's local directory that should be
    mounted into the job's container.

Volume Mount
------------------------------------------------------------------------------------------------------------------------

The volume mount creates a new named Docker volume and mounts it into the job's container.

Example volume mount configuration:

.. code-block:: javascript

   {
      "version": "2.0",
      "mounts": {"my-mount": {"type": "volume", "driver": "my-driver", "driver_opts": {"foo": "bar"}}}
   }

The volume mount uses these additional fields in its configuration:

**driver**: JSON string

    The *driver* is an optional string that specifies the Docker volume driver to use.

**driver_opts**: JSON object

    The *driver_opts* is an optional object that specifies the Docker driver options to use as key/value pairs.
