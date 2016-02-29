#@PydevCodeAnalysisIgnore
from __future__ import unicode_literals

import django
from django.test import TestCase

import source.test.utils as source_test_utils
from source.triggers.parse_trigger_condition import ParseTriggerCondition


class TestParseTriggerConditionIsConditionMet(TestCase):

    def setUp(self):
        django.setup()

    def test_no_conditions(self):
        '''Tests calling ParseTriggerCondition.is_condition_met() with no conditions'''

        condition = ParseTriggerCondition(None, None)
        source_file = source_test_utils.create_source(media_type='text/plain')
        
        self.assertEqual(condition.is_condition_met(source_file), True)
    
    def test_media_type_match(self):
        '''Tests calling ParseTriggerCondition.is_condition_met() with a matching media type'''

        condition = ParseTriggerCondition('text/plain', None)
        source_file = source_test_utils.create_source(media_type='text/plain')
        
        self.assertEqual(condition.is_condition_met(source_file), True)

    def test_media_type_mismatch(self):
        '''Tests calling ParseTriggerCondition.is_condition_met() with a mismatched media type'''

        condition = ParseTriggerCondition('application/json', None)
        source_file = source_test_utils.create_source(media_type='text/plain')
        
        self.assertEqual(condition.is_condition_met(source_file), False)

    def test_has_data_types(self):
        '''Tests calling ParseTriggerCondition.is_condition_met() with a source file that has all required data types'''

        condition = ParseTriggerCondition(None, set(['A', 'B', 'C']))
        source_file = source_test_utils.create_source(media_type='text/plain')
        source_file.add_data_type_tag('A')
        source_file.add_data_type_tag('B')
        source_file.add_data_type_tag('C')
        source_file.add_data_type_tag('D')
        source_file.add_data_type_tag('E')
        
        self.assertEqual(condition.is_condition_met(source_file), True)

    def test_does_not_have_data_types(self):
        '''Tests calling ParseTriggerCondition.is_condition_met() with a source file that does not have all required data types'''

        condition = ParseTriggerCondition(None, set(['A', 'B', 'C']))
        source_file = source_test_utils.create_source(media_type='text/plain')
        source_file.add_data_type_tag('A')
        source_file.add_data_type_tag('B')
        
        self.assertEqual(condition.is_condition_met(source_file), False)

    def test_both_correct(self):
        '''Tests calling ParseTriggerCondition.is_condition_met() with a source file that meets both criteria'''

        condition = ParseTriggerCondition('text/plain', set(['A', 'B', 'C']))
        source_file = source_test_utils.create_source(media_type='text/plain')
        source_file.add_data_type_tag('A')
        source_file.add_data_type_tag('B')
        source_file.add_data_type_tag('C')
        
        self.assertEqual(condition.is_condition_met(source_file), True)

    def test_media_type_incorrect(self):
        '''Tests calling ParseTriggerCondition.is_condition_met() with a source file that only has the correct data types'''

        condition = ParseTriggerCondition('application/json', set(['A', 'B', 'C']))
        source_file = source_test_utils.create_source(media_type='text/plain')
        source_file.add_data_type_tag('A')
        source_file.add_data_type_tag('B')
        source_file.add_data_type_tag('C')
        
        self.assertEqual(condition.is_condition_met(source_file), False)

    def test_data_types_incorrect(self):
        '''Tests calling ParseTriggerCondition.is_condition_met() with a source file that only has the correct media type'''

        condition = ParseTriggerCondition('text/plain', set(['A', 'B', 'C', 'D']))
        source_file = source_test_utils.create_source(media_type='text/plain')
        source_file.add_data_type_tag('A')
        source_file.add_data_type_tag('B')
        source_file.add_data_type_tag('C')
        
        self.assertEqual(condition.is_condition_met(source_file), False)
