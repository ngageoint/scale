# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trigger', '0001_initial'),
        ('job', '0007_job_job_type_rev'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobtype',
            name='trigger_rule',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='trigger.TriggerRule', null=True),
            preserve_default=True,
        ),
    ]
