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

from dataset.dataset_serializers import DataSetListSerializerV6, DataSetDetailsSerializerV6
from dataset.exceptions import InvalidDataSetDefinition
from dataset.models import DataSet
from dataset.definition.definition import DataSetDefinition
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
        #   created_time, dataset_id, dataset_name
        created_time = rest_util.parse_timestamp(request, 'created', required=False)
        dataset_ids = rest_util.parse_int_list(request, 'id', required=False)
        dataset_names = rest_util.parse_string_list(request, 'name', required=False)

        order = rest_util.parse_string_list(request, 'order', ['name', 'version'])

        data_sets = DataSet.objects.get_datasets_v6(created_time=created_time,
            dataset_ids=dataset_ids, dataset_names=dataset_names, order=order)

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

        name = rest_util.parse_string(request, 'name', required=False)
        title = rest_util.parse_string(request, 'title', required=False)
        description = rest_util.parse_string(request, 'description', required=False)
        version = rest_util.parse_string(request, 'version', required=False)
        definition = rest_util.parse_dict(request, 'definition', required=True)

        # validate the definition
        try:
            dataset_def = DataSetDefinition(definition)
        except InvalidDataSetDefinition as ex:
            message = 'DataSet definition is invalid'
            logger.exception(message)
            raise BadParameter('%s: %s' % (message, unicode(ex)))

        existing_dataset = DataSet.objects.filter(name=name, version=version).first()
        if not existing_dataset:
            try:
                dataset = DataSet.objects.create_dataset_v6(version, dataset_def, name=name, title=title, description=description)
            except Exception as ex:
                message = 'Unable to create new dataset'
                logger.exception(message)
                raise BadParameter('%s: %s' % (message, unicode(ex)))
        else:
            try:
                DataSet.objects.edit_dataset_v6(existing_dataset.id, definition, title=title, description=description)
            except Exception as ex:
                message = 'Unable to edit dataset: %i' % existing_dataset.id
                logger.exception(message)
                raise BadParameter('%s: %s' % (message, unicode(ex)))

        try:
            dataset = DataSet.objects.get_details_v6(name, version)
        except DataSet.DoesNotExist:
            raise Http404

        url = reverse('dataset_details_view', args=[dataset.name, dataset.version], request=request)
        serializer = DataSetDetailsSerializerV6(dataset)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=dict(location=url))

class DataSetIDDetailsView(GenericAPIView):
    """This view is the endpoint for retrieving/updating the details of a dataset by id"""
    queryset = DataSet.objects.all()

    serializer_class = DataSetDetailsSerializerV6

    def get(self, request, dataset_id):
        """Retrieves the details for a dataset and returns them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param dataset_id: The id of the dataset
        :type dataset_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        if self.request.version == 'v6':
            return self.get_v6(request, dataset_id)
        else:
            raise Http404 # not implemented for versions < 6

    def get_v6(self, request, dataset_id):
        """Retrieves the details for a dataset and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param dataset_id: The id of the dataset
        :type dataset_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        try:
            dataset = DataSet.objects.get_dataset_id_v6(dataset_id)
        except DataSet.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(dataset)
        return Response(serializer.data)

    def patch(self, request, dataset_id):
        """Edits an existing dataset via dataset_id and returns the updated details

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param dataset_id: The id of the dataset
        :type dataset_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if self.request.version == 'v6':
            return self.patch_v6(request, dataset_id)
        else:
            raise Http404

    # Dataset TODO
    def patch_v6(self, request, dataset_id):
        """Edits an existing dataset via dataset_id and returns the updated details

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param dataset_id: The id of the dataset
        :type dataset_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        # validate the given dataset interface
        dataset_dict = rest_util.parse_dict(request, '', required=False)

        try:
            if dataset_dict:
                dataset = DataSet(dataset_dict)
        except InvalidDataSetDefinition as ex:
            raise BadParameter('DataSet invalid: %s' % unicode(ex))

        # validate dataset definition

        # update the dataset
        try:
           dataset = DataSet.objects.edit_dataset_v6(dataset_id=dataset, definition=dataset.definition)
        except (ValueError, Exception) as ex:
            logger.exception('Unable to update dataset: %i', dataset_id)
            raise BadParameter(unicode(ex))

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
            return self.post_v6(request, dataset_id)
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

        # TODO - implement when implement datasetmember/file

        return Response({'message': 'To Be implemented'})

class DataSetDetailsView(GenericAPIView):
    """This view is the endpoint for retrieving details of a specific dataset"""

    queryset = DataSet.objects.all()

    serializer_class = DataSetDetailsSerializerV6

    def get(self, request, name, version):
        """
        Retrieves the details for a data set and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param name: The name of the dataset
        :type name: string
        :param dataset_version: The version of the dataset
        :type version: string
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if self.request.version == 'v6':
            return self.get_v6(request, name, version)
        else:
            raise Http404

    def get_v6(self, request, name, version):
        """Retrieves the details for a dataset version and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param name: The name of the dataset
        :type name: string
        :param version: The version of the dataset
        :type version: string
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        try:
            dataset = DataSet.objects.get_details_v6(name, version)
        except DataSet.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(dataset)
        return Response(serializer.data)


    def patch(self, request, name, version):
        """Edits an existing dataset and returns the updated details

        :param request: the HTTP PATCH request
        :type request: :class:`rest_framework.request.Request`
        :param name: The name of the dataset
        :type name: string
        :param version: The version of the dataset
        :type version: string
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if self.request.version == 'v6':
            return self.patch_v6(request, name, version)
        else:
            raise Http404

    def patch_v6(self, request, name, version):
        """Edits an existing dataset and returns the updated details

        :param request: the HTTP PATCH request
        :type request: :class:`rest_framework.request.Request`
        :param name: The name of the dataset
        :type name: string
        :param version: The version of the dataset
        :type version: string
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        # validate the dataset configuration
        dataset_dict = rest_util.parse_dict(request, 'definition', required=False)

        try:
            if dataset_dict:
                definition = DataSetDefinition(dataset_dict).get_dict()
        except InvalidDataSetDefinition as ex:
            raise BadParameter('DataSet definition invalid: %s' % unicode(ex))

        # fetch the current dataset model
        try:
            dataset = DataSet.objects.get(name=name, version=version)
        except DataSet.DoesNotExist:
            raise Http404

        # Edit the dataset
        try:
            with transaction.atomic():
                # DataSet.objects.edit_dataset_v6(dataset_id=dataset.id, ...)
                i = 0
        except (ValueError, InvalidDataSetDefinition) as ex:
            logger.exception('Unable to update dataset: %i', dataset.id)
            raise BadParameter(unicode(ex))

        return HttpResponse(status=204)

    # def get_serializer_class(self):
    #     if self.request.version == 'v6':
    #         return DataSetIDDetailsSerializerV6
    #     else:
    #         raise Http404 # not implemented for versions < 6.0.0

class DataSetVersionsView(ListCreateAPIView):
    """This view is the endpoint for retrieving the details of a specific dataset by version"""
    queryset = DataSet.objects.all()

    serializer_class = DataSetDetailsSerializerV6

    def list(self, request, name):
        """Determines api version and call specific method

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param name: The name of the dataset
        :type name: string
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        if self.request.version == 'v6':
            return self.list_v6(request, name)
        else:
            raise Http404

    def list_v6(self, request, name):
        """Retrieves the list of versions for a dataset with the given name and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param name: The name of the dataset
        :type name: string
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """
        order = ['-version']

        datasets = DataSet.objects.get_dataset_versions_v6(name, order)

        page = self.paginate_queryset(datasets)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

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
        name = rest_util.parse_string(request, 'name', required=True)
        version = rest_util.parse_string(request, 'version', required=True)
        title = rest_util.parse_string(request, 'title', required=False)
        description = rest_util.parse_string(request, 'description', required=False)

        # Validate the dataset definition
        definition_dict = rest_util.parse_dict(request, 'definition', required=True)

        # Validate the dataset'
        validation = DataSet.objects.validate_dataset_v6(name, version, definition_dict, title=title, description=description)

        resp_dict = {'is_valid': validation.is_valid, 'errors': [e.to_dict() for e in validation.errors],
                     'warnings': [w.to_dict() for w in validation.warnings]}
        return Response(resp_dict)

class DataSetFilesView(ListCreateAPIView):
    """Returns the files associated with a specific dataset """

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