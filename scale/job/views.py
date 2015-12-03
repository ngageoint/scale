import logging

from datetime import datetime
from django.db import transaction
from django.http.response import Http404, HttpResponseServerError
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from job.configuration.interface.error_interface import ErrorInterface
from job.configuration.interface.exceptions import InvalidInterfaceDefinition
from job.serializers import (JobDetailsSerializer, JobListSerializer, JobTypeDetailsSerializer,
                             JobTypeFailedStatusListSerializer, JobTypeListSerializer,
                             JobTypeRunningStatusListSerializer, JobTypeStatusListSerializer, JobUpdateListSerializer,
                             JobWithExecutionListSerializer, JobExecutionListSerializer,
                             JobExecutionDetailsSerializer, JobExecutionLogSerializer)
from models import Job, JobExecution, JobType
from queue.models import Queue
import rest_framework.status as status
import util.rest as rest_util


logger = logging.getLogger(__name__)


class JobTypesView(APIView):
    '''This view is the endpoint for retrieving the list of all job types.'''
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        '''Retrieves the list of all job types and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''

        started = rest_util.parse_timestamp(request, u'started', required=False)
        ended = rest_util.parse_timestamp(request, u'ended', required=False)
        rest_util.check_time_range(started, ended)

        names = rest_util.parse_string_list(request, u'name', required=False)
        categories = rest_util.parse_string_list(request, u'category', required=False)
        order = rest_util.parse_string_list(request, u'order', [u'name', u'version'])

        job_types = JobType.objects.get_job_types(started, ended, names, categories, order)

        page = rest_util.perform_paging(request, job_types)
        serializer = JobTypeListSerializer(page, context={u'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class JobTypeDetailsView(APIView):
    '''This view is the endpoint for retrieving/updating details of a job type.'''
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request, job_type_id):
        '''Retrieves the details for a job type and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param job_type_id: The id of the job type
        :type job_type_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''
        try:
            job_type = JobType.objects.get_details(job_type_id)
        except JobType.DoesNotExist:
            raise Http404

        serializer = JobTypeDetailsSerializer(job_type)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, job_type_id):
        '''Modify job type info with a subset of fields

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param job_type_id: The ID for the job type.
        :type job_type_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''

        # Validate that no extra fields are included
        rest_util.check_update(request, [u'error_mapping', u'is_paused'])

        # Validate JSON
        error_mapping = rest_util.parse_dict(request, u'error_mapping', required=False)
        is_paused = rest_util.parse_bool(request, u'is_paused', required=False)
        if error_mapping is not None:
            try:
                ErrorInterface(error_mapping)
            except InvalidInterfaceDefinition:
                return Response(u'Input failed schema validation.', status=status.HTTP_400_BAD_REQUEST)

        try:
            if error_mapping is not None:
                JobType.objects.update_error_mapping(error_mapping, job_type_id)
            if is_paused is not None:
                Queue.objects.update_job_type_pause(job_type_id, is_paused)
            job_type = JobType.objects.get_details(job_type_id)
            serializer = JobTypeDetailsSerializer(job_type)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except JobType.DoesNotExist:
            raise Http404


class JobTypeDetailsCreateView(APIView):
    '''This view is the endpoint for retrieving/updating details of a job type.'''
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def post(self, request):
        '''Creates a new JobType and returns its ID in JSON form

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''

        name = rest_util.parse_string(request, u'name')
        version = rest_util.parse_string(request, u'version')
        title = rest_util.parse_string(request, u'title', default_value=u'Unknown Job Type')
        description = rest_util.parse_string(request, u'description')
        category = rest_util.parse_string(request, u'category', default_value=u'unknown')
        author_name = rest_util.parse_string(request, u'author_name', required=False)
        author_url = rest_util.parse_string(request, u'author_url', required=False)

        is_system = False
        is_long_running = False
        is_active = rest_util.parse_bool(request, u'is_active', default_value=True)
        is_operational = rest_util.parse_bool(request, u'is_operational', default_value=True)
        is_paused = rest_util.parse_bool(request, u'is_paused', default_value=False)
        requires_cleanup = True

        uses_docker = True
        docker_privileged = rest_util.parse_bool(request, u'docker_privileged', default_value=False)
        docker_image = rest_util.parse_string(request, u'docker_image')
        interface = rest_util.parse_dict(request, u'interface')
        error_mapping = rest_util.parse_dict(request, u'error_mapping', default_value={})

        priority = rest_util.parse_int(request, u'priority', default_value=260)
        timeout = rest_util.parse_int(request, u'timeout', default_value=1800)
        max_tries = rest_util.parse_int(request, u'max_tries', default_value=3)
        cpus_required = rest_util.parse_float(request, u'cpus_required', default_value=1)
        mem_required = rest_util.parse_float(request, u'mem_required', default_value=5120)
        disk_out_const_required = rest_util.parse_float(request, u'disk_out_const_required', default_value=0)
        disk_out_mult_required = rest_util.parse_float(request, u'disk_out_mult_required', default_value=0)

        icon_code = rest_util.parse_string(request, u'icon_code', default_value=u'f013')

        try:
            try:
                job_type = JobType.objects.get(name=name, version=version)
                job_type.description = description
                job_type.docker_image = docker_image
                job_type.interface = interface
                job_type.priority = priority
                job_type.timeout = timeout
                job_type.max_tries = max_tries
                job_type.cpus_required = cpus_required
                job_type.mem_required = mem_required
                job_type.disk_out_const_required = disk_out_const_required

            except JobType.DoesNotExist:
                job_type = JobType.objects.create_job_type(name, version, description, docker_image, interface,
                                                           priority, timeout, max_tries, cpus_required, mem_required,
                                                           disk_out_const_required, None)
            job_type.title = title
            job_type.category = category
            job_type.author_name = author_name
            job_type.author_url = author_url
            job_type.is_system = is_system
            job_type.is_long_running = is_long_running
            job_type.is_active = is_active
            job_type.is_operational = is_operational
            job_type.is_paused = is_paused
            job_type.requires_cleanup = requires_cleanup
            job_type.uses_docker = uses_docker
            job_type.docker_privileged = docker_privileged
            job_type.error_mapping = error_mapping
            job_type.icon_code = icon_code
            job_type.disk_out_mult_required = disk_out_mult_required
            job_type.save()

        except InvalidInterfaceDefinition:
            raise rest_util.BadParameter('Interface definition failed to validate.')
        return Response({'job_type_id': job_type.id}, status=status.HTTP_200_OK)


class JobTypesRunningView(APIView):
    '''This view is the endpoint for retrieving the status of all currently running job types.'''
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        '''Retrieves the current status of running job types and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''

        # Get all the running job types with statistics
        running_status = JobType.objects.get_running_status()

        # Wrap the response with paging information
        page = rest_util.perform_paging(request, running_status)
        serializer = JobTypeRunningStatusListSerializer(page, context={u'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class JobTypesSystemFailuresView(APIView):
    '''This view is the endpoint for viewing system errors organized by job type.'''
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        '''Retrieves the job types that have failed with system errors and returns them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''

        # Get all the failed job types with statistics
        failed_status = JobType.objects.get_failed_status()

        # Wrap the response with paging information
        page = rest_util.perform_paging(request, failed_status)
        serializer = JobTypeFailedStatusListSerializer(page, context={u'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class JobTypesStatusView(APIView):
    '''This view is the endpoint for retrieving overall job type status information.'''

    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        '''Retrieves the list of all job types with status and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''

        # Get a list of all job type status counts
        started = rest_util.parse_timestamp(request, u'started', u'PT3H0M0S')
        ended = rest_util.parse_timestamp(request, u'ended', required=False)
        job_type_statuses = JobType.objects.get_status(started, ended)

        page = rest_util.perform_paging(request, job_type_statuses)
        serializer = JobTypeStatusListSerializer(page, context={u'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class JobsView(APIView):
    '''This view is the endpoint for retrieving a list of all available jobs.'''
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        '''Retrieves jobs and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''

        started = rest_util.parse_timestamp(request, u'started', required=False)
        ended = rest_util.parse_timestamp(request, u'ended', required=False)
        rest_util.check_time_range(started, ended)

        job_status = rest_util.parse_string(request, u'status', required=False)
        job_type_ids = rest_util.parse_int_list(request, u'job_type_id', required=False)
        job_type_names = rest_util.parse_string_list(request, u'job_type_name', required=False)
        job_type_categories = rest_util.parse_string_list(request, u'job_type_category', required=False)

        order = rest_util.parse_string_list(request, u'order', required=False)

        jobs = Job.objects.get_jobs(started, ended, job_status, job_type_ids, job_type_names, job_type_categories,
                                    order)

        page = rest_util.perform_paging(request, jobs)
        serializer = JobListSerializer(page, context={u'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class JobDetailsView(APIView):
    '''This view is the endpoint for retrieving details about a single job.'''
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request, job_id):
        '''Retrieves jobs and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param job_id: The ID for the job.
        :type job_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''

        try:
            job = Job.objects.get_details(job_id)
        except Job.DoesNotExist:
            raise Http404

        serializer = JobDetailsSerializer(job)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, job_id):
        '''Modify job info with a subset of fields

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param job_id: The ID for the job.
        :type job_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''

        # Validate that no extra fields are included
        rest_util.check_update(request, [u'status'])

        # Validate JSON
        status_code = rest_util.parse_string(request, u'status')
        if status_code != 'CANCELED':
            raise rest_util.BadParameter('Invalid or read-only status. Allowed values: CANCELED')

        try:
            Queue.objects.handle_job_cancellation(job_id, datetime.utcnow())
            job = Job.objects.get_details(job_id)
            serializer = JobDetailsSerializer(job)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Job.DoesNotExist:
            raise Http404
        except JobExecution.DoesNotExist:
            raise Http404
        except Exception, e:
            return HttpResponseServerError(str(e))

class JobUpdatesView(APIView):
    '''This view is the endpoint for retrieving job updates over a given time range.'''

    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        '''Retrieves the job updates for a given time range and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''
        started = rest_util.parse_timestamp(request, u'started', required=False)
        ended = rest_util.parse_timestamp(request, u'ended', required=False)
        rest_util.check_time_range(started, ended)

        job_status = rest_util.parse_string(request, u'status', required=False)
        job_type_ids = rest_util.parse_int_list(request, u'job_type_id', required=False)
        job_type_names = rest_util.parse_string_list(request, u'job_type_name', required=False)
        job_type_categories = rest_util.parse_string_list(request, u'job_type_category', required=False)

        order = rest_util.parse_string_list(request, u'order', required=False)

        jobs = Job.objects.get_job_updates(started, ended, job_status, job_type_ids, job_type_names,
                                           job_type_categories, order)

        page = rest_util.perform_paging(request, jobs)
        Job.objects.populate_input_files(page)
        serializer = JobUpdateListSerializer(page, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class JobsWithExecutionView(APIView):
    '''This view is the endpoint for viewing jobs and their associated latest execution'''
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        '''Gets jobs and their associated latest execution

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''
        started = rest_util.parse_timestamp(request, u'started', required=False)
        ended = rest_util.parse_timestamp(request, u'ended', required=False)
        rest_util.check_time_range(started, ended)

        job_status = rest_util.parse_string(request, u'status', required=False)
        job_type_ids = rest_util.parse_int_list(request, u'job_type_id', required=False)
        job_type_names = rest_util.parse_string_list(request, u'job_type_name', required=False)
        job_type_categories = rest_util.parse_string_list(request, u'job_type_category', required=False)

        order = rest_util.parse_string_list(request, u'order', required=False)

        jobs = Job.objects.get_jobs(started, ended, job_status, job_type_ids, job_type_names, job_type_categories,
                                    order)
        page = rest_util.perform_paging(request, jobs)

        # Add the latest execution for each matching job
        paged_jobs = list(page.object_list)
        job_exes_dict = JobExecution.objects.get_latest(page.object_list)
        for job in paged_jobs:
            job.latest_job_exe = job_exes_dict[job.id] if job.id in job_exes_dict else None
        page.object_list = paged_jobs

        serializer = JobWithExecutionListSerializer(page, context={u'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class JobExecutionsView(APIView):
    '''This view is the endpoint for viewing job executions and their associated job_type id, name, and version'''
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        '''Gets job executions and their associated job_type id, name, and version

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''
        started = rest_util.parse_timestamp(request, u'started', required=False)
        ended = rest_util.parse_timestamp(request, u'ended', required=False)
        rest_util.check_time_range(started, ended)

        job_status = rest_util.parse_string(request, u'status', required=False)
        job_type_ids = rest_util.parse_int_list(request, u'job_type_id', required=False)
        job_type_names = rest_util.parse_string_list(request, u'job_type_name', required=False)
        job_type_categories = rest_util.parse_string_list(request, u'job_type_category', required=False)

        node_ids = rest_util.parse_int_list(request, u'node_id', required=False)

        order = rest_util.parse_string_list(request, u'order', required=False)

        job_exes = JobExecution.objects.get_exes(started, ended, job_status, job_type_ids, job_type_names,
                                                 job_type_categories, node_ids, order)
        page = rest_util.perform_paging(request, job_exes)

        serializer = JobExecutionListSerializer(page, context={u'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class JobExecutionDetailsView(APIView):
    '''This view is the endpoint for viewing job execution detail'''
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request, job_exe_id):
        '''Gets job execution and associated job_type id, name, and version

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param job_exe_id: the job execution id
        :type job_exe_id: int
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''
        try:
            job_exe = JobExecution.objects.get_details(job_exe_id)
        except JobExecution.DoesNotExist:
            raise Http404

        serializer = JobExecutionDetailsSerializer(job_exe)
        return Response(serializer.data, status=status.HTTP_200_OK)


class JobExecutionLogView(APIView):
    '''This view is the endpoint for viewing job execution logs'''
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request, job_exe_id):
        '''Gets job execution logs. This can be a slightly slow operation so it's a separate view from the details.

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param job_exe_id: the job execution id
        :type job_exe_id: int
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''
        try:
            job_exe = JobExecution.objects.get_logs(job_exe_id)
        except JobExecution.DoesNotExist:
            raise Http404

        serializer = JobExecutionLogSerializer(job_exe)
        return Response(serializer.data, status=status.HTTP_200_OK)
