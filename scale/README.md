# Scale Scheduler / Services API

This document describes how to develop on the scheduler and services API portion of the Scale project. The scheduler and
services are written in Python 2.7 using the Django framework - Python 3 support is coming. For unit testing a
PostgreSQL 9.3+ database with PostGIS extensions must be accessible to your environment. The following sections detail
the steps to set up your development environment for various platforms. Linux or MacOS are the preferred platforms for
local development as you will have a much simpler configuration path for Scale build time dependencies.

# Prerequisites

Scale development requires a local Postgres database with PostGIS extensions installed. The easiest way to get started
on most platforms is with a Docker container and all the bootstrap configurations described, except Cloud9, use this
method. The following are the baseline prerequisites for Scale development:

- Running Docker Community Edition 1.10+ Engine (use Docker for Windows or Mac on those platforms)
- Python 2.7.x

## Cloud9

Cloud9 comes with built in support for PostGres / PostGIS databases, making development of Scale both portable and
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
sudo cloud9-init.sh

# Run unit tests
python manage.py test
```

## Linux

Platform specific prerequisites:
- Root access on CentOS7 / RHEL7 Linux OS

From a fresh clone of Scale run the following commands to initialize your environment:

```bash
# Change to Python code directory
cd scale

# Initialize database and install native dependencies.
sudo environment/cent7-init.sh

# Initialize virtual environment
virtualenv environment/scale
source environment/scale/bin/activate

# Load up database with schema migrations to date and fixtures
python manage.py migrate
python manage.py load_all_data

# Run unit tests
python manage.py test
```

## MacOS

## Windows


***** Activate your virtualenv *****
Whenever you want to do something on the command line with your virtualenv you
must first activate the virtualenv. To do this change directory to your
virtualenv directory. Run Scripts\activate.bat. Now anything run on this
command line will be done with your virtualenv Python.

***** Install Python libraries *****
First activate your virtualenv. Then perform a pip install for your Python
environment using pip\dev_win.txt. You will need to separately install the
libraries with native code (these are commented out in pip\dev_win.txt.)

***** Set up local settings *****
Make a copy of local_settings_SAMPLE_DEV.py and rename it to local_settings.py.
Make any additional changes needed (such as database configuration) for your
development environment.

***** Migrate *****
Whenever you pull updates from Git, make sure that you perform a migration.
This will ensure that your database is up-to-date with the latest model changes.
To migrate any changes, launch the "Migrate DB Changes" run configuration. Then
launch the "Load Initial Data" run configuration to load/update any initial
data to the database.

***** Start Scale Server *****
Launch the "Start Scale Server" run configuration to start the Scale server.

***** Make Migrations *****
Migrations are the mechanism by which Django 1.7 tracks changes to the database
models. Whenever you make changes to any database models, BEFORE you commit the
changes to Git, make sure you perform a Django makemigrations command. This
will encapsulate the model changes in migration files that can be used to
update the database and keep everybody in sync. To create the migration files,
launch the "Make DB Migrations" run configuration.

***** Unit Tests *****
Launch the "Run Tests" run configuration to perform the entire unit testing
suite. The results will also indicate if there are any code deprecation
warnings. Make sure that all tests pass before merging any code into the master
branch and also ensure that there are no deprecation warnings.

***** Generate Documentation *****
To generate the documentation, first activate your virtualenv. Then change
directory to /docs and run the following commands on the command line:

make code_docs
make html

***** Definition of Done *****
Before merging your code into the master branch, your code must meet all
conditions of the "Definition of Done."

1. Proper heading in all files
2. Properly organized imports in all files
	Organized first in three separate sections separated by a new line:
		a. Standard Python imports (math, logging, etc)
		b. Python library imports (Django, etc)
		c. Scale code imports
	and then in each section make sure the "import FOO" statements precede the
	"from FOO import BAR" statements and finally ordered alphabetically.
3. Add or update necessary unit tests for code updates.
4. All unit tests run successfully and there are no deprecation warnings (ignore
   warnings for dependencies.)
5. No Pep8 warnings in code
6. All Python files have appropriate docstring information filled out.
7. Any necessary updates are made to the documentation.
8. All documentation is generated successfully with no warnings