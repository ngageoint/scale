
.. _architecture_scan:

Scan
========================================================================================================================

Scan is the name of Scale's system job that scans for pre-existing source data files and ingests them into
Scale. A Scan job scans a given workspace for pre-existing files. Scale administrators would commonly use the Scan job
to bulk ingest data from a workspace prior to wiring it up for Strike processing.

When a file is identified within the workspace being scanned, its file name is checked against a number of rules using regular
expressions configured for that Scan job. When the first rule that matches the new file's name is reached, that rule's
other fields indicate how Scan should handle the file, such as tagging it with data type tags or moving the file to a
new location in a different workspace.

Scanning may be performed in two stages: dry run and ingest. When scanning is performed as a dry run, no ingest jobs will
result, but a file count will be stored in the Scan model. This can be valuable if it is desirable to identify the files
or count that will be matched prior to launching the actual ingest operations. There is no requirement to perform a dry
run first.

.. _architecture_scan_spec:

Scan Configuration Specification Version 1.0
------------------------------------------------------------------------------------------------------------------------

A valid Scan configuration is a JSON document with the following structure:
 
.. code-block:: javascript

   {
       "version": "1.0",
       "workspace": STRING,
       "scanner": {
           "type": STRING
       },
       "recursive": true,
       "files_to_ingest": [
           {
               "filename_regex": STRING,
               "data_types": [
                   STRING,
                   STRING
               ],
               "new_workspace": STRING,
               "new_file_path": STRING
           }
       ]
   }

**version**: JSON string

    The *version* is an optional string value that defines the version of the configuration used. This allows updates to
    be made to the specification while maintaining backwards compatibility by allowing Scale to recognize an older
    version and convert it to the current version. The default value for *version* if it is not included is the latest
    version, which is currently 1.0. It is recommended, though not required, that you include the *version* so that
    future changes to the specification will still accept your Scan configuration.

**workspace**: JSON string

    The *workspace* field is a required string that specifies the name of the workspace that is being scanned. The
    type of the workspace (its broker type) will determine which types of scanner can be used.

**scanner**: JSON object

    The *scanner* field is a required object that specifies the type and configuration of the scanner that will scan
    *workspace* for files.

    **type**: JSON string

        The *type* is a required string that specifies the type of the scanner to use. The other fields that configure
        the scanner are based upon the type of the scanner in the *type* field. Certain scanner types may only be used
        on workspaces with corresponding broker types. The valid scanner types are:

        **dir**

            A "dir" scanner identifies files within a directory. This scanner may only be used with a
            *host* workspace.

        **s3**

            An "s3" scanner identifies objects within an Amazon Web Services (AWS) Simple Storage Service (S3) bucket.
            This scanner may only be used with an *s3* workspace.

        Additional *scanner* fields may be required depending on the type of scanner selected. See below for more
        information on each scanner type.

**recursive**: JSON boolean

    The *recursive* field is an optional boolean that indicates whether a scanner should be limited to the root of a workspace
    or traverse the entire tree. If ommitted, the default is true for full tree recursion.

**files_to_ingest**: JSON array

    The *files_to_ingest* field is a list of JSON objects that define the rules for how to handle files that appear in
    the scanned workspace. The array must contain at least one item. Each JSON object has the following fields:

    **filename_regex**: JSON string

        The *filename_regex* field is a required string that defines a regular expression to check against the names of
        new files in the scanned workspace. When a new file appears in the workspace, the file's name is checked
        against each expression in order of the *files_to_ingest* array. If an expression matches the new file name in
        the workspace, that file is ingested according to the other fields in the JSON object and all subsequent rules
        in the list are ignored (first rule matched is applied).

    **data_types**: JSON array

        The *data_types* field is an optional list of strings. Any file that matches the corresponding file name regular
        expression will have these data type strings "tagged" with the file. If not provided, *data_types* defaults to
        an empty array.

    **new_workspace**: JSON string

        The *new_workspace* field optionally specifies the name of a new workspace to which the file should be copied.
        This allows the ingest process to move files to a different workspace after they appear in the scanned
        workspace.

    **new_file_path**: JSON string

        The *new_file_path* field is an optional string that specifies a new relative path for storing new files. If
        *new_workspace* is also specified, the file is moved to the new workspace at this new path location (instead of
        using the current path the new file originally came in on). If *new_workspace* is not specified, the file is
        moved to this new path location within the original scanned workspace. In either of these cases, three
        additional and dynamically named directories, for the current year, month, and day, will be appended to the
        *new_file_path* value automatically by the Scale system (i.e. workspace_path/YYYY/MM/DD).

Directory Scanner
------------------------------------------------------------------------------------------------------------------------

The directory scanner uses a workspace that mounts a host directory into the container and scans that
directory for files. Therefore this scanner only works with a host workspace. For each file detected in the mounted
host directory, its file name is checked for the trailing file name suffix specified in the optional *transfer_suffix*
configuration field. If the file name contains the suffix, the scanner will skip that file. 

Example directory watching scanner configuration:

.. code-block:: javascript

   {
       "version": "2.0",
       "workspace": "my-host-workspace",
       "scanner": {
           "type": "dir-watcher",
           "transfer_suffix": "_tmp"
       },
       "recursive": true,
       "files_to_ingest": [
           {
               "filename_regex": "*.h5",
               "data_types": [
                   "data type 1",
                   "data type 2"
               ],
               "new_workspace": "my-new-workspace",
               "new_file_path": "/new/file/path"
           }
       ]
   }

The directory watching scanner requires one additional field in its configuration:

**transfer_suffix**: JSON string

    The *transfer_suffix* field is an optional string that defines a suffix that is used on the file names to indicate 
    that files are still transferring and have not yet finished being copied into the scanned directory.

S3 Scanner
------------------------------------------------------------------------------------------------------------------------

The S3 scanner identifies objects within an Amazon Web Services (AWS) Simple Storage Service (S3) backed workspace. 
After the scanner finds a new object in the S3 bucket, it applies the configured Scan rules. 

Example S3 scanner configuration:

.. code-block:: javascript

   {
       "version": "1.0",
       "workspace": "my-s3-workspace",
       "scanner": {
           "type": "s3"
       },
       "recursive": true,
       "files_to_ingest": [
           {
               "filename_regex": "*.h5",
               "data_types": [
                   "data type 1",
                   "data type 2"
               ],
               "new_workspace": "my-new-workspace",
               "new_file_path": "/new/file/path"
           }
       ]
   }

The S3 scanner derives all its configuration from the associated workspace and
presently does not need any additional configuration.
