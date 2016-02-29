Master [![Build Status](https://travis-ci.org/ngageoint/scale.svg?branch=master)](https://travis-ci.org/ngageoint/scale)

Develop [![Build Status](https://travis-ci.org/ngageoint/scale.svg?branch=develop)](https://travis-ci.org/ngageoint/scale)

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
This will download a centos7 base image and start 3 virtual machines, a master and two slaves. You can add additional
slaves by editing `Vagrantfile` and adding them to the `HOSTS` and `mesos-slaves` sections before doing the `vagrant up`.
Ansible will be used to push the configuration out and can take a while to run. You make need to modify
`ansible/group_vars/vagrant` or `ansible/vagrant.yml` if you need to specify a local docker index, etc.

Once the cluster has started (it takes a while), you can visit http://master for the main scale interface or
http://master:5050 for the mesos master interface.
If you want to attempt a strike ingest, download some sample landsat data (multiple TIF files, one per band, in a
.tar.gz with no subdirectories). Suitable data can be found in the scale "SAMPLE_DATA" release on github.
Visit (http://master:8081) and upload the tar.gz file. You should see the data ingest in a short amount of time.

Go to the Jobs tab and find the completed `landsat-tiles` job and look at the Products tab. You'll find an overview html
file. Select that for an OpenLayers view of the processed data.

Alternately, you can ingest directly from the filesystem.
Save the tar.gz in the `vagrant` directory, run `vagrant ssh master`. Ingest the file as follows:
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
It is possible to setup a scale cluster using vagrant. Specific configurations are not discussed here, see the vagrant
documentation site for information on your specific VM provider. The remainder of this section assumes you'll be externally
provisioning hardware or VMs for a scale cluster. The ansible deployment scripts assume Centos 7 or similar as they
utilize yum for dependency installation. Other recent Linux distributions should work but will require changes to the
scripts or manual setup and installation.

Decide on a cluster layout
--------------------------
You'll need machines for the following roles. Multiple rolls can exist on a single machine.
 - Zookeeper - one or more systems for a zookeeper cluster, this is often the same machine as the mesos master
 - Mesos master - one or more systems for the mesos master and optional backups.
 - Database - a system for a Postgres database. This should be dedicated for production systems with heavy load.
 - Mesos slaves/agents - multiple systems for execution of Scale tasks. These should be dedicated systems.
 - Scale scheduler - a system for running the scale scheduler. This will often be the same system as the mesos master.
 - Scale web API - a system for the RESTful API server. Thi will often be the same system as the mesos master.
 - Static web server - a system for serving static web files and acting as a proxy to the web API. This will often
                       be the same as the mesos API. This should have a static IP address or well known DNS name.
 - NFS server - Scale currently requires NFS for storing ingested data. This may be a dedicated NFS server or it may
                serve local directories from an existing server such as the mesos master. A dedicated machine is
                recommended for production clusters.
 - Docker registry - A registry for storing algorithm and task images. This could also mirror standard docker images.
                     A dedicated system is recommended for production use but this might be the same system as
                     the mesos master. It is possible to store the task images in the Docker Hub but not recommended.
 - A build system - This will be used to build the docker images, etc. This can be a dedicated machine or the mesos
                    master. It is recommended this be a dedicated machine for production clusters. There can be multiple
                    build systems. (i.e. each developer builds on her own workstation)
 - A deployment system - This system runs ansible for configuration and deployment. This will typically be the same as
                         the build system but can be any system with ssh access to the cluster systems including the
                         mesos master.

Configure docker on the cluster machines
----------------------------------------
There is an ansible role which will install and configure docker but since the configuration tends to be very specific
to the system configuration it is recommended that docker be manually installed and configured on cluster machines.
Version 1.9 of docker has been tested and is recommended at this point. It can be obtained from [the docker website](http://get.docker.com)
Follow the recommendations on the docker website for installation. We recommend dedicted lvm devicemapper on Centos 7
or overlay on XFS for Centos 7 as configurations. The vagrant images use btrfs and work well but this has not been tested
in production. Overlay occasionally has some hiccups so it's recommended that you use a recent kernel version with
overlay.

Configure the build and deployment machine(s)
---------------------------------------------
Install ansible 1.9 (ansible 2.x currently has some bugs which will prevent it from working with the deployment scripts)
and rsync on the deployment machine. Install docker (recommend the same version as above) on the build machine.

Setup an ansible inventory file. This should contain groups for: mesos-masters, mesos-slaves, db, zookeeper, nfs,
registry, build, scale-scheduler, scale-web, mesos, and scale-framework. And example cluster with one system for
master services (scalemaster=10.1.1.100), two slaves, and dedicated db and registry is shown below. Builds are performed
on the local host. The `mynet` entry is important as it allows you to configure variables for your network either in the
inventory file or in `group_vars/mynet`.
````````
[mesos-masters]
scalemaster

[mesos-slaves]
scaleslave1
scaleslave2

[db]
scaledb

[zookeeper]
scalemaster

[nfs]
scalemaster

[registry]
scaleregistry

[build]
localhost     ansible_connection=local

[scale-scheduler]
scalemaster

[scale-web]
scalemaster

[mesos:children]
mesos-masters
mesos-slaves

[scale-framework:children]
scale-scheduler
scale-web

[mynet]
scalemaster
scaleslave1
scaleslave2
scaledb
scaleregistry
localhost

[mynet:vars]
mesos_zk='zk://10.1.1.100:2181/mesos'
scheduler_zk='zk://10.1.1.100:2181/scale'
docker_registry='scaleregistry:5000/'
scale_docker_version='3'
mesos_master_ip='10.1.1.100'
mesos_slave_ip='{{ ansible_all_ipv4_addresses[-1] }}'
zookeeper_servers='{{ mesos_master_ip }}'
mesos_slave_resources='cpus:4;mem:8092'
db_username='scaleuser'
db_password='scalepassword'
db_host='scaledb'
django_build_dir="/scale/scale"
scale_url_prefix=""
allowed_hosts='"*"'
btrfs=false
````````
The slave resources should have slightly less memory allocated than the system contains to ensure there is no virtual
memory thrashing. It's also possible to allocate one less core per machine if you want to reserve that for logins, etc.

The `django_build_dir` is the location of the django source code on the build system (`scale` directory in the git checkout).
The `scale_url_prefix` is an extra prefix in the url that will be accessed for scale. For example, `http://myhost.mynet.prv/scale`
would require `/scale` as the prefix. If you intend to serve at the top level, leave this as an empty string.

If `btrfs` is true, docker will be installed and configured. This is generally used for the vagrant configuration. See
the above notes on installing docker. See the `group_vars/vagrant` file for further documentation on the configurations.

Setup ssh for passwordless remote access for the current user. This is typically done with an ssh keypair and ssh-agent.
See your ssh manpage or favorite search engine for details. You should also setup passwordless sudo for the deployment users
on the various cluster machines. It's possible to use a standard sudo setup using the `--ask-become-pass` option.

Build scale
-----------
It's possible to setup an alternate build system for the scale docker images using Jenkins for example. This section
shows how to use ansible to build manually.

Ensure you have the inventory file setup properly. Assuming the inventory is in the default location (`/etc/ansible/hosts`)
run the following commands. Use `-i` if the inventory file is elsewhere.
````
cd /path/to/scale/ansible
ansible-playbook build.yml
````

Ansible tags are available to build specific portions of scale. See the various roles for more details.

Setup the cluster and database
------------------------------
````
cd /path/to/scale/ansible
ansible-playbook setup.yml
````

This will setup the database including the example jobs. If you don't want to include them, use the various ansible
tags to select or ignore pieces of the setup. This typically needs to be done once when there's a clean database
and not every time there's a new build.

Deploy the cluster
------------------
````
cd /path/to/scale/ansible
ansible-playbook site.yml
````

This will deploy the various components and restart the servers as necessary. This should be run each time there's a build
to be deployed. You can restart individual components with tags. For example:
`ansible-playbook site.yml --tags=scale-scheduler,scale-static-web`

Verify functionality
--------------------
Go to port 80 on your static web server and ensure scale is running and there are no errors. If the master and scheduler
appear red, connect to port 5050 on your mesos master. This will display the mesos master dashboard. Select the Frameworks
and Slaves tabs and verify the scale framework is listed and all the mesos slaves. If so, the scheduler might need to be
restarted to resync the database. Use `ansible-playbook site.yml --tags=scale-scheduler` or login to the scheduler system
and run `docker restart scale-scheudler`.

Contributing
============
Scale was developed at the National Geospatial-Intelligence Agency (NGA) in collaboration with
[Ball Aerospace](http://www.ballaerospace.com/) and [Applied Information Sciences (AIS)](http://www.appliedis.com/).
The government has "unlimited rights" and is releasing this software to increase the impact of government investments by
providing developers with the opportunity to take things in new directions. The software use, modification, and
distribution rights are stipulated within the Apache 2.0 license.

All pull request contributions to this project will be released under the Apache 2.0 or compatible license. Software
source code previously released under an open source license and then modified by NGA staff is considered a "joint work"
(see 17 USC § 101); it is partially copyrighted, partially public domain, and as a whole is protected by the copyrights
of the non-government authors and must be released according to the terms of the original open source license.

