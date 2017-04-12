.. _system_dependencies:

System Dependencies
===================

Scale requires the following to be installed on all masters and slaves

* Apache Mesos 0.21.X
* Docker 1.5.x
* Python 2.7.x

* virtualenv
* pip
* python-setuptools
* geos
* postgis2_93

**Installation on CentOS7**

*Apache Mesos*

#. Download the mesos rpm from mesosphere
#. ``rpm -i mesos-0.21.1-1.1.centos701406.x86_64.rpm``

*Docker*

#. ``yum install -y docker``
#. edit /etc/sysconfig/docker and add any private registries
#. ``systemctl enable docker``
#. ``systemctl start docker``

When docker is installed a new docker group is added.  Whichever user runs the scale3 nodes will need to be aded to the docker group.

*Python and virtualenv*

#. ``sudo yum install gcc httpd openssl-devel zlib-devel sqlite-devel bzip2-devel -y``
#. unzip a Python distribution
#. from the unzipped directory run:

  #. ``./configure``
  #. ``sudo make altinstall``

#. Download the distributions for setuptools, pip, and virtualenv
#. For each of the above, unzip the distribution and run ''/usr/local/bin/python2.7 setup.py install''

*Geos and Postgis*

#. ``yum install -y geos geos-devel libpqxx gdal-libs proj`` 