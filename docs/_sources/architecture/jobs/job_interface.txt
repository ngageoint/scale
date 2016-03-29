
.. _architecture_jobs_interface:

Job Interface
===============================================================================

The job interface is a JSON document that defines the interface for executing
the job's algorithm. It will describe the algorithm's inputs and outputs, as
well as the command line details for how to invoke the algorithm.

Consider the following example algorithm, called make_geotiff.py.
make_geotiff.py is a Python script that takes a PNG image file and a CSV
containing georeference information for the PNG. It combines the information
from the two files to create a GeoTIFF file, which is an image format that
contains georeference information. The job interface for the algorithm could be
defined as follows:

**Example job interface:**

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

The *command* value specifies that the algorithm is executed by invoking Python with the make_geotiff.py script. The
*command_arguments* value describes the command line arguments to pass to the make_geotiff.py script. The *image* file
input is first (this will be the absolute file system path of the file), the *georeference_data* file input will be
next, and finally an output directory is provided for the script to write any output files. The *input_data* value is a
list detailing the inputs to the algorithm; in this case an input called *image* that is a file with media type
*image/png* and an input called *georeference_data* which is a CSV file. Finally the *output_data* value is a list of
the algorithm outputs, which is a GeoTIFF file in this instance. To see all of the options for defining a job interface,
please refer to the Job Interface Specification below.

.. _architecture_jobs_interface_spec:

Job Interface Specification Version 1.0
-------------------------------------------------------------------------------

A valid job interface is a JSON document with the following structure:
 
.. code-block:: javascript

   {
      "version": STRING,
      "command": STRING,
      "command_arguments": STRING,
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
               STRING,
               STRING
            ]
         },
         {
            "name": STRING,
            "type": "files",
            "required": true|false,
            "media_types": [
               STRING,
               STRING
            ]
         }
      ],
      "output_data": [
         {
            "name": STRING,
            "type": "file",
            "required": true|false,
            "media_type": STRING
         },
         {
            "name": STRING,
            "type": "files",
            "required": true|false,
            "media_type": STRING
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

**command**: JSON string

    The *command* is a required string value that defines the main command to execute on the command line without any of
    the command line arguments. Unlike *command_arguments*, no string substitution will be performed.

**command_arguments**: JSON string

    The *command_arguments* is a required string value that defines the command line arguments to be passed to the
    *command* when it is executed. Although required, *command_arguments* may be an empty string (i.e. ""). Scale will
    perform string substitution on special values denoted by the pattern *${...}*. You can indicate that an input should
    be passed on the command line by using *${INPUT NAME}*. The value that is substituted depends on the type of the
    input. If you need the command line argument to be passed with a flag, you can use the following pattern:
    *${FLAG:INPUT NAME}*. There is also a special substitution value
    *${job_output_dir}*, which will be replaced with the absolute file system path of the output directory where the
    algorithm may write its output files. The algorithm should produce a results manifest named "results_manifest.json".
    The format for the results manifest can be found here: :ref:`algorithms_results_manifest`. Any output files must be
    registered in the results manifest.

**input_data**: JSON array

    The *input_data* is an optional list of JSON objects that define the inputs the algorithm receives to perform its
    function. If not provided, *input_data* defaults to an empty list (no inputs). The JSON object that represents each
    input has the following fields:

    **name**: JSON string

        The *name* is a required string that defines the name of the input. The name of every input and output in the
        interface must be unique. This name must only be composed of less than 256 of the following characters:
        alphanumeric, " ", "_", and "-".

    **required**: JSON boolean

        The *required* field is optional and indicates if the input is required for the algorithm to run successfully.
        If not provided, the *required* field defaults to *true*.

    **type**: JSON string

        The *type* is a required string from a defined set that defines the type of the input. The *input_data* JSON
        object may have additional fields depending on its *type*. The valid types are:

        **property**

            A "property" input is a string that is passed to the algorithm on the command line. When the algorithm is
            executed, the value of each "property" input will be substituted where its input name is located within
            the *command_arguments* string. A "property" input has no additional fields.

        **file**

            A "file" input is a single file that is provided to the algorithm. When the algorithm is executed, the
            absolute file system path of each input file will be substituted where its input name is located within the
            *command_arguments* string. A "file" input has the following additional fields:

            **media_types**: JSON array

                A *media_types* field on a "file" input is an optional list of strings that designate the required media
                types for any file being passed in the input. Any file that does not match one of the listed media types
                will be prevented from being passed to the algorithm. If not provided, the *media_types* field defaults
                to an empty list and all media types are accepted for the input.

        **files**

            A "files" input is a list of one or more files that is provided to the algorithm. When the algorithm is
            executed, the absolute file system path of a directory containing the list of files will be substituted
            where its input name is located within the *command_arguments* string. A "files" input has the following
            additional fields:

            **media_types**: JSON array

                A *media_types* field on a "files" input is an optional list of strings that designate the required
                media types for any files being passed in the input. Any file that does not match one of the listed
                media types will be prevented from being passed to the algorithm. If not provided, the *media_types*
                field defaults to an empty list and all media types are accepted for the input.

**output_data**: JSON array

    The *output_data* is an optional list of JSON objects that define the outputs the algorithm will produce as a result
    of its successful execution. If not provided, *output_data* defaults to an empty list (no outputs). The JSON object
    that represents each output has the following fields:

    **name**: JSON string

        The *name* is a required string that defines the name of the output. The name of every input and output in the
        interface must be unique. This name must only be composed of less than 256 of the following characters:
        alphanumeric, " ", "_", and "-".

    **required**: JSON boolean

        The *required* field is optional and indicates if the output is guaranteed to be produced by the algorithm on a
        **successful** run. If the algorithm may or may not product an output under normal conditions, the *required*
        field should be set to *false*. If not provided, the *required* field defaults to *true*.

    **type**: JSON string

        The *type* is a required string from a defined set that defines the type of the output. The *output_data* JSON
        object may have additional fields depending on its *type*. The valid types are:

        **file**

            A "file" output is a single file that is produced by the algorithm. A "file" output has the following
            additional fields:

            **media_type**: JSON string

                A *media_type* field on a "file" output is an optional string defining the media type of the file
                produced. If not provided, the media type of the file will be determined by Scale using the file
                extension as guidance.

        **files**

            A "files" output is a list of one or more files that are produced by the algorithm. A "files" output has the
            following additional fields:

            **media_type**: JSON string

                A *media_type* field on a "files" output is an optional string defining the media type of each file
                produced. If not provided, the media type of each file will be determined by Scale using the file
                extension as guidance.