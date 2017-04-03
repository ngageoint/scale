# Scale Scheduler / Services API

This document describes how to develop on the scheduler and services API portion of the Scale project. The scheduler and
services are written in Python 2.7 using the Django framework - Python 3 support is coming. A PostgreSQL 9.3+ database
with PostGIS extensions must be accessible to your environment. The following sections detail the steps to set up your
development environment for various platforms. Linux or MacOS are the preferred platforms for local development as you
will have a much simpler configuration path for Scale build time dependencies.

## Development

Isolation of development dependencies is done via virtualenv. This is a standard way to ensure system and project
dependencies are separated for Python development. The configuration of virtualenv for your chosen development platform
is detailed in the [Development Platforms](#development-platforms) section below. Whenever you start a development
session, you should activate your virtualenv:

```bash
source environment/scale/bin/activate
```

When you are done, you can either run the following command or just close the terminal window:

```bash
deactivate
```

### Project Settings

All Scale configuration settings are stored following Django convention within `scale/settings.py`. These settings may
be overridden for development purposes in `scale/local_settings.py` or `scale/local_settings_docker.py` for deployment
within Docker. One of the first required steps when beginning development is to make a copy of
`scale/local_settings_dev.py` to `scale/local_settings.py` and updating with your environment specific settings -
primarily database connection settings.

### Migrations

Migrations are the mechanism by which Django tracks changes to the database.
Whenever you pull updates from Git, make sure that you perform a migration. This will ensure that your database is
up-to-date with the latest model changes. To migrate any changes and apply fixtures, run the following from your
terminal:

```bash
python manage.py migrate
python manage.py load_all_data
```

When making Scale model changes, it is your responsibility to generate the appropriate migrations. This will encapsulate
the model changes in migration files that can be used to update the database and keep everybody in sync. The following
command will generate the migration files (ensure you commit these files):

```bash
python manage.py makemigrations
```

### Web Server

In order to use the Django web server in development, you may launch by running the following from the terminal:

```bash
python manage.py runserver 0.0.0.0:8080
```

Port 8080 is recommend as it will be consistently supported across all platforms. Cloud9 imposes restrictions on the
ports that can be exposed to the internet.

### Unit Tests

Scale makes extensive use of unit tests as a first line of defense against software regressions. All new features must
be covered by unit tests that exercise both success and failure cases. The entire unit test suite may be executed by
running the following from the terminal:

```bash
python manage.py test
```

Individual Django apps within the Scale project may also be tested individually (using `job` app for example):

```bash
python manage.py test job
```

### Documentation

Scale uses Sphinx for project and REST API documentation. With `docs` as your current working directory, the following
commands run from the terminal will generate the documentation:

```bash
make code_docs
make html
```

### Definition of Done

We welcome community contributions to the Scale project, and the following guidelines will help with making Pull
Requests (PRs) that ensure the projects long term maintainability. Before PRs are accepted, your code must meet all
conditions of the "Definition of Done."

1. Proper heading in all files
1. Properly organized imports in all files, organized first in three separate sections separated by a new line (section
ordering below), `import FOO` statements precede `from FOO import BAR` statements and finally ordered alphabetically
    1. Standard Python imports (math, logging, etc)
    1. Python library imports (Django, etc)
    1. Scale code imports
1. Add or update necessary unit tests for code updates
1. All unit tests run successfully and there are no deprecation warnings (ignore warnings for dependencies)
1. No Pep8 warnings in code
1. All Python files have appropriate docstring information filled out
1. Any necessary updates are made to the documentation
1. All documentation is generated successfully with no warnings

### Development Platforms

Scale development requires a local Postgres database with PostGIS extensions installed. The easiest way to get started
on most platforms is with a Docker container and all the bootstrap configurations described, except Cloud9, use this
method. The following are the baseline prerequisites for Scale development:

- Running Docker Community Edition 1.10+ Engine (use Docker for Windows or Mac on those platforms)
- Python 2.7.x

The core Scale team uses JetBrains PyCharm or Cloud9 IDE for development. These are in no way required but are
our preferred choices.

#### Cloud9

Cloud9 comes with built in support for Postgres / PostGIS databases, making development of Scale both portable and
quick to start using a hosted Cloud 9 environment.

The basics steps to get started are:

1. Browse to https://c9.io/new (signup will be required if you don't have existing account).
1. Ensure Hosted workspace is selected.
1. Select private (one free with new account) or public based on your preference.
1. Enter the Scale Git address to clone: https://github.com/ngageoint/scale.git
1. Select Django template and Create workspace

Once the workspace has initialized you should see the Cloud9 IDE in your browser. In the terminal enter the following
commands to initialize for development:

```bash
# Change to Python code directory
cd scale

# Initialize database and install Scale Python packages.
sudo sh cloud9-init.sh

# Run unit tests
python manage.py test

# Launch web server
python manage.py runserver 0.0.0.0:8080
```

#### Linux

Platform specific prerequisites:
- Root access on CentOS7 / RHEL7 Linux OS

From a fresh clone of Scale run the following commands to initialize your environment:

```bash
# Change to Python code directory
cd scale

# Initialize database and install native dependencies.
sudo sh environment/cent7-init.sh

# Activate virtualenv
source environment/scale/bin/activate
```
Going forward, anytime you need to develop Scale, just activate your virtualenv and you're ready:

```bash
# Activate virtualenv
source environment/scale/bin/activate
```

#### MacOS

Platform specific prerequisites:
- Homebrew
- Docker for Mac 1.17 installed and running

From a fresh clone of Scale run the following commands to initialize your environment:

```bash
# Change to Python code directory
cd scale

# Initialize database and install native dependencies.
sh environment/mac-init.sh

# Activate virtualenv
source environment/scale/bin/activate
```
Going forward, anytime you need to develop Scale, just activate your virtualenv and you're ready:

```bash
# Activate virtualenv
source environment/scale/bin/activate
```

#### Windows (10+ only)

Platform specific prerequisites:
- Python 2.7 installed and included in PATH
- Virtualenv installed and included in PATH
- OSGeo4W install of GDAL, GEOS and PROJ included in PATH
(https://docs.djangoproject.com/en/1.10/ref/contrib/gis/install/#modify-windows-environment)
- Docker for Windows 1.17 installed and included in PATH

From a fresh clone of Scale run the following commands to initialize your environment:

```bat
REM Change to Python code directory
cd scale

REM Initialize database and configure Scale to point to it.
environment\win-init.sh

REM Activate virtualenv
environment\scale\bin\activate.bat
```

Going forward, anytime you need to develop Scale, just activate your virtualenv and you're ready:

```bat
REM Activate virtualenv
environment\scale\bin\activate.bat
```


