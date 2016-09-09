
.. _architecture_strike:

Strike
========================================================================================================================

Strike is the name of Scale's system job that monitors and handles incoming source data files that are ingested into
Scale. A Strike job monitors a given workspace for new files. Scale administrators will want to create a Strike job for
each data feed that will be processed by Scale.

When a new file is copied into the monitored workspace, its file name is checked against a number of rules using regular
expressions configured for that Strike job. When the first rule that matches the new file's name is reached, that rule's
other fields indicate how Strike should handle the file, such as tagging it with data type tags or moving the file to a
new location in a different workspace.

.. _architecture_strike_spec:

Strike Configuration Specification Version 2.0
------------------------------------------------------------------------------------------------------------------------

A valid Strike configuration is a JSON document with the following structure:
 
.. code-block:: javascript

   {
       "version": "2.0",
       "workspace": STRING,
       "monitor": {
           "type": STRING
       },
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
    version, which is currently 2.0. It is recommended, though not required, that you include the *version* so that
    future changes to the specification will still accept your Strike configuration.

**workspace**: JSON string

    The *workspace* field is a required string that specifies the name of the workspace that is being monitored. The
    type of the workspace (its broker type) will determine which types of monitor can be used.

**monitor**: JSON object

    The *monitor* field is a required object that specifies the type and configuration of the monitor that will watch
    *workspace* for new files.

    **type**: JSON string

        The *type* is a required string that specifies the type of the monitor to use. The other fields that configure
        the monitor are based upon the type of the monitor in the *type* field. Certain monitor types may only be used
        on workspaces with corresponding broker types. The valid monitor types are:

        **dir-watcher**

            A "dir-watcher" monitor watches a file directory for incoming files. This monitor may only be used with a
            *host* workspace.

        **s3**

            An "s3" monitor utilizes an Amazon Web Services (AWS) Simple Queue Service (SQS) to receive AWS S3 file
            notification events. This monitor may only be used with an *s3* workspace.

        Additional *monitor* fields may be required depending on the type of monitor selected. See below for more
        information on each monitor type.

**files_to_ingest**: JSON array

    The *files_to_ingest* field is a list of JSON objects that define the rules for how to handle files that appear in
    the monitored workspace. The array must contain at least one item. Each JSON object has the following fields:

    **filename_regex**: JSON string

        The *filename_regex* field is a required string that defines a regular expression to check against the names of
        new files in the monitored workspace. When a new file appears in the workspace, the file's name is checked
        against each expression in order of the *files_to_ingest* array. If an expression matches the new file name in
        the workspace, that file is ingested according to the other fields in the JSON object and all subsequent rules
        in the list are ignored (first rule matched is applied).

    **data_types**: JSON array

        The *data_types* field is an optional list of strings. Any file that matches the corresponding file name regular
        expression will have these data type strings "tagged" with the file. If not provided, *data_types* defaults to
        an empty array.

    **new_workspace**: JSON string

        The *new_workspace* field optionally specifies the name of a new workspace to which the file should be copied.
        This allows the ingest process to move files to a different workspace after they appear in the monitored
        workspace.

    **new_file_path**: JSON string

        The *new_file_path* field is an optional string that specifies a new relative path for storing new files. If
        *new_workspace* is also specified, the file is moved to the new workspace at this new path location (instead of
        using the current path the new file originally came in on). If *new_workspace* is not specified, the file is
        moved to this new path location within the original monitored workspace. In either of these cases, three
        additional and dynamically named directories, for the current year, month, and day, will be appended to the
        *new_file_path* value automatically by the Scale system (i.e. workspace_path/YYYY/MM/DD).

Directory Watching Monitor
------------------------------------------------------------------------------------------------------------------------

The directory watching monitor uses a workspace that mounts a host directory into the container and watches that
directory for new files. Therefore this monitor only works with a host workspace. When a new file appears in the mounted
host directory, its file name is checked for the trailing file name suffix specified in the *transfer_suffix*
configuration field. While the file name contains the suffix, the monitor will continue tracking the size of the file
and how long it takes to copy the file into the directory. Whenever the file copy is complete, the process copying the
file should rename the file and remove the *transfer_suffix*. Once the monitor sees the renamed file, it will apply the
*files_to_ingest* rules against it. The monitor will create two sub-directories in the host directory, *deferred* and
*ingesting*.  If a copied file does not match any of the ingest rules, it is moved to the *deferred* directory. If the
file matches an ingest rule, it is moved to *ingesting* and an ingest job is created to ingest it.

Example directory watching monitor configuration:

.. code-block:: javascript

   {
       "version": "2.0",
       "workspace": "my-host-workspace",
       "monitor": {
           "type": "dir-watcher",
           "transfer_suffix": "_tmp"
       },
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

The directory watching monitor requires one additional field in its configuration:

**transfer_suffix**: JSON string

    The *transfer_suffix* field is a required string that defines a suffix that is used on the file names (by the
    system or process that is transferring files into the directory) to indicate that the files are still transferring
    and have not yet finished being copied into the monitored directory.

S3 Monitor
------------------------------------------------------------------------------------------------------------------------

The S3 monitor polls an AWS SQS queue for object creation notifications that describe new source data files available in
an AWS S3 bucket (so this monitor only works with an S3 workspace). After the monitor finds a new file in the S3 bucket,
it applies the file against the configured Strike rules.

Example S3 monitor configuration:

.. code-block:: javascript

   {
       "version": "2.0",
       "workspace": "my-host-workspace",
       "monitor": {
           "type": "s3",
           "sqs_name": "my-sqs"
           "credentials": {
               "access_key_id": "AKIAIOSFODNN7EXAMPLE",
               "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
           },
           "region_name": "us-east-1"
       },
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

The S3 monitor requires one additional field in its configuration:

**sqs_name**: JSON string

    The *sqs_name* field is a required string that defines the name of the SQS queue that should be polled for object
    creation notifications that describe new files in the S3 bucket.

**credentials**

    The *credentials* is a JSON object that provides the necessary information to access the bucket. This attribute
    should be omitted when using IAM role-based security. If it is included for key-based security, then both
    sub-attributes must be included. An IAM account should be created and granted the appropriate permissions to the
    bucket before attempting to use it here.

    **access_key_id**: JSON string

        The *access_key_id* is a unique identifier for the user account in IAM that will be used as a proxy for read and
        write operations within Scale.

    **secret_access_key**: JSON string

        The *secret_access_key* is a generated token that the system can use to prove it should be able to make requests
        on behalf of the associated IAM account without requiring the actual password used by that account.

**region_name**: JSON string

    The *region_name* is an optional string that specifies the AWS region where the SQS Queue is located. This is not
    always required, as environment variables or configuration files could set the default region, but it is a highly
    recommended setting for explicitly indicating the SQS region.