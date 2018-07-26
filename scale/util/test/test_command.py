from __future__ import unicode_literals

import django
from django.test import TestCase

from util.command import environment_expansion
from util.exceptions import UnbalancedBrackets


class TestEnvironmentExpansion(TestCase):
    def setUp(self):
        django.setup()

        self.env_dict = {'HELLO': 'Hello', 'THERE': 'there', 'SUPER_FRIEND': 'friend', "COUNT": 1}

    def test_naked_var_expansion_success(self):
        result = environment_expansion(self.env_dict, '$HELLO $THERE')
        self.assertEquals('Hello there', result)

    def test_naked_var_expansion_numeral_success(self):
        result = environment_expansion(self.env_dict, '$HELLO $THERE number $COUNT')
        self.assertEquals('Hello there number 1', result)

    def test_wrapped_var_expansion_success(self):
        result = environment_expansion(self.env_dict, '${HELLO} ${THERE}')
        self.assertEquals('Hello there', result)

    def test_missing_var_expansion_no_remove(self):
        result = environment_expansion(self.env_dict, '${HELLO} ${THERE} ${PEOPLE}', remove_extras=False)
        self.assertEquals('Hello there ${PEOPLE}', result)

    def test_missing_var_expansion_remove(self):
        result = environment_expansion(self.env_dict, '${HELLO} ${THERE} ${PEOPLE}', remove_extras=True)
        self.assertEquals('Hello there', result)

    def test_missing_var_expansion_remove_2(self):
        result = environment_expansion(self.env_dict, '${HELLO} ${THERE} ${PEOPLE} ${HELLO}', remove_extras=True)
        self.assertEquals('Hello there Hello', result)

    def test_unmatched_curly_var_expansion_ignored(self):
        with self.assertRaises(UnbalancedBrackets):
            environment_expansion(self.env_dict, '${HELLO} ${THERE ${SUPER_FRIEND}')

    def test_prefixed_var_expansion_success(self):
        result = environment_expansion(self.env_dict, '${THERE/#/-t }')
        self.assertEquals('-t there', result)

    def test_multi_instances_var_expansion_success(self):
        result = environment_expansion(self.env_dict, '$HELLO ${THERE/#/-t }, ${SUPER_FRIEND}')
        self.assertEquals('Hello -t there, friend', result)
