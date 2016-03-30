
.. _architecture_jobs_job_data:

Job Data
========================================================================================================================

The job data is a JSON document that defines the actual data and configuration on which a specific job will run. It will
describe all of the data being passed to the job's inputs, as well as configuration for how to handle the job's output.
The job data is required when placing a specific job on the queue for the first time.

Consider our previous example algorithm, make_geotiff.py, from :ref:`architecture_jobs_interface`. The job data for
queuing and running a make_geotiff.py job could be defined as follows:

**Example job data:**

.. code-block:: javascript

   {
      "version": "1.0",
      "input_data": [
         {
            "name": "image",
            "file_id": 1234
         },
         {
            "name": "georeference_data",
            "file_id": 1235
         }
      ],
      "output_data": [
         {
            "name": "geo_image",
            "workspace_id": 12
         }
      ]
   }

The *input_data* value is a list detailing the data to pass to each input to the job. In this case the input called
*image* that takes a PNG image file is being passed a file from the Scale system that has the unique ID 1234, and the
input called *georeference_data* which takes a CSV file is being passed a Scale file with the ID 1235. The *output_data*
value is a list detailing the configuration for handling the job's outputs, which in our example is a single GeoTIFF
file. The configuration in our example defines that after the GeoTIFF file is produced by the job, it should be stored
in the workspace with the unique ID 12. To see all of the options for defining job data, please refer to the Job Data
Specification below.

.. _architecture_jobs_job_data_spec:

Job Data Specification Version 1.0
------------------------------------------------------------------------------------------------------------------------

A valid job data is a JSON document with the following structure:
 
.. code-block:: javascript

   {
      "version": STRING,
      "input_data": [
         {
            "name": STRING,
            "value": STRING
         },
         {
            "name": STRING,
            "file_id": INTEGER
         },
         {
            "name": STRING,
            "file_ids": [
               INTEGER,
               INTEGER
            ]
         }
      ],
      "output_data": [
         {
            "name": STRING,
            "workspace_id": INTEGER
         }
      ]
   }

**version**: JSON string

    The *version* is an optional string value that defines the version of the data specification used. This allows
    updates to be made to the specification while maintaining backwards compatibility by allowing Scale to recognize an
    older version and convert it to the current version. The default value for *version* if it is not included is the
    latest version, which is currently 1.0. It is recommended, though not required, that you include the *version* so
    that future changes to the specification will still accept your job data.

**input_data**: JSON array

    The *input_data* is a list of JSON objects that define the actual data the job receives for its inputs. If not
    provided, *input_data* defaults to an empty list (no input data). For the job data to be valid, every required input
    in the matching job interface must have a corresponding entry in this *input_data* field. The JSON object that
    represents each input data has the following fields:

    **name**: JSON string

        The *name* is a required string that gives the name of the input that the data is being provided for. It should
        match the name of an input in the job's interface. The name of every input and output in the job data must be
        unique.

    The other fields that describe the data being passed to the input are based upon the *type* of the input as it is
    defined in the job interface, see :ref:`architecture_jobs_interface_spec`. The valid types from the job interface
    specification are:

    **property**

        A "property" input has the following additional field:

        **value**: JSON string

            The *value* field contains the string value that will be passed to the "property" input.

    **file**

        A "file" input has the following additional field:

        **file_id**: JSON number

            The required *file_id* field contains the unique ID of a file in the Scale system that will be passed to the
            input. The file must meet all of the criteria defined in the job interface for the input.

    **files**

        A "files" input has the following additional field:

        **file_ids**: JSON array

            The required *file_ids* field is a list of unique IDs of the files in the Scale system that will be passed
            to the input. Each file must meet all of the criteria defined in the job interface for the input. A "files"
            input will accept a *file_id* field instead of a *file_ids* field (the input will be passed a list
            containing the single file).

**output_data**: JSON array

    The *output_data* is a list of JSON objects that define the details for how the job should handle its
    outputs. If not provided, *output_data* defaults to an empty list (no output data). For the job data to be valid,
    every output in the matching job interface must have a corresponding entry in this *output_data* field. The JSON
    object that represents each output data has the following fields:

    **name**: JSON string

        The *name* is a required string that gives the name of the input that the data is being provided for. It should
        match the name of an input in the job's interface. The name of every input and output in the job data must be
        unique.

    The other fields that describe the output configuration are based upon the *type* of the output as it is defined in
    the job interface, see :ref:`architecture_jobs_interface_spec`. The valid types from the job interface specification
    are:

    **file**

        A "file" output has the following additional field:

        **workspace_id**: JSON number

            The required *workspace_id* field contains the unique ID of the workspace in the Scale system that this
            output file should be stored in after it is produced.

    **files**

        A "files" output has the following additional field:

        **workspace_id**: JSON number

            The required *workspace_id* field contains the unique ID of the workspace in the Scale system that these
            output files should be stored in after they are produced.