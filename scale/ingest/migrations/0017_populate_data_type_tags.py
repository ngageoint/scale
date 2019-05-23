# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0016_ingest_data_type_tags'),
    ]

    operations = [
        migrations.RunSQL('UPDATE ingest SET data_type_tags = REGEXP_SPLIT_TO_ARRAY(data_type, \',\') WHERE data_type != NULL AND data_type != \'\'')
    ]
