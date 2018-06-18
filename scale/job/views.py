from __future__ import unicode_literals

import logging

import rest_framework.status as status
from django.db import transaction
from django.http.response import Http404, HttpResponse
from django.utils import timezone
from job.seed.exceptions import InvalidSeedManifestDefinition
from rest_framework.generics import GenericAPIView, ListAPIView, ListCreateAPIView, RetrieveAPIView
from rest_framework.parsers import JSONParser
from rest_framework.renderers import StaticHTMLRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

import trigger.handler as trigger_handler
from job.configuration.data.exceptions import InvalidConnection
from job.configuration.exceptions import InvalidJobConfiguration
from job.configuration.interface.error_interface import ErrorInterface
from job.configuration.interface.exceptions import InvalidInterfaceDefinition
from job.configuration.interface.job_interface import JobInterface
from job.configuration.json.job_config_2_0 import JobConfigurationV2
from job.deprecation import JobInterfaceSunset
from job.exceptions import InvalidJobField
from job.messages.cancel_jobs_bulk import create_cancel_jobs_bulk_message
from job.serializers import (JobDetailsSerializer, JobSerializer, JobTypeDetailsSerializer,
                             JobTypeFailedStatusSerializer, JobTypeSerializer, JobTypePendingStatusSerializer,
                             JobTypeRunningStatusSerializer, JobTypeStatusSerializer, JobUpdateSerializer,
                             JobWithExecutionSerializer, JobExecutionSerializer, JobExecutionDetailsSerializer,
                             JobDetailsSerializerV5, JobExecutionSerializerV5, JobExecutionDetailsSerializerV5,
                             JobSerializerV5, JobTypeDetailsSerializerV5, JobTypeSerializerV5, JobUpdateSerializerV5)
from messaging.manager import CommandMessageManager
from models import Job, JobExecution, JobInputFile, JobType
from node.resources.exceptions import InvalidResources
from node.resources.json.resources import Resources
from queue.messages.requeue_jobs_bulk import create_requeue_jobs_bulk_message
from queue.models import Queue
from storage.models import ScaleFile
from storage.serializers import ScaleFileSerializerV5
from trigger.configuration.exceptions import InvalidTriggerRule, InvalidTriggerType, InvalidTriggerMissingConfiguration
import util.rest as rest_util
from util.rest import BadParameter
from vault.exceptions import InvalidSecretsConfiguration

logger = logging.getLogger(__name__)


class JobTypesView(ListCreateAPIView):
    """This view is the endpoint for retrieving the list of all job types."""
    queryset = JobType.objects.all()

    #serializer_class = JobTypeSerializer

    # TODO: remove this class and un-comment serializer declaration when REST API v5 is removed
    def get_serializer_class(self):
        """Returns the appropriate serializer based off the requests version of the REST API. """

        if self.request.version == 'v6':
            return JobTypeSerializer
        else:
            return JobTypeSerializerV5

    def list(self, request):
        """Retrieves the list of all job types and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """


        if self.request.version == 'v6':
            return self.list_v6(request)
        else:
            return self.list_v5(request)


    def list_v5(self, request):
        """Retrieves the list of all job types and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        names = rest_util.parse_string_list(request, 'name', required=False)
        categories = rest_util.parse_string_list(request, 'category', required=False)
        is_active = rest_util.parse_bool(request, 'is_active', default_value=True)
        is_operational = rest_util.parse_bool(request, 'is_operational', required=False)
        order = rest_util.parse_string_list(request, 'order', ['name', 'version'])

        job_types = JobType.objects.get_job_types(started=started, ended=ended, names=names, categories=categories,
                                                  is_active=is_active, is_operational=is_operational, order=order)

        page = self.paginate_queryset(job_types)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


    def list_v6(self, request):
        """Retrieves the list of all job types and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        names = rest_util.parse_string_list(request, 'name', required=False)
        is_active = rest_util.parse_bool(request, 'is_active', default_value=True)
        is_operational = rest_util.parse_bool(request, 'is_operational', required=False)
        order = rest_util.parse_string_list(request, 'order', ['name', 'version'])

        job_types = JobType.objects.get_job_types(started=started, ended=ended, names=names,
                                                  is_active=is_active, is_operational=is_operational, order=order)

        page = self.paginate_queryset(job_types)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request):
        """Creates a new job type and returns a link to the detail URL

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        # TODO: remove conditional and un-comment serializer instantiation when REST API v5 is removed
        # serializer = JobTypeDetailsSerializer(job_type)
        if self.request.version == 'v6':
            return self.create_v6(request)
        else:
            return self.create_v5(request)

    def create_v5(self, request):
        """Creates a legacy job type and returns a link to the detail URL

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        # No longer required as of Seed adoption.
        name = rest_util.parse_string(request, 'name', required=False)
        version = rest_util.parse_string(request, 'version', required=False)
        title = None

        # Validate the job interface / manifest
        interface_dict = rest_util.parse_dict(request, 'interface')
        interface = None

        try:
            if interface_dict:
                interface = JobInterfaceSunset.create(interface_dict)
        except InvalidInterfaceDefinition as ex:
            raise BadParameter('Job type interface invalid: %s' % unicode(ex))

        # Validate the job configuration and pull out secrets
        configuration_dict = rest_util.parse_dict(request, 'configuration', required=False)
        configuration = None
        secrets = None
        try:
            if configuration_dict:
                configuration = JobConfigurationV2(configuration_dict)
                secrets = configuration.get_secret_settings(interface.get_dict())
                configuration.validate(interface.get_dict())
        except InvalidJobConfiguration as ex:
            raise BadParameter('Job type configuration invalid: %s' % unicode(ex))

        # Validate the error mapping
        error_dict = rest_util.parse_dict(request, 'error_mapping', required=False)
        error_mapping = None
        try:
            if error_dict:
                error_mapping = ErrorInterface(error_dict)
                error_mapping.validate()
        except InvalidInterfaceDefinition as ex:
            raise BadParameter('Job type error mapping invalid: %s' % unicode(ex))

        # Validate the custom resources
        resources_dict = rest_util.parse_dict(request, 'custom_resources', required=False)
        custom_resources = None
        try:
            if resources_dict:
                custom_resources = Resources(resources_dict)
        except InvalidResources as ex:
            raise BadParameter('Job type custom resources invalid: %s' % unicode(ex))

        # Check for optional trigger rule parameters
        trigger_rule_dict = rest_util.parse_dict(request, 'trigger_rule', required=False)
        if (('type' in trigger_rule_dict and 'configuration' not in trigger_rule_dict) or
                ('type' not in trigger_rule_dict and 'configuration' in trigger_rule_dict)):
            raise BadParameter('Trigger type and configuration are required together.')
        is_active = trigger_rule_dict['is_active'] if 'is_active' in trigger_rule_dict else True

        # Attempt to look up the trigger handler for the type
        rule_handler = None
        if trigger_rule_dict and 'type' in trigger_rule_dict:
            try:
                rule_handler = trigger_handler.get_trigger_rule_handler(trigger_rule_dict['type'])
            except InvalidTriggerType as ex:
                logger.exception('Invalid trigger type for new job type: %s', name)
                raise BadParameter(unicode(ex))

        # Extract the fields that should be updated as keyword arguments
        extra_fields = {}
        # TODO: Remove interface from base_fields in v6
        base_fields = {'name', 'version', 'interface', 'manifest', 'trigger_rule', 'error_mapping', 'custom_resources',
                       'configuration'}
        for key, value in request.data.iteritems():
            if key not in base_fields and key not in JobType.UNEDITABLE_FIELDS:
                extra_fields[key] = value
        if title:
            extra_fields['title'] = title
        # Change mem_required to mem_const_required, TODO: remove once mem_required field is removed from REST API
        if 'mem_required' in extra_fields:
            extra_fields['mem_const_required'] = extra_fields['mem_required']
            del extra_fields['mem_required']

        try:
            with transaction.atomic():

                # Attempt to create the trigger rule
                trigger_rule = None
                if rule_handler and 'configuration' in trigger_rule_dict:
                    trigger_rule = rule_handler.create_trigger_rule(trigger_rule_dict['configuration'], name,
                                                                    is_active)
                # Create the job type
                job_type = JobType.objects.create_legacy_job_type(name=name, version=version, interface=interface,
                                                                  trigger_rule=trigger_rule, error_mapping=error_mapping,
                                                                  custom_resources=custom_resources,
                                                                  configuration=configuration, secrets=secrets,
                                                                  **extra_fields)

        except (InvalidJobField, InvalidTriggerType, InvalidTriggerRule, InvalidConnection,
                InvalidSecretsConfiguration, ValueError) as ex:
            logger.exception('Unable to create new job type: %s', name)
            raise BadParameter(unicode(ex))

        # Fetch the full job type with details
        try:
            job_type = JobType.objects.get_details(job_type.id)
        except JobType.DoesNotExist:
            raise Http404

        url = reverse('job_type_details_view', args=[job_type.id], request=request)

        serializer = JobTypeDetailsSerializerV5(job_type)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=dict(location=url))

    def create_v6(self, request):
        """Creates a Seed job type and returns a link to the detail URL

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        # Validate the job interface / manifest
        manifest_dict = rest_util.parse_dict(request, 'manifest', required=True)

        # Validate the job configuration and pull out secrets
        configuration_dict = rest_util.parse_dict(request, 'configuration', required=False)

        # Check for optional trigger rule parameters
        trigger_rule_dict = rest_util.parse_dict(request, 'trigger_rule', required=False)

        # Extract the fields that should be updated as keyword arguments
        extra_fields = {}
        base_fields = JobType.BASE_FIELDS_V6
        for key, value in request.data.iteritems():
            if key not in base_fields and key not in JobType.UNEDITABLE_FIELDS_V6:
                extra_fields[key] = value

        try:
            with transaction.atomic():

                # Create the job type
                job_type = JobType.objects.create_seed_job_type(manifest_dict=manifest_dict,
                                                                trigger_rule_dict=trigger_rule_dict,
                                                                configuration_dict=configuration_dict,
                                                                **extra_fields)

        except (InvalidJobField, InvalidTriggerType, InvalidTriggerRule, InvalidTriggerMissingConfiguration,
                InvalidConnection, InvalidSecretsConfiguration, ValueError) as ex:
            message = 'Unable to create new job type'
            logger.exception(message)
            raise BadParameter('%s: %s' % (message, unicode(ex)))
        except InvalidSeedManifestDefinition as ex:
            message = 'Job type interface invalid'
            logger.exception(message)
            raise BadParameter('%s: %s' % (message, unicode(ex)))
        except InvalidJobConfiguration as ex:
            message = 'Job type configuration invalid'
            logger.exception(message)
            raise BadParameter('%s: %s' % (message, unicode(ex)))
        except InvalidResources as ex:
            message = 'Job type custom resources invalid'
            logger.exception(message)
            raise BadParameter('%s: %s' % (message, unicode(ex)))

        # Fetch the full job type with details
        try:
            job_type = JobType.objects.get_details(job_type.id)
        except JobType.DoesNotExist:
            raise Http404

        url = reverse('job_type_details_view', args=[job_type.id], request=request)
        serializer = JobTypeDetailsSerializer(job_type)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=dict(location=url))


class JobTypeDetailsView(GenericAPIView):
    """This view is the endpoint for retrieving/updating details of a job type."""
    queryset = JobType.objects.all()

    # TODO: remove this class and un-comment serializer declaration when REST API v5 is removed
    # serializer_class =     JobTypeDetailsSerializer
    def get_serializer_class(self):
        """Returns the appropriate serializer based off the requests version of the REST API. """

        if self.request.version == 'v6':
            return JobTypeDetailsSerializer
        else:
            return JobTypeDetailsSerializerV5

    def get(self, request, job_type_id):
        """Retrieves the details for a job type and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param job_type_id: The id of the job type
        :type job_type_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        try:
            job_type = JobType.objects.get_details(job_type_id)
        except JobType.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(job_type)
        return Response(serializer.data)

    def patch(self, request, job_type_id):
        """Edits an existing job type and returns the updated details

        :param request: the HTTP PATCH request
        :type request: :class:`rest_framework.request.Request`
        :param job_type_id: The ID for the job type.
        :type job_type_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if self.request.version == 'v6':
            return self.patch_v6(request, job_type_id)
        else:
            return self.patch_v5(request, job_type_id)

    def patch_v5(self, request, job_type_id):
        """Edits an existing legacy job type and returns the updated details

        :param request: the HTTP PATCH request
        :type request: :class:`rest_framework.request.Request`
        :param job_type_id: The ID for the job type.
        :type job_type_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        # Validate the job interface
        interface_dict = rest_util.parse_dict(request, 'interface', required=False)
        interface = None
        try:
            if interface_dict:
                interface = JobInterface(interface_dict)
        except InvalidInterfaceDefinition as ex:
            raise BadParameter('Job type interface invalid: %s' % unicode(ex))

        # Validate the job configuration and pull out secrets
        configuration_dict = rest_util.parse_dict(request, 'configuration', required=False)
        configuration = None
        secrets = None
        try:
            if configuration_dict:
                configuration = JobConfigurationV2(configuration_dict)
                if interface:
                    secrets = configuration.get_secret_settings(interface.get_dict())
                    configuration.validate(interface.get_dict())
                else:
                    stored_interface = JobType.objects.values_list('interface', flat=True).get(pk=job_type_id)
                    secrets = configuration.get_secret_settings(stored_interface)
                    configuration.validate(stored_interface)
        except InvalidJobConfiguration as ex:
            raise BadParameter('Job type configuration invalid: %s' % unicode(ex))

        # Validate the error mapping
        error_dict = rest_util.parse_dict(request, 'error_mapping', required=False)
        error_mapping = None
        try:
            if error_dict:
                error_mapping = ErrorInterface(error_dict)
                error_mapping.validate()
        except InvalidInterfaceDefinition as ex:
            raise BadParameter('Job type error mapping invalid: %s' % unicode(ex))

        # Validate the custom resources
        resources_dict = rest_util.parse_dict(request, 'custom_resources', required=False)
        custom_resources = None
        try:
            if resources_dict:
                custom_resources = Resources(resources_dict)
        except InvalidResources as ex:
            raise BadParameter('Job type custom resources invalid: %s' % unicode(ex))

        # Check for optional trigger rule parameters
        trigger_rule_dict = rest_util.parse_dict(request, 'trigger_rule', required=False)
        if (('type' in trigger_rule_dict and 'configuration' not in trigger_rule_dict) or
                ('type' not in trigger_rule_dict and 'configuration' in trigger_rule_dict)):
            raise BadParameter('Trigger type and configuration are required together.')
        is_active = trigger_rule_dict['is_active'] if 'is_active' in trigger_rule_dict else True
        remove_trigger_rule = rest_util.has_params(request, 'trigger_rule') and not trigger_rule_dict

        # Fetch the current job type model
        try:
            job_type = JobType.objects.select_related('trigger_rule').get(pk=job_type_id)
        except JobType.DoesNotExist:
            raise Http404

        # Attempt to look up the trigger handler for the type
        rule_handler = None
        if trigger_rule_dict and 'type' in trigger_rule_dict:
            try:
                rule_handler = trigger_handler.get_trigger_rule_handler(trigger_rule_dict['type'])
            except InvalidTriggerType as ex:
                logger.exception('Invalid trigger type for job type: %i', job_type_id)
                raise BadParameter(unicode(ex))

        # Extract the fields that should be updated as keyword arguments
        extra_fields = {}
        # TODO: Remove interface from base_fields in v6
        base_fields = {'name', 'version', 'interface', 'manifest', 'trigger_rule', 'error_mapping', 'custom_resources',
                       'configuration'}
        for key, value in request.data.iteritems():
            if key not in base_fields and key not in JobType.UNEDITABLE_FIELDS:
                extra_fields[key] = value
        # Change mem_required to mem_const_required, TODO: remove once mem_required field is removed from REST API
        if 'mem_required' in extra_fields:
            extra_fields['mem_const_required'] = extra_fields['mem_required']
            del extra_fields['mem_required']

        try:
            from recipe.configuration.definition.exceptions import InvalidDefinition
        except:
            logger.exception('Failed to import higher level recipe application.')
            pass

        try:
            with transaction.atomic():

                # Attempt to create the trigger rule
                trigger_rule = None
                if rule_handler and 'configuration' in trigger_rule_dict:
                    trigger_rule = rule_handler.create_trigger_rule(trigger_rule_dict['configuration'],
                                                                    job_type.name, is_active)

                # Update the active state separately if that is only given trigger field
                if not trigger_rule and job_type.trigger_rule and 'is_active' in trigger_rule_dict:
                    job_type.trigger_rule.is_active = is_active
                    job_type.trigger_rule.save()

                # Edit the job type
                JobType.objects.edit_legacy_job_type(job_type_id=job_type_id, interface=interface,
                                                     trigger_rule=trigger_rule, remove_trigger_rule=remove_trigger_rule,
                                                     error_mapping=error_mapping, custom_resources=custom_resources,
                                                     configuration=configuration, secrets=secrets, **extra_fields)
        except (InvalidJobField, InvalidTriggerType, InvalidTriggerRule, InvalidConnection, InvalidDefinition,
                InvalidSecretsConfiguration, ValueError, InvalidInterfaceDefinition) as ex:
            logger.exception('Unable to update job type: %i', job_type_id)
            raise BadParameter(unicode(ex))

        # Fetch the full job type with details
        try:
            job_type = JobType.objects.get_details(job_type.id)
        except JobType.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(job_type)
        return Response(serializer.data)

    def patch_v6(self, request, job_type_id):
        """Edits an existing Seed job type and returns the updated details

        :param request: the HTTP PATCH request
        :type request: :class:`rest_framework.request.Request`
        :param job_type_id: The ID for the job type.
        :type job_type_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        # Validate the job interface / manifest
        manifest_dict = rest_util.parse_dict(request, 'manifest', required=False)

        # Validate the job configuration and pull out secrets
        configuration_dict = rest_util.parse_dict(request, 'configuration', required=False)

        # Check for optional trigger rule parameters
        trigger_rule_dict = rest_util.parse_dict(request, 'trigger_rule', required=False)
        remove_trigger_rule = rest_util.has_params(request, 'trigger_rule') and not trigger_rule_dict

        # Extract the fields that should be updated as keyword arguments
        extra_fields = {}
        restricted_fields = []
        for key, value in request.data.iteritems():
            if key in JobType.UNEDITABLE_FIELDS_V6:
                restricted_fields.append(key)
            if key not in JobType.BASE_FIELDS_V6:
                extra_fields[key] = value

        # Fail request if an attempt was made to manipulate restricted fields
        if restricted_fields:
            raise BadParameter("Attempt was made to edit restricted fields: %s" % ','.join(restricted_fields))

        try:
            with transaction.atomic():

                # Create the job type
                job_type = JobType.objects.edit_seed_job_type(job_type_id=job_type_id,
                                                              manifest_dict=manifest_dict,
                                                              trigger_rule_dict=trigger_rule_dict,
                                                              configuration_dict=configuration_dict,
                                                              remove_trigger_rule=remove_trigger_rule,
                                                              **extra_fields)

        except (InvalidJobField, InvalidTriggerType, InvalidTriggerRule, InvalidTriggerMissingConfiguration,
                InvalidConnection, InvalidSecretsConfiguration, ValueError) as ex:
            message = 'Unable to edit job type'
            logger.exception(message)
            raise BadParameter('%s: %s' % (message, unicode(ex)))
        except InvalidSeedManifestDefinition as ex:
            message = 'Job type interface invalid'
            logger.exception(message)
            raise BadParameter('%s: %s' % (message, unicode(ex)))
        except InvalidJobConfiguration as ex:
            message = 'Job type configuration invalid'
            logger.exception(message)
            raise BadParameter('%s: %s' % (message, unicode(ex)))
        except InvalidResources as ex:
            message = 'Job type resources invalid'
            logger.exception(message)
            raise BadParameter('%s: %s' % (message, unicode(ex)))

        # Fetch the full job type with details
        try:
            job_type = JobType.objects.get_details(job_type_id)
        except JobType.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(job_type)
        return Response(serializer.data)


class JobTypesValidationView(APIView):
    """This view is the endpoint for validating a new job type before attempting to actually create it"""
    queryset = JobType.objects.all()

    def post(self, request):
        """Validates a new job type and returns any warnings discovered

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        name = rest_util.parse_string(request, 'name', required=False)
        version = rest_util.parse_string(request, 'version', required=False)

        # Validate the job interface
        # TODO: Remove all reference to interface in models and views come v6 API
        interface_dict = manifest_dict = rest_util.parse_dict(request, 'manifest', required=False)
        if not interface_dict:
            interface_dict = rest_util.parse_dict(request, 'interface')

        interface = None

        try:
            if interface_dict:
                interface = JobInterfaceSunset.create(interface_dict)
        except InvalidInterfaceDefinition as ex:
            raise BadParameter('Job type interface invalid: %s' % unicode(ex))

        # Pull down top-level fields from Seed Interface
        if manifest_dict:
            if not name:
                name = interface.get_name()

            if not version:
                version = interface.get_job_version()

        # Validate the job configuration
        configuration_dict = rest_util.parse_dict(request, 'configuration', required=False)
        configuration = None
        try:
            configuration = JobConfigurationV2(configuration_dict)
        except InvalidJobConfiguration as ex:
            raise BadParameter('Job type configuration invalid: %s' % unicode(ex))

        # Validate the error mapping
        error_dict = rest_util.parse_dict(request, 'error_mapping', required=False)
        error_mapping = None
        try:
            if error_dict:
                error_mapping = ErrorInterface(error_dict)
        except InvalidInterfaceDefinition as ex:
            raise BadParameter('Job type error mapping invalid: %s' % unicode(ex))

        # Validate the custom resources
        resources_dict = rest_util.parse_dict(request, 'custom_resources', required=False)
        try:
            if resources_dict:
                Resources(resources_dict)
        except InvalidResources as ex:
            raise BadParameter('Job type custom resources invalid: %s' % unicode(ex))

        # Check for optional trigger rule parameters
        trigger_rule_dict = rest_util.parse_dict(request, 'trigger_rule', required=False)
        if (('type' in trigger_rule_dict and 'configuration' not in trigger_rule_dict) or
                ('type' not in trigger_rule_dict and 'configuration' in trigger_rule_dict)):
            raise BadParameter('Trigger type and configuration are required together.')

        # Attempt to look up the trigger handler for the type
        rule_handler = None
        if trigger_rule_dict and 'type' in trigger_rule_dict:
            try:
                rule_handler = trigger_handler.get_trigger_rule_handler(trigger_rule_dict['type'])
            except InvalidTriggerType as ex:
                logger.exception('Invalid trigger type for job validation: %s', name)
                raise BadParameter(unicode(ex))

        # Attempt to look up the trigger rule configuration
        trigger_config = None
        if rule_handler and 'configuration' in trigger_rule_dict:
            try:
                trigger_config = rule_handler.create_configuration(trigger_rule_dict['configuration'])
            except InvalidTriggerRule as ex:
                logger.exception('Invalid trigger rule configuration for job validation: %s', name)
                raise BadParameter(unicode(ex))

        try:
            from recipe.configuration.definition.exceptions import InvalidDefinition
        except:
            logger.exception('Failed to import higher level recipe application.')
            pass

        # Validate the job type
        try:
            warnings = JobType.objects.validate_job_type(name=name, version=version, interface=interface,
                                                         error_mapping=error_mapping, trigger_config=trigger_config,
                                                         configuration=configuration)
        except (InvalidInterfaceDefinition, InvalidDefinition, InvalidTriggerType, InvalidTriggerRule) as ex:
            logger.exception('Unable to validate new job type: %s', name)
            raise BadParameter(unicode(ex))

        results = [{'id': w.key, 'details': w.details} for w in warnings]
        return Response({'warnings': results})


class JobTypesPendingView(ListAPIView):
    """This view is the endpoint for retrieving the status of all currently pending job types."""
    queryset = JobType.objects.all()
    serializer_class = JobTypePendingStatusSerializer

    def list(self, request):
        """Retrieves the current status of pending job types and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        # Get all the pending job types with statistics
        pending_status = JobType.objects.get_pending_status()

        # Wrap the response with paging information
        page = self.paginate_queryset(pending_status)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class JobTypesRunningView(ListAPIView):
    """This view is the endpoint for retrieving the status of all currently running job types."""
    queryset = JobType.objects.all()
    serializer_class = JobTypeRunningStatusSerializer

    def list(self, request):
        """Retrieves the current status of running job types and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        # Get all the running job types with statistics
        running_status = JobType.objects.get_running_status()

        # Wrap the response with paging information
        page = self.paginate_queryset(running_status)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class JobTypesSystemFailuresView(ListAPIView):
    """This view is the endpoint for viewing system errors organized by job type."""
    queryset = JobType.objects.all()
    serializer_class = JobTypeFailedStatusSerializer

    def list(self, request):
        """Retrieves the job types that have failed with system errors and returns them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        # Get all the failed job types with statistics
        failed_status = JobType.objects.get_failed_status()

        # Wrap the response with paging information
        page = self.paginate_queryset(failed_status)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class JobTypesStatusView(ListAPIView):
    """This view is the endpoint for retrieving overall job type status information."""
    queryset = JobType.objects.all()
    serializer_class = JobTypeStatusSerializer

    def list(self, request):
        """Retrieves the list of all job types with status and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        # Get a list of all job type status counts
        started = rest_util.parse_timestamp(request, 'started', 'PT3H0M0S')
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        is_operational = rest_util.parse_bool(request, 'is_operational', required=False)

        job_type_statuses = JobType.objects.get_status(started=started, ended=ended, is_operational=is_operational)

        page = self.paginate_queryset(job_type_statuses)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class JobsView(ListAPIView):
    """This view is the endpoint for retrieving a list of all available jobs."""
    queryset = Job.objects.all()

    # TODO: remove this class and un-comment serializer declaration when REST API v5 is removed
    # serializer_class = JobSerializer
    def get_serializer_class(self):
        """Returns the appropriate serializer based off the requests version of the REST API. """

        if self.request.version == 'v6':
            return JobSerializer
        else:
            return JobSerializerV5
    
    def list(self, request):
        """Retrieves jobs and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        statuses = rest_util.parse_string_list(request, 'status', required=False)
        job_ids = rest_util.parse_int_list(request, 'job_id', required=False)
        job_type_ids = rest_util.parse_int_list(request, 'job_type_id', required=False)
        job_type_names = rest_util.parse_string_list(request, 'job_type_name', required=False)
        job_type_categories = rest_util.parse_string_list(request, 'job_type_category', required=False)
        batch_ids = rest_util.parse_int_list(request, 'batch_id', required=False)
        error_categories = rest_util.parse_string_list(request, 'error_category', required=False)
        include_superseded = rest_util.parse_bool(request, 'include_superseded', required=False)

        order = rest_util.parse_string_list(request, 'order', required=False)

        jobs = Job.objects.get_jobs(started=started, ended=ended, statuses=statuses, job_ids=job_ids,
                                    job_type_ids=job_type_ids, job_type_names=job_type_names,
                                    job_type_categories=job_type_categories, batch_ids=batch_ids,
                                    error_categories=error_categories, include_superseded=include_superseded,
                                    order=order)

        page = self.paginate_queryset(jobs)
        serializer = self.get_serializer(page, many=True)

        return self.get_paginated_response(serializer.data)


class CancelJobsView(GenericAPIView):
    """This view is the endpoint for canceling jobs"""
    parser_classes = (JSONParser,)
    queryset = Job.objects.all()
    serializer_class = JobSerializer

    def post(self, request):
        """Submit command message to cancel jobs that fit the given filter criteria

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :returns: the HTTP response to send back to the user
        """

        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        error_categories = rest_util.parse_string_list(request, 'error_categories', required=False)
        error_ids = rest_util.parse_int_list(request, 'error_ids', required=False)
        job_ids = rest_util.parse_int_list(request, 'job_ids', required=False)
        job_status = rest_util.parse_string(request, 'status', required=False)
        job_type_ids = rest_util.parse_int_list(request, 'job_type_ids', required=False)

        # Create and send message
        msg = create_cancel_jobs_bulk_message(started=started, ended=ended, error_categories=error_categories,
                                              error_ids=error_ids, job_ids=job_ids, job_type_ids=job_type_ids,
                                              status=job_status)
        CommandMessageManager().send_messages([msg])

        return Response(status=status.HTTP_202_ACCEPTED)


class RequeueJobsView(GenericAPIView):
    """This view is the endpoint for re-queuing jobs that have failed or been canceled"""
    parser_classes = (JSONParser,)
    queryset = Job.objects.all()
    serializer_class = JobSerializer

    def post(self, request):
        """Submit command message to re-queue jobs that fit the given filter criteria

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :returns: the HTTP response to send back to the user
        """

        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        error_categories = rest_util.parse_string_list(request, 'error_categories', required=False)
        error_ids = rest_util.parse_int_list(request, 'error_ids', required=False)
        job_ids = rest_util.parse_int_list(request, 'job_ids', required=False)
        job_status = rest_util.parse_string(request, 'status', required=False)
        job_type_ids = rest_util.parse_int_list(request, 'job_type_ids', required=False)
        priority = rest_util.parse_int(request, 'priority', required=False)

        # Create and send message
        msg = create_requeue_jobs_bulk_message(started=started, ended=ended, error_categories=error_categories,
                                               error_ids=error_ids, job_ids=job_ids, job_type_ids=job_type_ids,
                                               priority=priority, status=job_status)
        CommandMessageManager().send_messages([msg])

        return Response(status=status.HTTP_202_ACCEPTED)


class JobDetailsView(GenericAPIView):
    """This view is the endpoint for retrieving details about a single job."""
    queryset = Job.objects.all()

    # TODO: remove this class and un-comment serializer declaration when REST API v5 is removed
    # serializer_class = JobExecutionSerializer
    def get_serializer_class(self):
        """Returns the appropriate serializer based off the requests version of the REST API. """

        if self.request.version == 'v6':
            return JobDetailsSerializer
        else:
            return JobDetailsSerializerV5
    
    def get(self, request, job_id):
        """Retrieves jobs and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param job_id: The ID for the job.
        :type job_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        try:
            # TODO: remove this check when REST API v5 is removed
            if request.version == 'v6':
                job = Job.objects.get_details(job_id)
            else:
                job = Job.objects.get_details_v5(job_id)
        except Job.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(job)
        return Response(serializer.data)

    def patch(self, request, job_id):
        """Modify job info with a subset of fields

        :param request: the HTTP PATCH request
        :type request: :class:`rest_framework.request.Request`
        :param job_id: The ID for the job.
        :type job_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        # Validate that no extra fields are included
        rest_util.check_update(request, ['status'])

        # Validate JSON
        status_code = rest_util.parse_string(request, 'status')
        if status_code != 'CANCELED':
            raise rest_util.BadParameter('Invalid or read-only status. Allowed values: CANCELED')

        try:
            Queue.objects.handle_job_cancellation(job_id, timezone.now())
            # TODO: remove this check when REST API v5 is removed
            if request.version == 'v6':
                job = Job.objects.get_details(job_id)
            else:
                job = Job.objects.get_details_v5(job_id)
        except (Job.DoesNotExist, JobExecution.DoesNotExist):
            raise Http404

        serializer = self.get_serializer(job)
        return Response(serializer.data)

class JobInputFilesView(ListAPIView):
    """This is the endpoint for retrieving details about input files associated with a job."""
    queryset = JobInputFile.objects.all()
    serializer_class = ScaleFileSerializerV5

    def get(self, request, job_id):
        """Retrieve detailed information about the input files for a job

        -*-*-
        parameters:
          - name: job_id
            in: path
            description: The ID of the job the file is associated with
            required: true
            example: 67302
          - name: started
            in: query
            description: The start time of a start/end time range
            required: false
            example: 2016-01-01T00:00:00Z
          - name: ended
            in: query
            description: The end time of a start/end time range
            required: false
            example: 2016-01-02T00:00:00Z
          - name: time_field
            in: query
            description: 'The database time field to apply `started` and `ended` time filters
                          [Valid fields: `source`, `data`, `last_modified`]'
            required: false
            example: source
          - name: file_name
            in: query
            description: The name of a specific file in Scale
            required: false
            example: some_file_i_need_to_find.zip
          - name: job_input
            in: query
            description: The name of the input the file is passed to in a job
            required: false
            example: input_1
        responses:
          '200':
            description: A JSON list of files with metadata
        -*-*-

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param job_id: The ID for the job.
        :type job_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)
        time_field = rest_util.parse_string(request, 'time_field', required=False,
                                            accepted_values=ScaleFile.VALID_TIME_FIELDS)
        file_name = rest_util.parse_string(request, 'file_name', required=False)
        job_input = rest_util.parse_string(request, 'job_input', required=False)

        files = JobInputFile.objects.get_job_input_files(job_id, started=started, ended=ended, time_field=time_field,
                                                         file_name=file_name, job_input=job_input)

        page = self.paginate_queryset(files)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class JobUpdatesView(ListAPIView):
    """This view is the endpoint for retrieving job updates over a given time range."""
    queryset = Job.objects.all()

    # TODO: remove when REST API v5 is removed
    def get_serializer_class(self):
        """Returns the appropriate serializer based off the requests version of the REST API. """

        if self.request.version == 'v6':
            return JobUpdateSerializer
        return JobUpdateSerializerV5

    def get(self, request):
        """Retrieves the job updates for a given time range and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        statuses = rest_util.parse_string_list(request, 'status', required=False)
        job_type_ids = rest_util.parse_int_list(request, 'job_type_id', required=False)
        job_type_names = rest_util.parse_string_list(request, 'job_type_name', required=False)
        job_type_categories = rest_util.parse_string_list(request, 'job_type_category', required=False)
        include_superseded = rest_util.parse_bool(request, 'include_superseded', required=False)

        order = rest_util.parse_string_list(request, 'order', required=False)

        jobs = Job.objects.get_job_updates(started=started, ended=ended, statuses=statuses, job_type_ids=job_type_ids,
                                           job_type_names=job_type_names, job_type_categories=job_type_categories,
                                           include_superseded=include_superseded, order=order)

        page = self.paginate_queryset(jobs)
        Job.objects.populate_input_files(page)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

# TODO: remove when REST API v5 is removed
class JobsWithExecutionView(ListAPIView):
    """This view is the endpoint for viewing jobs and their associated latest execution"""
    queryset = Job.objects.all()
    serializer_class = JobWithExecutionSerializer

    def list(self, request):
        """Gets jobs and their associated latest execution

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version != 'v6':
            return self.list_v5(request)
        else:
            raise Http404

    def list_v5(self, request):
        """Gets jobs and their associated latest execution

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        statuses = rest_util.parse_string_list(request, 'status', required=False)
        job_ids = rest_util.parse_int_list(request, 'job_id', required=False)
        job_type_ids = rest_util.parse_int_list(request, 'job_type_id', required=False)
        job_type_names = rest_util.parse_string_list(request, 'job_type_name', required=False)
        job_type_categories = rest_util.parse_string_list(request, 'job_type_category', required=False)
        error_categories = rest_util.parse_string_list(request, 'error_category', required=False)
        include_superseded = rest_util.parse_bool(request, 'include_superseded', required=False)

        order = rest_util.parse_string_list(request, 'order', required=False)

        jobs = Job.objects.get_jobs(started=started, ended=ended, statuses=statuses, job_ids=job_ids,
                                    job_type_ids=job_type_ids, job_type_names=job_type_names,
                                    job_type_categories=job_type_categories, error_categories=error_categories,
                                    include_superseded=include_superseded, order=order)

        # Add the latest execution for each matching job
        page = self.paginate_queryset(jobs)
        job_exes_dict = JobExecution.objects.get_latest(page)
        for job in page:
            job.latest_job_exe = job_exes_dict[job.id] if job.id in job_exes_dict else None
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class JobExecutionsView(ListAPIView):
    """This view is the endpoint for viewing job executions and their associated job_type id, name, and version"""
    queryset = JobExecution.objects.all()

    # TODO: remove this class and un-comment serializer declaration when REST API v5 is removed
    # serializer_class = JobExecutionSerializer
    def get_serializer_class(self):
        """Returns the appropriate serializer based off the requests version of the REST API. """

        if self.request.version == 'v6':
            return JobExecutionSerializer
        else:
            return JobExecutionSerializerV5
    
    def list(self, request, job_id=None):
        """Gets job executions and their associated job_type id, name, and version

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param job_id: The ID for the job.
        :type job_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        # TODO: remove this check when REST API v5 is removed
        if not job_id:
            if request.version != 'v6':
                return self.list_v5(request)
            else:
                raise Http404
        else:
            started = rest_util.parse_timestamp(request, 'started', required=False)
            ended = rest_util.parse_timestamp(request, 'ended', required=False)
            rest_util.check_time_range(started, ended)

            statuses = rest_util.parse_string_list(request, 'status', required=False)
            node_ids = rest_util.parse_int_list(request, 'node_id', required=False)


            job_exes = JobExecution.objects.get_job_exes(job_id=job_id, started=started, ended=ended,
                                                         statuses=statuses, node_ids=node_ids)

            page = self.paginate_queryset(job_exes)
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

    # TODO: remove when REST API v5 is removed
    def list_v5(self, request):
        """Gets job executions and their associated job_type id, name, and version

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        job_statuses = rest_util.parse_string_list(request, 'status', required=False)
        job_type_ids = rest_util.parse_int_list(request, 'job_type_id', required=False)
        job_type_names = rest_util.parse_string_list(request, 'job_type_name', required=False)
        job_type_categories = rest_util.parse_string_list(request, 'job_type_category', required=False)

        node_ids = rest_util.parse_int_list(request, 'node_id', required=False)

        order = rest_util.parse_string_list(request, 'order', required=False)

        job_exes = JobExecution.objects.get_exes(started, ended, job_statuses, job_type_ids, job_type_names,
                                                 job_type_categories, node_ids, order)

        page = self.paginate_queryset(job_exes)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class JobExecutionDetailsView(RetrieveAPIView):
    """This view is the endpoint for viewing job execution detail"""
    queryset = JobExecution.objects.all()

    # TODO: remove this class and un-comment serializer declaration when REST API v5 is removed
    # serializer_class = JobExecutionDetailsSerializer
    def get_serializer_class(self):
        """Returns the appropriate serializer based off the requests version of the REST API. """

        if self.request.version == 'v6':
            return JobExecutionDetailsSerializer
        else:
            return JobExecutionDetailsSerializerV5
    
    def retrieve(self, request, job_id, exe_num=None):
        """Gets job execution and associated job_type id, name, and version

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param job_id: The ID for the job.
        :type job_id: int encoded as a str
        :param exe_num: the execution number
        :type exe_num: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        # TODO: remove this check when REST API v5 is removed
        if not exe_num:
            if request.version != 'v6':
                job_exe_id = job_id
                return self.retrieve_v5(request, job_exe_id)
            else:
                raise Http404
        else:
            try:
                job_exe = JobExecution.objects.get_job_exe_details(job_id=job_id, exe_num=exe_num)
            except JobExecution.DoesNotExist:
                raise Http404

            serializer = self.get_serializer(job_exe)
            return Response(serializer.data)

    # TODO: remove when REST API v5 is removed
    def retrieve_v5(self, request, job_exe_id):
        """Gets job execution and associated job_type id, name, and version

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param job_exe_id: the job execution id
        :type job_exe_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        try:
            job_exe = JobExecution.objects.get_details(job_exe_id)
        except JobExecution.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(job_exe)
        return Response(serializer.data)


class JobExecutionSpecificLogView(RetrieveAPIView):
    """This view is the endpoint for viewing the text of specific job execution logs"""
    renderer_classes = (JSONRenderer, rest_util.PlainTextRenderer, StaticHTMLRenderer)

    def retrieve(self, request, job_exe_id, log_id):
        """Gets job execution log specified.

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param job_exe_id: the job execution id
        :type job_exe_id: int
        :param log_id: the log name to get (stdout, stderr, or combined)
        :type log_id: str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        try:
            job_exe = JobExecution.objects.get_logs(job_exe_id)
        except JobExecution.DoesNotExist:
            raise Http404

        include_stdout = include_stderr = True
        if log_id == 'stdout':
            include_stderr = False
        elif log_id == 'stderr':
            include_stdout = False

        started = rest_util.parse_timestamp(request, 'started', required=False)

        if request.accepted_renderer.format == 'json':
            logs, last_modified = job_exe.get_log_json(include_stdout, include_stderr, started)
        elif request.accepted_renderer.format == 'txt':
            logs, last_modified = job_exe.get_log_text(include_stdout, include_stderr, started, False)
        elif request.accepted_renderer.format == 'html':
            logs, last_modified = job_exe.get_log_text(include_stdout, include_stderr, started, True)
            if logs is not None:
                logs = '<html><head><style>.stdout {} .stderr {color: red;}</style></head><body>' + logs + '</body></html>'
        else:
            return HttpResponse('%s is not a valid content type request.' % request.accepted_renderer.content_type,
                                content_type='text/plain', status=406)

        if logs is None:
            rsp = HttpResponse(status=204)
        else:
            rsp = Response(data=logs)
        return rsp
