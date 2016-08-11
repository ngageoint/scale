# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0002_workspace_is_move_enabled'),
        ('ingest', '0002_auto_20160414_0937'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ingest',
            name='ingest_path',
        ),
        migrations.RemoveField(
            model_name='ingest',
            name='transfer_path',
        ),
        migrations.AddField(
            model_name='ingest',
            name='new_file_path',
            field=models.CharField(max_length=1000, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='ingest',
            name='new_workspace',
            field=models.ForeignKey(related_name='+', blank=True, to='storage.Workspace', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='ingest',
            name='transfer_started',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='ingest',
            name='workspace',
            field=models.ForeignKey(related_name='+', blank=True, to='storage.Workspace', null=True),
            preserve_default=True,
        ),
    ]
