# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('queue', '0005_queue_node_required'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='queuedepthbyjobtype',
            name='job_type',
        ),
        migrations.DeleteModel(
            name='QueueDepthByJobType',
        ),
        migrations.DeleteModel(
            name='QueueDepthByPriority',
        ),
    ]
