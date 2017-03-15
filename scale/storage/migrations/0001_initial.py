# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import util.deprecation
import django.db.models.deletion
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CountryData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
                ('fips', models.CharField(max_length=2)),
                ('gmi', models.CharField(max_length=3)),
                ('iso2', models.CharField(max_length=2)),
                ('iso3', models.CharField(max_length=3)),
                ('iso_num', models.IntegerField()),
                ('border', django.contrib.gis.db.models.fields.GeometryField(srid=4326)),
                ('effective', models.DateTimeField()),
                ('is_deleted', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('deleted', models.DateTimeField(null=True, blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True, db_index=True)),
            ],
            options={
                'db_table': 'country_data',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ScaleFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file_name', models.CharField(max_length=250, db_index=True)),
                ('media_type', models.CharField(max_length=250)),
                ('file_size', models.BigIntegerField()),
                ('data_type', models.TextField(blank=True)),
                ('file_path', models.CharField(max_length=1000)),
                ('is_deleted', models.BooleanField(default=False)),
                ('uuid', models.CharField(max_length=32, db_index=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('deleted', models.DateTimeField(null=True, blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('data_started', models.DateTimeField(db_index=True, null=True, blank=True)),
                ('data_ended', models.DateTimeField(null=True, blank=True)),
                ('geometry', django.contrib.gis.db.models.fields.GeometryField(srid=4326, null=True, verbose_name='Geometry', blank=True)),
                ('center_point', django.contrib.gis.db.models.fields.PointField(srid=4326, null=True, blank=True)),
                ('meta_data', util.deprecation.JSONStringField(default={}, null=True, blank=True)),
                ('countries', models.ManyToManyField(to='storage.CountryData')),
            ],
            options={
                'db_table': 'scale_file',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Workspace',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50, db_index=True)),
                ('title', models.CharField(max_length=50, null=True, blank=True)),
                ('description', models.CharField(max_length=500, blank=True)),
                ('base_url', models.URLField(null=True, blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('json_config', util.deprecation.JSONStringField(default={}, null=True, blank=True)),
                ('used_size', models.BigIntegerField(null=True, blank=True)),
                ('total_size', models.BigIntegerField(null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('archived', models.DateTimeField(null=True, blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'workspace',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='scalefile',
            name='workspace',
            field=models.ForeignKey(to='storage.Workspace', on_delete=django.db.models.deletion.PROTECT),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='countrydata',
            unique_together=set([('name', 'effective')]),
        ),
        migrations.AlterIndexTogether(
            name='countrydata',
            index_together=set([('name', 'effective')]),
        ),
    ]
