# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import logging

import rest_framework.status as status
from django.db import transaction
from django.http.response import Http404, HttpResponse
from rest_framework.generics import GenericAPIView, ListAPIView, ListCreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from data.data.exceptions import InvalidData
from data.data.json.data_v6 import DataV6
from dataset.dataset_serializers import DataSetListSerializerV6, DataSetDetailsSerializerV6, DataSetFilesSerializerV6, DataSetMemberSerializerV6, DataSetMemberDetailsSerializerV6
from dataset.exceptions import InvalidDataSetDefinition, InvalidDataSetMember
from dataset.models import DataSet, DataSetMember
from dataset.definition.definition import DataSetDefinition
from dataset.definition.json.definition_v6 import DataSetDefinitionV6
import util.rest as rest_util
from util.rest import BadParameter

logger = logging.getLogger(__name__)

class DataSetView(ListCreateAPIView):
    """This view is the endpoint for retrieving the list of all datasets."""
    queryset = DataSet.objects.all()

    serializer_class = DataSetListSerializerV6

    def list(self, request):
        """Retrieves the list of all datasets and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if self.request.version == 'v6':
            return self.list_v6(request)
        else:
            raise Http404 # no datasets before v6

    def list_v6(self, request):
        """Retrieves the list of all datasets and returns it in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        # filter options:
        #   started, ended, dataset_id, keywords
        started = rest_util.parse_timestamp(request, 'started', required=False)
        ended = rest_util.parse_timestamp(request, 'ended', required=False)
        rest_util.check_time_range(started, ended)
        dataset_ids = rest_util.parse_int_list(request, 'id', required=False)
        keywords = rest_util.parse_string_list(request, 'keyword', required=False)

        order = rest_util.parse_string_list(request, 'order', required=False)

        data_sets = DataSet.objects.get_datasets_v6(started=started, ended=ended,
            dataset_ids=dataset_ids, keywords=keywords, order=order)

        page = self.paginate_queryset(data_sets)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request):
        """Creates a new dataset and returns a link to the detail URL

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`

        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if self.request.version == 'v6':
            return self.create_v6(request)
        else:
            raise Http404 # no datasets before v6

    def create_v6(self, request):
        """Creates or edits a dataset and returns a link to the detail URL

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        title = rest_util.parse_string(request, 'title', required=False)
        description = rest_util.parse_string(request, 'description', required=False)
        definition = rest_util.parse_dict(request, 'definition', required=True)

        # validate the definition
        try:
            dataset_def = DataSetDefinitionV6(definition=definition).get_definition()
        except InvalidDataSetDefinition as ex:
            message = 'DataSet definition is invalid'
            logger.exception(message)
            raise BadParameter('%s: %s' % (message, unicode(ex)))

        try:
            dataset = DataSet.objects.create_dataset_v6(dataset_def, title=title, description=description)
        except Exception as ex:
            message = 'Unable to create new dataset'
            logger.exception(message)
            raise BadParameter('%s: %s' % (message, unicode(ex)))

        try:
            dataset = DataSet.objects.get_details_v6(dataset.id)
        except DataSet.DoesNotExist:
            raise Http404

        url = reverse('dataset_details_view', args=[dataset.id], request=request)
        serializer = DataSetDetailsSerializerV6(dataset)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=dict(location=url))

class DataSetDetailsView(GenericAPIView):
    """This view is the endpoint for retrieving details of a specific dataset"""

    queryset = DataSet.objects.all()

    serializer_class = DataSetDetailsSerializerV6

    def get(self, request, dataset_id):
        """
        Retrieves the details for a data set and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param dataset_id: The dataset id
        :type dataset_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if self.request.version == 'v6':
            return self.get_v6(request, dataset_id=dataset_id)
        else:
            raise Http404

    def get_v6(self, request, dataset_id):
        """Retrieves the details for a dataset version and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param dataset_id: The dataset id
        :type dataset_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        try:
            dataset = DataSet.objects.get_details_v6(dataset_id)
        except DataSet.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(dataset)
        return Response(serializer.data)

    def post(self, request, dataset_id):
        """ Adds a datsetmember to the dataset

        :param request: the HTTP request
        :type request: :class:`rest_framework.request.Request`
        :param dataset_id: The id of the dataset
        :type dataset_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if self.request.version == 'v6':
            return self.post_v6(request, dataset_id=dataset_id)
        else:
            raise Http404 # no datasets before v6

    def post_v6(self, request, dataset_id):
        """ Adds a datsetmember to the dataset

        :param request: the HTTP request
        :type request: :class:`rest_framework.request.Request`
        :param dataset_id: The id of the dataset
        :type dataset_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        data = rest_util.parse_dict(request, 'data', required=True)

        # validate the definition
        try:
            data = DataV6(data=data).get_data()
        except InvalidData as ex:
            message = 'Data is invalid'
            logger.exception(message)
            raise BadParameter('%s: %s' % (message, unicode(ex)))

        try:
            dataset = DataSet.objects.get(pk=dataset_id)
        except DataSet.DoesNotExist:
            raise Http404

        try:
            dsm = DataSetMember.objects.create_dataset_member_v6(dataset=dataset, data=data)
        except InvalidDataSetMember as ex:
            message = 'DataSetMember is invalid'
            logger.exception(message)
            raise BadParameter('%s: %s' % (message, unicode(ex)))

        url = reverse('dataset_member_details_view', args=[dsm.id], request=request)
        serializer = DataSetMemberSerializerV6(dataset)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=dict(location=url))


class DataSetMembersView(GenericAPIView):
    """This view is the endpoint for retrieving members of a specific dataset"""

    queryset = DataSetMember.objects.all()

    serializer_class = DataSetMemberSerializerV6

    def list(self, request, dataset_id):
        """
        Retrieves the details for a data set and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param dataset_id: The dataset id
        :type dataset_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if self.request.version == 'v6':
            return self.list_v6(request, dataset_id=dataset_id)
        else:
            raise Http404

    def list_v6(self, request, dataset_id):
        """Retrieves the members for a dataset version and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param dataset_id: The dataset id
        :type dataset_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        try:
            dataset = DataSet.objects.get(pk=dataset_id)
        except DataSet.DoesNotExist:
            raise Http404

        dsm = DataSetMember.objects.get_dataset_members(dataset=dataset)

        serializer = self.get_serializer(dsm)
        return Response(serializer.data)


class DataSetMemberDetailsView(GenericAPIView):
    """This view is the endpoint for retrieving details of a specific dataset member"""

    queryset = DataSetMember.objects.all()

    serializer_class = DataSetMemberDetailsSerializerV6

    def get(self, request, dsm_id):
        """
        Retrieves the details for a data set and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param dsm_id: The dataset member id
        :type dsm_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if self.request.version == 'v6':
            return self.get_v6(request, dsm_id=dsm_id)
        else:
            raise Http404

    def get_v6(self, request, dataset_id):
        """Retrieves the details for a dataset version and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param dataset_id: The dataset id
        :type dataset_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        try:
            dataset = DataSet.objects.get_details_v6(dataset_id)
        except DataSet.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(dataset)
        return Response(serializer.data)


class DataSetValidationView(APIView):
    """This view is the endpoint for validating a new dataset before attempting to create it"""
    queryset = DataSet.objects.all()

    def post(self, request):
        """Validates a new dataset and returns any errors/warnings discovered

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if request.version == 'v6':
            return self.post_v6(request)
        else:
            Http404()

    def post_v6(self, request):
        """Validates a new dataset and returns any warnings discovered

        :param request: the HTTP POST request
        :type request: :class:`rest_framework.request.Request`
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        # Validate the minimum info is present:
        title = rest_util.parse_string(request, 'title', required=False)
        description = rest_util.parse_string(request, 'description', required=False)

        # Validate the dataset definition
        definition_dict = rest_util.parse_dict(request, 'definition', required=True)

        # Validate the dataset'
        validation = DataSet.objects.validate_dataset_v6(definition_dict, title=title, description=description)

        resp_dict = {'is_valid': validation.is_valid, 'errors': [e.to_dict() for e in validation.errors],
                     'warnings': [w.to_dict() for w in validation.warnings]}
        return Response(resp_dict)

class DataSetFilesView(ListCreateAPIView):
    """Returns the files associated with a specific dataset """

    serializer_class = DataSetFilesSerializerV6

    def list(self, request, name=None, version=None, dataset_id=None):
        """Determines api version and call specific method

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param name: The name of the dataset
        :type name: string
        :param version: The version of the dataset
        :type version: string
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        if self.request.version == 'v6':
            if name and version:
                return self.list_files_name_v6(request, name, version)
            elif dataset_id:
                return self.list_files_id_v6(request, dataset_id)
        else:
            raise Http404


    def list_files_name_v6(self, request, name, version):
        """ Returns a list of files associated with the given dataset

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param name: The name of the dataset
        :type name: string
        :param version: The version of the dataset
        :type version: string
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        return Response({'message': 'TODO'})


    def list_files_id_v6(self, request, dataset_id):
        """ Returns a list of files associated with the given dataset

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param name: The name of the dataset
        :type name: string
        :param version: The version of the dataset
        :type version: string
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        return Response({'message': 'TODO'})