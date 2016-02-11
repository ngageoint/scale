# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('node', '0003_node_is_paused_errors'),
        ('queue', '0004_remove_queue_is_job_type_paused'),
    ]

    operations = [
        migrations.AddField(
            model_name='queue',
            name='node_required',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='node.Node', null=True),
            preserve_default=True,
        ),
    ]
