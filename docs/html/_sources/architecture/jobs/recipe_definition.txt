
.. _architecture_jobs_recipe_definition:

Recipe Definition
========================================================================================================================

A recipe is a collection of jobs that get run together. The recipe definition is a JSON document that defines how the
recipe is run. It will describe the recipe's inputs, the jobs that will be run as part of the recipe, and how the inputs
and outputs of those jobs are connected.

Consider the following example algorithms, called make_geotiff.py and detect_points.py. make_geotiff.py is a Python
script that takes a PNG image file and a CSV containing georeference information for the PNG. It combines the
information from the two files to create a GeoTIFF file, which is an image format that contains georeference
information. detect_points.py is a Python script that takes a GeoTIFF image file and creates a GeoJSON file that
contains the coordinates of various points of interest found in the GeoTIFF. The job interfaces of the two algorithms
could be defined as follows (see :ref:`architecture_jobs_interface` for how to define job interfaces):

.. code-block:: javascript

   {
      "version": "1.0",
      "command": "python make_geotiff.py",
      "command_arguments": "${image} ${georeference_data} ${job_output_dir}",
      "input_data": [
         {
            "name": "image",
            "type": "file",
            "media_types": [
               "image/png"
            ]
         },
         {
            "name": "georeference_data",
            "type": "file",
            "media_types": [
               "text/csv"
            ]
         }
      ],
      "output_data": [
         {
            "name": "geo_image",
            "type": "file",
            "media_type": "image/tiff"
         }
      ]
   }

.. code-block:: javascript

   {
      "version": "1.0",
      "command": "python detect_points.py",
      "command_arguments": "${image} ${job_output_dir}",
      "input_data": [
         {
            "name": "image",
            "type": "file",
            "media_types": [
               "image/tiff"
            ]
         }
      ],
      "output_data": [
         {
            "name": "geo_image",
            "type": "file",
            "media_type": "application/vnd.geo+json"
         }
      ]
   }

Now we would like to combine those two algorithms into a recipe that runs both jobs. The recipe will take a PNG and a
CSV, pass these files to the make_geotiff.py algorithm, and then pass the resulting GeoTIFF file to the detect_points.py
algorithm. The recipe definition could be described as follows:

**Example recipe definition:**

.. code-block:: javascript

   {
      "version": "1.0",
      "input_data": [
         {
            "name": "image",
            "type": "file",
            "media_types": [
               "image/png"
            ]
         },
         {
            "name": "georeference_data",
            "type": "file",
            "media_types": [
               "text/csv"
            ]
         }
      ],
      "jobs": [
         {
            "name": "make_geotiff",
            "job_type": {
               "name": "geotiff-maker",
               "version": "1.2.3"
            },
            "recipe_inputs": [
               {
                  "recipe_input": "image",
                  "job_input": "image"
               },
               {
                  "recipe_input": "georeference_data",
                  "job_input": "georeference_data"
               }
            ]
         },
         {
            "name": "detect_points",
            "job_type": {
               "name": "point-detector",
               "version": "4.5.6"
            },
            "dependencies": [
               {
                  "name": "make_geotiff",
                  "connections": [
                     {
                        "output": "geo_image",
                        "input": "image"
                     }
                  ]
               }
            ]
         }
      ]
   }

The *input_data* value is a list detailing the inputs to the recipe; in this case an input called *image* that is a file
with media type *image/png* and an input called *georeference_data* which is a CSV file. These inputs happen to be
identical to the inputs of the make_geotiff.py job. The *job* value is a list of all of the jobs that make up this
recipe and how their inputs and outputs are connected with the rest of the recipe. The make_geotiff.py and
detect_points.py are both job types that are stored in Scale. The *job_type* object indicates the type of the job that
we want to run within the recipe. The *name* value defines the name of the job within the recipe (for linking jobs
together). The "make_geotiff" job uses the *recipe_inputs* list to connect the recipe inputs to its job inputs. The
recipe inputs happen to have the same name of the "make_geotiff" job inputs in this example, but the names do not need
to be the same. The "detect_points" job uses the *dependencies* list to describe that it depends on the "make_geotiff"
job to successfully complete before "detect_points" is put on the queue. The *connections* list indicates the output
"geo_image" from the "make_geotiff" job should be fed to the "image" input of the "detect_points" job. To see all of the
options for defining a recipe, please refer to the Recipe Definition Specification below.

.. _architecture_jobs_recipe_definition_spec:

Recipe Definition Specification Version 1.0
-------------------------------------------------------------------------------

A valid recipe definition is a JSON document with the following structure:
 
.. code-block:: javascript

   {
      "version": STRING,
      "input_data": [
         {
            "name": STRING,
            "type": "property",
            "required": true|false
         },
         {
            "name": STRING,
            "type": "file",
            "required": true|false,
            "media_types": [
               STRING, STRING
            ]
         },
         {
            "name": STRING,
            "type": "files",
            "required": true|false,
            "media_types": [
               STRING, STRING
            ]
         }
      ],
      "jobs": [
         {
            "name": STRING,
            "job_type": {
               "name": STRING,
               "version": STRING
            },
            "recipe_inputs": [
               {
                  "recipe_input": STRING,
                  "job_input": STRING
               }
            ],
            "dependencies": [
               {
                  "name": STRING,
                  "connections": [
                     {
                        "output": STRING,
                        "input": STRING
                     }
                  ]
               }
            ]
         }
      ]
   }

**version**: JSON string

    The *version* is an optional string value that defines the version of the definition specification used. This allows
    updates to be made to the specification while maintaining backwards compatibility by allowing Scale to recognize an
    older version and convert it to the current version. The default value for *version* if it is not included is the
    latest version, which is currently 1.0. It is recommended, though not required, that you include the *version* so
    that future changes to the specification will still accept the recipe definition.

    Scale must recognize the version number as valid for the recipe to work. Currently, "1.0" is the only valid version.

**input_data**: JSON array

    The *input_data* is an optional list of JSON objects that define the inputs the recipe receives to run all of its
    jobs. If not provided, *input_data* defaults to an empty list (no inputs). The JSON object that represents each
    input has the following fields:

    **name**: JSON string

        The *name* is a required string that defines the name of the input. The name of every input in the recipe must
        be unique. This name must only be composed of less than 256 of the following characters:
        alphanumeric, " ", "_", and "-".

    **required**: JSON boolean

        The *required* field is optional and indicates if the input is required for the recipe to run successfully. If
        not provided, the *required* field defaults to *true*.

    **type**: JSON string

        The *type* is a required string from a defined set that defines the type of the input. The *input_data* JSON
        object may have additional fields depending on its *type*. The valid types are:

        **property**

            A "property" input is a string that is passed to the recipe. A "property" input has no additional fields.

        **file**

            A "file" input is a single file that is provided to the recipe. A "file" input has the following additional
            fields:

            **media_types**: JSON array

                A *media_types* field on a "file" input is an optional list of strings that designate the required media
                types for any file being passed in the input. Any file that does not match one of the listed media types
                will be prevented from being passed to the recipe. If not provided, the *media_types* field defaults to
                an empty list and all media types are accepted for the input.

        **files**

            A "files" input is a list of one or more files that is provided to the recipe. A "files" input has the
            following additional fields:

            **media_types**: JSON array

                A *media_types* field on a "files" input is an optional list of strings that designate the required
                media types for any files being passed in the input. Any file that does not match one of the listed
                media types will be prevented from being passed to the recipe. If not provided, the *media_types* field
                defaults to an empty list and all media types are accepted for the input.

**jobs**: JSON array

    The *jobs* value is a required list of JSON objects that define the jobs that will be run as part of the recipe. The
    JSON object that represents each job has the following fields:

    **name**: JSON string

        The *name* is a required string that defines the name of the job within the recipe. The name of every job in the
        recipe must be unique. This name must only be composed of less than 256 of the following characters:
        alphanumeric, " ", "_", and "-".

    **job_type**

        The *job_type* object is a required reference to the job type to run for this place in the recipe. A job type
        is uniquely identified by the combination of its system name and version.

        **name**: JSON string

            The name used by the system to refer to a job, including in database, recipe, or service references.

        **version**: JSON string

            The specific version of a job to run since a named job could have multiple versions.

    **recipe_inputs**: JSON array

        The *recipe_inputs* value is an optional list that specifies the recipe inputs that should be passed to this
        job's inputs. If not provided, *recipe_inputs* defaults to an empty list (no recipe inputs used by this job).
        The JSON object that represents each connection to a recipe input has the following fields:

        **recipe_input**: JSON string

            The *recipe_input* is a required string that defines the name of the recipe input to pass to the job.

        **job_input**: JSON string

            The *job_input* is a required string that defines the name of the job input that the recipe input should be
            passed to.

    **dependencies**: JSON array

        The *dependencies* value is an optional list that specifies the other jobs that this job is dependent on. If not
        provided, *dependencies* defaults to an empty list (no dependencies so this job will be queued immediately when
        the recipe is created).The JSON object that represents each connection to a recipe input has the following
        fields:

        **name**: JSON string

            The *name* is a required string that provides the name of the job that is being depended upon. The *name*
            value must match the name of another job within the recipe definition. Circular job dependencies are
            invalid.

        **connections**: JSON array

            The *connections* value is an optional list that specifies the outputs of the job depended upon that should
            be passed to this job's inputs. If not provided, *connections* defaults to an empty list (no outputs used by
            this job). The JSON object that represents each connection to a job output has the following fields:

            **output**: JSON string

                The *output* is a required string that defines the name of the output of the depended upon job.

            **input**: JSON string

                The *input* is a required string that defines the name of this job's input that should receive the
                output from the depended upon job.