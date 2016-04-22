
.. _architecture_django:

Django/Code Base
========================================================================================================================

The Scale source code (this powers the scheduler, database schema, web server, and built-in jobs) is built upon Django,
a powerful Python web framework. The Scale system is made up of many Django "apps" that represent logical pieces of the
system. Source code documentation for every app is provided below:

.. toctree::
   :maxdepth: 1

   code_docs/cli
   code_docs/error
   code_docs/ingest
   code_docs/job
   code_docs/mesos_api
   code_docs/metrics
   code_docs/node
   code_docs/port
   code_docs/product
   code_docs/queue
   code_docs/recipe
   code_docs/scheduler
   code_docs/shared_resource
   code_docs/source
   code_docs/storage
   code_docs/trigger
   code_docs/util
   code_docs/manage
