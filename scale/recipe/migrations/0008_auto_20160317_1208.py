# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0007_auto_20160310_1318'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='last_modified',
            field=models.DateTimeField(auto_now=True),  # Removed db_index to workaround a migration hashing bug
            preserve_default=True,
        ),
        migrations.AlterIndexTogether(
            name='recipe',
            index_together=set([('last_modified', 'recipe_type')]),
        ),
    ]
