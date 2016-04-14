
.. _algorithm_integration_step2:

Capturing your algorithm outputs with a Scale Results Manifest
==============================================================

Generating a results manifest should either be done within your algorithm or within the algorithm's wrapper script.
Once an algorithm is complete a results manifest file is used to convey what products should be archived by Scale and
passed onto other algorithms.  It is **HIGHLY** recommended that the algorithm write out the manifest JSON file as
prescribed in the Scale documentation.

Click here for results manifest specification:  :ref:`algorithm_integration_results_manifest`

Below are examples of wrapper scripts if you cannot modify the algorithm.  These should only be used if you do not have
access to the source code for your algorithm.

**ONLY FILES IN THE RESULTS MANIFEST WILL BE SAVED BY SCALE**

File paths listed in the results manifest must be absolute paths to the file.  The results manifest must be called
"results_manifest.json" and must be present in the root of the output directory provided by Scale.
The output names in the results manifest must match the **output_data** field in the
:ref:`job interface <architecture_jobs_interface_spec>`.

Simple Results Manifest Example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: javascript
   :linenos:
   
    {
       "version": "1.1",
       "output_data": [
          {
             "name" : "output_file_csv",
             "file": {
                "path" : "/tmp/job_exe_231/outputs/results.csv"
             }
          },
          {
             "name" : "output_file_tif",
             "file": {
                "path" : "/tmp/job_exe_231/outputs/myimage1.tif"
             }
          },
          {
             "name" : "output_file_tif2",
             "file": {
                "path" : "/tmp/job_exe_231/outputs/myimage2.tif"
             }
          }          
       ]
    }
    

Example Code for generating results manifests
---------------------------------------------

Shell Script
++++++++++++
.. code-block:: bash
    :linenos:
    
    # Gather the output files and put them  in a manifest
    function join { local IFS="$1"; shift; echo "$*"; }


    manifest_files=()
    
    #Find the files in the output directory
    image1_tif=$(find $OUTDIR -name "*image1.tif")
    image2_tif=$(find $OUTDIR -name "*image2.tif")
    csv_data=$(find $OUTDIR -name "*results.csv")

    #If the file was found, add it to the manifest list
    if [ -n "$image1_tif" ] ; then
      manifest_files+=("{\"name\":\"output_file_tif\", \"path\":\"$image1_tif\"}")
    fi

    if [ -n "$image2_tif" ] ; then
      manifest_files+=("{\"name\":\"output_file_tif2\", \"path\":\"$image2_tif2\"}")
    fi

    if [ -n "$csv_data" ] ; then
      manifest_files+=("{\"name\":\"output_file_csv\", \"path\":\"$csv_data\"}")
    fi

    
    manifest_files_text=$(join , "${manifest_files[@]}")

    results_manifest_text={\"version\":\"1.0\",\"files\":[$manifest_files_text]}
    echo "$results_manifest_text" > $OUTDIR/results_manifest.json

Python
++++++
.. code-block:: python
    :linenos:
    
    import json
    from glob import glob
    
    def generateResultsManifest(outdir):

        try:
            outputCSV = glob(os.path.join(outdir, '*results.csv'))[0]
            outputImage1 = glob(os.path.join(outdir, '*image1.tif'))[0]
            outputImage2 = glob(os.path.join(outdir, '*image2.tif'))[0]
        except:
            #Error in finding results
            sys.exit(5)

        jsonDict={}
        jsonDict['version'] = '1.1'
        jsonDict['output_data'] = []
        
        tempDict = {}
        tempDict['name'] = 'output_file_tif'
        tempDict['file'] = {'path': outputImage1}
        jsonDict['output_data'].append(tempDict)
        
        tempDict = {}
        tempDict['name'] = 'output_file_tif2'
        tempDict['file'] = {'path': outputImage2}
        jsonDict['output_data'].append(tempDict)
        
        tempDict = {}
        tempDict['name'] = 'output_file_csv'
        tempDict['file'] = {'path': outputCSV}
        jsonDict['output_data'].append(tempDict)
        
        with open(os.path.join(outdir, 'results_manifest.json'), 'w') as fout:
            jsonString = json.dumps(jsonDict)
            fout.write(jsonString)
            

See the example algorithms for additional examples.
