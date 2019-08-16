# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import logging

import rest_framework.status as status
from django.http.response import Http404, HttpResponse
from rest_framework.generics import GenericAPIView, ListAPIView, ListCreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from data.data.exceptions import InvalidData
from data.data.json.data_v6 import DataV6, convert_data_to_v6_json
from dataset.dataset_serializers import DataSetListSerializerV6, DataSetDetailsSerializerV6, DataSetFileSerializerV6, DataSetMemberSerializerV6, DataSetMemberDetailsSerializerV6
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

        if self.request.version == 'v6' or self.request.version == 'v7':
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

        if self.request.version == 'v6' or self.request.version == 'v7':
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
            dataset_def = DataSetDefinitionV6(definition=definition, do_validate=True).get_definition()
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

        if self.request.version == 'v6' or self.request.version == 'v7':
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

        if self.request.version == 'v6' or self.request.version == 'v7':
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

        template = rest_util.parse_dict(request, 'data_template', required=False)
        dry_run = rest_util.parse_bool(request, 'dry_run', default_value=False)
        
        #file filters
        data_started = rest_util.parse_timestamp(request, 'data_started', required=False)
        data_ended = rest_util.parse_timestamp(request, 'data_ended', required=False)
        rest_util.check_time_range(data_started, data_ended)

        source_started = rest_util.parse_timestamp(request, 'source_started', required=False)
        source_ended = rest_util.parse_timestamp(request, 'source_ended', required=False)
        rest_util.check_time_range(source_started, source_ended)

        source_sensor_classes = rest_util.parse_string_list(request, 'source_sensor_class', required=False)
        source_sensors = rest_util.parse_string_list(request, 'source_sensor', required=False)
        source_collections = rest_util.parse_string_list(request, 'source_collection', required=False)
        source_tasks = rest_util.parse_string_list(request, 'source_task', required=False)

        mod_started = rest_util.parse_timestamp(request, 'modified_started', required=False)
        mod_ended = rest_util.parse_timestamp(request, 'modified_ended', required=False)
        rest_util.check_time_range(mod_started, mod_ended)

        job_type_ids = rest_util.parse_int_list(request, 'job_type_id', required=False)
        job_type_names = rest_util.parse_string_list(request, 'job_type_name', required=False)
        job_ids = rest_util.parse_int_list(request, 'job_id', required=False)
        file_names = rest_util.parse_string_list(request, 'file_name', required=False)
        job_outputs = rest_util.parse_string_list(request, 'job_output', required=False)
        recipe_ids = rest_util.parse_int_list(request, 'recipe_id', required=False)
        recipe_type_ids = rest_util.parse_int_list(request, 'recipe_type_id', required=False)
        recipe_nodes = rest_util.parse_string_list(request, 'recipe_node', required=False)
        batch_ids = rest_util.parse_int_list(request, 'batch_id', required=False)

        order = rest_util.parse_string_list(request, 'order', required=False)
        
        data = rest_util.parse_dict_list(request, 'data', required=False)
        data_list = []

        try:
            if data:
                for d in data:
                    data = DataV6(data=d, do_validate=True).get_data()
                    data_list.append(data)
            else:
                data_list = DataSetMember.objects.build_data_list(template=template, 
                    data_started=data_started, data_ended=data_ended,
                    source_started=source_started, source_ended=source_ended,
                    source_sensor_classes=source_sensor_classes, source_sensors=source_sensors,
                    source_collections=source_collections, source_tasks=source_tasks,
                    mod_started=mod_started, mod_ended=mod_ended, job_type_ids=job_type_ids,
                    job_type_names=job_type_names, job_ids=job_ids,
                    file_names=file_names, job_outputs=job_outputs, recipe_ids=recipe_ids,
                    recipe_type_ids=recipe_type_ids, recipe_nodes=recipe_nodes, batch_ids=batch_ids,
                    order=order)
        except InvalidData as ex:
            message = 'Data is invalid'
            logger.exception(message)
            raise BadParameter('%s: %s' % (message, unicode(ex)))
            
        try:
            dataset = DataSet.objects.get(pk=dataset_id)
        except DataSet.DoesNotExist:
            raise Http404

        validation = DataSetMember.objects.validate_data_list(dataset=dataset, data_list=data_list)
        members = []
        if validation.is_valid and not dry_run:
            members = DataSetMember.objects.create_dataset_members(dataset=dataset, data_list=data_list)
            serializer = DataSetMemberSerializerV6(members, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif not validation.is_valid:
            raise BadParameter('%s: %s' % ('Error(s) validating data against dataset', validation.errors))

        resp_dict = []
        for dl in data_list:
            resp_dict.append(convert_data_to_v6_json(dl).get_dict())
        return Response(resp_dict)


class DataSetMembersView(ListAPIView):
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

        if self.request.version == 'v6' or self.request.version == 'v7':
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

        page = self.paginate_queryset(dsm)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


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

        if self.request.version == 'v6' or self.request.version == 'v7':
            return self.get_v6(request, dsm_id=dsm_id)
        else:
            raise Http404

    def get_v6(self, request, dsm_id):
        """Retrieves the details for a dataset member and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param dsm_id: The dataset member id
        :type dsm_id: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        try:
            dsm = DataSetMember.objects.get_details_v6(dsm_id)
        except DataSet.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(dsm)
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

