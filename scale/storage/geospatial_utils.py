"""Defines functions for geospatial information"""
import json

import django.contrib.gis.geos as geos

from job.configuration.results.exceptions import InvalidResultsManifest


def parse_geo_json_file(geo_json_path):
    """Parses GeoJSON from a file and returns a geometry object and metadata.

    :param geo_json_path: The absolute file path of the GeoJSON file
    :type geo_json_path: str
    :rtype: GEOSGeometry, dict
    :returns: the geometry and metadata
    """
    with open(geo_json_path, u'r') as geo_json_file:
        geo_json = json.load(geo_json_file)

    return parse_geo_json(geo_json)


def parse_geo_json(geo_json):
    """Parses GeoJSON and returns a geometry object and metadata.

    :param geo_json: The geo json to parse
    :type geo_json: dict
    :rtype: GEOSGeometry, dict
    :returns: the geometry and metadata
    """

    geom = None
    geom_json = None
    props = None
    if geo_json[u'type'] == u'Feature':
        geom_json = geo_json[u'geometry']
        if u'properties' in geo_json:
            props = geo_json[u'properties']
    elif geo_json[u'type'] == u'FeatureCollection':
        # Currently handles collections by just grabbing first entry
        geom_json = geo_json[u'features'][0][u'geometry']
        if u'properties' in geo_json[u'features'][0]:
            props = geo_json[u'features'][0][u'properties']
    else:
        # The GeoJSON is just a geometry
        geom_json = geo_json

    # Parse geometry
    if geom_json:
        try:
            geom = geos.GEOSGeometry(json.dumps(geom_json), srid=4326)
        except geos.GEOSException as geos_error:
            raise InvalidResultsManifest(geos_error)

    return geom, props


def get_center_point(geom):
    """Returns a center point for the given geometry object.

    :param geom: The geometry
    :type geom: GEOSGeometry
    :rtype: Point
    :returns: the center point
    """
    if geom:
        center = geom.centroid
        return center
