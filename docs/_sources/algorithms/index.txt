
.. _algorithms:

========================================================================================================================
Algorithms
========================================================================================================================
This document explains the steps necessary to integrate an algorithm into the Scale system. The Scale system utilizes
Docker containers to run algorithms in an isolated environment. The first step will be to build a Docker image that
encapsulates an algorithm.

To build the Docker image, Docker must be installed on the system and the Docker daemon running. Depending on the
linux system, the following packages will need to be installed: docker-io and lxc for Centos6 and docker and lxc for Centos7.
Next the Docker daemon service needs to be started by either the service command for Centos6 or the systemctl command for Centos7.
(systemctl enable docker; systemctl start docker) 

Then create a Dockerfile file to execute the necessary Docker commands to build the image. The following is an example of the format
of a Dockerfile:

**Dockerfile example**

Example removed, we need a good, general example here

.. toctree::
   :maxdepth: 1

   results_manifest
