# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Scheduler',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_paused', models.BooleanField(default=False)),
                ('master_hostname', models.CharField(default=b'localhost', max_length=250)),
                ('master_port', models.IntegerField(default=5050)),
            ],
            options={
                'db_table': 'scheduler',
            },
            bases=(models.Model,),
        ),
    ]
