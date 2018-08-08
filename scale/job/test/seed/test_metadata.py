from __future__ import unicode_literals

import django
from django.test import TestCase
from job.seed.exceptions import InvalidSeedMetadataDefinition
from job.seed.metadata import SeedMetadata


class TestSeedMetadata(TestCase):
    """Tests functions in the manifest module."""

    def setUp(self):
        django.setup()

    def test_metadata_from_json_feature(self):
        json = {
            'type': 'Feature',
            'geometry': None,
            'properties': None
        }

        object = SeedMetadata.metadata_from_json(json)
        self.assertEquals(object.get_data(), json)

    def test_metadata_from_json_geometry(self):
        json = {
            'type': 'Point',
            'coordinates': [0,0]
        }

        object = SeedMetadata.metadata_from_json(json)

        self.assertIn('geometry', object.get_data())
        self.assertIn('properties', object.get_data())
        self.assertEquals(json, object.get_data()['geometry'])

    def test_metadata_from_json_feature_collection(self):
        json = {
            'type': 'FeatureCollection',
            'features': []
        }

        with self.assertRaises(InvalidSeedMetadataDefinition) as ex:
            SeedMetadata.metadata_from_json(json)

            self.assertContains('UNSUPPORTED_GEOJSON', ex)

    def test_metadata_from_json_geometry_collection(self):
        json = {
            'type': 'GeometryCollection',
            'geometry': None
        }

        with self.assertRaises(InvalidSeedMetadataDefinition) as ex:
            SeedMetadata.metadata_from_json(json)

            self.assertContains('UNSUPPORTED_GEOJSON', ex)

    def test_metadata_from_json_invalid_geojson(self):
        json = {
            'type': 'Invalid'
        }

        with self.assertRaises(InvalidSeedMetadataDefinition) as ex:
            SeedMetadata.metadata_from_json(json)

            self.assertContains('JSON_VALIDATION_ERROR', ex)