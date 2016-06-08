"""Defines utility methods for testing files and workspaces"""
from __future__ import unicode_literals

import datetime

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


def create_file(file_name='my_test_file.txt', media_type='text/plain', file_size=100, file_path=None, workspace=None,
                countries=None):
    """Creates a Scale file model for unit testing

    :returns: The file model
    :rtype: :class:`storage.models.ScaleFile`
    """

    if not workspace:
        workspace = create_workspace()
    scale_file = ScaleFile.objects.create(file_name=file_name, media_type=media_type, file_size=file_size,
                                          file_path=file_path or 'file/path/' + file_name, workspace=workspace)
    if countries:
        scale_file.countries = countries
        scale_file.save()
    return scale_file


def create_workspace(name=None, title=None, json_config=None, base_url=None, is_active=True, archived=None):
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
    if is_active is False and not archived:
        archived = timezone.now()

    return Workspace.objects.create(name=name, title=title, json_config=json_config, base_url=base_url,
                                    is_active=is_active, archived=archived)
