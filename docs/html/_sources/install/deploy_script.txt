.. _deploy_script:

===============================================================================
Deploy Script
===============================================================================

Scale provides a deploy script to make the process of deploying scale to a machine easier.
To run the deploy script:
Unzip the release tar.gz file
run ``scale/scripts/deploy.sh <mesos-master> [<deploy.to.directory> [<scale-user> [<scale-group>]]]``

The script will stop any scale or mesos services running, copy the files to the correct location, and retrive the python dependencies in a virtual environment.

The deploy shuts down the following services before being run:

* mesos-master
* mesos-slave
* scale-web
* scale-scheduler

After the script is run, you will need to restart the services manually.  This was split to a separate step since the deployed to system could be a master or a slave. 