.. _scale_configuration:

===============================================================================
Scale Configuration
===============================================================================

Local settings for scale are contained in /etc/scale/local_settings.py.  A sample of this file can be found in the distribution under /scale/local_settings_SAMPLE_PROD.py

The script ``/scripts/deployServicesFromTemplates.sh`` will install and enable all the scale services on a CentOS7.  To install/deploy less, modify the script, or manually perform similar steps.


===============================================================================
Mesos Configuration
===============================================================================

Scale uses mesos to assign processing to nodes.  You must configure the mesos slave nodes to point to the correct mesos master (or zookeeper).
Additionally, you must add docker to the available mesos containerizers.  For a mesosphere installation, this can be done with the following commands:

#. ``echo <mesos-master>:5050 > /tmp/master``
#. ``sudo mv /tmp/master /etc/mesos-slave``
#. ``echo mesos,docker > /tmp/containerizers``
#. ``sudo mv /tmp/containerizers /etc/mesos-slave``

Also disable zookeeper for the master and slave:

#. Modify /etc/default/mesos-master and remove the ZK line
#. Modify /etc/default/mesos-slave and remove the ZK line (this file will be empty now)