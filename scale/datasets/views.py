# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.http.response import Http404, HttpResponse
from rest_framework.generics import GenericAPIView, ListAPIView, ListCreateAPIView, RetrieveAPIView

from datasets.dataset_serializers import DataSetListSerializerV6
import DataSet
import util.rest as rest_util

logger = logging.getLogger(__name__)

class DataSetsView(ListCreateAPIView):
    """This view is the endpoint for retrieving the list of all datasets."""
    queryset = DataSet.objects.all()
    
    def get_serializer_class(self):
        """Returns the appropriate serilazer based off the requests version of the REST API."""
        if self.request.version == 'v6':
            return DataSetListSerializerV6
        else: 
            raise Http404 # not implemented for versions < 6.0.0
        
    def list(self, request):
        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)

        names = rest_util.parse_string_list(request, 'name', required=False)
        categories = rest_util.parse_string_list(request, 'category', required=False)
        is_active = rest_util.parse_bool(request, 'is_active', default_value=True)
        is_operational = rest_util.parse_bool(request, 'is_operational', required=False)
        order = rest_util.parse_string_list(request, 'order', ['name', 'version'])
        
        data_sets = DataSet.objects.get_data_sets(started=started, ended=ended, names=names, categories=categories,
                                  is_active=is_active, is_operational=is_operational, order=order)
        
        page = self.paginate_queryset(data_sets)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

class DataSetsIDDetailsView(GenericAPIView):
    """This view is the endpoint for retrieving details of a specific dataset"""
    
    queryset = DataSet.objects.all()
    
    def get(self, request, name, version):
        """
        Retrieves the details for a data set and return them in JSON form
        
        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param data_set_name: The name of the data set
        :type data_set_name: str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        
    def get_serializer_class(self):
        if self.request.version == 'v6':
            return DataSetIDDetailsSerializerV6
        else: 
            raise Http404 # not implemented for versions < 6.0.0