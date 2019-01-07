# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.http.response import Http404, HttpResponse
from rest_framework.generics import GenericAPIView, ListAPIView, ListCreateAPIView, RetrieveAPIView

from datasets.dataset_serializers import DataSetListSerializerV6
import DataSet
import util.rest as rest_util

logger = logging.getLogger(__name__)

class DataSetView(ListCreateAPIView):
    """This view is the endpoint for retrieving the list of all datasets."""
    queryset = DataSet.objects.all()

    serilazer_class = DataSetSerializer

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
        #   created_time, dataset_id
        created_time = rest_util.parse_timestamp(request, 'created_time', required=False)
        dataset_ids = rest_util.parse_int_list(request, 'dataset_id', required=False)
        dataset_names = rest_util.parse_string_list(request, 'dataset_name', required=False)

        order = rest_util.parse_string_list(request, 'order', ['name', 'version'])
        
        data_sets = DataSet.objects.get_datasets_v6(created_time=created_time, 
            dataset_id=dataset_ids, dataset_names, order=order)
        
        page = self.paginate_queryset(data_sets)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

class DataSetIDDetailsView(GenericAPIView):
    """This view is the endpoint for retrieving/updating the details of a dataset by id"""
    queryset = DataSet.objects.all()
    
    serializer_class = DataSetSerializer
    
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
            dataset = DataSet.objects.get_details_v6(dataset_id)
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
        dataset_dict = rest_util.parse_dict(reequest, '', required=False)
        
        try:
            if dataset_dict:
                dataset = DataSet(dataset_dict)
        except InvalidDatasetDefinition as ex:
            raise BadParameter('DataSet invalid: %s' % unicode(ex))
        
        # validate dataset definition
            
        # update the dataset
        try: 
            DataSet.objects.edit_dataset_v6(dataset_id=dataset, definition=dataset.definition)
        except (ValueError, Exception) as ex:
            logger.exception('Unable to update dataset: %i', dataset_id)
            raise BadParameter(unicode(ex))
    
class DataSetVersionsView():
    """This view is the endpoint for retrieving the details of a specific dataset by version"""
    queryset = DataSet.objects.all()
    
    serializer_class = DataSetSerializer
    
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

        datasets = DataSet.objects.get_dataset_revisions_v6(name, order)

        page = self.paginate_queryset(datasets)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class DataSetDetailsView(GenericAPIView):
    """This view is the endpoint for retrieving details of a specific dataset"""
    
    queryset = DataSet.objects.all()
    
    serializer_class = DataSetDetailsSerializer
    
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
                definition = DataSetDefinition(dataset_dict).get_definition()
        except InvalidDatasetDefinition as ex:
            raise BadParameter('DataSet definition invalid: %s' % unicode(ex))
        
        # fetch the current dataset model
        try:
            dataset = DataSet.objects.get(name=name, version=version)
        except DataSet.DoesNotExist
            raise Http404
            
        # Edit the dataset
        try:
            with transaction.atomic():
                DataSet.objects.edit_dataset_v6(dataset_id=dataset.id, ...)
        except (ValueError, InvalidDatasetDefinition) as ex:
            logger.exception('Unable to update dataset: %i', dataset.id)
            raise BadParameter(unicode(ex))
            
        return HttpResponse(status=204)

    def get_serializer_class(self):
        if self.request.version == 'v6':
            return DataSetIDDetailsSerializerV6
        else: 
            raise Http404 # not implemented for versions < 6.0.0

class DataSetRevisionsView():
    """This view is for retrieving the revisions of a certain dataset"""
    queryset = DataSet.objects.all()
    
    serializer_class = DataSetRevisionSerializer
    
    def list(self, request, name, version):
        """Determine api version and call specific method

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
            return self.list_v6(request, name, version)
        else:
            raise Http404
            
    def list_v6(self, request, name, version):
        """Retrieves the list of versions for a dataset with the given name and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param name: The name of the dataset
        :type name: string
        :param version: The version of the dataset
        :type version: string
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        order = ['-revision_num']

        try:
            dataset_revisions = DataSetRevision.objects.get_dataset_revisions_v6(name, version, order)
        except DataSet.DoesNotExist:
            raise Http404

        page = self.paginate_queryset(dataset_revisions)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
    
class DataSetRevisionDetailsView():
    """This view is for retrieving the details of a specific revision of a dataset"""
    queryset = DataSet.objects.all()
    
    serializer_class = DataSetRevisionDetailsSerializer
    
    def get(self, request, name, version, revision_num):
        """Retrieves the details for a dataset version and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param name: The name of the dataset
        :type name: string
        :param version: The version of the dataset
        :type version: string
        :param revision_num: The revision number of the dataset
        :type revision_num: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        if self.request.version == 'v6':
            return self.get_v6(request, name, version, revision_num)
        else:
            raise Http404

    def get_v6(self, request, name, version, revision_num):
        """Retrieves the details for a dataset version and return them in JSON form

        :param request: the HTTP GET request
        :type request: :class:`rest_framework.request.Request`
        :param name: The name of the dataset
        :type name: string
        :param version: The version of the dataset
        :type version: string
        :param revision_num: The revision number of the dataset
        :type revision_num: int encoded as a str
        :rtype: :class:`rest_framework.response.Response`
        :returns: the HTTP response to send back to the user
        """

        try:
            dataset_rev = DataSetRevision.objects.get_details_v6(name, version, revision_num)
        except DataSet.DoesNotExist:
            raise Http404
        except DataSetRevision.DoesNotExist:
            raise Http404

        serializer = self.get_serializer(dataset_rev)
        return Response(serializer.data)

class DataSetValidationView():
    """This view is the endpoint for validating a new dataset before attempting to actually create it"""
    queryset = DataSet.objects.all()
    
    def post(self, request):
        """Validates a new dataset and returns any warnings discovered
        
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

        # Validate the dataset definition
        definition_dict = rest_util.parse_dict(request, 'definition', required=False)

        # Validate the dataset        
        validation = DataSet.objects.validate_dataset_v6(definition=definition)
        
        resp_dict = {'is_valid': validation.is_valid, 'errors': [e.to_dict() for e in validation.errors],
                     'warnings': [w.to_dict() for w in validation.warnings]}
        return Response(resp_dict)
