from __future__ import unicode_literals

import django
from django.test import TestCase

from node.resources.exceptions import InvalidResources
from node.resources.json.resources import Resources


class TestResources(TestCase):

    def setUp(self):
        django.setup()

    def test_successful_validation(self):
        """Tests successful validation done in __init__"""

        # Try minimal acceptable configuration
        Resources()

        # Test with a few resources and check default version
        resource_dict = {'resources': {'foo': 1.0, 'cpus': 2}}
        resources = Resources(resource_dict)
        self.assertEqual(resources.get_dict()['version'], '1.0')

    def test_invalid_resources(self):
        """Tests validation done in __init__ where the resource values are invalid"""

        # Blank resource
        resources = {'resources': {'foo': ''}}
        self.assertRaises(InvalidResources, Resources, resources)

        # String resource value
        resources = {'resources': {'foo': 'my_string'}}
        self.assertRaises(InvalidResources, Resources, resources)
