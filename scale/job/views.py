from __future__ import unicode_literals

import logging
from datetime import datetime

import django.core.urlresolvers as urlresolvers
import rest_framework.status as status
from django.db import transaction
from django.http.response import Http404
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

import trigger.handler as trigger_handler
import util.rest as rest_util
from job.configuration.data.exceptions import InvalidConnection
from job.configuration.interface.error_interface import ErrorInterface
from job.configuration.interface.exceptions import InvalidInterfaceDefinition
from job.configuration.interface.job_interface import JobInterface
from job.exceptions import InvalidJobField
from job.serializers import (JobDetailsSerializer, JobListSerializer, JobTypeDetailsSerializer,
                             JobTypeFailedStatusListSerializer, JobTypeListSerializer,
                             JobTypeRunningStatusListSerializer, JobTypeStatusListSerializer, JobUpdateListSerializer,
                             JobWithExecutionListSerializer, JobExecutionListSerializer,
                             JobExecutionDetailsSerializer, JobExecutionLogSerializer)
from models import Job, JobExecution, JobType
from queue.models import Queue
from trigger.configuration.exceptions import InvalidTriggerRule, InvalidTriggerType
from util.rest import BadParameter

logger = logging.getLogger(__name__)


class JobTypesView(APIView):
    """This view is the endpoint for retrieving the list of all job types."""
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
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
        order = rest_util.parse_string_list(request, 'order', ['name', 'version'])

        job_types = JobType.objects.get_job_types(started, ended, names, categories, order)

        page = rest_util.perform_paging(request, job_types)
        serializer = JobTypeListSerializer(page, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
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

        # Validate the error mapping
        error_dict = rest_util.parse_dict(request, 'error_mapping', required=False)
        error_mapping = None
        try:
            if error_dict:
                error_mapping = ErrorInterface(error_dict)
                error_mapping.validate()
        except InvalidInterfaceDefinition as ex:
            raise BadParameter('Job type error mapping invalid: %s' % unicode(ex))

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
        base_fields = {'name', 'version', 'interface', 'trigger_rule', 'error_mapping'}
        for key, value in request.DATA.iteritems():
            if key not in base_fields and key not in JobType.UNEDITABLE_FIELDS:
                extra_fields[key] = value

        try:
            with transaction.atomic():

                # Attempt to create the trigger rule
                trigger_rule = None
                if rule_handler and 'configuration' in trigger_rule_dict:
                    trigger_rule = rule_handler.create_trigger_rule(trigger_rule_dict['configuration'], name, is_active)

                # Create the job type
                job_type = JobType.objects.create_job_type(name, version, interface, trigger_rule, error_mapping,
                                                           **extra_fields)
        except (InvalidJobField, InvalidTriggerType, InvalidTriggerRule, InvalidConnection, ValueError) as ex:
            logger.exception('Unable to create new job type: %s', name)
            raise BadParameter(unicode(ex))

        # Fetch the full job type with details
        try:
            job_type = JobType.objects.get_details(job_type.id)
        except JobType.DoesNotExist:
            raise Http404

        url = urlresolvers.reverse('job_type_details_view', args=[job_type.id])
        serializer = JobTypeDetailsSerializer(job_type)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=dict(location=url))


class JobTypeDetailsView(APIView):
    """This view is the endpoint for retrieving/updating details of a job type."""
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

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

        serializer = JobTypeDetailsSerializer(job_type)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, job_type_id):
        """Edits an existing job type and returns the updated details

        :param request: the HTTP GET request
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

        # Validate the error mapping
        error_dict = rest_util.parse_dict(request, 'error_mapping', required=False)
        error_mapping = None
        try:
            if error_dict:
                error_mapping = ErrorInterface(error_dict)
                error_mapping.validate()
        except InvalidInterfaceDefinition as ex:
            raise BadParameter('Job type error mapping invalid: %s' % unicode(ex))

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
        base_fields = {'name', 'version', 'interface', 'trigger_rule', 'error_mapping'}
        for key, value in request.DATA.iteritems():
            if key not in base_fields and key not in JobType.UNEDITABLE_FIELDS:
                extra_fields[key] = value

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
                JobType.objects.edit_job_type(job_type_id, interface, trigger_rule, remove_trigger_rule, error_mapping,
                                              **extra_fields)
        except (InvalidJobField, InvalidTriggerType, InvalidTriggerRule, InvalidConnection, InvalidDefinition,
                ValueError) as ex:
            logger.exception('Unable to update job type: %i', job_type_id)
            raise BadParameter(unicode(ex))

        # Fetch the full job type with details
        try:
            job_type = JobType.objects.get_details(job_type.id)
        except JobType.DoesNotExist:
            raise Http404

        serializer = JobTypeDetailsSerializer(job_type)
        return Response(serializer.data, status=status.HTTP_200_OK)


class JobTypesValidationView(APIView):
    """This view is the endpoint for validating a new job type before attempting to actually create it
    """
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

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

        # Validate the error mapping
        error_dict = rest_util.parse_dict(request, 'error_mapping', required=False)
        error_mapping = None
        try:
            if error_dict:
                error_mapping = ErrorInterface(error_dict)
        except InvalidInterfaceDefinition as ex:
            raise BadParameter('Job type error mapping invalid: %s' % unicode(ex))

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

        # Validate the job interface
        try:
            warnings = JobType.objects.validate_job_type(name, version, interface, error_mapping, trigger_config)
        except (InvalidDefinition, InvalidTriggerType, InvalidTriggerRule) as ex:
            logger.exception('Unable to validate new job type: %s', name)
            raise BadParameter(unicode(ex))

        results = [{'id': w.key, 'details': w.details} for w in warnings]
        return Response({'warnings': results}, status=status.HTTP_200_OK)


class JobTypesRunningView(APIView):
    """This view is the endpoint for retrieving the status of all currently running job types."""
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        """Retrieves the current status of running job types and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        # Get all the running job types with statistics
        running_status = JobType.objects.get_running_status()

        # Wrap the response with paging information
        page = rest_util.perform_paging(request, running_status)
        serializer = JobTypeRunningStatusListSerializer(page, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class JobTypesSystemFailuresView(APIView):
    """This view is the endpoint for viewing system errors organized by job type."""
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        """Retrieves the job types that have failed with system errors and returns them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        # Get all the failed job types with statistics
        failed_status = JobType.objects.get_failed_status()

        # Wrap the response with paging information
        page = rest_util.perform_paging(request, failed_status)
        serializer = JobTypeFailedStatusListSerializer(page, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class JobTypesStatusView(APIView):
    """This view is the endpoint for retrieving overall job type status information."""

    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        """Retrieves the list of all job types with status and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        # Get a list of all job type status counts
        started = rest_util.parse_timestamp(request, 'started', 'PT3H0M0S')
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        job_type_statuses = JobType.objects.get_status(started, ended)

        page = rest_util.perform_paging(request, job_type_statuses)
        serializer = JobTypeStatusListSerializer(page, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class JobsView(APIView):
    """This view is the endpoint for retrieving a list of all available jobs."""
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        """Retrieves jobs and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        job_status = rest_util.parse_string(request, 'status', required=False)
        job_ids = rest_util.parse_int_list(request, 'job_id', required=False)
        job_type_ids = rest_util.parse_int_list(request, 'job_type_id', required=False)
        job_type_names = rest_util.parse_string_list(request, 'job_type_name', required=False)
        job_type_categories = rest_util.parse_string_list(request, 'job_type_category', required=False)

        order = rest_util.parse_string_list(request, 'order', required=False)

        jobs = Job.objects.get_jobs(started, ended, job_status, job_ids, job_type_ids, job_type_names,
                                    job_type_categories, order)

        page = rest_util.perform_paging(request, jobs)
        serializer = JobListSerializer(page, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class JobDetailsView(APIView):
    """This view is the endpoint for retrieving details about a single job."""
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

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

        serializer = JobDetailsSerializer(job)
        return Response(serializer.data, status=status.HTTP_200_OK)

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
            Queue.objects.handle_job_cancellation(job_id, datetime.utcnow())
            job = Job.objects.get_details(job_id)
        except (Job.DoesNotExist, JobExecution.DoesNotExist):
            raise Http404

        serializer = JobDetailsSerializer(job)
        return Response(serializer.data, status=status.HTTP_200_OK)


class JobUpdatesView(APIView):
    """This view is the endpoint for retrieving job updates over a given time range."""

    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

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

        job_status = rest_util.parse_string(request, 'status', required=False)
        job_type_ids = rest_util.parse_int_list(request, 'job_type_id', required=False)
        job_type_names = rest_util.parse_string_list(request, 'job_type_name', required=False)
        job_type_categories = rest_util.parse_string_list(request, 'job_type_category', required=False)

        order = rest_util.parse_string_list(request, 'order', required=False)

        jobs = Job.objects.get_job_updates(started, ended, job_status, job_type_ids, job_type_names,
                                           job_type_categories, order)

        page = rest_util.perform_paging(request, jobs)
        Job.objects.populate_input_files(page)
        serializer = JobUpdateListSerializer(page, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class JobsWithExecutionView(APIView):
    """This view is the endpoint for viewing jobs and their associated latest execution"""
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        """Gets jobs and their associated latest execution

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        job_status = rest_util.parse_string(request, 'status', required=False)
        job_ids = rest_util.parse_int_list(request, 'job_id', required=False)
        job_type_ids = rest_util.parse_int_list(request, 'job_type_id', required=False)
        job_type_names = rest_util.parse_string_list(request, 'job_type_name', required=False)
        job_type_categories = rest_util.parse_string_list(request, 'job_type_category', required=False)

        order = rest_util.parse_string_list(request, 'order', required=False)

        jobs = Job.objects.get_jobs(started, ended, job_status, job_ids, job_type_ids, job_type_names,
                                    job_type_categories, order)
        page = rest_util.perform_paging(request, jobs)

        # Add the latest execution for each matching job
        paged_jobs = list(page.object_list)
        job_exes_dict = JobExecution.objects.get_latest(page.object_list)
        for job in paged_jobs:
            job.latest_job_exe = job_exes_dict[job.id] if job.id in job_exes_dict else None
        page.object_list = paged_jobs

        serializer = JobWithExecutionListSerializer(page, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class JobExecutionsView(APIView):
    """This view is the endpoint for viewing job executions and their associated job_type id, name, and version"""
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        """Gets job executions and their associated job_type id, name, and version

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        job_status = rest_util.parse_string(request, 'status', required=False)
        job_type_ids = rest_util.parse_int_list(request, 'job_type_id', required=False)
        job_type_names = rest_util.parse_string_list(request, 'job_type_name', required=False)
        job_type_categories = rest_util.parse_string_list(request, 'job_type_category', required=False)

        node_ids = rest_util.parse_int_list(request, 'node_id', required=False)

        order = rest_util.parse_string_list(request, 'order', required=False)

        job_exes = JobExecution.objects.get_exes(started, ended, job_status, job_type_ids, job_type_names,
                                                 job_type_categories, node_ids, order)
        page = rest_util.perform_paging(request, job_exes)

        serializer = JobExecutionListSerializer(page, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class JobExecutionDetailsView(APIView):
    """This view is the endpoint for viewing job execution detail"""
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request, job_exe_id):
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

        serializer = JobExecutionDetailsSerializer(job_exe)
        return Response(serializer.data, status=status.HTTP_200_OK)


class JobExecutionLogView(APIView):
    """This view is the endpoint for viewing job execution logs"""
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request, job_exe_id):
        """Gets job execution logs. This can be a slightly slow operation so it's a separate view from the details.

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param job_exe_id: the job execution id
        :type job_exe_id: int
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        try:
            job_exe = JobExecution.objects.get_logs(job_exe_id)
        except JobExecution.DoesNotExist:
            raise Http404

        serializer = JobExecutionLogSerializer(job_exe)
        return Response(serializer.data, status=status.HTTP_200_OK)
