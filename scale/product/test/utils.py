"""Defines utility methods for testing products"""
from __future__ import unicode_literals

from job.test import utils as job_utils
from product.models import FileAncestryLink, ProductFile
from storage.test import utils as storage_utils


def create_file_link(ancestor=None, descendant=None, job=None, job_exe=None, recipe=None):
    """Creates a file ancestry link model for unit testing

    :returns: The file ancestry link model
    :rtype: :class:`product.models.FileAncestryLink`
    """

    if not job:
        if descendant and descendant.job:
            job = descendant.job
        else:
            job = job_utils.create_job()
    if not job_exe:
        if descendant and descendant.job_exe:
            job_exe = descendant.job_exe
        else:
            job_exe = job_utils.create_job_exe(job_type=job.job_type, job=job)

    return FileAncestryLink.objects.create(ancestor=ancestor, descendant=descendant, job=job, job_exe=job_exe,
                                           recipe=recipe)


def create_product(job_exe=None, workspace=None, has_been_published=False, file_name='my_test_file.txt',
                   file_path='/file/path/my_test_file.txt', media_type='text/plain', file_size=100, countries=None):
    """Creates a product file model for unit testing

    :returns: The product model
    :rtype: :class:`product.models.ProductFile`
    """

    if not job_exe:
        job_exe = job_utils.create_job_exe()
    if not workspace:
        workspace = storage_utils.create_workspace()

    product_file = ProductFile.objects.create(job_exe=job_exe, job=job_exe.job, job_type=job_exe.job.job_type,
                                              has_been_published=has_been_published, file_name=file_name,
                                              media_type=media_type, file_size=file_size, file_path=file_path,
                                              workspace=workspace)
    if countries:
        product_file.countries = countries
        product_file.save()
    return product_file
