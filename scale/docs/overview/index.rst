
.. _overview:

===============================================================================
Overview
===============================================================================

.. |br| raw:: html

	<br />

Scale is a system that provides management of automated processing on a cluster
of machines. It allows users to define *jobs*, which can be any type of script
or algorithm. These jobs run on ingested source data and produce product files.
The produced *products* can be disseminated to appropriate users and/or used to
evaluate the producing algorithm in terms of performance and accuracy.

**Mesos and Nodes** |br|
Scale runs across a cluster of networked machines (called *nodes*) that process
the jobs. Scale utilizes Apache Mesos, a free and open source project, for
managing the available resources on the nodes. Mesos informs Scale of available
computing resources and Scale schedules jobs to run on those resources.

**Ingest** |br|
Scale ingests source files using a Scale component called *Strike*. Strike is a
process that monitors an ingest directory into which source data files are
being copied. After a new source data file has been ingested, Scale produces
and places jobs on the *queue* depending on the type of the ingested file. Many
Strike processes can be run simultaneously, allowing Scale to monitor many
different ingest directories.

**Jobs** |br|
Scale creates jobs based on its known *job types*. A job type defines key
characteristics about an algorithm that Scale needs to know in order to run it
(what command to run, the algorithm's inputs and outputs, etc.) Job types are
labeled with versions, allowing Scale to run multiple versions of the same
algorithm. Jobs may be created automatically due to an event, such as the
ingest of a particular type of source data file, or they may be created
manually by a user. Jobs that need to be executed are placed onto and
prioritized within a queue before being scheduled onto an available node. When
multiple jobs need to be run in a serial or parallel sequence, a *recipe* can
be created that defines the job workflow.  

**Products** |br|
Jobs can produce products as a result of their successful execution. Products
may be disseminated to users or used to analyze and improve the algorithms that
produced them. Scale allows the creation of different *workspaces*. A workspace
defines a separate location for storing source or product files. When a job is
created, it is given a workspace to use for storing its results, allowing a
user to control whether the job's results are available to a wider audience or
are restricted to a private workspace for the user's own use.