
.. _architecture_jobs_recipe_data:

Recipe Data
========================================================================================================================

The recipe data is a JSON document that defines the actual data and configuration on which a recipe will run. It will
describe all of the data being passed to the recipe's inputs, as well as the workspace for storing the output for all of
the recipe's jobs. The recipe data is required when creating and queuing a recipe.

Consider our previous example recipe definition from :ref:`architecture_jobs_recipe_definition`. The recipe data for
creating a recipe with that example definition could be defined as follows:

**Example recipe data:**

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
      "workspace_id": 12
   }

The *input_data* value is a list detailing the data to pass to each input in the recipe. In this case the input called
*image* that takes a PNG image file is being passed a file from the Scale system that has the unique ID 1234, and the
input called *georeference_data* which takes a CSV file is being passed a Scale file with the ID 1235. The
*workspace_id* value indicates that any files produced by the jobs in the recipe should be stored in the workspace with
the unique ID 12. To see all of the options for defining recipe data, please refer to the Recipe Data Specification
below.

.. _architecture_jobs_recipe_data_spec:

Recipe Data Specification Version 1.0
------------------------------------------------------------------------------------------------------------------------

A valid recipe data is a JSON document with the following structure:
 
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
      "workspace_id": INTEGER
   }

**version**: JSON string

    The *version* is an optional string value that defines the version of the data specification used. This allows
    updates to be made to the specification while maintaining backwards compatibility by allowing Scale to recognize an
    older version and convert it to the current version. The default value for *version* if it is not included is the
    latest version, which is currently 1.0. It is recommended, though not required, that you include the *version* so
    that future changes to the specification will still accept your recipe data.

**input_data**: JSON array

    The *input_data* is a list of JSON objects that define the actual data the recipe receives for its inputs. If not
    provided, *input_data* defaults to an empty list (no input data). For the recipe data to be valid, every required
    input in the matching recipe definition must have a corresponding entry in this *input_data* field. The JSON object
    that represents each input data has the following fields:

    **name**: JSON string

        The *name* is a required string that gives the name of the input that the data is being provided for. It should
        match the name of an input in the recipe's definition. The name of every input in the recipe data must be
        unique.

    The other fields that describe the data being passed to the input are based upon the *type* of the input as it is
    defined in the recipe definition, see :ref:`architecture_jobs_recipe_definition_spec`. The valid types from the
    recipe definition specification are:

    **property**

        A "property" input has the following additional field:

        **value**: JSON string

            The *value* field contains the string value that will be passed to the "property" input.

    **file**

        A "file" input has the following additional field:

        **file_id**: JSON number

            The required *file_id* field contains the unique ID of a file in the Scale system that will be passed to the
            input. The file must meet all of the criteria defined in the recipe definition for the input.

    **files**

        A "files" input has the following additional field:

        **file_ids**: JSON array

            The required *file_ids* field is a list of unique IDs of the files in the Scale system that will be passed
            to the input. Each file must meet all of the criteria defined in the recipe definition for the input. A
            "files" input will accept a *file_id* field instead of a *file_ids* field (the input will be passed a list
            containing the single file).

**workspace_id**: JSON number

    The *workspace_id* is required if any of the jobs in the recipe produce any output files. The *workspace_id* value
    is an integer providing the unique ID of the workspace to use for storing any files produced by the recipe's jobs.