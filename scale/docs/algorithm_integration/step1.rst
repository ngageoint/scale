
.. _algorithm_integration_step1:

Making a Scale-compatible Algorithm
===================================


**Algorithms must**:

* **Run standalone without any user inputs**
    Algorithms must be fully automated.  If your algorithm is prompting for input from a user, the job will continue to
    wait until it times out.
* **Fail gracefully**
    Ideally your algorithm will capture its faults and failures and report an exit code and log an informative message
    to standard error.  Exit codes for an algorithm can be mapped for debugging and metric purposes.  If failures are
    not captured appropriately, Scale will likely report a general algorithm error, which will make debugging your
    algorithm more difficult.
* **Not display popups**
    Algorithms must not display error dialogs, file selection menus, splash screens, etc. since there is no user that is
    able to make a selection or close these windows.  Popup displays will cause an algorithm to hang (since they won't
    be closed) until the job times out.  This is a common issue with IDL and output will need to be displayed to the
    standard output instead.
* **Run on Linux**
    Any external libraries needed must be compiled for Linux.  Do not bundle your algorithm with Windows DLLs.
* **Not have hardcoded paths**
    File paths must not be embedded in the source code such that changing the path requires re-compiling code.
    Necessary file paths should be passable into the algorithm either via a configuration file or passed from the
    command line.
    

**Scale will**:

* Give the input file(s) absolute path
* Provide an empty output directory
* Provide dedicated resources that you request
* Capture standard output and standard error
* Capture exit codes

**Scale will not**:

* Resolve relative paths
* Provide output file names
* Automatically create NFS mounts in the Docker container
* Capture output products not listed in the :ref:`results manifest <algorithm_integration_results_manifest>` and
  :ref:`job interface <architecture_jobs_interface_spec>`


*Creating Executables*
----------------------

*C/C++*
+++++++
* Compiled on Linux
* Should provide cmake/makefiles for algorithm

*IDL*
+++++
* Code should be compiled into .sav files with IDL's save command
* IDL .sav files are run using runtime license
* Some IDL function calls, such as ENVI, require special licensing which is limited

*Java*
++++++
* Code should be compiled into .jar files
* Needed .jar libraries should be within its own folder

*MATLAB*
++++++++
* Code should be compiled into executables using MATLAB's deploytool or mcc command
* Compiling MATLAB code will require any toolboxes used to be specified and available at compile time
* Compiled MATLAB code runs using MATLAB's compiled runtime mode, which does not require a license

*Python*
++++++++
* Code should be in its own folder
* Needed Python modules will need to be installed in the Docker container

    
Wrapping algorithms
-------------------

If a script wraps the algorithm execution, exit codes will need to be captured and returned by the wrapper script.

Example Python wrapper
++++++++++++++++++++++


.. code-block:: python
    :linenos:
    
    import subprocess
    import logging
    import sys
    import json
    import os
    from glob import glob

    #Setup Logger to capture print statements
    log=logging.getLogger()
    log.setLevel(10)
    consoleFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(consoleFormatter)
    log.addHandler(consoleHandler)

    #Use subprocess to execute algorithms
    def runAlgorithm(tiffpath, outdir):
        tiffBasename = os.path.basename(tiffpath)
        outFilePath = os.path.join(outdir, tiffBasename.replace('.tif', '_tiffinfo_log.txt'))
        
        arglist = [r'/usr/bin/tiffinfo', tiffpath, '>', outFilePath]

        log.info('Command:')
        myCommand = ' '.join(arglist)
        log.debug(myCommand)
        log.info('Executing command...')

        exitCode = subprocess.Popen(arglist, shell=False).wait()
        
        log.info('Returning from algorithm...')
        
        return exitCode
    
    #Capture results in manifest
    def generateResultsManifest(outdir):

        try:
            outputLog = glob(os.path.join(outdir, '*tiffinfo_log.txt'))[0]
        except:
            log.error('Error in locating output files')
            sys.exit(10)
        
        if not outputLog:
            log.error('No outputs found in directory for manifest')
            sys.exit(11)

        jsonDict={}
        jsonDict['version'] = '1.1'
        jsonDict['output_data'] = []
        
        tempDict = {}
        tempDict['name'] = 'tiffinfo_log'
        tempDict['file'] = {'path': outputLog}
        jsonDict['output_data'].append(tempDict)
        
        with open(os.path.join(outdir, 'results_manifest.json'), 'w') as fout:
            jsonString = json.dumps(jsonDict)
            fout.write(jsonString)
    
        log.info('Completed manifest creation')
        
    if __name__ == '__main__':
    
        argv = sys.argv
        if argv is None:
            log.error('No inputs passed to algorithm')
            sys.exit(2)
        argc=len(argv)-1

        tiffpath = argv[1]
        outdir = argv[2]

        log.debug('Tiff path: {}'.format(tiffpath))
        log.debug('Output directory: {}'.format(outdir))
        
        exitCode = runAlgorithm(tiffpath, outdir)
        
        if exitCode != 0:
            log.error('algorithm exited with code: {}'.format(exitCode))
        
        log.info('Completed Python Wrapper')
        
        sys.exit(exitCode)
        

Example shell wrapper
+++++++++++++++++++++

Wrapping an algorithm with a shell script is useful when you need to:

* Mount NFS directories for the algorithm to reference
* Setup additional environment variables or append to system paths
* Determine additional command line input arguments for the algorithm

The bash script will capture the arguments passed to it that are specified in the
:ref:`job interface <architecture_jobs_interface_spec>`


.. code-block:: bash
    :linenos:
    
    #!/bin/bash
    
    #Capture command line arguments
    INPUT_H5=$1
    OUTDIR=$2
    
    #Set known arguments if needed
    NUMWORKERS=10

    PYTHON=/usr/local/miniconda/bin/python

    echo 'Mounting directory'
    mkdir -p /dted
    mount -o soft,rw,lookupcache=positive dted:/dted /dted

    SCRIPT=/app/my_algorithm.py

    #Call your algorithm and pass in the arguments needed
    $PYTHON $SCRIPT $INPUT_H5 $NUMWORKERS $OUTDIR /dted
    
    #Capture exit code from algorithm
    rc=$?

    #It is good practice to unmount your directory when finished
    umount -lf /dted
    echo 'Unmounting directory'

    #If the algorithm didn't exit successfully, exit wrapper with same code
    if [ $rc != 0 ] ; then
      echo "Caught exit(${rc}) from $SCRIPT"
      exit $rc
    else
      echo "$SCRIPT Success."
    fi

    echo 'Wrapper finished'

    exit $rc
