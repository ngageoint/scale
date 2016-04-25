
.. _algorithm_integration_results_manifest:

Results Manifest
===============================================================================

The results manifest is a JSON document that defines the output of an algorithm's run. Using the results manifest, you
can specify your outputs, parse information, run_information and errors. In addition, you can register artifacts by
printing a line to stdout with the following format "ARTIFACT:<output_name>:<path_to_file>". The artifact string must be
on a separate line, and if there are any conflicts with the manifest file, the manifest file takes precedence.

The following are some example output manifest files:

**Results manifest with one output**

.. code-block:: javascript

   {
      "version": "1.1",
      "output_data": [
         {
            "name" : "output_file",
            "file": {  
               "path" : "/tmp/job_exe_231/outputs/output.csv"
            }
         }
      ]
   }

The above manifest simply says that the output with the name "output_file" can be found on the local computer at the
location "/tmp/job_exe_231/outputs/output.csv".

**Results manifest with a parsed input**

.. code-block:: javascript

   {
      "version": "1.1",
      "parse_results": [
         {
            "filename" : "myfile.h5",
            "data_types" : [
               "H5",
               "VEG"
            ],
            "geo_metadata": {
               "data_started" : "2015-05-15T10:34:12Z",
               "data_ended" : "2015-05-15T10:36:12Z",
            }
         }
      ]
   }

This example is the result of one of the inputs (myfile.h5) being parsed.

Results Manifest Specification Version 1.1
----------------------------------------------------------------------------------

A valid results manifest is a JSON document with the following structure:

.. code-block:: javascript

   {
      "version": STRING,
      "output_data": [
         {
            "name": STRING,
            "file": {
               "path": STRING,
               "geo_metadata": {
                  "data_started": STRING(ISO-8601),
                  "data_ended": STRING(ISO-8601),
                  "geo_json": JSON
               }
            },
            "files": [
               {
                  "path": STRING,
                  "geo_metadata": {
                     "data_started": STRING(ISO-8601),
                     "data_ended": STRING(ISO-8601),
                     "geo_json": JSON
                  }
               }
            ]
         }
      ],
      "parse_results": [
         {
            "filename": STRING,
            "new_workspace_path": STRING,
            "data_types": [
               STRING,
               STRING
            ],
            "geo_metadata": {
               "data_started": STRING(ISO-8601),
               "data_ended": STRING(ISO-8601),
               "geo_json": JSON
            }
         }
      ],
      "info": {},  # TODO: document when completed
      "errors": {}  # TODO: document when completed
   }

**version**: JSON string

    The *version* is an optional string value that defines the version of the results manifest specification used.
    This allows updates to be made to the specification while maintaining backwards compatibility by allowing Scale
    to recognize an older version and convert it to the current version. The default value for *version* if it is
    not included is the latest version, which is currently 1.1. It is recommended, though not required, that you
    include the *version* so that future changes to the specification will still accept your results manifest

**output_data** JSON array

    The *output_data* is an optional array of output files that your algorithm produced. If not provided, it
    defaults to an empty list.  The JSON object that represents each *output_data* entry has the following
    fields:

    **name**: JSON string
 
        The *name* is a required string that indicates which field in the job_interface this output corresponds to.

    **file**: JSON object

        The *file* is an optional sting field, however either *file* or *files* must be present.  
        The *file* field should be used if the "file" output_type was used in the job interface.
        The *file* object has the following fields:

        **path**: JSON string

        The *path* is the location of the file on the machine that ran the algorithm. 

        **geo_metadata**: JSON object

        The *geo_metadata* contains additional geospatial information associated with the output file.  It contains
        the following fields:

            **data_started**: JSON string (ISO-8601)

                The *data_started* is an optional JSON string that is formatted to the ISO-8601 standard. 
                This field represents when the data from this file started.

            **data_ended**: JSON string (ISO-8601)

                The *data_ended* is an optional JSON string that is formatted to the ISO-8601 standard. 
                This field represents when the data from this file ended.

            **geo_json**: JSON object

                The *geo_json* is an optional JSON string containing the geospatial extents of the data.
                It is currently required that this contain a 3D geometry.
                In addition to storing the extents of the data, a center point is auto calculated.

    **files**: JSON array

        The *files* is an optional array of JSON objects, however either *file* or *files* must be present.
        The *files* field should be used if the "files" output_type was used in the job interface.
        Each *files* object has the following fields:

        **path**: JSON string

        The *path* is the location of the file on the machine that ran the algorithm. 

        **geo_metadata**: JSON object

        The *geo_metadata* contains additional geospatial information associated with the output file.  It contains
        the following fields:

            **data_started**: JSON string (ISO-8601)

                The *data_started* is an optional JSON string that is formatted to the ISO-8601 standard. 
                This field represents when the data from this file started.

            **data_ended**: JSON string (ISO-8601)

                The *data_ended* is an optional JSON string that is formatted to the ISO-8601 standard. 
                This field represents when the data from this file ended.

            **geo_json**: JSON object

                The *geo_json* is an optional JSON string containing the geospatial extents of the data.
                It is currently required that this contain a 3D geometry.
                In addition to storing the extents of the data, a center point is auto calculated.

**parse_results**: JSON array

    The parse_results is an array of JSON objects that contain information from parsing inputs to your algorithm.
    These results should be used to associate meta-data with input files to the algorithm.  Each of the parse results
    corresponds to a input from the job interface of the type "file".  Additionally, the file must be a "source" file.
    A "source" file is something that was not produced by an algorithm. Files produced by algorithms are known as
    "product" files. As an algorithm developer, this is not important, but when you are tying an algorithm to the
    scale data, this distinction is important.  Each parse_results object has the following fields:

    **filename**: JSON string

        The *filename* is a required JSON string that is the name of the file that you have performed the parsing on.

    **new_workspace_path**: JSON string

        The *new_workspace_path* is an optional JSON string that is a new location where the file should be stored.

    **data_started**: JSON string (ISO-8601)

        The *data_started* is an optional JSON string that is formatted to the ISO-8601 standard. This field represents
        when the data from this file started.

    **data_ended**: JSON string (ISO-8601)

        The *data_ended* is an optional JSON string that is formatted to the ISO-8601 standard. This field represents
        when the data from this file ended.

    **data_types**: JSON array

        The *data_types* is an optional array of JSON strings. Each of the strings is a file data type that this input
        file can be associated with.

    **gis_data_path**: JSON string

        The *gis_data_path* is an optional path to a GeoJSON file. The contents of the this file will be set in the
        meta_data for the given input file. The geometry will also be set for the file. In addition to storing the
        extents of the data, a center point is auto calculated.

        
Results Manifest Specification Version 1.0
----------------------------------------------------------------------------------

A valid version 1.0 results manifest is a JSON document with the following structure:

.. code-block:: javascript

   {
      "version": STRING,
      "files": [
         {
            "name": STRING,
            "path": STRING
         },
         {
            "name": STRING,
            "paths": [
               STRING,
               STRING
            ]
         }
      ],
      "parse_results": [
         {
            "filename": STRING,
            "data_started": STRING(ISO-8601),
            "data_ended": STRING(ISO-8601),
            "data_types": [
               STRING,
               STRING
            ],
            "gis_data_path": STRING
         }
      ],
      "info": {},  # TODO: document when completed
      "errors": {}  # TODO: document when completed
   }

**version**: JSON string

    The *version* is an optional string value that defines the version of the results manifest specification used.
    This allows updates to be made to the specification while maintaining backwards compatibility by allowing Scale
    to recognize an older version and convert it to the current version. The default value for *version* if it is
    not included is the latest version, which is currently 1.0. It is recommended, though not required, that you
    include the *version* so that future changes to the specification will still accept your results manifest

**files** JSON array

    The *files* is an optional array of output files that your algorithm produced. If not provided, files
    defaults to an empty list.  The JSON object that represents each *files* entry has the following
    fields:

    **name**: JSON string
 
        The *name* is a required string that indicates which field in the job_interface this output corresponds to.

    **path**: JSON string

        The *path* is an optional sting field, however either *path* or *paths* must be present.
        The *path* is the location of the file on the machine that ran the algorithm. The *path* field should be used
        if the "file" output_type was used in the job interface.

    **paths**: JSON array

        The *paths* is an optional array of JSON strings, however either *path* or *paths* must be present.
        Each string in the array is a path to a file that corresponds to a job_output. The *paths* field should be used
        if the "files" output_type was used in the job interface.

**parse_results**: JSON array

    The parse_results is an array of JSON objects that contain information from parsing inputs to your algorithm.
    These results should be used to associate meta-data with input files to the algorithm.  Each of the parse results
    corresponds to a input from the job interface of the type "file".  Additionally, the file must be a "source" file.
    A "source" file is something that was not produced by an algorithm. Files produced by algorithms are known as
    "product" files. As an algorithm developer, this is not important, but when you are tying an algorithm to the
    scale data, this distinction is important.  Each parse_results object has the following fields:

    **filename**: JSON string

        The *filename* is a required JSON string that is the name of the file that you have performed the parsing on.

    **data_started**: JSON string (ISO-8601)

        The *data_started* is an optional JSON string that is formatted to the ISO-8601 standard. This field represents
        when the data from this file started.

    **data_ended**: JSON string (ISO-8601)

        The *data_ended* is an optional JSON string that is formatted to the ISO-8601 standard. This field represents
        when the data from this file ended.

    **data_types**: JSON array

        The *data_types* is an optional array of JSON strings. Each of the strings is a file data type that this input
        file can be associated with.

    **gis_data_path**: JSON string

        The *gis_data_path* is an optional path to a GeoJSON file. The contents of the this file will be set in the
        meta_data for the given input file. The geometry will also be set for the file. In addition to storing the
        extents of the data, a center point is auto calculated.
