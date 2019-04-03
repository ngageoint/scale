Scale
=====
[![Join the chat at https://gitter.im/ngageoint/scale](https://badges.gitter.im/ngageoint/scale.svg)](https://gitter.im/ngageoint/scale?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Build Status](https://travis-ci.org/ngageoint/scale.svg?branch=master)](https://travis-ci.org/ngageoint/scale)

Scale is a system that provides management of automated processing on a cluster of machines. It allows
users to define jobs, which can be any type of script or algorithm. These jobs run on ingested source
data and produce product files. The produced products can be disseminated to appropriate users and/or
used to evaluate the producing algorithm in terms of performance and accuracy.

Mesos and Nodes
---------------
Scale runs across a cluster of networked machines (called nodes) that process the jobs. Scale utilizes
Apache Mesos, a free and open source project, for managing the available resources on the nodes. Mesos
informs Scale of available computing resources and Scale schedules jobs to run on those resources.

Ingest
------
Scale ingests source files using a Scale component called Strike. Strike is a process that monitors an
ingest directory into which source data files are being copied. After a new source data file has been
ingested, Scale produces and places jobs on the queue depending on the type of the ingested file.
Many Strike processes can be run simultaneously, allowing Scale to monitor many different ingest directories.

Jobs
----
Scale creates jobs based on its known job types. A job type defines key characteristics about an algorithm
that Scale needs to know in order to run it (what command to run, the algorithm.s inputs and outputs, etc.)
Job types are labeled with versions, allowing Scale to run multiple versions of the same algorithm. Jobs may
be created automatically due to an event, such as the ingest of a particular type of source data file, or
they may be created manually by a user. Jobs that need to be executed are placed onto and prioritized within
a queue before being scheduled onto an available node. When multiple jobs need to be run in a serial or parallel
sequence, a recipe can be created that defines the job workflow.

Products
--------
Jobs can produce products as a result of their successful execution. Products may be disseminated to users
or used to analyze and improve the algorithms that produced them. Scale allows the creation of different
workspaces. A workspace defines a separate location for storing source or product files. When a job is created,
it is given a workspace to use for storing its results, allowing a user to control whether the job.s results
are available to a wider audience or are restricted to a private workspace for the user's own use.

Scale Dependencies
==================
Scale requires several external components to run as intended. PostgreSQL is used to store all internal system state
and must be accessible to both the scheduler and web server processes. Fluentd along with Elasticsearch are used to
collect and store all algorithm logs. A message broker is required for in-flight storage of internal Scale messages
and must be accessible to all system components. The following versions of these services are required to support Scale:

- Elasticsearch 6.6.2
- Fluentd 1.4
- PostgreSQL 9.4+
- PostGIS 2.0+
- Message Broker (RabbitMQ 3.6+ or Amazon SQS)


Note: We strongly recommend using managed services for PostgreSQL (AWS RDS), Messaging (AWS SQS) and Elasticsearch 
(AWS Elasticsearch Service), if available to you. Use of these services in Docker containers should be avoided
in all but development environments. Reference the Architecture documentation for additional details on configuring
supporting services.

Quick Start
===========
While Scale can be entirely run on a pure Apache Mesos cluster, we strongly recommend using Data Center Operating System
(DC/OS). DC/OS provides service discovery, load-balancing and fail-over for Scale, as well as deployment scripts for
nearly all imaginable target infrastructures. This stack allows Scale users to focus on use of the framework while
minimizing effort spent on deployment and configuration. A complete quick start guide can be found at:

https://ngageoint.github.io/scale/quickstart.html

Algorithm Development
=====================
Scale is designed to allow development of recipes and jobs for your domain without having to concern yourself with the
complexities of cluster scheduling or data flow management. As long as your processing can be accomplished with
discrete inputs on a Linux command line, it can be run in Scale. Simple examples of a complete processing chain can be
found within the above quick start or you can refer to our in-depth documentation for step-by-step Scale integration:

https://ngageoint.github.io/scale/docs/algorithm_integration/index.html

Scale Development
-----------------
If you want to contribute to the actual Scale open source project, we welcome your contributions. There are 2 primary
components of Scale:

- Scale User Interface: https://github.com/ngageoint/scale/tree/master/scale-ui
- Scheduler / Service APIs: https://github.com/ngageoint/scale/tree/master/scale

The links provide specific development environment setup instructions for each individual component.

Build
=====
Scale is tested and built using a combination of Travis CI and Docker Hub. All unit test execution and documentation
generation are done using Travis CI. We require that any pull request fully pass unit test checks prior to being merged.
Docker Hub builds are saved to `x.x.x-snapshot` image tags between releases and on release tags are matched to release
version.

A new release can be cut using the generate-release.sh shell script from a cloned Scale repository (where numbers refer
to MAJOR MINOR PATCH versions respectively):

```bash
./generate-release.sh 4 0 0 
```

There is no direct connection between the Travis CI and Docker Hub builds, but both are launched via push to the GitHub
repository.

Contributing
============
Scale was developed at the National Geospatial-Intelligence Agency (NGA). The government has "unlimited rights" and 
is releasing this software to increase the impact of government investments by providing developers with the opportunity
to take things in new directions. The software use, modification, and distribution rights are stipulated within the 
Apache 2.0 license.

All pull request contributions to this project will be released under the Apache 2.0 or compatible license. Software
source code previously released under an open source license and then modified by NGA staff is considered a "joint work"
(see 17 USC § 101); it is partially copyrighted, partially public domain, and as a whole is protected by the copyrights
of the non-government authors and must be released according to the terms of the original open source license.
