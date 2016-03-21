# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgjson.fields


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0012_auto_20160310_1318'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='docker_params',
            field=djorm_pgjson.fields.JSONField(default={}, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='jobexecution',
            name='docker_params',
            field=djorm_pgjson.fields.JSONField(default={}, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='jobtype',
            name='docker_params',
            field=djorm_pgjson.fields.JSONField(default={}, null=True, blank=True),
            preserve_default=True,
        ),
    ]
