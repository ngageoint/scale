
.. _architecture_port:

Import/Export
========================================================================================================================

Scale has the ability to export and import certain configuration settings related to executing workflows such as errors,
job types, and recipe types. This feature allows a user to build a recipe or job in one installation for testing
purposes and then easily migrate it to another installation for production use without having to reconstruct everything
using the web application user interface.

Operating this way has a number of advantages. It permits trying things out without affecting the production system. It
saves time since wiring up all the recipe connections can be time consuming. It avoids potential errors that could be
introduced by manually recreating a fully tested and working configuration. It helps with upgrades since the import
process has the ability to handle some types of changes automatically for the user. The import process is different than
a traditional database dump/restore in that it includes a lot of logic to ensure that a job type or recipe type cannot
be changed in a way that would invalidate its connections/dependencies. It also keeps track of past versions and
snapshots the definitions/interfaces that were used at the time each execution took place.

Future versions of the import system may assist the user with additional types of changes by using a wizard-based guide,
prompting the user for how certain conflicts should be resolved.

**Example configuration export:**

.. code-block:: javascript

   {
      "version": "1.0",
      "errors": [
         {
            "name": "my-error",
            "title": "My Error",
            "description": "My error description.",
            "category": "DATA"
         }
      ],
      "job_types": [
         {
            "name": "my-job",
            "version": "1.0.0",
            "title": "My Job",
            "description": "My job description.",
            "category": "example",
            "author_name": null,
            "author_url": null,
            "is_operational": true,
            "icon_code": "f013",
            "docker_privileged": false,
            "docker_image": null,
            "priority": 100,
            "timeout": 1800,
            "max_tries": 3,
            "cpus_required": 1.0,
            "mem_required": 64.0,
            "disk_out_const_required": 64.0,
            "disk_out_mult_required": 0.0,
            "interface": {
               "version": "1.0",
               "command": "my-cmd",
               "command_arguments": "${input_file} ${job_output_dir}",
               "input_data": [
                  {
                     "media_types": [
                        "image/png"
                     ],
                     "required": true,
                     "type": "file",
                     "name": "input_file"
                  }
               ],
               "output_data": [
                  {
                     "media_type": "image/jpg",
                     "required": true,
                     "type": "file",
                     "name": "my-output-file"
                  }
               ],
               "shared_resources": []
            }
            "error_mapping": {
               "version": "1.0",
               "exit_codes": {
                  "1": "my-error"
               }
            },
            "trigger_rule": {
               "type": "PARSE",
               "name": "my-rule",
               "configuration": {
                  "version": "1.0",
                  "data": {
                     "workspace_name": "products",
                     "input_data_name": "input_file"
                  },
                  "condition": {
                     "media_type": "image/png",
                     "data_types": []
                  }
               }
            }
         }
      ],
      "recipe_types": [
         {
            "name": "my-recipe",
            "version": "1.0.0",
            "title": "My Recipe",
            "description": "My recipe description.",
            "definition": {
               "version": "1.0",
               "input_data": [
                  {
                     "media_types": [
                        "image/png"
                     ], 
                     "required": true,
                     "type": "file",
                     "name": "input_file"
                   }
               ],
               "jobs": []
            },
            "trigger_rule": {
               "type": "PARSE",
               "name": "my-rule",
               "configuration": {
                  "version": "1.0",
                  "data": {
                     "workspace_name": "products",
                     "input_data_name": "input_file"
                  },
                  "condition": {
                     "media_type": "image/png",
                     "data_types": []
                  }
               }
            }
         } 
      ]
   }

The *errors* field is used to define the meaning of any exit codes that a job type may produce at the end of its
execution when it detects a known problem. The *job_types* field lists all of the types of jobs to import, which is the
smallest unit of work in Scale. A job type includes basic attributes, as well as all the associated error mappings,
command line interface, and trigger rule that kicks off the job as data arrives. The *recipe_types* field lists all of
the types of recipes to import, which is used to build a processing workflow composed of job types to execute under
different conditions. Recipes types support sequential and/or parallel processing constructs and therefore can trigger
processing as data arrives or other jobs generate products upon completion. To see all of the options for an exported
configuration, please refer to the Configuration Specification below.

.. _architecture_port_spec:

Import/Export Configuration Specification Version 1.0
------------------------------------------------------------------------------------------------------------------------

A valid exported configuration is a JSON document with the following structure:
 
.. code-block:: javascript

   {
      "version": "1.0",
      "errors": [
         ...
      ],
      "job_types": [
         ...
      ],
      "recipe_types": [
         ...
      ]
   }

**version**: JSON string

    The *version* is an optional string value that defines the version of the configuration used. This allows updates to
    be made to the specification while maintaining backwards compatibility by allowing Scale to recognize an older
    version and convert it to the current version. The default value for *version* if it is not included is the latest
    version, which is currently 1.0. It is recommended, though not required, that you include the *version* so that
    future changes to the specification will still accept your ingest trigger rule configuration.

**errors**: JSON array

    The *errors* field is optional and contains JSON objects that define attributes required to import a new error or
    edit an existing error identified by the name attribute.

**job_types**: JSON array

    The *job_types* field is optional and contains JSON objects that define attributes required to import a new job type
    or edit an existing job type identified by the combination of the name and version attributes.

**recipe_types**: JSON array

    The *recipe_types* field is optional and contains JSON objects that define attributes required to import a new
    recipe type or edit an existing recipe type identified by the combination of the name and version attributes.
