
.. _cli_overview:

Overview
========================================================================================================================

The Scale command line client (cli) interfaces with the scale system providing an alternative interface to some
functionality as well as a number of support and convenience functions.

The cli is written in go and can be built on multiple platforms including Linux, Windows, and Mac OSX.
Command summaries are available with the `-h` argument which can be used with most commands and sub-commands.

The cli provides a hierarchy of commands with major functional groups, such as job management, containing a number of
commands relevant to that functional group. Similar functions across multiple groups will have similar names and arguments.

Configuration Environment
-------------------------
The cli needs to know how to locate your scale system. The usual way to specify this is with a scale config file or
the `SCALE_URL` environment variable. This can be overwritten with the `--url` argument. This should point to the API
endpoint for the scale instance. For example: `http://localhost/api/v3`

A scale config file resides at `$HOME/.scaleconfig` and is a YAML file containing configuration defaults for various
options. An example scale config file looks like::

    ---
    url: http://scalemaster/api/v3
    registry: scaleregistry.localnet.prv:5000


The currently supported fields and values are:

+---------------+--------------------------------------------------------------+
| **Field Name**| **Description**                                              |
+===============+==============================================================+
| url           | The scale API server URL.                                    |
|               | Only required for operations which connect to the API server |
+---------------+--------------------------------------------------------------+
| registry      | Optional docker registry. If not specified, pushes and pulls |
|               | will use the primary docker index at docker.io               |
+---------------+--------------------------------------------------------------+
