from __future__ import unicode_literals

import logging

import rest_framework.status as status
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import JSONParser
from rest_framework.response import Response

from job.models import JobType
from queue.models import Queue
import util.rest as rest_util
from util.rest import BadParameter

logger = logging.getLogger(__name__)


class QueueScaleHelloView(GenericAPIView):
    """This view is the endpoint for queuing new Scale Hello jobs."""
    parser_classes = (JSONParser,)
    #queryset = Job.objects.all()

    def post(self, request):
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
