from __future__ import unicode_literals

import django

from django.test.testcases import TestCase
from mock import MagicMock

from data.interface.exceptions import InvalidInterface, InvalidInterfaceConnection
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
        with self.assertRaises(InvalidInterface) as context:
            interface.add_parameter(dup_param)
        self.assertEqual(context.exception.error.name, 'DUPLICATE_INPUT')

    def test_add_parameter_from_output_interface(self):
        """Tests calling Interface.add_parameter_from_output_interface()"""

        interface = Interface()
        output_interface = Interface()

        file_param = FileParameter('input_1', ['application/json'])
        output_interface.add_parameter(file_param)
        json_param = JsonParameter('input_2', 'integer')
        output_interface.add_parameter(json_param)

        interface.add_parameter_from_output_interface('input_1', 'input_1', output_interface)
        self.assertSetEqual(set(interface.parameters.keys()), {'input_1'})

        # Duplicate parameter
        with self.assertRaises(InvalidInterfaceConnection) as context:
            interface.add_parameter_from_output_interface('input_1', 'input_1', output_interface)
        self.assertEqual(context.exception.error.name, 'DUPLICATE_INPUT')

    def test_validate(self):
        """Tests calling Interface.validate()"""

        interface = Interface()

        file_param = FileParameter('input_1', ['application/json'])
        interface.add_parameter(file_param)

        json_param = JsonParameter('input_2', 'integer')
        interface.add_parameter(json_param)

        warnings = interface.validate()
        self.assertListEqual(warnings, [])

        mock_param = MagicMock()
        mock_param.name = 'input_3'
        mock_param.validate.side_effect = InvalidInterface('MOCK', '')
        interface.add_parameter(mock_param)

        # Invalid parameter
        with self.assertRaises(InvalidInterface) as context:
            interface.validate()
        self.assertEqual(context.exception.error.name, 'MOCK')

    def test_validate_connection(self):
        """Tests calling Interface.validate_connection()"""

        interface = Interface()
        connecting_interface = Interface()

        file_param = FileParameter('input_1', ['application/json'])
        interface.add_parameter(file_param)
        connecting_interface.add_parameter(file_param)
        json_param = JsonParameter('input_2', 'integer')
        interface.add_parameter(json_param)
        connecting_interface.add_parameter(json_param)

        # Valid connection
        interface.validate_connection(connecting_interface)

        new_file_param = FileParameter('input_3', ['image/gif'], required=True)
        interface.add_parameter(new_file_param)

        # Connection is missing required input 3
        with self.assertRaises(InvalidInterfaceConnection) as context:
            interface.validate_connection(connecting_interface)
        self.assertEqual(context.exception.error.name, 'PARAM_REQUIRED')

        connecting_interface.add_parameter(new_file_param)
        mock_param = MagicMock()
        mock_param.name = 'input_4'
        mock_param.validate_connection.side_effect = InvalidInterfaceConnection('MOCK', '')
        interface.add_parameter(mock_param)
        connecting_interface.add_parameter(mock_param)

        # Invalid connection
        with self.assertRaises(InvalidInterfaceConnection) as context:
            interface.validate_connection(connecting_interface)
        self.assertEqual(context.exception.error.name, 'MOCK')
