
.. _rest:

========
REST API
========

Scale provides a RESTful HTTP interface for its own web UI and for any external applications that would like to connect
to Scale. The following sections describe the services available.

.. _rest_versions:

API Versions
------------
Current Version: ``v6``

The Scale API uses a versioning scheme based on a prefix in the URL path. Any time a breaking change is made to the API
a new version prefix will be included so that users can opt-in to the changes over time. In the short-term, the system
will support both the old (deprecated) and current API versions within the same release. Eventually, deprecated API
versions will be removed in later releases.

It is recommended to make calls to the current REST API version. The future API version is still under construction and
may change at any time. The deprecated versions will be removed in the future, so please migrate any calls to the
current version.

All endpoints should include a prefix of the form ``vX``, where ``X`` is the desired version number. Making a request
without a version prefix or an invalid version prefix will result in a 404 error.

Request Example: ``/v6/jobs/``

.. _rest_services:

Current v6 Services
------------------

.. toctree::
   :maxdepth: 1

   v6/batch
   v6/data
   v6/diagnostic
   v6/error
   v6/ingest
   v6/job
   v6/job_type
   v6/metrics
   v6/node
   v6/queue
   v6/recipe
   v6/recipe_type
   v6/scale_file
   v6/scan
   v6/scheduler
   v6/strike
   v6/system
   v6/workspace
   v6/deprecated
