from __future__ import absolute_import
from __future__ import unicode_literals

import logging

import rest_framework.status as status
from django.db import transaction
from django.http.response import Http404, HttpResponse
from django.utils import timezone
from job.seed.exceptions import InvalidSeedManifestDefinition
from job.seed.manifest import SeedManifest
from rest_framework.generics import GenericAPIView, ListAPIView, ListCreateAPIView, RetrieveAPIView
from rest_framework.parsers import JSONParser
from rest_framework.renderers import StaticHTMLRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from data.data.exceptions import InvalidData
from data.data.json.data_v6 import DataV6
from job.configuration.exceptions import InvalidJobConfiguration
from job.configuration.interface.exceptions import InvalidInterfaceDefinition
from job.configuration.json.job_config_v6 import convert_config_to_v6_json, JobConfigurationV6
from job.exceptions import InvalidJobField, NonSeedJobType
from job.messages.cancel_jobs_bulk import create_cancel_jobs_bulk_message
from job.serializers import (JobSerializerV6, JobDetailsSerializerV6, JobExecutionSerializerV6,
                             JobExecutionDetailsSerializerV6)
from job.job_type_serializers import (JobTypeSerializerV6, JobTypeListSerializerV6, JobTypeRevisionSerializerV6,
                                      JobTypeRevisionDetailsSerializerV6, JobTypeDetailsSerializerV6,
                                      JobTypePendingStatusSerializerV6, JobTypeRunningStatusSerializerV6,
                                      JobTypeFailedStatusSerializerV6, JobTypeStatusSerializerV6)
from messaging.manager import CommandMessageManager
from job.models import Job, JobExecution, JobInputFile, JobType, JobTypeRevision
from node.resources.json.resources import Resources
from queue.messages.requeue_jobs_bulk import create_requeue_jobs_bulk_message
from queue.models import Queue
from storage.models import ScaleFile
from storage.serializers import ScaleFileSerializerV6
import util.rest as rest_util
from util.rest import BadParameter
from vault.exceptions import InvalidSecretsConfiguration

logger = logging.getLogger(__name__)


class JobTypesView(ListCreateAPIView):
    """This view is the endpoint for retrieving the list of all job types."""
    queryset = JobType.objects.all()
    serializer_class = JobTypeSerializerV6

    def list(self, request):
        """Retrieves the list of all job types and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        keywords = rest_util.parse_string_list(request, 'keyword', required=False)
        is_active = rest_util.parse_bool(request, 'is_active', required=False)
        is_system = rest_util.parse_bool(request, 'is_system', required=False)
        ids = rest_util.parse_int_list(request, 'id', required=False)
        order = ['name']

        job_types = JobType.objects.get_job_types_v6(keywords=keywords, ids=ids, is_active=is_active,
                                                     is_system=is_system, order=order)

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

        if self.request.version == 'v6':
            return self.create_v6(request)
        elif self.request.version == 'v7':
            return self.create_v6(request)
        else:
            return Http404

    def create_v6(self, request):
        """Creates or edits a Seed job type and returns a link to the detail URL

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        # Optional icon code value
        icon_code = rest_util.parse_string(request, 'icon_code', required=False)

        # Optional is published value
        is_published = rest_util.parse_string(request, 'is_published', required=False)

        # Optional max scheduled value
        max_scheduled = rest_util.parse_int(request, 'max_scheduled', required=False)

        # Require docker image value
        docker_image = rest_util.parse_string(request, 'docker_image', required=True)

        # Validate the job interface / manifest
        manifest_dict = rest_util.parse_dict(request, 'manifest', required=True)

        # If editing an existing job type, automatically update recipes containing said job type
        auto_update = rest_util.parse_bool(request, 'auto_update', required=False)

        manifest = None
        try:
            manifest = SeedManifest(manifest_dict, do_validate=True)
        except InvalidSeedManifestDefinition as ex:
            message = 'Seed Manifest invalid'
            logger.exception(message)
            raise BadParameter('%s: %s' % (message, unicode(ex)))

        # Validate the job configuration and pull out secrets
        configuration_dict = rest_util.parse_dict(request, 'configuration', required=False)

        configuration = None
        if configuration_dict:
            try:
                configuration = JobConfigurationV6(configuration_dict, do_validate=True).get_configuration()
            except InvalidJobConfiguration as ex:
                message = 'Job type configuration invalid'
                logger.exception(message)
                raise BadParameter('%s: %s' % (message, unicode(ex)))

        # Check for invalid fields
        fields = {'icon_code', 'is_published', 'max_scheduled', 'docker_image', 'configuration', 'manifest',
                  'auto_update'}
        for key, value in request.data.iteritems():
            if key not in fields:
                raise InvalidJobField

        name = manifest_dict['job']['name']
        version = manifest_dict['job']['jobVersion']

        existing_job_type = JobType.objects.filter(name=name, version=version).first()
        if not existing_job_type:
            try:
                # Create the job type
                job_type = JobType.objects.create_job_type_v6(icon_code=icon_code,
                                                              is_published=is_published,
                                                              max_scheduled=max_scheduled,
                                                              docker_image=docker_image,
                                                              manifest=manifest,
                                                              configuration=configuration)

            except (InvalidJobField, InvalidSecretsConfiguration, ValueError) as ex:
                message = 'Unable to create new job type'
                logger.exception(message)
                raise BadParameter('%s: %s' % (message, unicode(ex)))
            except InvalidSeedManifestDefinition as ex:
                message = 'Job type manifest invalid'
                logger.exception(message)
                raise BadParameter('%s: %s' % (message, unicode(ex)))
            except InvalidJobConfiguration as ex:
                message = 'Job type configuration invalid'
                logger.exception(message)
                raise BadParameter('%s: %s' % (message, unicode(ex)))
        else:
            try:
                JobType.objects.edit_job_type_v6(job_type_id=existing_job_type.id, manifest=manifest,
                                                 docker_image=docker_image, icon_code=icon_code, is_active=None,
                                                 is_paused=None, max_scheduled=max_scheduled,
                                                 is_published=is_published, configuration=configuration,
                                                 auto_update=auto_update)
            except (InvalidJobField, InvalidSecretsConfiguration, ValueError, InvalidInterfaceDefinition) as ex:
                logger.exception('Unable to update job type: %i', existing_job_type.id)
                raise BadParameter(unicode(ex))
            except InvalidSeedManifestDefinition as ex:
                message = 'Job type manifest invalid'
                logger.exception(message)
                raise BadParameter('%s: %s' % (message, unicode(ex)))
            except InvalidJobConfiguration as ex:
                message = 'Job type configuration invalid'
                logger.exception(message)
                raise BadParameter('%s: %s' % (message, unicode(ex)))

        # Fetch the full job type with details
        try:
            job_type = JobType.objects.get_details_v6(name, version)
        except JobType.DoesNotExist:
            raise Http404

        url = reverse('job_type_details_view', args=[job_type.name, job_type.version], request=request)
        serializer = JobTypeDetailsSerializerV6(job_type)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=dict(location=url))

class JobTypeVersionsView(ListAPIView):
    """This view is the endpoint for retrieving versions of a job type."""
    queryset = JobType.objects.all()
    serializer_class = JobTypeSerializerV6

    def list(self, request, name):
        """Retrieves the list of versions for a job type with the given name and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param name: The name of the job type
        :type name: string
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        is_active = rest_util.parse_bool(request, 'is_active', required=False)
        order = ['-version']

        job_types = JobType.objects.get_job_type_versions_v6(name, is_active, order)

        page = self.paginate_queryset(job_types)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

class JobTypeNamesView(ListCreateAPIView):
    """This view is the endpoint for retrieving the list of all job types."""
    queryset = JobType.objects.all()

    serializer_class = JobTypeListSerializerV6

    def list(self, request):
        """Retrieves the list of all job types and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if self.request.version == 'v6':
            return self.list_v6(request)
        elif self.request.version == 'v7':
            return self.list_v6(request)
        else:
            return Http404

    def list_v6(self, request):
        """Retrieves the list of all job type names and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        keywords = rest_util.parse_string_list(request, 'keyword', required=False)
        is_active = rest_util.parse_bool(request, 'is_active', required=False)
        is_system = rest_util.parse_bool(request, 'is_system', required=False)
        ids = rest_util.parse_int_list(request, 'id', required=False)
        order = ['name']

        job_types = JobType.objects.get_job_type_names_v6(keywords=keywords, ids=ids, is_active=is_active,
                                                     is_system=is_system, order=order)

        page = self.paginate_queryset(job_types)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class JobTypeDetailsView(GenericAPIView):
    """This view is the endpoint for retrieving/updating details of a version of a job type."""
    queryset = JobType.objects.all()
    serializer_class = JobTypeDetailsSerializerV6

    def get(self, request, name, version):
        """Retrieves the details for a job type version and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param name: The name of the job type
        :type name: string
        :param version: The version of the job type
        :type version: string
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        try:
            job_type = JobType.objects.get_details_v6(name, version)
        except JobType.DoesNotExist:
            raise Http404
        except NonSeedJobType as ex:
            logger.exception('Attempting to use v6 interface for non seed image with name=%s, version=%s', name, version)
            raise BadParameter(unicode(ex))

        serializer = self.get_serializer(job_type)
        return Response(serializer.data)

    def patch(self, request, name, version):
        """Edits an existing seed job type and returns the updated details

        :param request: the HTTP PATCH request
        :type request: :class:`rest_framework.request.Request`
        :param job_type_id: The ID for the job type.
        :type job_type_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        auto_update = rest_util.parse_bool(request, 'auto_update', required=False)
        icon_code = rest_util.parse_string(request, 'icon_code', required=False)
        is_published = rest_util.parse_string(request, 'is_published', required=False)
        is_active = rest_util.parse_bool(request, 'is_active', required=False)
        is_paused = rest_util.parse_bool(request, 'is_paused', required=False)
        max_scheduled = rest_util.parse_int(request, 'max_scheduled', required=False)
        # Validate the job configuration and pull out secrets
        configuration_dict = rest_util.parse_dict(request, 'configuration', required=False)
        configuration = None
        try:
            if configuration_dict:
                configuration = JobConfigurationV6(configuration_dict).get_configuration()
        except InvalidJobConfiguration as ex:
            raise BadParameter('Job type configuration invalid: %s' % unicode(ex))

        # Fetch the current job type model
        try:
            job_type = JobType.objects.get(name=name, version=version)
        except JobType.DoesNotExist:
            raise Http404

        # Check for invalid fields
        fields = {'icon_code', 'is_published', 'is_active', 'is_paused', 'max_scheduled', 'configuration'}
        for key, value in request.data.iteritems():
            if key not in fields:
                raise InvalidJobField

        try:
            with transaction.atomic():
                # Edit the job type
                JobType.objects.edit_job_type_v6(job_type_id=job_type.id, manifest=None, is_published=is_published,
                                                 docker_image=None, icon_code=icon_code, is_active=is_active,
                                                 is_paused=is_paused, max_scheduled=max_scheduled,
                                                 configuration=configuration, auto_update=auto_update)
        except (InvalidJobField, InvalidSecretsConfiguration, ValueError,
                InvalidJobConfiguration, InvalidInterfaceDefinition) as ex:
            logger.exception('Unable to update job type: %i', job_type.id)
            raise BadParameter(unicode(ex))

        return HttpResponse(status=204)


class JobTypeRevisionsView(ListAPIView):
    """This view is the endpoint for retrieving revisions of a job type."""
    queryset = JobTypeRevision.objects.all()
    serializer_class = JobTypeRevisionSerializerV6

    def list(self, request, name, version):
        """Retrieves the list of versions for a job type with the given name and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param name: The name of the job type
        :type name: string
        :param version: The version of the job type
        :type version: string
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        order = ['-revision_num']

        try:
            job_type_revisions = JobTypeRevision.objects.get_job_type_revisions_v6(name, version, order)
        except JobType.DoesNotExist:
            raise Http404

        page = self.paginate_queryset(job_type_revisions)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class JobTypeRevisionDetailsView(GenericAPIView):
    """This view is the endpoint for retrieving/updating details of a version of a job type."""
    queryset = JobTypeRevision.objects.all()
    serializer_class = JobTypeRevisionDetailsSerializerV6

    def get(self, request, name, version, revision_num):
        """Retrieves the details for a job type version and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param name: The name of the job type
        :type name: string
        :param version: The version of the job type
        :type version: string
        :param revision_num: The revision number of the job type
        :type revision_num: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        try:
            job_type_rev = JobTypeRevision.objects.get_details_v6(name, version, revision_num)
        except JobType.DoesNotExist:
            raise Http404

        except JobTypeRevision.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(job_type_rev)
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

        # Validate the seed manifest and job configuration
        manifest_dict = rest_util.parse_dict(request, 'manifest', required=True)
        configuration_dict = rest_util.parse_dict(request, 'configuration', required=True)

        # Validate the job type
        validation = JobType.objects.validate_job_type_v6(manifest_dict=manifest_dict,
                                                          configuration_dict=configuration_dict)

        resp_dict = {'is_valid': validation.is_valid, 'errors': [e.to_dict() for e in validation.errors],
                     'warnings': [w.to_dict() for w in validation.warnings]}
        return Response(resp_dict)


class JobTypesPendingView(ListAPIView):
    """This view is the endpoint for retrieving the status of all currently pending job types."""
    queryset = JobType.objects.all()

    def get_serializer_class(self):
        """Returns the appropriate serializer based off the requests version of the REST API. """

        return JobTypePendingStatusSerializerV6

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

    def get_serializer_class(self):
        """Returns the appropriate serializer based off the requests version of the REST API. """

        return JobTypeRunningStatusSerializerV6

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

    def get_serializer_class(self):
        """Returns the appropriate serializer based off the requests version of the REST API. """

        return JobTypeFailedStatusSerializerV6

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

    def get_serializer_class(self):
        """Returns the appropriate serializer based off the requests version of the REST API. """

        return JobTypeStatusSerializerV6

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

        job_type_statuses = JobType.objects.get_status(started=started, ended=ended)

        page = self.paginate_queryset(job_type_statuses)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class JobsView(ListAPIView):
    """This view is the endpoint for retrieving a list of all available jobs."""
    queryset = Job.objects.all()
    serializer_class = JobSerializerV6

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

        source_started = rest_util.parse_timestamp(request, 'source_started', required=False)
        source_ended = rest_util.parse_timestamp(request, 'source_ended', required=False)
        rest_util.check_time_range(source_started, source_ended)

        source_sensor_classes = rest_util.parse_string_list(request, 'source_sensor_class', required=False)
        source_sensors = rest_util.parse_string_list(request, 'source_sensor', required=False)
        source_collections = rest_util.parse_string_list(request, 'source_collection', required=False)
        source_tasks = rest_util.parse_string_list(request, 'source_task', required=False)

        statuses = rest_util.parse_string_list(request, 'status', required=False)
        job_ids = rest_util.parse_int_list(request, 'job_id', required=False)
        job_type_ids = rest_util.parse_int_list(request, 'job_type_id', required=False)
        job_type_names = rest_util.parse_string_list(request, 'job_type_name', required=False)
        batch_ids = rest_util.parse_int_list(request, 'batch_id', required=False)
        recipe_ids = rest_util.parse_int_list(request, 'recipe_id', required=False)
        error_categories = rest_util.parse_string_list(request, 'error_category', required=False)
        error_ids = rest_util.parse_int_list(request, 'error_id', required=False)
        is_superseded = rest_util.parse_bool(request, 'is_superseded', required=False)

        order = rest_util.parse_string_list(request, 'order', required=False)

        jobs = Job.objects.get_jobs_v6( started=started, ended=ended,
                                       source_started=source_started, source_ended=source_ended,
                                       source_sensor_classes=source_sensor_classes, source_sensors=source_sensors,
                                       source_collections=source_collections, source_tasks=source_tasks,
                                       statuses=statuses, job_ids=job_ids,
                                       job_type_ids=job_type_ids, job_type_names=job_type_names,
                                       batch_ids=batch_ids, recipe_ids=recipe_ids,
                                       error_categories=error_categories, error_ids=error_ids,
                                       is_superseded=is_superseded, order=order)
        page = self.paginate_queryset(jobs)
        serializer = self.get_serializer(page, many=True)

        return self.get_paginated_response(serializer.data)

    def post(self, request):
        """Creates a new job, places it on the queue, and returns the new job information in JSON form

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        job_type_id = rest_util.parse_int(request, 'job_type_id')
        job_data = rest_util.parse_dict(request, 'input', {})
        configuration_dict = rest_util.parse_dict(request, 'configuration', required=False)
        configuration = None

        try:
            jobData = DataV6(job_data, do_validate=True)
        except InvalidData as ex:
            logger.exception('Unable to queue new job. Invalid input: %s', job_data)
            raise BadParameter(unicode(ex))

        try:
            job_type = JobType.objects.get(pk=job_type_id)
        except JobType.DoesNotExist:
            raise Http404

        if configuration_dict:
            try:
                existing = convert_config_to_v6_json(job_type.get_job_configuration())
                configuration = JobConfigurationV6(configuration_dict, existing=existing,
                                                   do_validate=True).get_configuration()
            except InvalidJobConfiguration as ex:
                message = 'Job type configuration invalid'
                logger.exception(message)
                raise BadParameter('%s: %s' % (message, unicode(ex)))

        try:
            job_id = Queue.objects.queue_new_job_for_user_v6(job_type=job_type, job_data=jobData.get_data(),
                                                             job_configuration=configuration)
        except InvalidData as err:
            logger.exception('Invalid job data.')
            return Response('Invalid job data: ' + unicode(err), status=status.HTTP_400_BAD_REQUEST)

        try:
            job_details = Job.objects.get_details(job_id)
        except Job.DoesNotExist:
            raise Http404

        serializer = JobDetailsSerializerV6(job_details)
        job_url = reverse('job_details_view', args=[job_id], request=request)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=dict(location=job_url))


class CancelJobsView(GenericAPIView):
    """This view is the endpoint for canceling jobs"""
    parser_classes = (JSONParser,)
    queryset = Job.objects.all()
    serializer_class = JobSerializerV6

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

        job_type_names = rest_util.parse_string_list(request, 'job_type_names', required=False)
        batch_ids = rest_util.parse_int_list(request, 'batch_ids', required=False)
        recipe_ids = rest_util.parse_int_list(request, 'recipe_ids', required=False)
        is_superseded = rest_util.parse_bool(request, 'is_superseded', required=False)

        job_types = rest_util.parse_dict_list(request, 'job_types', required=False)

        for jt in job_types:
            if 'name' not in jt or 'version' not in jt:
                raise BadParameter('Job types argument invalid: %s' % job_types)
            existing_job_type = JobType.objects.filter(name=jt['name'], version=jt['version']).first()
            if not existing_job_type:
                raise BadParameter('Job Type with name: %s and version: %s does not exist' % (jt['name'], jt['version']))
            job_type_ids.append(existing_job_type.id)

        # Create and send message
        msg = create_cancel_jobs_bulk_message(started=started, ended=ended, error_categories=error_categories,
                                              error_ids=error_ids, job_ids=job_ids, job_type_ids=job_type_ids,
                                              status=job_status, job_type_names=job_type_names,
                                              batch_ids=batch_ids, recipe_ids=recipe_ids,
                                              is_superseded=is_superseded)
        CommandMessageManager().send_messages([msg])

        return Response(status=status.HTTP_202_ACCEPTED)


class RequeueJobsView(GenericAPIView):
    """This view is the endpoint for re-queuing jobs that have failed or been canceled"""
    parser_classes = (JSONParser,)
    queryset = Job.objects.all()

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

        job_type_names = rest_util.parse_string_list(request, 'job_type_names', required=False)
        batch_ids = rest_util.parse_int_list(request, 'batch_ids', required=False)
        recipe_ids = rest_util.parse_int_list(request, 'recipe_ids', required=False)
        is_superseded = rest_util.parse_bool(request, 'is_superseded', required=False)

        job_types = rest_util.parse_dict_list(request, 'job_types', required=False)

        for jt in job_types:
            if 'name' not in jt or 'version' not in jt:
                raise BadParameter('Job types argument invalid: %s' % job_types)
            existing_job_type = JobType.objects.filter(name=jt['name'], version=jt['version']).first()
            if not existing_job_type:
                raise BadParameter('Job Type with name: %s and version: %s does not exist' % (jt['name'], jt['version']))
            job_type_ids.append(existing_job_type.id)

        # Create and send message
        msg = create_requeue_jobs_bulk_message(started=started, ended=ended, error_categories=error_categories,
                                               error_ids=error_ids, job_ids=job_ids, job_type_ids=job_type_ids,
                                               priority=priority, status=job_status, job_type_names=job_type_names,
                                               batch_ids=batch_ids, recipe_ids=recipe_ids, is_superseded=is_superseded)
        CommandMessageManager().send_messages([msg])

        return Response(status=status.HTTP_202_ACCEPTED)


class JobDetailsView(GenericAPIView):
    """This view is the endpoint for retrieving details about a single job."""
    queryset = Job.objects.all()
    serializer_class = JobDetailsSerializerV6

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


class JobInputFilesView(ListAPIView):
    """This is the endpoint for retrieving details about input files associated with a job."""
    queryset = JobInputFile.objects.all()
    serializer_class = ScaleFileSerializerV6

    def get(self, request, job_id):
        """Retrieve detailed information about the input files for a job

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


class JobExecutionsView(ListAPIView):
    """This view is the endpoint for viewing job executions and their associated job_type id, name, and version"""
    queryset = JobExecution.objects.all()
    serializer_class = JobExecutionSerializerV6

    def list(self, request, job_id=None):
        """Gets job executions and their associated job_type id, name, and version

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param job_id: The ID for the job.
        :type job_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v6':
            return self.list_v6(request, job_id)
        elif request.version == 'v7':
            return self.list_v6(request, job_id)
        else:
            raise Http404

    def list_v6(self, request, job_id):
        """Gets job executions and their associated job_type id, name, and version

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        statuses = rest_util.parse_string_list(request, 'status', required=False)
        node_ids = rest_util.parse_int_list(request, 'node_id', required=False)
        error_ids = rest_util.parse_int_list(request, 'error_id', required=False)
        error_cats = rest_util.parse_string_list(request, 'error_category', required=False)

        job_exes = JobExecution.objects.get_job_exes(job_id=job_id, statuses=statuses, node_ids=node_ids,
                                                     error_ids=error_ids, error_categories=error_cats)

        page = self.paginate_queryset(job_exes)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class JobExecutionDetailsView(RetrieveAPIView):
    """This view is the endpoint for viewing job execution detail"""
    queryset = JobExecution.objects.all()
    serializer_class = JobExecutionDetailsSerializerV6

    def retrieve(self, request, job_id, exe_num):
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

        try:
            job_exe = JobExecution.objects.get_job_exe_details(job_id=job_id, exe_num=exe_num)
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
