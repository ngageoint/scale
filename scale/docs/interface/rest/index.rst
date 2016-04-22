
.. _rest:

======================
RESTful HTTP Interface
======================

Scale provides a RESTful HTTP interface for its own web UI and for any external
applications that would like to connect to Scale. The following sections
describe the services available for each component of Scale.

.. _rest_versions:

API Versions
------------
:Latest Version: ``v3``
:Other Versions: No prefix

The Scale API uses a versioning scheme based on a prefix in the URL path. Any time a breaking change is made to the API
a new version prefix will be included so that users can opt-in to the changes over time. In the short-term, the system
will support both the old and new API versions within the same release. Eventually, old API versions will be deprecated
and subsequently removed in later releases.

Since the API did not initially include a version scheme, the legacy URLs do not contain a prefix and the first release
to include a version prefix is 3.0. Therefore, any URL listed in the documentation below will work as-is in the current
release, but users should start including the version prefix in all requests going forward.

All endpoints should include a prefix of the form ``vX``, where ``X`` is the desired version number. Making a request
with an invalid version prefix will result in a 404 error.

| Documentation Example: ``/job-types/``
| Actual Request Example: ``/v3/job-types/``
|

.. _rest_services:

Services
--------

.. toctree::
   :maxdepth: 1

   error
   ingest
   job
   job_execution
   job_type
   metrics
   node
   port
   product
   queue
   recipe
   recipe_type
   scale_file
   scheduler
   source_file
   strike
   system
   trigger
   workspace
