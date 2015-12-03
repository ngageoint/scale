
.. _development:

===============================================================================
Development
===============================================================================

**Setting up the project**

Follow the instructions in scale/README.txt within the projects

**Remote Debugging**

The scale scheduler will attempt to connect to a pydev remote debugging server if the following conditions are true:

* Debug is on in django settings
* A pydev debug server is running on on your development machine.  To start this in Eclipse open the Debug perspective and select "Pydev->Start Debug Server"
* The REMOTE_DEBUG_HOST environment variable is set on the machine you wish to debug.  This should be set to the hostname of the machine with pydev debug server running.
* The PYDEV_SRC environment variable is set on the machine you wish to debug.  This should be set to a pydev installation.  In order to set this environment variable for the default scale service installation, modify /etc/scale/Environment 

In addition to setting the PYDEV_SRC and REMOTE_DEBUG_HOST, you must ensure the pydev installation has been modified  correctly.

Within your pydev installation, modify pysrc/pydevd_file_utils.py and change the PATHS_FROM_ECLIPSE_TO_PYTHON to match your installation.