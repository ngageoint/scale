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
        self.assertEquals(object.data, json)

    def test_metadata_from_json_geometry(self):
        json = {
            'type': 'Point',
            'coordinates': [0,0]
        }

        object = SeedMetadata.metadata_from_json(json)

        self.assertIn('geometry', object._data)
        self.assertIn('properties', object._data)
        self.assertEquals(json, object._data['geometry'])

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

    def test_get_properties_null(self):
        object = SeedMetadata()

        self.assertEquals({}, object.properties)

    def test_get_properties_empty_dict(self):
        object = SeedMetadata()
        object._data['properties'] = {}

        self.assertEquals({}, object.properties)

    def test_get_properties_values(self):
        object = SeedMetadata()
        value = { 'key': 'value' }
        object._data['properties'] = value

        self.assertEquals(value, object.properties)

    def test_get_data_copy_by_value(self):
        object = SeedMetadata()

        self.assertIsNot(object.data, object._data)
        self.assertDictEqual(object.data, object._data)

    def test_set_properties_null_properties(self):
        object = SeedMetadata()

        object.set_property('key', 'value')

        self.assertDictEqual({'key':'value'}, object._data['properties'])

    def test_set_properties_empty_properties(self):
        object = SeedMetadata()
        object._data['properties'] = {}

        object.set_property('key', 'value')

        self.assertDictEqual({'key': 'value'}, object._data['properties'])

    def test_set_properties_existing_properties(self):
        object = SeedMetadata()

        object.set_property('key', 'value')

        self.assertDictEqual({'key': 'value'}, object._data['properties'])