
.. _architecture_jobs_task_results:

Task Results
========================================================================================================================

The task results JSON document describes the results of all tasks once a job execution has finished (reached a terminal
state).

.. _architecture_jobs_task_results_spec:

Task Results Specification Version 1.0
------------------------------------------------------------------------------------------------------------------------

A valid task results is a JSON document with the following structure:

.. code-block:: javascript

   {
      "version": STRING,
      "tasks": [{
         "task_id": STRING,
         "type": STRING,
         "was_launched": BOOLEAN,
         "launched": STRING,
         "was_started": BOOLEAN,
         "started": STRING,
         "was_timed_out": BOOLEAN,
         "ended": STRING,
         "status": STRING,
         "exit_code": INTEGER
      }]
   }

**version**: JSON string

    The *version* is an optional string value that defines the version of the configuration specification used. This
    allows updates to be made to the specification while maintaining backwards compatibility by allowing Scale to
    recognize an older version and convert it to the current version. The default value for *version* if it is not
    included is the latest version, which is currently 1.0.

    Scale must recognize the version number as valid for the job to work. The only valid execution configuration version
    is ``"1.0"``.

**tasks**: JSON array

    The *tasks* field is an optional JSON array of objects that describe each task in the execution. Each task object
    has the following fields:

    **task_id**: JSON string

        The *task_id* field is a required string defining the unique Scale ID for the task.

    **type**: JSON string

        The *type* field is a required string defining the type of the task and only has the following valid values:
        "pull", "pre", "main", or "post".

    **was_launched**: JSON boolean

        The *was_launched* field is a required boolean that indicates whether the task was launched.

    **launched**: JSON string

        The *launched* field is an optional string that is an ISO-8601 datetime describing when the task was launched.

    **was_started**: JSON boolean

        The *was_started* field is an optional boolean that indicates whether the task started running.

    **started**: JSON string

        The *started* field is an optional string that is an ISO-8601 datetime describing when the task started running.

    **was_timed_out**: JSON boolean

        The *was_timed_out* field is an optional boolean that indicates whether the task timed out.

    **ended**: JSON string

        The *ended* field is an optional string that is an ISO-8601 datetime describing when the task ended.

    **status**: JSON string

        The *status* field is an optional string that describes the final status of the task. The valid values are
        "FAILED", "COMPLETED", and "CANCELED".

    **exit_code**: JSON number

        The *exit_code* field is an optional integer that describes the exit code returned by the task execution.
