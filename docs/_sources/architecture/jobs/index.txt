
.. _architecture_jobs:

Jobs and Recipes
================

Jobs represent the various algorithms or units of work that get executed in Scale. Recipes represent a graph/workflow of
jobs that allow jobs to depend upon one another and for files produced by one job to be fed as input into another job.

.. toctree::
   :maxdepth: 1

   batch_definition
   error_interface
   job_interface
   job_type_configuration
   job_data
   job_configuration
   recipe_definition
   recipe_data
