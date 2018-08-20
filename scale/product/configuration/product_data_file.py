"""Defines the product data file input type contained within job data"""
from __future__ import unicode_literals

import os

from django.db import transaction
from django.utils.text import get_valid_filename
from django.utils.timezone import now

from job.configuration.data.data_file import AbstractDataFileStore
from job.execution.container import SCALE_JOB_EXE_OUTPUT_PATH
from product.models import FileAncestryLink, ProductFile
from recipe.models import Recipe
from storage.models import Workspace


class ProductDataFileStore(AbstractDataFileStore):
    """Implements the data file store class to provide a way to validate product file output configuration and store
    product data files.
    """

    def get_workspaces(self, workspace_ids):
        """See :meth:`job.configuration.data.data_file.AbstractDataFileStore.get_workspaces`
        """

        workspaces = Workspace.objects.filter(id__in=workspace_ids)

        results = {}
        for workspace in workspaces:
            results[workspace.id] = workspace.is_active

        return results

    def store_files(self, data_files, input_file_ids, job_exe):
        """See :meth:`job.configuration.data.data_file.AbstractDataFileStore.store_files`
        """

        workspace_ids = data_files.keys()
        workspaces = Workspace.objects.filter(id__in=workspace_ids)
        results = {}
        remote_path = self._calculate_remote_path(job_exe, input_file_ids)

        with transaction.atomic():
            for workspace in workspaces:
                file_list = data_files[workspace.id]
                files_to_store = []
                for file_metadata in file_list:
                    local_path = file_metadata.local_path
                    if local_path.startswith(SCALE_JOB_EXE_OUTPUT_PATH):
                        rel_local_path = os.path.relpath(local_path, SCALE_JOB_EXE_OUTPUT_PATH)
                    else:
                        rel_local_path = os.path.basename(local_path)
                    file_metadata.remote_path = os.path.join(remote_path, rel_local_path)

                    files_to_store.append(file_metadata)

                product_files = ProductFile.objects.upload_files(files_to_store, input_file_ids, job_exe, workspace)

                for i in range(len(product_files)):
                    full_local_path = file_list[i].local_path
                    product_file = product_files[i]
                    results[full_local_path] = product_file.id

            FileAncestryLink.objects.create_file_ancestry_links(input_file_ids, set(results.values()), job_exe.job,
                                                                job_exe.id)

        return results

    def _calculate_remote_path(self, job_exe, input_file_ids):
        """Returns the remote path for storing the products

        :param job_exe: The job execution model (with related job and job_type fields) that is storing the files
        :type job_exe: :class:`job.models.JobExecution`
        :param input_file_ids: Set of input file IDs
        :type input_file_ids: set of int
        :returns: The remote path for storing the products
        :rtype: str
        """

        remote_path = ''
        job_recipe = Recipe.objects.get_recipe_for_job(job_exe.job_id)
        if job_recipe:
            recipe = job_recipe.recipe
            recipe_type_path = get_valid_filename(recipe.recipe_type.name)
            recipe_version_path = get_valid_filename(recipe.recipe_type.version)
            remote_path = os.path.join(remote_path, 'recipes', recipe_type_path, recipe_version_path)
        job_type_path = get_valid_filename(job_exe.job.job_type.name)
        job_version_path = get_valid_filename(job_exe.job.job_type.version)
        remote_path = os.path.join(remote_path, 'jobs', job_type_path, job_version_path)

        # Try to use source start time from the job
        the_date = job_exe.job.source_started

        if not the_date:
            # Try to grab source started the old way through the source ancestor file
            for source_file in FileAncestryLink.objects.get_source_ancestors(list(input_file_ids)):
                if source_file.data_started:
                    if not the_date or source_file.data_started < the_date:
                        the_date = source_file.data_started

        # No data start time populated, use current time
        if not the_date:
            remote_path = os.path.join(remote_path, 'unknown_source_data_time')
            the_date = now()

        year_dir = str(the_date.year)
        month_dir = '%02d' % the_date.month
        day_dir = '%02d' % the_date.day
        return os.path.join(remote_path, year_dir, month_dir, day_dir, 'job_exe_%i' % job_exe.id)
