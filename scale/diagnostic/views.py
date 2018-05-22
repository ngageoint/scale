from __future__ import unicode_literals

import logging

from django.http.response import Http404
import rest_framework.status as status
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import JSONParser
from rest_framework.response import Response

from job.models import JobType
from queue.models import Queue
from queue.serializers import QueueStatusSerializer
from recipe.configuration.data.recipe_data import RecipeData
from recipe.models import RecipeType
import util.rest as rest_util
from util.rest import BadParameter

logger = logging.getLogger(__name__)


class QueueScaleBakeView(GenericAPIView):
    """This view is the endpoint for queuing new Scale Bake jobs."""
    parser_classes = (JSONParser,)
    queryset = Queue.objects.all()
    serializer_class = QueueStatusSerializer

    def post(self, request):
        """Determine api version and call specific method

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v4':
            return self.post_v4(request)
        elif request.version == 'v5':
            return self.post_v5(request)
        elif request.version == 'v6':
            return self.post_v6(request)

        raise Http404()
        
    # TODO: remove when REST API v4 is removed
    def post_v4(self, request):
        """Handles v4 post request

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        return self.queue_bake_jobs(request)
        
    def post_v5(self, request):
        """Handles v5 post request

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        return self.queue_bake_jobs(request)
        
    def post_v6(self, request):
        """Handles v6 post request

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        return self.queue_bake_jobs(request)
        
    def queue_bake_jobs(self, request):
        """Creates and queues the specified number of Scale Bake jobs

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        num = rest_util.parse_int(request, 'num')

        if num < 1:
            raise BadParameter('num must be at least 1')

        # TODO: in the future, send command message to do this asynchronously
        job_type = JobType.objects.get(name='scale-bake', version='1.0')
        for _ in xrange(num):
            Queue.objects.queue_new_job_for_user(job_type, {})

        return Response(status=status.HTTP_202_ACCEPTED)


class QueueScaleCasinoView(GenericAPIView):
    """This view is the endpoint for queuing new Scale Casino recipes."""
    parser_classes = (JSONParser,)
    queryset = Queue.objects.all()
    serializer_class = QueueStatusSerializer

    def post(self, request):
        """Determine api version and call specific method

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v4':
            return self.post_v4(request)
        elif request.version == 'v5':
            return self.post_v5(request)
        elif request.version == 'v6':
            return self.post_v6(request)

        raise Http404()
        
    # TODO: remove when REST API v4 is removed
    def post_v4(self, request):
        """Handles v4 post request

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        return self.queue_casino_recipes(request)
        
    def post_v5(self, request):
        """Handles v5 post request

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        return self.queue_casino_recipes(request)
        
    def post_v6(self, request):
        """Handles v6 post request

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        return self.queue_casino_recipes(request)
        
    def queue_casino_recipes(self, request):
        """Creates and queues the specified number of Scale Casino recipes

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        num = rest_util.parse_int(request, 'num')

        if num < 1:
            raise BadParameter('num must be at least 1')

        # TODO: in the future, send command message to do this asynchronously
        recipe_type = RecipeType.objects.get(name='scale-casino', version='1.0')
        for _ in xrange(num):
            Queue.objects.queue_new_recipe_for_user(recipe_type, RecipeData())

        return Response(status=status.HTTP_202_ACCEPTED)


class QueueScaleHelloView(GenericAPIView):
    """This view is the endpoint for queuing new Scale Hello jobs."""
    parser_classes = (JSONParser,)
    queryset = Queue.objects.all()
    serializer_class = QueueStatusSerializer

    def post(self, request):
        """Determine api version and call specific method

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v4':
            return self.post_v4(request)
        elif request.version == 'v5':
            return self.post_v5(request)
        elif request.version == 'v6':
            return self.post_v6(request)

        raise Http404()
        
    # TODO: remove when REST API v4 is removed
    def post_v4(self, request):
        """Handles v4 post request

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        return self.queue_hello_jobs(request)
        
    def post_v5(self, request):
        """Handles v5 post request

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        return self.queue_hello_jobs(request)
        
    def post_v6(self, request):
        """Handles v6 post request

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        return self.queue_hello_jobs(request)
        
    def queue_hello_jobs(self, request):
        """Creates and queues the specified number of Scale Hello jobs

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        num = rest_util.parse_int(request, 'num')

        if num < 1:
            raise BadParameter('num must be at least 1')

        # TODO: in the future, send command message to do this asynchronously
        job_type = JobType.objects.get(name='scale-hello', version='1.0')
        for _ in xrange(num):
            Queue.objects.queue_new_job_for_user(job_type, {})

        return Response(status=status.HTTP_202_ACCEPTED)


class QueueScaleRouletteView(GenericAPIView):
    """This view is the endpoint for queuing new Scale Roulette jobs."""
    parser_classes = (JSONParser,)
    queryset = Queue.objects.all()
    serializer_class = QueueStatusSerializer

    def post(self, request):
        """Determine api version and call specific method

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v4':
            return self.post_v4(request)
        elif request.version == 'v5':
            return self.post_v5(request)
        elif request.version == 'v6':
            return self.post_v6(request)

        raise Http404()
        
    # TODO: remove when REST API v4 is removed
    def post_v4(self, request):
        """Handles v4 post request

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        return self.queue_roulette_jobs(request)
        
    def post_v5(self, request):
        """Handles v5 post request

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        return self.queue_roulette_jobs(request)
        
    def post_v6(self, request):
        """Handles v6 post request

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        return self.queue_roulette_jobs(request)
        
    def queue_roulette_jobs(self, request):
        """Creates and queues the specified number of Scale Roulette jobs

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        num = rest_util.parse_int(request, 'num')

        if num < 1:
            raise BadParameter('num must be at least 1')

        # TODO: in the future, send command message to do this asynchronously
        job_type = JobType.objects.get(name='scale-roulette', version='1.0')
        for _ in xrange(num):
            Queue.objects.queue_new_job_for_user(job_type, {})

        return Response(status=status.HTTP_202_ACCEPTED)
