"""Defines the serializers for ingests"""
import rest_framework.serializers as serializers

from ingest.models import Ingest
from job.serializers import JobBaseSerializer
from source.serializers import SourceFileBaseSerializer, SourceFileSerializer
from storage.serializers import DataTypeField, WorkspaceSerializer, WorkspaceDetailsSerializer
from util.rest import ModelIdSerializer


class ScanBaseSerializer(ModelIdSerializer):
    """Converts scan model fields to REST output"""

    name = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    job = ModelIdSerializer()
    dry_run_job = ModelIdSerializer()


class ScanSerializer(ScanBaseSerializer):
    """Converts scan model fields to REST output"""

    job = JobBaseSerializer()
    dry_run_job = JobBaseSerializer()

    file_count = serializers.IntegerField()

    created = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()


class ScanDetailsSerializer(ScanSerializer):
    """Converts scan model fields to REST output"""

    configuration = serializers.JSONField(source='get_scan_configuration_as_dict')


class StrikeBaseSerializer(ModelIdSerializer):
    """Converts strike model fields to REST output"""

    name = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    job = ModelIdSerializer()


class StrikeSerializer(StrikeBaseSerializer):
    """Converts strike model fields to REST output"""

    job = JobBaseSerializer()

    created = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()


class StrikeDetailsSerializer(StrikeSerializer):
    """Converts strike model fields to REST output"""

    configuration = serializers.JSONField(source='get_strike_configuration_as_dict')


class IngestBaseSerializer(ModelIdSerializer):
    """Converts ingest model fields to REST output"""

    file_name = serializers.CharField()
    scan = ModelIdSerializer()
    strike = ModelIdSerializer()
    status = serializers.ChoiceField(choices=Ingest.INGEST_STATUSES)

    bytes_transferred = serializers.IntegerField()  # TODO: BigIntegerField?
    transfer_started = serializers.DateTimeField()
    transfer_ended = serializers.DateTimeField()

    media_type = serializers.CharField()
    file_size = serializers.IntegerField()  # TODO: BigIntegerField?
    data_type = DataTypeField()

    file_path = serializers.CharField()
    workspace = ModelIdSerializer()
    new_file_path = serializers.CharField()
    new_workspace = ModelIdSerializer()

    job = ModelIdSerializer()
    ingest_started = serializers.DateTimeField()
    ingest_ended = serializers.DateTimeField()

    source_file = ModelIdSerializer()
    data_started = serializers.DateTimeField()
    data_ended = serializers.DateTimeField()

    created = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()


class IngestSerializer(IngestBaseSerializer):
    """Converts ingest model fields to REST output"""

    scan = ScanBaseSerializer()
    strike = StrikeBaseSerializer()

    workspace = WorkspaceSerializer()
    new_workspace = WorkspaceSerializer()

    job = ModelIdSerializer()
    source_file = SourceFileBaseSerializer()


class IngestDetailsSerializer(IngestSerializer):
    """Converts ingest model fields to REST output"""

    scan = ScanDetailsSerializer()
    strike = StrikeDetailsSerializer()

    workspace = WorkspaceDetailsSerializer()
    new_workspace = WorkspaceDetailsSerializer()

    job = ModelIdSerializer()
    source_file = SourceFileSerializer()


class IngestStatusValuesSerializer(serializers.Serializer):
    """Converts ingest model fields to REST output"""

    time = serializers.DateTimeField()
    files = serializers.IntegerField()
    size = serializers.IntegerField()


class IngestStatusSerializer(serializers.Serializer):
    """Converts ingest model fields to REST output"""

    strike = StrikeSerializer()
    most_recent = serializers.DateTimeField()
    files = serializers.IntegerField()
    size = serializers.IntegerField()
    values = IngestStatusValuesSerializer(many=True)
