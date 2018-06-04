from __future__ import unicode_literals

import django

from django.test.testcases import TestCase

from data.interface.exceptions import InvalidInterface
from data.interface.interface import Interface
from data.interface.parameter import FileParameter, JsonParameter


class TestInterface(TestCase):
    """Tests related to the Interface class"""

    def setUp(self):
        django.setup()

    def test_add_parameter(self):
        """Tests calling Interface.add_parameter()"""

        interface = Interface()

        file_param = FileParameter('input_1', ['application/json'])
        interface.add_parameter(file_param)

        json_param = JsonParameter('input_2', 'integer')
        interface.add_parameter(json_param)

        self.assertSetEqual(set(interface.parameters.keys()), {'input_1', 'input_2'})

        # Duplicate parameter
        dup_param = FileParameter('input_1', [], required=False)
        self.assertRaises(InvalidInterface, interface.add_parameter, dup_param)
