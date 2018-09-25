"""Defines utility methods for testing files and workspaces"""
from __future__ import unicode_literals

import datetime
import os

import django.contrib.gis.geos as geos
import django.utils.timezone as timezone

from storage.models import CountryData, ScaleFile, Workspace

COUNTRY_NAME_COUNTER = 1
WORKSPACE_NAME_COUNTER = 1
WORKSPACE_TITLE_COUNTER = 1


def create_country(name=None, fips='TT', gmi='TT', iso2='TT', iso3='TST', iso_num=0, border=None, effective=None):
    """Creates a country data model for unit testing

    :returns: The file model
    :rtype: :class:`storage.models.CountryData`
    """
    if not name:
        global COUNTRY_NAME_COUNTER
        name = 'test-country-%i' % COUNTRY_NAME_COUNTER
        COUNTRY_NAME_COUNTER += 1
    if not border:
        border = geos.Polygon(((0, 0), (0, 10), (10, 10), (10, 0), (0, 0)))
    if not effective:
        effective = timezone.now()

    return CountryData.objects.create(name=name, fips=fips, gmi=gmi, iso2=iso2, iso3=iso3, iso_num=iso_num,
                                      border=border, effective=effective)


def create_file(file_name='my_test_file.txt', file_type='SOURCE', media_type='text/plain', file_size=100, 
                data_type='', file_path=None, workspace=None, is_deleted=False, uuid='', last_modified=None,
                data_started=None, data_ended=None, source_started=None, source_ended=None, 
                source_sensor_class=None, source_sensor=None, source_collection=None, source_task=None,
                geometry=None, center_point=None, meta_data='', countries=None, job_exe=None, job_output=None,
                recipe=None, recipe_node=None, batch=None, is_superseded=False, superseded=None):
    """Creates a Scale file model for unit testing

    :returns: The file model
    :rtype: :class:`storage.models.ScaleFile`
    """

    if not workspace:
        workspace = create_workspace()

    job = None
    job_type = None
    if job_exe:
        job = job_exe.job
        job_type=job_exe.job.job_type
        
    recipe_type = None
    if recipe:
        recipe_type = recipe.recipe_type
        
    deleted = None
    if is_deleted:
        deleted = timezone.now()

    scale_file = ScaleFile.objects.create(file_name=file_name, file_type=file_type, media_type=media_type, file_size=file_size,
                                          data_type=data_type, file_path=file_path or 'file/path/' + file_name, workspace=workspace,
                                          is_deleted=is_deleted, deleted=deleted, uuid=uuid, last_modified=last_modified, 
                                          data_started=data_started, data_ended=data_ended, source_started=source_started, 
                                          source_ended=source_ended, source_sensor_class=source_sensor_class,  
                                          source_sensor=source_sensor, source_collection=source_collection, source_task=source_task,
                                          geometry=geometry, center_point=center_point, meta_data=meta_data,
                                          job_exe=job_exe, job=job, job_type=job_type, job_output=job_output,
                                          recipe=recipe, recipe_node=recipe_node, recipe_type=recipe_type, batch=batch,
                                          is_superseded=is_superseded, superseded=superseded)
    if countries:
        scale_file.countries = countries
        scale_file.save()
    return scale_file


def create_workspace(name=None, title=None, json_config=None, base_url=None, is_active=True, deprecated=None):
    """Creates a workspace model for unit testing

    :returns: The workspace model
    :rtype: :class:`storage.models.Workspace`
    """

    if not name:
        global WORKSPACE_NAME_COUNTER
        name = 'test-workspace-%i' % WORKSPACE_NAME_COUNTER
        WORKSPACE_NAME_COUNTER += 1
    if not title:
        global WORKSPACE_TITLE_COUNTER
        title = 'Test Workspace %i' % WORKSPACE_TITLE_COUNTER
        WORKSPACE_TITLE_COUNTER += 1
    if not json_config:
        json_config = {
            'version': '1.0',
            'broker': {
                'type': 'host',
                'host_path': '/host/path',
            }
        }
    if is_active is False and not deprecated:
        deprecated = timezone.now()

    return Workspace.objects.create(name=name, title=title, json_config=json_config, base_url=base_url,
                                    is_active=is_active, deprecated=deprecated)
