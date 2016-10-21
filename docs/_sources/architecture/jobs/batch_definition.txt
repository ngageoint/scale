
.. _architecture_jobs_batch_definition:

Batch Definition
================

A batch represents a collection of recipes that should be scheduled for re-processing. The batch definition is a JSON
document that defines exactly which recipes will be included in the batch. It will describe things like a date range and
specific jobs within a recipe type to queue for execution.

Consider the following example that is a request to re-process all recipes in the batch that were originally created
within the 2016 calendar year and have since gone through a revision. Additionally, the job names "Job 1" and "Job 2"
should also be included even if they have not actually changed since the original recipe type revision. The priority is
used to override the original priority of each job type.

**Example batch definition:**

.. code-block:: javascript

   {
      "version": "1.0",
      "date_range": {
         "type": "created",
         "started": "2016-01-01T00:00:00.000Z",
         "ended": "2016-12-31T00:00:00.000Z"
      },
      "job_names": [
          "Job 1",
          "Job 2"
      ],
      "priority": 1000
   }


.. _architecture_jobs_batch_definition_spec:

Batch Definition Specification Version 1.0
------------------------------------------

A valid batch definition is a JSON document with the following structure:
 
.. code-block:: javascript

   {
      "version": STRING,
      "date_range": {
         "type": "created",
         "started": STRING,
         "ended": STRING
      },
      "job_names": [
         STRING,
         STRING
      ],
      "all_jobs": true|false,
      "priority": INTEGER
   }

**version**: JSON string

    The *version* is an optional string value that defines the version of the definition specification used. This allows
    updates to be made to the specification while maintaining backwards compatibility by allowing Scale to recognize an
    older version and convert it to the current version. The default value for *version* if it is not included is the
    latest version, which is currently 1.0. It is recommended, though not required, that you include the *version* so
    that future changes to the specification will still accept the recipe definition.

    Scale must recognize the version number as valid for the recipe to work. Currently, "1.0" is the only valid version.

**date_range**: JSON object

    The *date_range* is an optional parameter that defines a date range of existing recipes to include in a batch. If
    not provided, *date_range* defaults to null (no date range limit). The *started* and *ended* parameters are each
    optional by themselves, but at least one of them (or both) must be included in a *date_range* declaration. The JSON
    object has the following fields:

    **type**: JSON string

        The *type* is an optional string from a defined set that defines the type of the date range. If this parameter
        is not included, it defaults to the "created" value. The valid types are:

        **created**

            A "created" date range matches recipes based on the timestamp of when they were originally created.

    **started**: JSON string

        The *started* date is an optional string that defines the minimum value of the date range filter. The value
        should follow the ISO-8601 datetime standard.

    **ended**: JSON string

        The *ended* date is an optional string that defines the maximum value of the date range filter. The value should
        follow the ISO-8601 datetime standard.

**job_names**: JSON array

    The *job_names* value is an optional list of strings that define specific jobs that will be re-processed as part of
    the batch recipe. Any job that has changed between the original recipe type revision and the current revision will
    automatically be included in the batch, however this parameter can be used to include additional jobs that did not
    have a revision change. If a job is selected to be re-processed, all of its dependent jobs will automatically be
    re-processed as well.

**all_jobs**: JSON boolean

    The *all_jobs* value is an optional parameter that indicates every job in the recipe should be re-processed,
    regardless of whether the recipe type revision actually changed. This parameter overrides the values included in the
    *job_names* parameter.

**priority**: JSON integer

    The *priority* value is an optional parameter that indicates every job in the recipe should be queued with an
    override priority instead of the default priority defined by the job type. This option allows for large batches to
    be executed with a lower priority to avoid impacting real-time processing or to fix products as quickly as possible
    using a higher priority.
