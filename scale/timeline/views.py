from __future__ import unicode_literals

from django.http.response import Http404
from django.http import JsonResponse
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
import rest_framework.status as status

import util.rest as rest_util
from job.models import JobType
from recipe.models import RecipeType


class TimelineRecipeTypeView(ListAPIView):
    """This view is the endpoint for retrieving recipe type timeline information"""

    def list(self, request):
        """Retrieves the list of recipe types and returns it in JSON form

        :param request: The HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v6':
            return self._list_v6(request)
        elif request.version == 'v7':
            return self._list_v6(request)

        raise Http404()

    def _list_v6(self, request):
        """Retrieves the list of all recipes and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        type_ids = rest_util.parse_int_list(request, 'recipe_type_id', required=False)
        type_names = rest_util.parse_string_list(request, 'recipe_type_name', required=False)

        if not started:
            return Response('Invalid parameter: start date is required', status=status.HTTP_400_BAD_REQUEST)

        results = RecipeType.objects.get_timeline_recipes_json(started=started, ended=ended, type_ids=type_ids,
                                                               type_names=type_names)
        data = {
            'results': results
        }
        return JsonResponse(data, content_type='application/json')

class TimelineJobTypeView(ListAPIView):
    """This view is the endpoint for retrieving recipe type timeline information"""

    def list(self, request):
        """Retrieves the list of recipe types and returns it in JSON form

        :param request: The HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        print('TimelineJobTypeView')
        if request.version == 'v6':
            return self._list_v6(request)
        elif request.version == 'v7':
            return self._list_v6(request)

        raise Http404()

    def _list_v6(self, request):
        """Retrieves the list of all recipes and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        import pdb; pdb.set_trace()
        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        type_ids = rest_util.parse_int_list(request, 'job_type_id', required=False)
        type_names = rest_util.parse_string_list(request, 'job_type_name', required=False)

        # try:
        results = JobType.objects.get_timeline_jobs_json(started=started, ended=ended, type_ids=type_ids,
                                                         type_names=type_names)
        data = {
            'results': results
        }
        return JsonResponse(data, content_type='application/json')

