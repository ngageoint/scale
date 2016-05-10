'''Defines the source data file input type contained within job data'''
from job.configuration.data.data_file import AbstractDataFileParseSaver
from source.models import SourceFile
from util.parse import parse_datetime


class SourceDataFileParseSaver(AbstractDataFileParseSaver):
    '''Implements the data file parse saver to provide a way to save parse results for source files.
    '''

    def save_parse_results(self, parse_results, input_file_ids):
        '''See :meth:`job.configuration.data.data_file.AbstractDataFileParseSaver.save_parse_results`
        '''

        file_name_to_id = {}
        source_files = SourceFile.objects.filter(id__in=input_file_ids)
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
