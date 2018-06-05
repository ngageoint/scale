from __future__ import unicode_literals

import django
from django.test import TestCase

from data.interface.exceptions import InvalidInterface
from data.interface.interface import Interface
from data.interface.json.interface_v6 import convert_interface_to_v6_json, InterfaceV6
from data.interface.parameter import FileParameter, JsonParameter


class TestInterfaceV6(TestCase):

    def setUp(self):
        django.setup()

    def test_convert_interface_to_v6_json(self):
        """Tests calling convert_interface_to_v6_json()"""

        # Try interface with nothing set
        interface = Interface()
        json = convert_interface_to_v6_json(interface)
        InterfaceV6(interface=json.get_dict(), do_validate=True)  # Revalidate

        # Try interface with a variety of parameters
        interface = Interface()
        interface.add_parameter(FileParameter('input_a', ['application/json'], required=True, multiple=False))
        interface.add_parameter(FileParameter('input_b', [], required=False, multiple=True))
        interface.add_parameter(JsonParameter('input_c', 'array', required=True))
        interface.add_parameter(JsonParameter('input_d', 'string', required=False))
        json = convert_interface_to_v6_json(interface)
        InterfaceV6(interface=json.get_dict(), do_validate=True)  # Revalidate
        self.assertSetEqual(set(json.get_interface().parameters.keys()), {'input_a', 'input_b', 'input_c', 'input_d'})

    def test_init_validation(self):
        """Tests the validation done in __init__"""

        # Try minimal acceptable configuration
        InterfaceV6(do_validate=True)

        # Invalid version
        interface = {'version': 'BAD'}
        self.assertRaises(InvalidInterface, InterfaceV6, interface, True)

        # Valid interface
        interface = {'version': '6', 'files': [{'name': 'input_a'},
                                               {'name': 'input_b', 'media_types': ['application/json'],
                                                'required': False, 'multiple': True}],
                     'json': [{'name': 'input_c', 'type': 'integer'},
                              {'name': 'input_d', 'type': 'object', 'required': False}]}
        InterfaceV6(interface=interface, do_validate=True)
