# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0015_auto_20160420_1345'),
        ('storage', '0002_workspace_is_move_enabled'),
    ]

    def populate_job_configuration(apps, schema_editor):
        from job.configuration.configuration.job_configuration import JobConfiguration, MODE_RO, MODE_RW
        from job.configuration.data.job_data import JobData
        # Go through all of the job models that have job data and populate their configuration
        Job = apps.get_model('job', 'Job')
        ScaleFile = apps.get_model('storage', 'ScaleFile')
        Workspace = apps.get_model('storage', 'Workspace')
        total_count = Job.objects.all().count()
        workspaces = {}
        for workspace in Workspace.objects.all().iterator():
            workspaces[workspace.id] = workspace
        print 'Populating new configuration field for %s jobs' % str(total_count)
        done_count = 0
        for job in Job.objects.select_related('job_type').iterator():
            if done_count % 1000 == 0:
                percent = (done_count / total_count) * 100.00
                print 'Completed %s of %s jobs (%f%%)' % (done_count, total_count, percent)
            done_count += 1

            # Ignore jobs that don't have their job data populated yet
            if not job.data:
                continue

            data = JobData(job.data)
            input_file_ids = data.get_input_file_ids()
            input_files = ScaleFile.objects.filter(id__in=input_file_ids).select_related('workspace').iterator()
            input_workspaces = set()
            for input_file in input_files:
                input_workspaces.add(input_file.workspace.name)

            configuration = JobConfiguration()
            for name in input_workspaces:
                configuration.add_job_task_workspace(name, MODE_RO)
            if not job.job_type.is_system:
                for name in input_workspaces:
                    configuration.add_pre_task_workspace(name, MODE_RO)
                    # We add input workspaces to post task so it can perform a parse results move if requested by the
                    # job's results manifest
                    configuration.add_post_task_workspace(name, MODE_RW)
                for workspace_id in data.get_output_workspace_ids():
                    workspace = workspaces[workspace_id]
                    if workspace.name not in input_workspaces:
                        configuration.add_post_task_workspace(workspace.name, MODE_RW)
            elif job.job_type.name == 'scale-ingest':
                ingest_id = data.get_property_values(['Ingest ID'])['Ingest ID']
                from ingest.models import Ingest
                ingest = Ingest.objects.select_related('workspace').get(id=ingest_id)
                configuration.add_job_task_workspace(ingest.workspace.name, MODE_RW)

            job.configuration = configuration.get_dict()
            job.save()
        print 'All %s jobs completed' % str(total_count)

    operations = [
        migrations.RunPython(populate_job_configuration),
    ]
