'''Defines utility methods for testing products'''
from job.test import utils as job_utils
from product.models import ProductFile
from storage.test import utils as storage_utils


def create_product(job_exe=None, workspace=None, has_been_published=False, file_name=u'my_test_file.txt',
                   file_path=u'/file/path/my_test_file.txt', media_type=u'text/plain', file_size=100):
    '''Creates a product file model for unit testing

    :returns: The product model
    :rtype: :class:`product.models.ProductFile`
    '''

    if not job_exe:
        job_exe = job_utils.create_job_exe()
    if not workspace:
        workspace = storage_utils.create_workspace()

    return ProductFile.objects.create(job_exe=job_exe, job=job_exe.job, job_type=job_exe.job.job_type,
                                      has_been_published=has_been_published, file_name=file_name,
                                      media_type=media_type, file_size=file_size, file_path=file_path,
                                      workspace=workspace)
