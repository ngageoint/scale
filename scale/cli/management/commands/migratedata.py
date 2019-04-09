import logging
import os
import fnmatch
import tempfile

from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from ingest.models import Ingest
from ingest.serializers import IngestDetailsSerializerV6
from ingest.triggers.ingest_recipe_handler import IngestRecipeHandler
from source.models import SourceFile
from storage.media_type import get_media_type
from storage.models import Workspace

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """Command that migrates existing data files into scale
    """

    help = 'Migrate existing data into scale'

    def add_arguments(self, parser):
        parser.add_argument("-n", action="store_true", dest="no_commit", help="Don't actually modify the database, just print new records")
        parser.add_argument("-w", "--workspace", action="store", help="Workspace name or ID to ingest.")
        parser.add_argument("-p", "--workspace-path", action="store", help="Path in the workspace to ingest.")
        parser.add_argument("-l", "--local-path", action="store",
                            help="If specified, use this as the workspace and workspace path instead of using the workspace mount.")
        parser.add_argument("-r", "--recipe", action="store", default=[], help="Recipe id to kick off after ingest complete")
        parser.add_argument("-d", "--data-type", action="append", default=[], help="Data type tag")
        parser.add_argument("-i", "--include", action="append", help="Include glob")
        parser.add_argument("-e", "--exclude", action="append", default=[], help="Exclude glob")

    # input dir, target workspace

    def handle(self, *args, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.

        This method migrates existing data files into scale.
        """
        logger.info(u'Command starting: migratedata')

        workspace, workspace_path, local_path, data_types = None, None, None, []
        if options['workspace'] is not None and options['workspace_path'] is not None:
            workspace, workspace_path = options['workspace'], options['workspace_path']
            tmp = Workspace.objects.filter(name=workspace)
            if tmp.count() > 0:
                workspace = tmp.first()
            else:
                workspace = Workspace.objects.get(id=int(workspace))
        else:
            logger.error('Must specify workspace and workspace-path.')
            return False
        if options['data_type'] is not None:
            data_types.extend(options['data_type'])

        mnt_dirs = None
        if options['local_path'] is not None:
            local_path = options['local_path']
        else:  # mount
            mnt_dirs = "/tmp", tempfile.mkdtemp()
            workspace.setup_download_dir(*mnt_dirs)
            local_path = os.path.join(mnt_dirs[1], workspace_path)

        logger.info("Ingesting files from %s/%s", workspace.name, workspace_path)
        filenames = self.generate_file_list(local_path, options['include'], options['exclude'])
        logger.info("Found %d files", len(filenames))

        # prepare for ingest ala strike
        ingest_records = {}
        for filename in filenames:
            logger.info("Generating ingest record for %s" % filename)
            ingest = Ingest()
            ingest.file_name = os.path.basename(filename)
            ingest.file_path = os.path.join(workspace_path, os.path.relpath(filename, local_path))
            ingest.transfer_started = datetime.utcfromtimestamp(os.path.getatime(filename))
            ingest.file_size = ingest.bytes_transferred = os.path.getsize(filename)
            ingest.transfer_ended = timezone.now()
            ingest.media_type = get_media_type(filename)
            ingest.workspace = workspace
            for data_type in data_types:
                ingest.add_data_type_tag(data_type)
            ingest.status = 'TRANSFERRED'
            if options['no_commit']:
                s = IngestDetailsSerializerV6()
                logger.info(s.to_representation(ingest))
            else:
                ingest.save()
                ingest_records[filename] = ingest.id
        logging.info("Ingests records created")

        # start ingest tasks for all the files
        if not options['no_commit']:
            logging.info("Starting ingest tasks")
            for filename in filenames:
                ingest = Ingest.objects.get(id=ingest_records[filename])
                logging.info("Processing ingest %s" % ingest.file_name)
                with transaction.atomic():
                    ingest.ingest_started = timezone.now()
                    sf = ingest.source_file = SourceFile.create()
                    sf.update_uuid(ingest.file_name)
                    for tag in ingest.get_data_type_tags():
                        sf.add_data_type_tag(tag)
                    sf.media_type = ingest.media_type
                    sf.file_name = ingest.file_name
                    sf.file_size = ingest.file_size
                    sf.file_path = ingest.file_path
                    sf.workspace = workspace
                    sf.is_deleted = False
                    sf.deleted = None
                    sf.save()
                    sf.set_countries()
                    sf.save()
                    ingest.status = 'INGESTED'
                    ingest.ingest_ended = timezone.now()
                    ingest.source_file = sf
                    ingest.save()
                    if options['recipe']:
                        IngestRecipeHandler().process_ingested_source_file(ingest.id, ingest.source_file, ingest.ingest_ended)



        logging.info("Ingests processed, monitor the queue for triggered jobs.")

        if mnt_dirs is not None:
            workspace.cleanup_download_dir(*mnt_dirs)

        logger.info(u'Command completed: migratedata')

    @staticmethod
    def generate_file_list(path, include, exclude):
        all_files = []
        for root, dirs, files in os.walk(path):
            tmp = []
            if include is None:
                tmp = files
            else:
                for inc in include:
                    tmp.extend(filter(lambda fname, glb=inc: fnmatch.fnmatch(fname, glb), files))
            for excl in exclude:
                tmp = filter(lambda fname, glb=excl: not fnmatch.fnmatch(fname, glb), tmp)
            all_files.extend(map(lambda fname, pth=root: os.path.join(pth, fname), tmp))
        return all_files
