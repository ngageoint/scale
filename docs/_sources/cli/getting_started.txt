.. _cli_getting_started:

Creating New Job Types
========================================================================================================================

A key feature of the command line client (cli) is the ability to creatae new job types from existing configurations
or templates. New templates can be specified or defaults can be used. Make sure you have your `url` and `registry`
values configured in `~/.scaleconfig` (see :ref:`cli_overview`) To create a new job type from the default template::

  1 > goscale jobs init -a baseimage=alpine -a maintainer="My Name" -a name=MyJob -a description="MyJob will get the job done" -a image_name="myjob_v1" myjob
  2 > cd myjob
  3 > goscale jobs validate
  4 > goscale jobs commit -p
  5 > goscale jobs deploy

Line 1 initializes the job type from the default template. `-a` specifies template substitutions supported in the default
template. The next step is to edit the files, especially `Dockerfile`, `entryPoint.sh`, and `job_type.yml` to configure
your job type.

Line 3 validates the `job_type.yml` and prints warnings if there are any found.

Line 4 embeds the job type JSON data in the `Dockerfile`, builds the docker image and pushes it to the docker registry.
Remove the `-p` to avoid pushing to the registry.

Line 5 attempts to pull the docker image to ensure it is up-to-date, extracts the job_type JSON from the image metadata,
and submits it to scale. If the job type does not currently exist, it will be created. If it exists and the job_type JSON
specifies a different version, the job type will be updated. If the job type exists and the version is the same, nothing will
happen.

Once the new job type is registered with scale, you can run it from the cli if there is no automatic ingest trigger
configured. You need to create a job data file (JSON or YAML) as described in :ref:`architecture_jobs_job_data`.
You can specify a job type name or job type ID to execute a job.::

  1 > goscale jobs run -d job_data.yml MyJob

