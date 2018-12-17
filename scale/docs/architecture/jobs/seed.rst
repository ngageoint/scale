
.. _architecture_seed_manifest:

Seed Manifest
========================================================================================================================

Seed is a general standard to aid in the discovery and consumption of a discrete unit of work contained within a Docker image.
Scale job types in v6 have a Seed manifest that takes the place of the old job interface :ref:`architecture_jobs_interface`.
Like the old job interface, the Seed manifest describes how to run a job. What inputs it expects, what outputs it produces,
and how to invoke the algorithm.

.. _architecture_seed_manifest_spec:

Seed Manifest Specification Version 1.0
------------------------------------------------------------------------------------------------------------------------

The full Seed manifest definition can be found here:
https://ngageoint.github.io/seed/seed.html