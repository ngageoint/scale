"""Defines the serializers for ingests"""
import rest_framework.serializers as serializers

from ingest.models import Ingest
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

class ScanSerializerV5(ScanBaseSerializer):
    """Converts scan model fields to REST output"""
    from job.serializers import JobBaseSerializerV5

    job = JobBaseSerializerV5()
    dry_run_job = JobBaseSerializerV5()

    file_count = serializers.IntegerField()

    created = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()
    
class ScanSerializerV6(ScanBaseSerializer):
    """Converts scan model fields to REST output"""
    from job.serializers import JobBaseSerializerV6

    job = JobBaseSerializerV6()
    dry_run_job = JobBaseSerializerV6()

    file_count = serializers.IntegerField()

    created = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()

class ScanDetailsSerializerV5(ScanSerializerV5):
    """Converts scan model fields to REST output"""

    configuration = serializers.JSONField(source='get_v1_configuration_json')
    
class ScanDetailsSerializerV6(ScanSerializerV6):
    """Converts scan model fields to REST output"""

    configuration = serializers.JSONField(source='get_v6_configuration_json')



class StrikeBaseSerializer(ModelIdSerializer):
    """Converts strike model fields to REST output"""

    name = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    job = ModelIdSerializer()


class StrikeSerializerV5(StrikeBaseSerializer):
    """Converts strike model fields to REST output"""
    from job.serializers import JobBaseSerializerV5

    job = JobBaseSerializerV5()

    created = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()
    
class StrikeSerializerV6(StrikeBaseSerializer):
    """Converts strike model fields to REST output"""
    from job.serializers import JobBaseSerializerV6

    job = JobBaseSerializerV6()

    created = serializers.DateTimeField()
    last_modified = serializers.DateTimeField()


class StrikeDetailsSerializerV5(StrikeSerializerV5):
    """Converts strike model fields to REST output"""

    configuration = serializers.JSONField(source='get_v5_strike_configuration_as_dict')
    
class StrikeDetailsSerializerV6(StrikeSerializerV6):
    """Converts strike model fields to REST output"""

    configuration = serializers.JSONField(source='get_v6_configuration_json')


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


class IngestDetailsSerializerV5(IngestSerializer):
    """Converts ingest model fields to REST output"""

    scan = ScanDetailsSerializerV5()
    strike = StrikeDetailsSerializerV5()

    workspace = WorkspaceDetailsSerializer()
    new_workspace = WorkspaceDetailsSerializer()

    job = ModelIdSerializer()
    source_file = SourceFileSerializer()
    
class IngestDetailsSerializerV6(IngestSerializer):
    """Converts ingest model fields to REST output"""

    scan = ScanDetailsSerializerV6()
    strike = StrikeDetailsSerializerV6()

    workspace = WorkspaceDetailsSerializer()
    new_workspace = WorkspaceDetailsSerializer()

    job = ModelIdSerializer()
    source_file = SourceFileSerializer()


class IngestStatusValuesSerializer(serializers.Serializer):
    """Converts ingest model fields to REST output"""

    time = serializers.DateTimeField()
    files = serializers.IntegerField()
    size = serializers.IntegerField()


class IngestStatusSerializerV5(serializers.Serializer):
    """Converts ingest model fields to REST output"""

    strike = StrikeSerializerV5()
    most_recent = serializers.DateTimeField()
    files = serializers.IntegerField()
    size = serializers.IntegerField()
    values = IngestStatusValuesSerializer(many=True)
    
class IngestStatusSerializerV6(serializers.Serializer):
    """Converts ingest model fields to REST output"""

    strike = StrikeSerializerV6()
    most_recent = serializers.DateTimeField()
    files = serializers.IntegerField()
    size = serializers.IntegerField()
    values = IngestStatusValuesSerializer(many=True)
