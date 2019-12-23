"""Defines the serializers for jobs and job types"""
from __future__ import absolute_import

import logging

import rest_framework.serializers as serializers

from storage.serializers import ScaleFileSerializerV6, ScaleFileDetailsSerializerV6, ScaleFileBaseSerializerV6
from util.rest import ModelIdSerializer

logger = logging.getLogger(__name__)

class DataSetFileBaseSerializerV6(ModelIdSerializer):
    """Converts the datasetfile model fields to REST output"""
    parameter_name = serializers.CharField()
    scale_file = ScaleFileBaseSerializerV6()
    
class DataSetFileSerializerV6(DataSetFileBaseSerializerV6):
    """Converts the datasetfile model fields to REST output"""
    parameter_name = serializers.CharField()
    scale_file = ScaleFileSerializerV6()
    
class DataSetBaseSerializerV6(ModelIdSerializer):
    """Converts dataset model fields to REST output"""
    title = serializers.CharField()
    description = serializers.CharField()
    created = serializers.DateTimeField()

class DataSetListSerializerV6(DataSetBaseSerializerV6):
    """Converts dataset model fields to REST output"""
    definition = serializers.JSONField(source='get_v6_definition_json', default=None)
    files = serializers.IntegerField()

class DataSetMemberSerializerV6(ModelIdSerializer):
    """Converts datasetmember model fields to REST output"""
    created = serializers.DateTimeField()
    data = serializers.JSONField(source='get_v6_data_json', required=False)
    file_ids = serializers.ListField(child=serializers.IntegerField())

class DataSetDetailsSerializerV6(DataSetBaseSerializerV6):
    """Converts dataset model fields to REST output"""
    definition = serializers.JSONField(source='get_v6_definition_json')
    members = DataSetMemberSerializerV6(source='get_dataset_members_json', required=False, many=True)
    files = DataSetFileBaseSerializerV6(source='get_dataset_files_json', required=False, many=True)

class DataSetMemberDetailsSerializerV6(DataSetMemberSerializerV6):
    dataset = ModelIdSerializer()
    files = DataSetFileSerializerV6(required=False, many=True)