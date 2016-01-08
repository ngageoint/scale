#@PydevCodeAnalysisIgnore
from __future__ import unicode_literals

import json

import django
from django.test import TestCase

from job.configuration.data.exceptions import InvalidConnection
from job.configuration.interface.job_interface import JobInterface
from recipe.configuration.data.exceptions import InvalidRecipeConnection
from recipe.configuration.definition.recipe_definition import RecipeDefinition
from source.triggers.configuration.parse_trigger_rule import ParseTriggerRuleConfiguration
from source.triggers.parse_trigger_handler import PARSE_TYPE
from storage.test import utils as storage_utils
from trigger.configuration.exceptions import InvalidTriggerRule


class TestParseTriggerRuleConfigurationInit(TestCase):

    def setUp(self):
        django.setup()

    def test_successful(self):
        '''Tests creating a ParseTriggerRuleConfiguration with valid configuration'''

        json_str = '{"condition": {"media_type": "text/plain", "data_types": ["A", "B"]}, "data": {"input_data_name": "my_input", "workspace_name": "my_workspace"}}'
        ParseTriggerRuleConfiguration(PARSE_TYPE, json.loads(json_str))

    def test_invalid(self):
        '''Tests creating a ParseTriggerRuleConfiguration with an invalid configuration'''

        json_str = '{"condition": {"media_type": "text/plain", "data_types": ["A", "B"]}}'
        self.assertRaises(InvalidTriggerRule, ParseTriggerRuleConfiguration, PARSE_TYPE, json.loads(json_str))


class TestParseTriggerRuleConfigurationValidate(TestCase):

    def setUp(self):
        django.setup()

    def test_successful(self):
        '''Tests calling ParseTriggerRuleConfiguration.validate() successfully'''

        workspace_name = 'Test_Workspace'
        storage_utils.create_workspace(name=workspace_name)
        json_str = '{"condition": {"media_type": "text/plain", "data_types": ["A", "B"]}, "data": {"input_data_name": "my_input", "workspace_name": "%s"}}' % workspace_name
        rule = ParseTriggerRuleConfiguration(PARSE_TYPE, json.loads(json_str))

        rule.validate()

    def test_bad_workspace(self):
        '''Tests calling ParseTriggerRuleConfiguration.validate() with a bad workspace'''

        json_str = '{"condition": {"media_type": "text/plain", "data_types": ["A", "B"]}, "data": {"input_data_name": "my_input", "workspace_name": "BAD_WORKSPACE"}}'
        rule = ParseTriggerRuleConfiguration(PARSE_TYPE, json.loads(json_str))

        self.assertRaises(InvalidTriggerRule, rule.validate)


class TestParseTriggerRuleConfigurationValidateTriggerForJob(TestCase):

    def setUp(self):
        django.setup()

    def test_successful(self):
        '''Tests calling ParseTriggerRuleConfiguration.validate_trigger_for_job() successfully with no warnings'''

        rule_json_str = '{"version": "1.0", "condition": {"media_type": "text/plain", "data_types": ["A", "B"]}, "data": {"input_data_name": "my_input", "workspace_name": "my_workspace"}}'
        rule_config = ParseTriggerRuleConfiguration(PARSE_TYPE, json.loads(rule_json_str))

        interface_json_str = '{"version": "1.0", "command": "my cmd", "command_arguments": "cmd args", "input_data": [{"name": "my_input", "type": "file", "media_types": ["text/plain", "application/json"]}], "output_data": [{"name": "my_output", "type": "file"}]}'
        job_interface = JobInterface(json.loads(interface_json_str))

        warnings = rule_config.validate_trigger_for_job(job_interface)

        self.assertListEqual(warnings, [])

    def test_bad_input_name(self):
        '''Tests calling ParseTriggerRuleConfiguration.validate_trigger_for_job() with a bad input name'''

        rule_json_str = '{"version": "1.0", "condition": {"media_type": "text/plain", "data_types": ["A", "B"]}, "data": {"input_data_name": "my_input", "workspace_name": "my_workspace"}}'
        rule_config = ParseTriggerRuleConfiguration(PARSE_TYPE, json.loads(rule_json_str))

        interface_json_str = '{"version": "1.0", "command": "my cmd", "command_arguments": "cmd args", "input_data": [{"name": "different_input_name", "type": "file", "media_types": ["text/plain", "application/json"]}], "output_data": [{"name": "my_output", "type": "file"}]}'
        job_interface = JobInterface(json.loads(interface_json_str))

        self.assertRaises(InvalidConnection, rule_config.validate_trigger_for_job, job_interface)

    def test_media_type_warning(self):
        '''Tests calling ParseTriggerRuleConfiguration.validate_trigger_for_job() with a warning for a mis-matched media type'''

        rule_json_str = '{"version": "1.0", "condition": {"media_type": "text/plain", "data_types": ["A", "B"]}, "data": {"input_data_name": "my_input", "workspace_name": "my_workspace"}}'
        rule_config = ParseTriggerRuleConfiguration(PARSE_TYPE, json.loads(rule_json_str))

        interface_json_str = '{"version": "1.0", "command": "my cmd", "command_arguments": "cmd args", "input_data": [{"name": "my_input", "type": "file", "media_types": ["application/json"]}], "output_data": [{"name": "my_output", "type": "file"}]}'
        job_interface = JobInterface(json.loads(interface_json_str))

        warnings = rule_config.validate_trigger_for_job(job_interface)

        self.assertEqual(len(warnings), 1)


class TestParseTriggerRuleConfigurationValidateTriggerForRecipe(TestCase):

    def setUp(self):
        django.setup()

    def test_successful(self):
        '''Tests calling ParseTriggerRuleConfiguration.validate_trigger_for_recipe() successfully with no warnings'''

        rule_json_str = '{"version": "1.0", "condition": {"media_type": "text/plain", "data_types": ["A", "B"]}, "data": {"input_data_name": "my_input", "workspace_name": "my_workspace"}}'
        rule_config = ParseTriggerRuleConfiguration(PARSE_TYPE, json.loads(rule_json_str))

        definition_json_str = '{"version": "1.0", "input_data": [{"name": "my_input", "type": "file", "media_types": ["text/plain", "application/json"]}], "jobs": [{"name": "my_job", "job_type": {"name": "test_job", "version": "1.0"}}]}'
        recipe_definition = RecipeDefinition(json.loads(definition_json_str))

        warnings = rule_config.validate_trigger_for_recipe(recipe_definition)

        self.assertListEqual(warnings, [])

    def test_bad_input_name(self):
        '''Tests calling ParseTriggerRuleConfiguration.validate_trigger_for_recipe() with a bad input name'''

        rule_json_str = '{"version": "1.0", "condition": {"media_type": "text/plain", "data_types": ["A", "B"]}, "data": {"input_data_name": "my_input", "workspace_name": "my_workspace"}}'
        rule_config = ParseTriggerRuleConfiguration(PARSE_TYPE, json.loads(rule_json_str))

        definition_json_str = '{"version": "1.0", "input_data": [{"name": "different_input_name", "type": "file", "media_types": ["text/plain", "application/json"]}], "jobs": [{"name": "my_job", "job_type": {"name": "test_job", "version": "1.0"}}]}'
        recipe_definition = RecipeDefinition(json.loads(definition_json_str))

        self.assertRaises(InvalidRecipeConnection, rule_config.validate_trigger_for_recipe, recipe_definition)

    def test_media_type_warning(self):
        '''Tests calling ParseTriggerRuleConfiguration.validate_trigger_for_recipe() with a warning for a mis-matched media type'''

        rule_json_str = '{"version": "1.0", "condition": {"media_type": "text/plain", "data_types": ["A", "B"]}, "data": {"input_data_name": "my_input", "workspace_name": "my_workspace"}}'
        rule_config = ParseTriggerRuleConfiguration(PARSE_TYPE, json.loads(rule_json_str))

        definition_json_str = '{"version": "1.0", "input_data": [{"name": "my_input", "type": "file", "media_types": ["application/json"]}], "jobs": [{"name": "my_job", "job_type": {"name": "test_job", "version": "1.0"}}]}'
        recipe_definition = RecipeDefinition(json.loads(definition_json_str))

        warnings = rule_config.validate_trigger_for_recipe(recipe_definition)

        self.assertEqual(len(warnings), 1)
