# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0014_auto_20160317_1208'),
        ('recipe', '0011_auto_20160330_1505'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipejobold',
            name='recipe',
            field=models.ForeignKey(to='recipe.Recipe', on_delete=django.db.models.deletion.PROTECT, db_index=False),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='RecipeJob',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('job_name', models.CharField(max_length=100)),
                ('is_original', models.BooleanField(default=True)),
                ('job', models.ForeignKey(to='job.Job', on_delete=django.db.models.deletion.PROTECT)),
                ('recipe', models.ForeignKey(to='recipe.Recipe', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'db_table': 'recipe_job',
            },
            bases=(models.Model,),
        ),
    ]
