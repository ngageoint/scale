"""Defines the views for the RESTful product services"""
from __future__ import unicode_literals

import logging

from django.http.response import Http404
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response

import util.rest as rest_util
from product.models import ProductFile
from product.serializers import ProductFileDetailsSerializer, ProductFileSerializer, ProductFileUpdateSerializer, ProductFileDetailsSerializerV5, \
    ProductFileUpdateSerializerV5, ProductFileSerializerV5
from source.models import SourceFile
from source.serializers import SourceFileSerializer
from storage.models import ScaleFile

logger = logging.getLogger(__name__)


class ProductsView(ListAPIView):
    """This view is the endpoint for retrieving a product by filename"""
    queryset = ScaleFile.objects.all()

    # TODO: remove when REST API v5 is removed
    def get_serializer_class(self):
        """Override the serializer for legacy API calls."""
        if self.request.version == 'v6':
            return ProductFileSerializer
        return ProductFileSerializerV5

    def list(self, request):
        """Retrieves the product for a given file name and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)
        time_field = rest_util.parse_string(request, 'time_field', required=False,
                                            accepted_values=ProductFile.VALID_TIME_FIELDS)

        job_type_ids = rest_util.parse_int_list(request, 'job_type_id', required=False)
        job_type_names = rest_util.parse_string_list(request, 'job_type_name', required=False)
        job_type_categories = rest_util.parse_string_list(request, 'job_type_category', required=False)
        job_ids = rest_util.parse_int_list(request, 'job_id', required=False)
        is_operational = rest_util.parse_bool(request, 'is_operational', required=False)
        is_published = rest_util.parse_bool(request, 'is_published', default_value=True)
        file_name = rest_util.parse_string(request, 'file_name', required=False)
        job_output = rest_util.parse_string(request, 'job_output', required=False)
        recipe_ids = rest_util.parse_int_list(request, 'recipe_id', required=False)
        recipe_type_ids = rest_util.parse_int_list(request, 'recipe_type_id', required=False)
        recipe_job = rest_util.parse_string(request, 'recipe_job', required=False)
        batch_ids = rest_util.parse_int_list(request, 'batch_id', required=False)

        order = rest_util.parse_string_list(request, 'order', required=False)

        products = ProductFile.objects.get_products(
            started=started, ended=ended, time_field=time_field, job_type_ids=job_type_ids,
            job_type_names=job_type_names, job_type_categories=job_type_categories, job_ids=job_ids,
            is_operational=is_operational, is_published=is_published, file_name=file_name, 
            job_output=job_output, recipe_ids=recipe_ids, recipe_type_ids=recipe_type_ids, 
            recipe_job=recipe_job, batch_ids=batch_ids, order=order,
        )

        page = self.paginate_queryset(products)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class ProductDetailsView(RetrieveAPIView):
    """This view is the endpoint for retrieving/updating details of a product file."""
    queryset = ScaleFile.objects.all()

    # TODO: remove when REST API v5 is removed
    def get_serializer_class(self):
        """Override the serializer for legacy API calls."""
        if self.request.version == 'v4' or self.request.version == 'v5':
            return ProductFileDetailsSerializerV5
        return ProductFileDetailsSerializer

    # TODO: remove the `file_name` arg when REST API v5 is removed
    def retrieve(self, request, product_id=None, file_name=None):
        """Retrieves the details for a product file and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param product_id: The id of the product
        :type product_id: int encoded as a string
        :param file_name: The name of the product
        :type file_name: string
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version != 'v6':
            return self.retrieve_v5(request, product_id, file_name)
        else:
            try:
                product = ProductFile.objects.get_details(product_id)
            except ScaleFile.DoesNotExist:
                raise Http404

        serializer = self.get_serializer(product)
        return Response(serializer.data)

    # TODO: remove when REST API v5 is removed
    def retrieve_v5(self, request, product_id=None, file_name=None):
        """Retrieves the details for a product file and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param product_id: The id of the product
        :type product_id: int encoded as a string
        :param file_name: The name of the product
        :type file_name: string
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        # Support retrieving by file name in addition to the usual identifier
        if file_name:
            products = ScaleFile.objects.filter(file_name=file_name, file_type='PRODUCT')
            products = products.values('id').order_by('-published')
            if not products:
                raise Http404
            product_id = products[0]['id']

        try:
            product = ProductFile.objects.get_details_v5(product_id)
        except ScaleFile.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(product)
        return Response(serializer.data)


class ProductSourcesView(ListAPIView):
    """This view is the endpoint for source files that a product file originated from."""
    queryset = ScaleFile.objects.all()
    serializer_class = SourceFileSerializer

    def list(self, request, product_id=None):
        """Retrieves the source files for a given product id and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        try:
            ScaleFile.objects.get(id=product_id, file_type='PRODUCT')
        except ScaleFile.DoesNotExist:
            raise Http404

        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)
        time_field = rest_util.parse_string(request, 'time_field', required=False,
                                            accepted_values=SourceFile.VALID_TIME_FIELDS)

        is_parsed = rest_util.parse_bool(request, 'is_parsed', required=False)
        file_name = rest_util.parse_string(request, 'file_name', required=False)

        order = rest_util.parse_string_list(request, 'order', required=False)

        sources = ProductFile.objects.get_product_sources(product_id, started, ended, time_field, is_parsed,
                                                          file_name, order)

        page = self.paginate_queryset(sources)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class ProductUpdatesView(ListAPIView):
    """This view is the endpoint for retrieving product updates over a given time range."""
    queryset = ScaleFile.objects.all()

    # TODO: remove when REST API v5 is removed
    def get_serializer_class(self):
        """Override the serializer for legacy API calls."""
        if self.request.version == 'v6':
            return ProductFileUpdateSerializer
        return ProductFileUpdateSerializerV5


    def list(self, request):
        """Retrieves the product updates for a given time range and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        job_type_ids = rest_util.parse_int_list(request, 'job_type_id', required=False)
        job_type_names = rest_util.parse_string_list(request, 'job_type_name', required=False)
        job_type_categories = rest_util.parse_string_list(request, 'job_type_category', required=False)
        is_operational = rest_util.parse_bool(request, 'is_operational', required=False)
        file_name = rest_util.parse_string(request, 'file_name', required=False)

        order = rest_util.parse_string_list(request, 'order', required=False)

        products = ProductFile.objects.get_products(
            started=started, ended=ended, job_type_ids=job_type_ids, job_type_names=job_type_names,
            job_type_categories=job_type_categories, is_operational=is_operational, file_name=file_name, order=order
        )

        page = self.paginate_queryset(products)
        ProductFile.objects.populate_source_ancestors(page)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
