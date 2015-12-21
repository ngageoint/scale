Scale
=====
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

Quick Start
===========
We've provided a vagrant and ansible setup to get you going quickly. Make sure vagrant, virtualbox, and ansible are installed then.
```
cd vagrant
vagrant plugin install vagrant-hostmanager
vagrant up
```
This will download a centos7 base image and start 3 virtual machines, a master and two slaves. You can add additional slaves by editing `Vagrantfile` and adding them to the `HOSTS` and `mesos-slaves` sections before doing the `vagrant up`. Ansible will be used to push the configuration out and can take a while to run. You make need to modify `ansible/group_vars/vagrant` or `ansible/vagrant.yml` if you need to specify a local docker index, etc.

Once the cluster has started (it takes a while), you can visit http://10.4.4.10 for the main scale interface or http://10.4.4.10:5050 for the mesos master interface.
If you want to attempt a strike ingest, download some sample landsat data (multiple TIF files, one per band, in a .tar.gz with no subdirectories). Suitable data can be found in the scale "SAMPLE_DATA" release on github. Save it in the `vagrant` directory, run `vagrant ssh master`. Ingest the file as follows:
```
cp /vagrant/LC80170302015307LGN00.tar.gz /exports/ingest/LC80170302015307LGN00.tar.gz_tmp
ln /exports/ingest/LC80170302015307LGN00.tar.gz_tmp /export/ingest/LC80170302015307LGN00.tar.gz
rm /export/ingest/LC80170302015307LGN00.tar.gz_tmp
```

NOTE: Country borders shapefile courtesy of [Bjorn Sandvik](http://thematicmapping.org/downloads/world_borders.php)

Setting up a development environment
====================================
1. Install a clean version of Python 2.7 with virtualenv.
1. Create a directory for the project (defined as "scale" from here on out.)
1. Change directory to scale and run "virtualenv env". This creates a stand alone Python install in your scale\env directory.
1. Enable the virtualenv (. ./env/bin/activate on Linux)
1. Optionally install PyDev Eclipse plugin for Python development.
1. Clone the repository to scale/scale
1. Install appropriate dependencies list from pip/ based on your environment
1. Create a scale/scale/scale/local_settings.py based on the sample files setting database info, etc.
1. Migrate db changes (should be done whenever new changes are pulled from git): `./manage.py migrate`
1. Run unit tests to verify the install: `./manage.py test`
1. Optionally generate documentation: `make code_docs && make html` in the docs directory

Setting up a scale cluster
==========================
TODO: Information on setting up a cluster

Contributing
============
Scale was developed at the National Geospatial-Intelligence Agency (NGA) in collaboration with [Ball Aerospace](http://www.ballaerospace.com/) and [Applied Information Sciences (AIS)](http://www.appliedis.com/). The government has "unlimited rights" and is releasing this software to increase the impact of government investments by providing developers with the opportunity to take things in new directions. The software use, modification, and distribution rights are stipulated within the Apache 2.0 license.

All pull request contributions to this project will be released under the Apache 2.0 or compatible license. Software source code previously released under an open source license and then modified by NGA staff is considered a "joint work" (see 17 USC § 101); it is partially copyrighted, partially public domain, and as a whole is protected by the copyrights of the non-government authors and must be released according to the terms of the original open source license.

#
