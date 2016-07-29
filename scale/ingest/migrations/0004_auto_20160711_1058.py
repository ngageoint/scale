# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0003_auto_20160711_1044'),
    ]

    def populate_new_workspace(apps, schema_editor):
        # Populate the new workspace and file_path fields for the ingest models
        Ingest = apps.get_model('ingest', 'Ingest')
        print 'Populating new_file_path and new_workspace fields for ingest models'
        Ingest.objects.update(new_file_path=models.F('file_path'), new_workspace=models.F('workspace'))
        print 'Setting file_path and workspace fields to null for ingest models'
        Ingest.objects.update(file_path='', workspace=None)

    operations = [
        migrations.RunPython(populate_new_workspace),
    ]
