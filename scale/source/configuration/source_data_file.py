"""Defines the source data file input type contained within job data"""
import logging

from job.configuration.data.data_file import AbstractDataFileParseSaver
from source.models import SourceFile
from storage.models import ScaleFile
from util.parse import parse_datetime

logger = logging.getLogger(__name__)


class SourceDataFileParseSaver(AbstractDataFileParseSaver):
    """Implements the data file parse saver to provide a way to save parse results for source files.
    """

    def save_parse_results(self, parse_results, input_file_ids):
        """See :meth:`job.configuration.data.data_file.AbstractDataFileParseSaver.save_parse_results`
        """

        file_name_to_id = {}
        source_files = ScaleFile.objects.filter(id__in=input_file_ids, file_type='SOURCE')
        for source_file in source_files:
            file_name_to_id[source_file.file_name] = source_file.id

        for file_name in parse_results:
            if file_name not in file_name_to_id:
                continue
            src_file_id = file_name_to_id[file_name]

            parse_result = parse_results[file_name]
            geo_json = parse_result[0]
            data_started = parse_result[1]
            data_ended = parse_result[2]
            data_types = parse_result[3]
            new_workspace_path = parse_result[4]
            if data_started:
                data_started = parse_datetime(data_started)
            if data_ended:
                data_ended = parse_datetime(data_ended)

            SourceFile.objects.save_parse_results(src_file_id, geo_json, data_started, data_ended, data_types,
                                                  new_workspace_path)

    def save_parse_results_v6(self, id_to_metadata):
        """Saves the given parse results to the source file for the given ID. All database changes occur in an atomic
        transaction.

        :param id_to_metadata: Mapping of IDs to metadata objects/
        :type id_to_metadata: { int: class:`job.seed.metadata.SeedMetadata` }
        """

        ids = id_to_metadata.keys()
        logger.debug('List of IDs to update: {}'.format(ids))
        source_file_ids = ScaleFile.objects.filter(id__in=ids, file_type='SOURCE').values_list('id', flat=True)
        ignored_ids = list(set(ids) - set(source_file_ids))
        if len(ignored_ids):
            logger.warning('Ignored all parse results for file IDs not of SOURCE file_type: {}'
                           .format(','.join(map(str, ignored_ids))))

        for file_id in source_file_ids:
            metadata = id_to_metadata[int(file_id)]

            geo_json = metadata.data
            data_started = metadata.get_property('dataStarted')
            data_ended = metadata.get_property('dataEnded')
            data_types = metadata.get_property('dataTypes', [])
            new_workspace_path = metadata.get_property('newWorkspacePath')

            if data_started:
                data_started = parse_datetime(data_started)
            if data_ended:
                data_ended = parse_datetime(data_ended)

            logger.debug('Captured input for file ID {}:\n{}\n{}\n{}\n{}'.format(file_id, geo_json,
                                                                                 data_started, data_ended, data_types))
            SourceFile.objects.save_parse_results(file_id, geo_json, data_started, data_ended, data_types,
                                                  new_workspace_path)
