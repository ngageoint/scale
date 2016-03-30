
.. _architecture_strike:

Strike
========================================================================================================================

Strike is the name of Scale's directory watching capability. A Strike process monitors a given directory on a Network
File System (NFS) for new files and ingests those files into a Scale workspace if they meet certain criteria. When a new
Strike process is created, a new job is created and executed to run the new process. A Strike process contains
configuration specifying the details of the NFS directory to monitor and how to ingest and store the files that appear
in the directory.

**Example Strike configuration:**

.. code-block:: javascript

   {
      "version": "1.0",
      "mount": "host:/my/path",
      "transfer_suffix": "_tmp",
      "files_to_ingest": [
          {
              "filename_regex": ".*h5",
              "data_types": [],
              "workspace_path": "/wrksp/path",
              "workspace_name": "rs"
          }
      ]
   }

The *mount* field specifies the NFS host and path that should be mounted in order to access the directory to be
monitored. The *transfer_suffix* field defines a suffix that is used on the file names to indicate that they are still
transferring and have not yet finished being copied into the monitored directory. The *files_to_ingest* value is a list
detailing the different files to ingest and how to ingest them. The *filename_regex* field defines a regular expression
to check against the names of newly copied files. If the expression matches a newly copied file name in the directory,
that file is ingested according to the other fields in the JSON object. The *data_types* field is list of strings. Any
file that matches the corresponding regular expression will have the data type strings "tagged" with the file. The data
type tags are used to categorize files and control which jobs and recipes they go to. The *workspace_path* specifies a
relative path within the workspace where each file will be stored. Three additional and dynamically named directories,
for the current year, month, and day, will be appended to the *workspace_path* value automatically by the Scale system
when a file is ingested (i.e. workspace_path/YYYY/MM/DD). The *workspace_name* field is the system name of the unique
workspace that should ingest the file. To see all of the options for a Strike process's configuration, please refer to
the Strike Configuration Specification below.

.. _architecture_strike_spec:

Strike Configuration Specification Version 1.0
------------------------------------------------------------------------------------------------------------------------

A valid Strike configuration is a JSON document with the following structure:
 
.. code-block:: javascript

   {
      "version": "1.0",
      "mount": STRING,
      "transfer_suffix": STRING,
      "files_to_ingest": [
          {
              "filename_regex": STRING,
              "data_types": [
                 STRING,
                 STRING
              ],
              "workspace_path": STRING,
              "workspace_name": STRING
          }
      ]
   }

**version**: JSON string

    The *version* is an optional string value that defines the version of the configuration used. This allows updates to
    be made to the specification while maintaining backwards compatibility by allowing Scale to recognize an older
    version and convert it to the current version. The default value for *version* if it is not included is the latest
    version, which is currently 1.0. It is recommended, though not required, that you include the *version* so that
    future changes to the specification will still accept your Strike configuration.

**mount**: JSON string

    The *mount* field is a required string that specifies the NFS host and path that should be mounted in order to
    access the monitored directory (format is *host:/file/path*).

**transfer_suffix**: JSON string

    The *transfer_suffix* field is a required string that defines a suffix that is used on the file names (by the
    system or process that is transferring files into the directory) to indicate that the files are still transferring
    and have not yet finished being copied into the monitored directory.

**files_to_ingest**: JSON array

    The *files_to_ingest* field is a list of JSON objects that define the rules for which files to ingest and how to
    ingest them. The array must contain at least one item. Each JSON object has the following fields:

    **filename_regex**: JSON string

        The *filename_regex* field is a required string that defines a regular expression to check against the names of
        newly copied files. When a new file is copied in the monitored directory, each expression is checked against the
        file name in order of the *files_to_ingest* array. If an expression matches a newly copied file name in the
        directory, that file is ingested according to the other fields in the JSON object and all subsequent
        rules/expressions in the list are ignored.

    **data_types**: JSON array

        The *data_types* field is an optional list of strings. Any file that matches the corresponding file name regular
        expression will have these data type strings "tagged" with the file. If not provided, *data_types* defaults to
        an empty array.

    **workspace_path**: JSON string

        The *workspace_path* field is a required string that specifies a relative path within the workspace where each
        file will be stored. Three additional and dynamically named directories, for the current year, month, and day,
        will be appended to the *workspace_path* value automatically by the Scale system when a file is ingested
        (i.e. workspace_path/YYYY/MM/DD).

    **workspace_name**: JSON string

        The *workspace_name* field is required and contains the unique system name of the workspace that should store
        each file that matches the corresponding file name regular expression.
