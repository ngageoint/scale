
.. _architecture_workspaces:

Workspaces
========================================================================================================================

A workspace in the Scale system is a location where files are stored (source files, product files, etc). A workspace
contains configuration specifying how files are stored into and retrieved from the workspace. Workspaces are configured
to use various *brokers*, which know how to store/retrieve files in different storage systems (e.g. NFS, FTP).

**Example workspace configuration:**

.. code-block:: javascript

   {
      "version": "1.0",
      "broker": {
         "type": "nfs",
         "mount": "host:/my/path"
      }
   }

The *broker* value is a JSON object providing the configuration for this workspace's broker. The *type* value indicates
that the NFS (Network File System) broker should be used for this workspace. The *mount* field specifies the NFS host
and path that should be mounted in order to access the files. To see all of the options for a workspace's configuration,
please refer to the Workspace Configuration Specification below.

.. _architecture_workspaces_spec:

Workspace Configuration Specification Version 1.0
------------------------------------------------------------------------------------------------------------------------

A valid workspace configuration is a JSON document with the following structure:
 
.. code-block:: javascript

   {
      "version": STRING,
      "broker": {
         "type": "nfs",
         "mount": STRING
      }
   }

**version**: JSON string

    The *version* is an optional string value that defines the version of the configuration used. This allows updates to
    be made to the specification while maintaining backwards compatibility by allowing Scale to recognize an older
    version and convert it to the current version. The default value for *version* if it is not included is the latest
    version, which is currently 1.0. It is recommended, though not required, that you include the *version* so that
    future changes to the specification will still accept your workspace configuration.

**broker**: JSON object

    The *broker* is a JSON object that defines the broker that the workspace should use for retrieving and storing
    files. The *broker* JSON object has the following fields:

    **type**: JSON string

        The *type* is a required string that specifies the type of the broker to use. The other fields that configure
        the broker are based upon the type of the broker in the *type* field. The valid broker types are:

        **nfs**

            An "nfs" broker utilizes an NFS (Network File System) for file storage. An NFS broker has the following
            additional field:

            **mount**: JSON string

                The *mount* is a required string that specifies the NFS host and path that should be mounted in order to
                access the files (format is *host:/file/path*).
