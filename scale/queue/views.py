"""Defines the views for the RESTful queue services"""
from __future__ import unicode_literals

import datetime
import logging

import django.core.urlresolvers as urlresolvers
import rest_framework.status as status
from django.http.response import Http404
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

import util.rest as rest_util
from job.configuration.data.exceptions import InvalidData, StatusError
from job.models import Job, JobType
from job.serializers import JobDetailsSerializer, JobListSerializer
from queue.models import JobLoad, Queue
from queue.serializers import JobLoadGroupListSerializer
from recipe.models import Recipe, RecipeType
from recipe.serializers import RecipeDetailsSerializer
from util.rest import BadParameter


logger = logging.getLogger(__name__)


class JobLoadView(APIView):
    """This view is the endpoint for retrieving the job load for a given time range."""

    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
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

        page = rest_util.perform_paging(request, job_loads_grouped)
        serializer = JobLoadGroupListSerializer(page, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


# TODO: Remove this once the UI migrates to /load
class QueueDepthView(APIView):
    """This view is the endpoint for retrieving the queue depth for a given time range.
    """

    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        """Retrieves the queue depth for a given time range and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        started = rest_util.parse_timestamp(request, 'started')
        ended = rest_util.parse_timestamp(request, 'ended')
        rest_util.check_time_range(started, ended)

        duration = ended - started
        if datetime.timedelta(days=0) > duration or datetime.timedelta(days=31) < duration:
            raise BadParameter('Time range must be between 0 and 31 days')

        results = Queue.objects.get_historical_queue_depth(started, ended)
        return Response(results)

    def _process_job_type_depths(self, job_type_qry, job_types, queue_depth_dict, depth_times):
        """Processes the queue depths that are split by job type

        :param job_type_qry: the query with the depth results
        :type job_type_qry: :class:`queue.views.QueueDepthView.QueueDepthByJobTypeFilter`
        :param job_types: the list of job types processed
        :type job_types: list
        :param queue_depth_dict: Dict of {time: ({job type ID: count}, {priority: count})}
        :type queue_depth_dict: dict
        :param depth_times: List to populate with ascending depth times
        :type depth_times: list
        """

        job_types_set = set()
        for job_type_depth in job_type_qry:
            if job_type_depth.depth_time in queue_depth_dict:
                job_type_dict = queue_depth_dict[job_type_depth.depth_time][0]
            else:
                job_type_dict = {}
                queue_depth_dict[job_type_depth.depth_time] = (job_type_dict, {})
                depth_times.append(job_type_depth.depth_time)
            # Don't process depths of 0, these are just placeholder values to mark the depth_time
            if job_type_depth.depth:
                if job_type_depth.job_type_id not in job_types_set:
                    job_types.append({'id': job_type_depth.job_type_id, 'name': job_type_depth.job_type.name,
                                      'version': job_type_depth.job_type.version})
                    job_types_set.add(job_type_depth.job_type_id)
                job_type_dict[job_type_depth.job_type_id] = job_type_depth.depth

    def _process_priority_depths(self, priority_qry, priorities, queue_depth_dict):
        """Processes the queue depths that are split by priority. The queue_depth_dict must have already been processed
        by _process_job_type_depths().

        :param priority_qry: the query with the depth results
        :type priority_qry: :class:`queue.views.QueueDepthView.QueueDepthByPriorityFilter`
        :param priorities: the list of priorities processed
        :type priorities: list
        :param queue_depth_dict: Dict of {time: ({job type ID: count}, {priority: count})}
        :type queue_depth_dict: dict
        """

        priorities_set = set()
        for priority_depth in priority_qry:
            priority_dict = queue_depth_dict[priority_depth.depth_time][1]
            # Don't process depths of 0, these are just placeholder values to mark the depth_time
            if priority_depth.depth:
                if priority_depth.priority not in priorities_set:
                    priorities.append({'priority': priority_depth.priority})
                    priorities_set.add(priority_depth.priority)
                priority_dict[priority_depth.priority] = priority_depth.depth

    def _process_queue_depths(self, job_types, priorities, queue_depth_dict, depth_times):
        """Processes and creates the queue depth list

        :param job_types: the list of job types processed
        :type job_types: list
        :param priorities: the list of priorities processed
        :type priorities: list
        :param queue_depth_dict: Dict of {time: ({job type ID: count}, {priority: count})}
        :type queue_depth_dict: dict
        :param depth_times: List with ascending depth times
        :type depth_times: list
        :rtype: list
        :returns: list of queue depth data
        """

        queue_depths = []
        for depth_time in depth_times:
            job_type_dict = queue_depth_dict[depth_time][0]
            priority_dict = queue_depth_dict[depth_time][1]
            job_types_depths = []
            priority_depths = []
            total = 0
            for job_type in job_types:
                depth = 0
                if job_type['id'] in job_type_dict:
                    depth = job_type_dict[job_type['id']]
                job_types_depths.append(depth)
                total += depth
            for priority in priorities:
                depth = 0
                if priority['priority'] in priority_dict:
                    depth = priority_dict[priority['priority']]
                priority_depths.append(depth)
            queue_depths.append({'time': depth_time, 'depth_per_job_type': job_types_depths,
                                 'depth_per_priority': priority_depths, 'total_depth': total})

        return queue_depths


class QueueNewJobView(APIView):
    """This view is the endpoint for creating new jobs and putting them on the queue."""
    parser_classes = (JSONParser,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

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
        serializer = JobDetailsSerializer(job_details, context={'request': request})
        job_exe_url = urlresolvers.reverse('job_execution_details_view', args=[job_exe_id])
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=dict(location=job_exe_url))


class QueueNewRecipeView(APIView):
    """This view is the endpoint for queuing recipes and returns the detail information for the recipe that was queued.
    """
    parser_classes = (JSONParser,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

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
        serializer = RecipeDetailsSerializer(recipe_details, context={'request': request})
        recipe_url = urlresolvers.reverse('recipe_details_view', args=[recipe_id])
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=dict(location=recipe_url))


class QueueStatusView(APIView):
    """This view is the endpoint for retrieving the queue status.
    """
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        """Retrieves the current status of the queue and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        queue_status = Queue.objects.get_queue_status()
        return Response({'queue_status': queue_status})


class RequeueJobsView(APIView):
    """This view is the endpoint for requeuing jobs which have already been executed."""
    parser_classes = (JSONParser,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

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

        page = rest_util.perform_paging(request, jobs)
        serializer = JobListSerializer(page, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


# TODO: Remove this once the UI migrates to /queue/requeue-jobs/
class RequeueExistingJobView(APIView):
    """This view is the endpoint for requeuing jobs which have already been executed for the maximum number of tries
    """
    parser_classes = (JSONParser,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def post(self, request):
        """Increase max_tries, place it on the queue, and returns the new job information in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param job_id: The ID of the job to requeue. This job must exist and must be in a FAILED or CANCELED state.
        :rtype: int
        :returns: the HTTP response to send back to the user
        """
        job_id = request.DATA['job_id']

        try:
            Queue.objects.requeue_existing_job(job_id)
            job_details = Job.objects.get_details(job_id)
            serializer = JobDetailsSerializer(job_details, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Job.DoesNotExist:
            raise Http404
        except InvalidData:
            logger.exception('Invalid job data submitted for requeue: %i', job_id)
            return Response('Job meta data failed to validate: %i' % job_id, status=status.HTTP_400_BAD_REQUEST)
        except StatusError:
            logger.exception('Incorrect status for job submitted for requeue: %i', job_id)
            return Response('Job must be in the CANCELED or FAILED state for requeue',
                            status=status.HTTP_409_CONFLICT)
