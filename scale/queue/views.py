"""Defines the views for the RESTful queue services"""
from __future__ import unicode_literals

import datetime
import logging

import django.core.urlresolvers as urlresolvers
import rest_framework.status as status
from django.http.response import Http404
from rest_framework.parsers import JSONParser
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response

import util.rest as rest_util
from job.configuration.data.exceptions import InvalidData, StatusError
from job.models import Job, JobType
from job.serializers import JobDetailsSerializer, JobSerializer
from queue.models import JobLoad, Queue
from queue.serializers import JobLoadGroupSerializer
from recipe.models import Recipe, RecipeType
from recipe.serializers import RecipeDetailsSerializer

logger = logging.getLogger(__name__)


class JobLoadView(ListAPIView):
    """This view is the endpoint for retrieving the job load for a given time range."""
    queryset = JobLoad.objects.all()
    serializer_class = JobLoadGroupSerializer

    def list(self, request):
        """Retrieves the job load for a given time range and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        started = rest_util.parse_timestamp(request, 'started', default_value=rest_util.get_relative_days(7))
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended, max_duration=datetime.timedelta(days=31))

        job_type_ids = rest_util.parse_int_list(request, 'job_type_id', required=False)
        job_type_names = rest_util.parse_string_list(request, 'job_type_name', required=False)
        job_type_categories = rest_util.parse_string_list(request, 'job_type_category', required=False)
        job_type_priorities = rest_util.parse_string_list(request, 'job_type_priority', required=False)

        job_loads = JobLoad.objects.get_job_loads(started, ended, job_type_ids, job_type_names, job_type_categories,
                                                  job_type_priorities)
        job_loads_grouped = JobLoad.objects.group_by_time(job_loads)

        page = self.paginate_queryset(job_loads_grouped)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class QueueNewJobView(GenericAPIView):
    """This view is the endpoint for creating new jobs and putting them on the queue."""
    parser_classes = (JSONParser,)
    serializer_class = JobDetailsSerializer

    def post(self, request):
        """Creates a new job, places it on the queue, and returns the new job information in JSON form

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        job_type_id = rest_util.parse_int(request, 'job_type_id')
        job_data = rest_util.parse_dict(request, 'job_data', {})

        try:
            job_type = JobType.objects.get(pk=job_type_id)
        except JobType.DoesNotExist:
            raise Http404

        try:
            job_id, job_exe_id = Queue.objects.queue_new_job_for_user(job_type, job_data)
        except InvalidData:
            return Response('Invalid job information.', status=status.HTTP_400_BAD_REQUEST)

        job_details = Job.objects.get_details(job_id)

        serializer = self.get_serializer(job_details)
        job_exe_url = urlresolvers.reverse('job_execution_details_view', args=[job_exe_id])
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=dict(location=job_exe_url))


class QueueNewRecipeView(GenericAPIView):
    """This view is the endpoint for queuing recipes and returns the detail information for the recipe that was queued.
    """
    parser_classes = (JSONParser,)
    serializer_class = RecipeDetailsSerializer

    def post(self, request):
        """Queue a recipe and returns the new job information in JSON form

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        recipe_type_id = rest_util.parse_int(request, 'recipe_type_id')
        recipe_data = rest_util.parse_dict(request, 'recipe_data', {})

        try:
            recipe_type = RecipeType.objects.get(pk=recipe_type_id)
        except RecipeType.DoesNotExist:
            raise Http404

        try:
            recipe_id = Queue.objects.queue_new_recipe_for_user(recipe_type, recipe_data)
        except InvalidData:
            return Response('Invalid recipe information.', status=status.HTTP_400_BAD_REQUEST)

        recipe_details = Recipe.objects.get_details(recipe_id)

        serializer = self.get_serializer(recipe_details)
        recipe_url = urlresolvers.reverse('recipe_details_view', args=[recipe_id])
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=dict(location=recipe_url))


class QueueStatusView(GenericAPIView):
    """This view is the endpoint for retrieving the queue status."""

    def get(self, request):
        """Retrieves the current status of the queue and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        queue_status = Queue.objects.get_queue_status()
        return Response({'queue_status': queue_status})


class RequeueJobsView(GenericAPIView):
    """This view is the endpoint for requeuing jobs which have already been executed."""
    parser_classes = (JSONParser,)
    serializer_class = JobSerializer

    def post(self, request):
        """Increase max_tries, place it on the queue, and returns the new job information in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :returns: the HTTP response to send back to the user
        """

        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        job_status = rest_util.parse_string(request, 'status', required=False)
        job_ids = rest_util.parse_int_list(request, 'job_ids', required=False)
        job_type_ids = rest_util.parse_int_list(request, 'job_type_ids', required=False)
        job_type_names = rest_util.parse_string_list(request, 'job_type_names', required=False)
        job_type_categories = rest_util.parse_string_list(request, 'job_type_categories', required=False)

        priority = rest_util.parse_int(request, 'priority', required=False)

        # Fetch all the jobs matching the filters
        jobs = Job.objects.get_jobs(started, ended, job_status, job_ids, job_type_ids, job_type_names,
                                    job_type_categories)
        if not jobs:
            raise Http404

        # Attempt to queue all jobs matching the filters
        requested_job_ids = {job.id for job in jobs}
        Queue.objects.requeue_jobs(requested_job_ids, priority)

        # Refresh models to get the new status information for all originally requested jobs
        jobs = Job.objects.get_jobs(job_ids=requested_job_ids)

        page = self.paginate_queryset(jobs)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


# TODO: Remove this once the UI migrates to /queue/requeue-jobs/
class RequeueExistingJobView(GenericAPIView):
    """This view is the endpoint for requeuing jobs which have already been executed for the maximum number of tries
    """
    parser_classes = (JSONParser,)
    serializer_class = JobDetailsSerializer

    def post(self, request):
        """Increase max_tries, place it on the queue, and returns the new job information in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param job_id: The ID of the job to requeue. This job must exist and must be in a FAILED or CANCELED state.
        :rtype: int
        :returns: the HTTP response to send back to the user
        """
        job_id = request.data['job_id']

        try:
            Queue.objects.requeue_existing_job(job_id)
            job_details = Job.objects.get_details(job_id)

            serializer = self.get_serializer(job_details)
            return Response(serializer.data)
        except Job.DoesNotExist:
            raise Http404
        except InvalidData:
            logger.exception('Invalid job data submitted for requeue: %i', job_id)
            return Response('Job meta data failed to validate: %i' % job_id, status=status.HTTP_400_BAD_REQUEST)
        except StatusError:
            logger.exception('Incorrect status for job submitted for requeue: %i', job_id)
            return Response('Job must be in the CANCELED or FAILED state for requeue',
                            status=status.HTTP_409_CONFLICT)
