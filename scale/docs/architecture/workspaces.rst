
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

        **s3**

            An "s3" broker utilizes the Amazon Web Services (AWS) Simple Storage Service (S3) for file storage

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
      "version": "1.0",
      "broker": {
         "type": "host",
         "host_path": "/the/absolute/host/path"
      }
   }

The host broker requires one additional field in its configuration:

**host_path**: JSON string

    The *host_path* is a required string that specifies the absolute path of the host's local directory that should be
    mounted into a job's container in order to access the workspace's files.

NFS Broker *(experimental)*
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
      "version": "1.0",
      "broker": {
         "type": "nfs",
         "nfs_path": "host:/my/path"
      }
   }

The NFS broker requires one additional field in its configuration:

**nfs_path**: JSON string

    The *nfs_path* is a required string that specifies the remote NFS path to use for storing and retrieving the
    workspace files. It should be in the format *host:/path*.

S3 Broker *(experimental)*
------------------------------------------------------------------------------------------------------------------------

The S3 broker references a storage location that exists as an S3 bucket in your AWS account. Please take note of the
bucket name, which is typically of the form *my_name.domain.com* since bucket names must be globally unique
(See `Bucket Restrictions`_). The bucket must be configured for read and/or write access through an appropriate IAM
account (Identity and Access Management). Once the IAM account is created and granted permissions to the bucket, then
there are two ways to handle authentication. IAM roles can be used to automatically grant permissions to the EC2
executing the broker operations (See `AWS Roles`_). This method is preferred because no secret keys are required.
Alternatively, an *ACCESS KEY ID* and *SECRET ACCESS KEY* can be generated and used with this broker
(See `AWS Credentials`_). These tokens allow 3rd party software to access resources on behalf of the associated account.

.. _Bucket Restrictions: http://docs.aws.amazon.com/AmazonS3/latest/dev/BucketRestrictions.html
.. _AWS Roles: http://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html
.. _AWS Credentials: http://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSGettingStartedGuide/AWSCredentials.html

**Security**

A dedicated IAM account should be used rather than the root AWS account to limit the risk of damage if a leak were to
occur and similarly the IAM account should be given the minimum possible permissions needed to work with the bucket. The
access tokens should also be changed periodically to further protect against leaks.

While this broker is in the experimental phase, the access keys are currently stored in plain text within the Scale
database and exposed via the REST interface. A future version will maintain these values using a more appropriate
encrypted store service.

Example S3 broker configuration:

.. code-block:: javascript

   {
      "version": "1.0",
      "broker": {
         "type": "s3",
         "bucket_name": "my_bucket.domain.com",
         "credentials": {
            "access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
         }
      }
   }

The S3 broker requires the following additional fields in its configuration:

**bucket_name**: JSON string

    The *bucket_name* is a required string that specifies the globally unique name of a storage bucket within S3. The
    bucket should be created before attempting to use it here.

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
