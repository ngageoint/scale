'''Defines the serializers for ingests'''
import rest_framework.serializers as serializers

from ingest.models import Ingest
from util.rest import ModelIdSerializer


class StrikeBaseSerializer(ModelIdSerializer):
    '''Converts strike model fields to REST output'''
    name = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    job = ModelIdSerializer()


class StrikeSerializer(StrikeBaseSerializer):
    '''Converts strike model fields to REST output'''
    from job.serializers import JobBaseSerializer

    job = JobBaseSerializer()

    created = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()


class StrikeDetailsSerializer(StrikeSerializer):
    '''Converts strike model fields to REST output'''
    configuration = serializers.JSONField()


class IngestBaseSerializer(ModelIdSerializer):
    '''Converts ingest model fields to REST output'''
    from storage.serializers import DataTypeField

    file_name = serializers.CharField()
    strike = ModelIdSerializer()
    status = serializers.ChoiceField(choices=Ingest.INGEST_STATUSES)

    bytes_transferred = serializers.IntegerField()  # TODO: BigIntegerField?
    transfer_started = serializers.DateTimeField()
    transfer_ended = serializers.DateTimeField()

    media_type = serializers.CharField()
    file_size = serializers.IntegerField()  # TODO: BigIntegerField?
    data_type = DataTypeField()

    ingest_started = serializers.DateTimeField()
    ingest_ended = serializers.DateTimeField()
    source_file = ModelIdSerializer()

    created = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()


class IngestSerializer(IngestBaseSerializer):
    '''Converts ingest model fields to REST output'''
    from source.serializers import SourceFileBaseSerializer

    strike = StrikeBaseSerializer()
    source_file = SourceFileBaseSerializer()


class IngestDetailsSerializer(IngestBaseSerializer):
    '''Converts ingest model fields to REST output'''
    from source.serializers import SourceFileSerializer

    transfer_path = serializers.CharField()
    file_path = serializers.CharField()
    ingest_path = serializers.CharField()

    strike = StrikeDetailsSerializer()
    source_file = SourceFileSerializer()


class IngestStatusValuesSerializer(serializers.Serializer):
    '''Converts ingest model fields to REST output'''
    time = serializers.DateTimeField()
    files = serializers.IntegerField()
    size = serializers.IntegerField()


class IngestStatusSerializer(serializers.Serializer):
    '''Converts ingest model fields to REST output'''
    strike = StrikeSerializer()
    most_recent = serializers.DateTimeField()
    files = serializers.IntegerField()
    size = serializers.IntegerField()
    values = IngestStatusValuesSerializer(many=True)
