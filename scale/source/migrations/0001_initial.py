# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SourceFile',
            fields=[
                ('file', models.OneToOneField(parent_link=True, primary_key=True, serialize=False, to='storage.ScaleFile')),
                ('is_parsed', models.BooleanField(default=False)),
                ('parsed', models.DateTimeField(null=True, blank=True)),
            ],
            options={
                'db_table': 'source_file',
            },
            bases=('storage.scalefile',),
        ),
    ]
