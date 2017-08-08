from __future__ import unicode_literals

import logging

import rest_framework.status as status
from django.db import transaction
from django.http.response import Http404, HttpResponse
from django.utils import timezone
from rest_framework.generics import GenericAPIView, ListAPIView, ListCreateAPIView, RetrieveAPIView
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
from job.configuration.json.job.job_config import JobConfiguration
from job.exceptions import InvalidJobField
from job.serializers import (JobDetailsSerializer, JobSerializer, JobTypeDetailsSerializer,
                             JobTypeFailedStatusSerializer, JobTypeSerializer, JobTypePendingStatusSerializer,
                             JobTypeRunningStatusSerializer, JobTypeStatusSerializer, JobUpdateSerializer,
                             JobWithExecutionSerializer, JobExecutionSerializer,
                             JobExecutionDetailsSerializer)
from models import Job, JobExecution, JobType
from node.resources.exceptions import InvalidResources
from node.resources.json.resources import Resources
from queue.models import Queue
from trigger.configuration.exceptions import InvalidTriggerRule, InvalidTriggerType
import util.rest as rest_util
from util.rest import BadParameter
from vault.exceptions import InvalidSecretsConfiguration

logger = logging.getLogger(__name__)


class JobTypesView(ListCreateAPIView):
    """This view is the endpoint for retrieving the list of all job types."""
    queryset = JobType.objects.all()
    serializer_class = JobTypeSerializer

    def list(self, request):
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

    def create(self, request):
        """Creates a new job type and returns a link to the detail URL

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        name = rest_util.parse_string(request, 'name')
        version = rest_util.parse_string(request, 'version')

        # Validate the job interface
        interface_dict = rest_util.parse_dict(request, 'interface')
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
                configuration = JobConfiguration(configuration_dict)
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
        base_fields = {'name', 'version', 'interface', 'trigger_rule', 'error_mapping', 'custom_resources',
                       'configuration'}
        for key, value in request.data.iteritems():
            if key not in base_fields and key not in JobType.UNEDITABLE_FIELDS:
                extra_fields[key] = value
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
                job_type = JobType.objects.create_job_type(name=name, version=version, interface=interface,
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
        serializer = JobTypeDetailsSerializer(job_type)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=dict(location=url))


class JobTypeDetailsView(GenericAPIView):
    """This view is the endpoint for retrieving/updating details of a job type."""
    queryset = JobType.objects.all()
    serializer_class = JobTypeDetailsSerializer

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
                configuration = JobConfiguration(configuration_dict)
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
        base_fields = {'name', 'version', 'interface', 'trigger_rule', 'error_mapping', 'custom_resources',
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
                JobType.objects.edit_job_type(job_type_id=job_type_id, interface=interface, trigger_rule=trigger_rule,
                                              remove_trigger_rule=remove_trigger_rule, error_mapping=error_mapping,
                                              custom_resources=custom_resources, configuration=configuration,
                                              secrets=secrets, **extra_fields)
        except (InvalidJobField, InvalidTriggerType, InvalidTriggerRule, InvalidConnection, InvalidDefinition,
                InvalidSecretsConfiguration, ValueError) as ex:
            logger.exception('Unable to update job type: %i', job_type_id)
            raise BadParameter(unicode(ex))

        # Fetch the full job type with details
        try:
            job_type = JobType.objects.get_details(job_type.id)
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
        name = rest_util.parse_string(request, 'name')
        version = rest_util.parse_string(request, 'version')

        # Validate the job interface
        interface_dict = rest_util.parse_dict(request, 'interface')
        interface = None
        try:
            if interface_dict:
                interface = JobInterface(interface_dict)
        except InvalidInterfaceDefinition as ex:
            raise BadParameter('Job type interface invalid: %s' % unicode(ex))

        # Validate the job configuration
        configuration_dict = rest_util.parse_dict(request, 'configuration', required=False)
        configuration = None
        try:
            configuration = JobConfiguration(configuration_dict)
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
        except (InvalidDefinition, InvalidTriggerType, InvalidTriggerRule) as ex:
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
    serializer_class = JobSerializer

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


class JobDetailsView(GenericAPIView):
    """This view is the endpoint for retrieving details about a single job."""
    queryset = Job.objects.all()
    serializer_class = JobDetailsSerializer

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
            job = Job.objects.get_details(job_id)
        except Job.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(job)
        return Response(serializer.data)

    def patch(self, request, job_id):
        """Modify job info with a subset of fields

        :param request: the HTTP GET request
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
            job = Job.objects.get_details(job_id)
        except (Job.DoesNotExist, JobExecution.DoesNotExist):
            raise Http404

        serializer = self.get_serializer(job)
        return Response(serializer.data)


class JobUpdatesView(ListAPIView):
    """This view is the endpoint for retrieving job updates over a given time range."""
    queryset = Job.objects.all()
    serializer_class = JobUpdateSerializer

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
    serializer_class = JobExecutionSerializer

    def list(self, request):
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
    serializer_class = JobExecutionDetailsSerializer

    def retrieve(self, request, job_exe_id):
        """Gets job execution and associated job_type id, name, and version

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param job_exe_id: the job execution id
        :type job_exe_id: int
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
