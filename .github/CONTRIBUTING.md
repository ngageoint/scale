### Definition of Done

We welcome community contributions to the Scale project, and the following guidelines will help with making Pull
Requests (PRs) that ensure the projects long term maintainability. Before PRs are accepted, your code must meet allconditions of the "Definition of Done."

1. Proper heading in all files
1. Properly organized imports in all files, organized first in three separate sections separated by a new line (section ordering below), `import FOO` statements precede `from FOO import BAR` statements and finally ordered alphabetically
    1. Standard Python imports (math, logging, etc)
    1. Python library imports (Django, etc)
    1. Scale code imports
1. Add or update necessary unit tests for code updates
1. All unit tests run successfully and there are no deprecation warnings (ignore warnings for dependencies)
1. No Pep8 warnings in code
1. All Python files have appropriate docstring information filled out
1. Any necessary updates are made to the documentation
1. All documentation is generated successfully with no warnings

### Unit Tests

Scale makes extensive use of unit tests as a first line of defense against software regressions. All new features must be covered by unit tests that exercise both success and failure cases. The entire unit test suite may be executed by running the following from the terminal:

```bash
python manage.py test
```

Individual Django apps within the Scale project may also be tested individually (using `job` app for example):

```bash
python manage.py test job
```

### Documentation

Scale uses Sphinx for project and REST API documentation. With `docs` as your current working directory, the following commands run from the terminal will generate the documentation:

```bash
make code_docs
make html
```
