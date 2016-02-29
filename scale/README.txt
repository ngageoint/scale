This README describes how to develop on the Scale project after you have
imported it into Eclipse PyDev on a Windows machine.

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