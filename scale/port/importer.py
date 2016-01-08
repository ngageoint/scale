'''Defines the functions used to import configuration'''
from __future__ import unicode_literals

import logging

from django.db import transaction
from django.db.models import Q

import port.serializers as serializers
import trigger.handler as trigger_handler
from error.models import Error
from job.configuration.data.exceptions import InvalidConnection
from job.configuration.interface.error_interface import ErrorInterface
from job.configuration.interface.exceptions import InvalidInterfaceDefinition
from job.configuration.interface.job_interface import JobInterface
from job.exceptions import InvalidJobField
from job.models import JobType
from job.triggers.configuration.trigger_rule import JobTriggerRuleConfiguration
from port.schema import Configuration, InvalidConfiguration, ValidationWarning
from recipe.configuration.data.exceptions import InvalidRecipeConnection
from recipe.configuration.definition.exceptions import InvalidDefinition
from recipe.configuration.definition.recipe_definition import RecipeDefinition
from recipe.models import RecipeType
from recipe.triggers.configuration.trigger_rule import RecipeTriggerRuleConfiguration
from trigger.configuration.exceptions import InvalidTriggerType, InvalidTriggerRule

logger = logging.getLogger(__name__)


def validate_config(config_dict):
    '''Validates a configuration export for any potential errors or warnings.

    :param config_dict: A dictionary of configuration changes to validate.
    :type config_dict: dict
    :returns: A list of warnings discovered during validation.
    :rtype: list[:class:`port.schema.ValidationWarning`]

    :raises :class:`port.schema.InvalidConfiguration`: If any part of the configuration violates the specification.
    '''

    class Validated(Exception):
        '''This exception is used to abort the import transaction so that no actual changes are made.'''
        pass

    warnings = []
    try:

        # Attempt a real import and then roll it back when successful to confirm the validation
        # This saves on duplicate code because the existing validation methods expect database models to exist
        with transaction.atomic():
            warnings = _import_config(config_dict)
            raise Validated('Configuration is valid, rolling back transaction.')
    except Validated:
        pass
    return warnings


@transaction.atomic()
def import_config(config_dict):
    '''Applies a previously exported configuration to the current system.

    :param config_dict: A dictionary of configuration changes to validate.
    :type config_dict: dict
    :returns: A list of warnings discovered during the import.
    :rtype: list[:class:`port.schema.ValidationWarning`]

    :raises :class:`port.schema.InvalidConfiguration`: If any part of the configuration violates the specification.
    '''
    return _import_config(config_dict)


def _import_config(config_dict):
    '''Applies a previously exported configuration to the current system.

    This method only exists to decouple the import logic from the atomic transaction so that this method can be reused
    for validation without making any permanent changes.

    :param config_dict: A dictionary of configuration changes to import.
    :type config_dict: dict
    :returns: A list of warnings discovered during the import.
    :rtype: list[:class:`port.schema.ValidationWarning`]

    :raises :class:`port.schema.InvalidConfiguration`: If any part of the configuration violates the specification.
    '''
    warnings = []

    # Validate the top-level configuration structure
    config = Configuration(config_dict)

    # Build a map of row-locked models to import
    # Note the locking order matters here and must be high-level to low-level
    recipe_type_map = None
    if config.recipe_types:
        recipe_type_map = _build_recipe_type_map(config.recipe_types)
    job_type_map = None
    if config.job_types:
        job_type_map = _build_job_type_map(config.job_types)
    error_map = None
    if config.errors:
        error_map = _build_error_map(config.errors)

    # Attempt to create/edit the models
    if error_map:
        for error_dict in config.errors:
            error = error_map.get(error_dict.get('name'))
            warnings.extend(_import_error(error_dict, error))
    if job_type_map:
        for job_type_dict in config.job_types:
            job_type_key = (job_type_dict.get('name'), job_type_dict.get('version'))
            job_type = job_type_map.get(job_type_key)
            warnings.extend(_import_job_type(job_type_dict, job_type))
    if recipe_type_map:
        for recipe_type_dict in config.recipe_types:
            recipe_type_key = (recipe_type_dict.get('name'), recipe_type_dict.get('version'))
            recipe_type = recipe_type_map.get(recipe_type_key)
            warnings.extend(_import_recipe_type(recipe_type_dict, recipe_type))
    return warnings


def _build_recipe_type_map(recipe_type_dicts):
    '''Builds a mapping of recipe type keys (name, version) to existing recipe type models.

    This method acquires a row-level lock on existing models that need to be updated.

    :param recipe_type_dicts: A list of recipe type dictionary configuration changes.
    :type recipe_type_dicts: list[dict]
    :returns: A row-locked mapping of recipe type keys (name, version) to recipe type models.
    :rtype: dict[tuple(string, string), :class:`recipe.models.RecipeType`]

    :raises :class:`port.schema.InvalidConfiguration`: If any part of the configuration violates the specification.
    '''
    if not recipe_type_dicts:
        return {}

    # Build a unique set of recipe type keys
    recipe_type_map = {}
    recipe_type_filters = []
    for recipe_type_dict in recipe_type_dicts:

        # Validate the required fields
        if 'name' not in recipe_type_dict or not recipe_type_dict['name']:
            raise InvalidConfiguration('Recipe type import missing required field "name".')
        if 'version' not in recipe_type_dict or not recipe_type_dict['version']:
            raise InvalidConfiguration('Recipe type import missing required field "version".')

        # Add the entry to the pending map
        recipe_type_key = (recipe_type_dict['name'], recipe_type_dict['version'])
        recipe_type_map[recipe_type_key] = None

        # Add the entry to the query set
        recipe_type_filter = Q(name=recipe_type_key[0], version=recipe_type_key[1])
        recipe_type_filters = recipe_type_filters | recipe_type_filter if recipe_type_filters else recipe_type_filter

    # Build a map of row-locked models to edit
    recipe_type_query = RecipeType.objects.select_for_update().order_by('id')
    if recipe_type_filters:
        recipe_type_query = recipe_type_query.filter(recipe_type_filters)
    for recipe_type in recipe_type_query:
        recipe_type_map[(recipe_type.name, recipe_type.version)] = recipe_type
    return recipe_type_map


def _build_job_type_map(job_type_dicts):
    '''Builds a mapping of job type keys (name, version) to existing job type models.

    This method acquires a row-level lock on existing models that need to be updated.

    :param job_type_dicts: A list of job type dictionary configuration changes.
    :type job_type_dicts: list[dict]
    :returns: A row-locked mapping of job type keys (name, version) to job type models.
    :rtype: dict[tuple(string, string), :class:`job.models.JobType`]

    :raises :class:`port.schema.InvalidConfiguration`: If any part of the configuration violates the specification.
    '''
    if not job_type_dicts:
        return {}

    # Build a unique set of job type keys
    job_type_map = {}
    job_type_filters = []
    for job_type_dict in job_type_dicts:

        # Validate the required fields
        if 'name' not in job_type_dict or not job_type_dict['name']:
            raise InvalidConfiguration('Job type import missing required field "name".')
        if 'version' not in job_type_dict or not job_type_dict['version']:
            raise InvalidConfiguration('Job type import missing required field "version".')

        # Add the entry to the pending map
        job_type_key = (job_type_dict['name'], job_type_dict['version'])
        job_type_map[job_type_key] = None

        # Add the entry to the query set
        job_type_filter = Q(name=job_type_key[0], version=job_type_key[1])
        job_type_filters = job_type_filters | job_type_filter if job_type_filters else job_type_filter

    # Build a map of row-locked models to edit
    job_type_query = JobType.objects.select_for_update().order_by('id')
    if job_type_filters:
        job_type_query = job_type_query.filter(job_type_filters)
    for job_type in job_type_query:
        # Editing system-level job types is not allowed
        if job_type.category == 'system':
            raise InvalidConfiguration('System job types cannot be edited: %s' % job_type.name)
        job_type_map[(job_type.name, job_type.version)] = job_type
    return job_type_map


def _build_error_map(error_dicts):
    '''Builds a mapping of error name to existing error models.

    This method acquires a row-level lock on existing models that need to be updated.

    :param error_dicts: A list of error dictionary configuration changes.
    :type error_dicts: list[dict]
    :returns: A row-locked mapping of error names to error models.
    :rtype: dict[string, :class:`error.models.Error`]

    :raises :class:`port.schema.InvalidConfiguration`: If any part of the configuration violates the specification.
    '''
    if not error_dicts:
        return {}

    # Build a unique set of error names
    error_map = {}
    for error_dict in error_dicts:
        if 'name' not in error_dict or not error_dict['name']:
            raise InvalidConfiguration('Error import missing required field "name".')
        error_map[error_dict['name']] = None

    # Build a map of row-locked models to edit
    errors = Error.objects.select_for_update().filter(name__in=error_map.keys()).order_by('id')
    for error in errors:
        # Editing system-level errors is not allowed
        if error.category == 'SYSTEM':
            raise InvalidConfiguration('System errors cannot be edited: %s' % error.name)
        error_map[error.name] = error
    return error_map


def _import_recipe_type(recipe_type_dict, recipe_type=None):
    '''Attempts to apply the given recipe types configuration to the system.

    Note that proper model locking must be performed before calling this method.

    :param recipe_type_dict: A dictionary of recipe type configuration changes to import.
    :type recipe_type_dict: dict
    :param recipe_type: The existing recipe type model to update if applicable.
    :type recipe_type: :class:`recipe.models.RecipeType`
    :returns: A list of warnings discovered during import.
    :rtype: list[:class:`port.schema.ValidationWarning`]

    :raises :class:`port.schema.InvalidConfiguration`: If any part of the configuration violates the specification.
    '''
    warnings = []

    # Parse the JSON content into validated model fields
    recipe_type_serializer = serializers.ConfigurationRecipeTypeSerializer(recipe_type, data=recipe_type_dict)
    if not recipe_type_serializer.is_valid():
        raise InvalidConfiguration('Invalid recipe type schema: %s -> %s' % (recipe_type_dict['name'],
                                                                             recipe_type_serializer.errors))
    result = recipe_type_serializer.object

    # Validate the recipe definition
    try:
        definition = RecipeDefinition(result.definition)
        warnings.extend(definition.validate_job_interfaces())
    except (InvalidDefinition, InvalidRecipeConnection) as ex:
        raise InvalidConfiguration('Recipe type definition invalid: %s -> %s' % (result.name, unicode(ex)))

    # Validate the trigger rule
    trigger_rule = result.trigger_rule
    if trigger_rule:
        trigger_config = trigger_rule.get_configuration()
        if not isinstance(trigger_config, RecipeTriggerRuleConfiguration):
            logger.exception('Recipe type trigger rule type invalid')
            raise InvalidConfiguration('Recipe type trigger type invalid: %s -> %s' % (result.name, trigger_rule.type))
        try:
            warnings.extend(trigger_config.validate_trigger_for_recipe(definition))

            # Create a new rule when the trigger content was provided
            if recipe_type_dict.get('trigger_rule'):
                rule_handler = trigger_handler.get_trigger_rule_handler(trigger_rule.type)
                trigger_rule = rule_handler.create_trigger_rule(trigger_rule.configuration, trigger_rule.name,
                                                                trigger_rule.is_active)
        except (InvalidDefinition, InvalidTriggerType, InvalidTriggerRule, InvalidRecipeConnection) as ex:
            logger.exception('Recipe type trigger rule invalid')
            raise InvalidConfiguration('Recipe type trigger rule invalid: %s -> %s' % (result.name, unicode(ex)))
    remove_trigger_rule = 'trigger_rule' in recipe_type_dict and not recipe_type_dict['trigger_rule']

    # Edit or create the associated recipe type model
    if recipe_type:
        try:
            RecipeType.objects.edit_recipe_type(result.id, result.title, result.description, definition, trigger_rule,
                                                remove_trigger_rule)
        except (InvalidDefinition, InvalidTriggerType, InvalidTriggerRule, InvalidRecipeConnection) as ex:
            logger.exception('Recipe type edit failed')
            raise InvalidConfiguration('Unable to edit existing recipe type: %s -> %s' % (result.name, unicode(ex)))
    else:
        try:
            RecipeType.objects.create_recipe_type(result.name, result.version, result.title, result.description,
                                                  definition, trigger_rule)
        except (InvalidDefinition, InvalidTriggerType, InvalidTriggerRule, InvalidRecipeConnection) as ex:
            logger.exception('Recipe type create failed')
            raise InvalidConfiguration('Unable to create new recipe type: %s -> %s' % (result.name, unicode(ex)))
    return warnings


def _import_job_type(job_type_dict, job_type=None):
    '''Attempts to apply the given job types configuration to the system.

    Note that proper model locking must be performed before calling this method.

    :param job_type_dict: A dictionary of job type configuration changes to import.
    :type job_type_dict: dict
    :param job_type: The existing job type model to update if applicable.
    :type job_type: :class:`job.models.JobType`
    :returns: A list of warnings discovered during import.
    :rtype: list[:class:`port.schema.ValidationWarning`]

    :raises :class:`port.schema.InvalidConfiguration`: If any part of the configuration violates the specification.
    '''
    warnings = []

    # Parse the JSON content into validated model fields
    job_type_serializer = serializers.ConfigurationJobTypeSerializer(job_type, data=job_type_dict)
    if not job_type_serializer.is_valid():
        raise InvalidConfiguration('Invalid job type schema: %s -> %s' % (job_type_dict['name'],
                                                                          job_type_serializer.errors))
    result = job_type_serializer.object

    # Importing system-level job types is not allowed
    if result.category == 'system':
        raise InvalidConfiguration('System job types cannot be imported: %s' % result.name)

    # Validate the job interface
    try:
        interface = JobInterface(result.interface)
    except InvalidInterfaceDefinition as ex:
        raise InvalidConfiguration('Job type interface invalid: %s -> %s' % (result.name, unicode(ex)))

    # Validate the error mapping
    try:
        error_mapping = ErrorInterface(result.error_mapping)
        warnings.extend(error_mapping.validate())
    except InvalidInterfaceDefinition as ex:
        raise InvalidConfiguration('Job type error mapping invalid: %s -> %s' % (result.name, unicode(ex)))

    # Validate the trigger rule
    trigger_rule = result.trigger_rule
    if trigger_rule:
        trigger_config = trigger_rule.get_configuration()
        if not isinstance(trigger_config, JobTriggerRuleConfiguration):
            logger.exception('Job type trigger rule type invalid')
            raise InvalidConfiguration('Job type trigger type invalid: %s -> %s' % (result.name, trigger_rule.type))

        try:
            warnings.extend(trigger_config.validate_trigger_for_job(interface))

            # Create a new rule when the trigger content was provided
            if job_type_dict.get('trigger_rule'):
                rule_handler = trigger_handler.get_trigger_rule_handler(trigger_rule.type)
                trigger_rule = rule_handler.create_trigger_rule(trigger_rule.configuration, trigger_rule.name,
                                                                trigger_rule.is_active)
        except (InvalidTriggerType, InvalidTriggerRule, InvalidConnection) as ex:
            logger.exception('Job type trigger rule invalid')
            raise InvalidConfiguration('Job type trigger rule invalid: %s -> %s' % (result.name, unicode(ex)))
    remove_trigger_rule = 'trigger_rule' in job_type_dict and not job_type_dict['trigger_rule']

    # Extract the fields that should be updated as keyword arguments
    extra_fields = {}
    base_fields = {'name', 'version', 'interface', 'trigger_rule', 'error_mapping'}
    for key in job_type_dict:
        if key not in base_fields:
            if key in JobType.UNEDITABLE_FIELDS:
                warnings.append(ValidationWarning(
                    'read-only', 'Job type includes read-only field: %s -> %s' % (result.name, key)
                ))
            else:
                extra_fields[key] = job_type_dict[key]

    # Edit or create the associated job type model
    if job_type:
        try:
            JobType.objects.edit_job_type(result.id, interface, trigger_rule, remove_trigger_rule, error_mapping,
                                          **extra_fields)
        except (InvalidJobField, InvalidTriggerType, InvalidTriggerRule, InvalidConnection, InvalidDefinition) as ex:
            logger.exception('Job type edit failed')
            raise InvalidConfiguration('Unable to edit existing job type: %s -> %s' % (result.name, unicode(ex)))
    else:
        try:
            JobType.objects.create_job_type(result.name, result.version, interface, trigger_rule, error_mapping,
                                            **extra_fields)
        except (InvalidJobField, InvalidTriggerType, InvalidTriggerRule, InvalidConnection, InvalidDefinition) as ex:
            logger.exception('Job type create failed')
            raise InvalidConfiguration('Unable to create new job type: %s -> %s' % (result.name, unicode(ex)))
    return warnings


def _import_error(error_dict, error=None):
    '''Attempts to apply the given error configuration to the system.

    Note that proper model locking must be performed before calling this method.

    :param error_dict: A dictionary of error configuration changes to import.
    :type error_dict: dict
    :param error: The existing error model to update if applicable.
    :type error: :class:`error.models.Error`
    :returns: A list of warnings discovered during import.
    :rtype: list[:class:`port.schema.ValidationWarning`]

    :raises :class:`port.schema.InvalidConfiguration`: If any part of the configuration violates the specification.
    '''
    warnings = []

    # Parse the JSON content and merge the fields into a model
    error_serializer = serializers.ConfigurationErrorSerializer(error, data=error_dict)
    if not error_serializer.is_valid():
        raise InvalidConfiguration('Invalid error schema: %s -> %s' % (error_dict['name'], error_serializer.errors))
    result = error_serializer.object

    # Importing system-level errors is not allowed
    if result.category == 'SYSTEM':
        raise InvalidConfiguration('System errors cannot be imported: %s' % result.name)

    result.save()
    return warnings
