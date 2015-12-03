'''Defines the serializers for products'''
from __future__ import unicode_literals

import rest_framework.pagination as pagination
import rest_framework.serializers as serializers
from rest_framework.fields import WritableField

from storage.serializers import ScaleFileBaseSerializer
from util.rest import ModelIdSerializer


class ProductFileBaseSerializer(ScaleFileBaseSerializer):
    '''Converts product file model fields to REST output'''
    is_operational = serializers.BooleanField()
    is_published = serializers.BooleanField()
    published = serializers.DateTimeField()
    unpublished = serializers.DateTimeField()
    job_type = ModelIdSerializer()
    job = ModelIdSerializer()
    job_exe = ModelIdSerializer()


class ProductFileSerializer(ProductFileBaseSerializer):
    '''Converts product file model fields to REST output'''
    from job.serializers import JobTypeBaseSerializer

    job_type = JobTypeBaseSerializer()


class ProductFileListSerializer(pagination.PaginationSerializer):
    '''Converts a list of product file models to paginated REST output'''

    class Meta(object):
        '''meta information for the serializer'''
        object_serializer_class = ProductFileSerializer


class ProductFileUpdateField(WritableField):
    '''Field for displaying the update information for a product file'''

    type_name = 'UpdateField'
    type_label = 'update'

    def to_native(self, value):
        '''Converts the model to its update information

        :param value: the product file model
        :type value: :class:`product.models.ProductFile`
        :rtype: dict
        :returns: the dict with the update information
        '''

        if value.is_deleted:
            action = 'DELETED'
            when = value.deleted
        elif value.is_published:
            action = 'PUBLISHED'
            when = value.published
        else:
            action = 'UNPUBLISHED'
            when = value.unpublished

        return {'action': action, 'when': when}


class ProductFileUpdateSerializer(ProductFileSerializer):
    '''Converts product file updates to REST output'''
    from source.serializers import SourceFileBaseSerializer

    update = ProductFileUpdateField(source='*')
    source_files = SourceFileBaseSerializer()


class ProductFileUpdateListSerializer(pagination.PaginationSerializer):
    '''Converts a list of product file updates to paginated REST output'''

    class Meta(object):
        '''meta information for the serializer'''
        object_serializer_class = ProductFileUpdateSerializer
