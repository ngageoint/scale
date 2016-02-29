'''Defines the views for the RESTful product services'''
from __future__ import unicode_literals

import logging

import rest_framework.status as status
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

import util.rest as rest_util
from product.models import ProductFile
from product.serializers import ProductFileListSerializer, ProductFileUpdateListSerializer

logger = logging.getLogger(__name__)


class ProductsView(APIView):
    '''This view is the endpoint for retrieving a product by filename
    '''
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        '''Retrieves the product for a given file name and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''
        started = rest_util.parse_timestamp(request, u'started', required=False)
        ended = rest_util.parse_timestamp(request, u'ended', required=False)
        rest_util.check_time_range(started, ended)

        job_type_ids = rest_util.parse_int_list(request, u'job_type_id', required=False)
        job_type_names = rest_util.parse_string_list(request, u'job_type_name', required=False)
        job_type_categories = rest_util.parse_string_list(request, u'job_type_category', required=False)
        is_operational = rest_util.parse_bool(request, u'is_operational', required=False)
        file_name = rest_util.parse_string(request, u'file_name', required=False)

        order = rest_util.parse_string_list(request, u'order', required=False)

        products = ProductFile.objects.get_products(started, ended, job_type_ids, job_type_names, job_type_categories,
                                                    is_operational, file_name, order)
        page = rest_util.perform_paging(request, products)
        serializer = ProductFileListSerializer(page, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductUpdatesView(APIView):
    '''This view is the endpoint for retrieving product updates over a given time range.
    '''

    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request):
        '''Retrieves the product updates for a given time range and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        '''
        started = rest_util.parse_timestamp(request, u'started', required=False)
        ended = rest_util.parse_timestamp(request, u'ended', required=False)
        rest_util.check_time_range(started, ended)

        job_type_ids = rest_util.parse_int_list(request, u'job_type_id', required=False)
        job_type_names = rest_util.parse_string_list(request, u'job_type_name', required=False)
        job_type_categories = rest_util.parse_string_list(request, u'job_type_category', required=False)
        is_operational = rest_util.parse_bool(request, u'is_operational', required=False)
        file_name = rest_util.parse_string(request, u'file_name', required=False)

        order = rest_util.parse_string_list(request, u'order', required=False)

        products = ProductFile.objects.get_products(started, ended, job_type_ids, job_type_names, job_type_categories,
                                                    is_operational, file_name, order)
        page = rest_util.perform_paging(request, products)
        ProductFile.objects.populate_source_ancestors(page)
        serializer = ProductFileUpdateListSerializer(page, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
