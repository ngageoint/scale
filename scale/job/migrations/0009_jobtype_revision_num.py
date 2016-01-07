# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0008_jobtype_trigger_rule'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobtype',
            name='revision_num',
            field=models.IntegerField(default=1),
            preserve_default=True,
        ),
    ]
