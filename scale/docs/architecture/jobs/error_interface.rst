
.. _architecture_errors_interface:

Errors Interface
===============================================================================

The error interface is a JSON document that defines the interface for translating
the job's exit codes to errors.

Consider the following example error definition, which adds one exit code (1) to map  to a Scale error (Unknown).

**Example error interface:**

.. code-block:: javascript

    {
        "version": "1.0",
        "exit_codes": {
            "1": "unknown"
        }
    }

   
.. _architecture_errors_interface_spec:

Error Interface Specification Version 1.0
-------------------------------------------------------------------------------

A valid error interface is a JSON document with the following structure:
 
.. code-block:: javascript

    {
        "version": STRING,
        "exit_codes": {
            STRING: STRING,
            STRING: STRING
        }
   }
   
**version**: JSON string

    The *version* is an optional string value that defines the version of the definition specification used. This allows
    updates to be made to the specification while maintaining backwards compatibility by allowing Scale to recognize an
    older version and convert it to the current version. The default value for *version* if it is not included is the
    latest version, which is currently 1.0. It is recommended, though not required, that you include the *version* so
    that future changes to the specification will still accept the recipe definition.
    
**exit_codes**: JSON object

    The *exit_codes* is a required object that defines what exit codes are mapped to the Scale errors in the database. 
    It is a map of strings, which are the algorithm's exit codes, to strings that are the name values of the errors in
    the database.
