
.. _architecture_jobs_job_type_configuration:

Job Type Configuration
========================================================================================================================

The job type configuration is a JSON document that defines a configuration that will be a part of a job type.  When
Scale schedules a new job it will reference this configuration and add and defined default settings to the
job_configuration as part of the job_task, and will ultimately be made available to the algorithm being run.

**Example job type configuration:**

.. code-block:: javascript

  {
     "version": "1.0",
     "default_settings": {
        "dted_path": "/path/to/dted",
        "DB_HOST": "scale"}
  }

In this example *dted_path* and *DB_HOST* are the names for two *default_settings* that will be added to the job_task of
the :ref:`architecture_jobs_job_configuration` as a setting when a job is scheduled, along with the value that follows.

.. _architecture_jobs_job_type_configuration_spec:

Job Type Configuration Specification Version 1.0
------------------------------------------------------------------------------------------------------------------------

A valid job type configuration is a JSON document with the following structure:

.. code-block:: javascript

   {
      "version": STRING,
      "default_settings": {
         STRING: STRING}
   }

**version**: JSON string

    The *version* is an optional string value that defines the version of the configuration specification used. This
    allows updates to be made to the specification while maintaining backwards compatibility by allowing Scale to
    recognize an older version and convert it to the current version. The default value for *version* if it is not
    included is the latest version, which is currently 1.0.

    Scale must recognize the version number as valid for the job to work. Currently, the only valid job type
    configuration version is ``"1.0"``.

**default_settings**: JSON array

    The *default_settings* is a JSON array that defines the settings parameters as a name/value pair to use for the
    job task. It has the following fields:

    **name**: JSON string

        The *name* is a required string describing the name of the setting to be added to the job configuration.

    **value**: JSON string

        The *value* is a required string describing the value to pass to the job configuration.
