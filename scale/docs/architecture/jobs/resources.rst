
.. _architecture_jobs_resources:

Resources
========================================================================================================================

The resources document is a JSON document that defines a set of named resources with floating point values.

**Example job configuration:**

.. code-block:: javascript

  {
     "version": "1.0",
     "resources": {
        "cpus": 1.5,
        "mem": 64.0,
        "foo": 3.1
     }
  }

In this example there are 1.5 CPUs, 64.0 MiB of memory, and 3.1 units of "foo".

.. _architecture_jobs_resources_spec:

Resources Specification Version 1.0
------------------------------------------------------------------------------------------------------------------------

A valid resources document is a JSON document with the following structure:

.. code-block:: javascript

   {
      "version": STRING,
      "resources": {STRING: NUMBER}
   }

**version**: JSON string

    The *version* is an optional string value that defines the version of the resources specification used. This
    allows updates to be made to the specification while maintaining backwards compatibility by allowing Scale to
    recognize an older version and convert it to the current version. The default value for *version* if it is not
    included is the latest version, which is currently 1.0.

**resources**: JSON object

    The *resources* is a JSON object that contains the resource names and their values (floating point allowed) as
    key/value pairs. Arbitrary resources names are supported, but a few resource names have pre-defined meanings:

        *cpus*: The number of CPUs

        *mem*: The amount of memory in MiB

        *disk*: The amount of local disk space in MiB
