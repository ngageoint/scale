
.. _architecture_workspaces:

Workspaces
========================================================================================================================

A workspace in the Scale system is a location where files are stored (source files, product files, etc). A workspace
contains configuration specifying how files are stored into and retrieved from the workspace. Workspaces are configured
to use various *brokers*, which know how to store/retrieve files in different storage systems (e.g. NFS).

**Example workspace configuration:**

.. code-block:: javascript

   {
      "version": "1.0",
      "broker": {
         "type": "nfs",
         "nfs_path": "host:/my/path"
      }
   }

The *broker* value is a JSON object providing the configuration for this workspace's broker. The *type* value indicates
that the NFS (Network File System) broker should be used for this workspace. The *nfs_path* field specifies the NFS host
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
         "type": STRING
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
    files. The *broker* JSON object always has the following field:

    **type**: JSON string

        The *type* is a required string that specifies the type of the broker to use. The other fields that configure
        the broker are based upon the type of the broker in the *type* field. The valid broker types are:

        **host**

            A "host" broker mounts a local directory from the host into the job's container. Usually this local
            directory is a shared file system that has been mounted onto the host.

        **nfs**

            An "nfs" broker utilizes an NFS (Network File System) for file storage

        Additional *broker* fields may be required depending on the type of broker selected. See below for more
        information on each broker type.

Host Broker
------------------------------------------------------------------------------------------------------------------------

The host broker mounts a local directory from the host into the job's container. This local directory should be a shared
file system that has been mounted onto all hosts in the cluster. All hosts must have the same shared file system mounted
at the same location for this broker to work properly.

**Permissions**

The Scale Docker containers run with a UID and GID of 7498. To ensure that permissions are appropriately handled within
Docker, make sure that your host's local directory is owned by a user/group with UID/GID of 7498/7498.

**Security**

There are potential security risks involved with mounting a host directory into a Docker container. It is recommended
that you use another broker type if possible.

Example host broker configuration:

.. code-block:: javascript

   {
      "version": STRING,
      "broker": {
         "type": "host",
         "host_path": "/the/absolute/host/path"
      }
   }

The host broker requires one additional field in its configuration:

**host_path**: JSON string

    The *host_path* is a required string that specifies the absolute path of the host's local directory that should be
    mounted into a job's container in order to access the workspace's files.

NFS Broker
------------------------------------------------------------------------------------------------------------------------

The NFS broker mounts a remote network file system volume into the job's container.

**Plugin Required**

In order to use Scale's NFS broker, you must install and run the Netshare Docker plugin. Please see
http://netshare.containx.io/ for more information.

**Permissions**

The Scale Docker containers run with a UID and GID of 7498. To ensure that permissions are appropriately handled within
Docker, make sure that the directories in your NFS file volume are owned by a user/group with UID/GID of 7498/7498.

Example NFS broker configuration:

.. code-block:: javascript

   {
      "version": STRING,
      "broker": {
         "type": "nfs",
         "nfs_path": "host:/my/path"
      }
   }

The NFS broker requires one additional field in its configuration:

**nfs_path**: JSON string

    The *nfs_path* is a required string that specifies the remote NFS path to use for storing and retrieving the
    workspace files. It should be in the format *host:/path*.
