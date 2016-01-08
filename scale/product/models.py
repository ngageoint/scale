'''Defines the database model for product files'''
from __future__ import unicode_literals

import logging
import os

import django.contrib.gis.db.models as models
import django.utils.timezone as timezone
from django.db import transaction
from django.db.models import Q

import storage.geospatial_utils as geo_utils
from recipe.models import RecipeJob
from source.models import SourceFile
from storage.models import ScaleFile
from util.parse import parse_datetime


logger = logging.getLogger(__name__)


class FileAncestryLinkManager(models.Manager):
    '''Provides additional methods for handling ancestry links for files used in jobs
    '''

    @transaction.atomic
    def create_file_ancestry_links(self, parent_ids, child_ids, job_exe):
        '''Creates the appropriate file ancestry links for the given parent and child files. All database changes are
        made in an atomic transaction.

        :param parent_ids: Set of parent file IDs
        :type parent_ids: set of int
        :param child_ids: Set of child file IDs. Passing None can be used to link input files to jobs and recipes
            without any derived products.
        :type child_ids: set of int
        :param job_exe: The job execution that is creating the file links
        :type job_exe: :class:`job.models.JobExecution`
        '''
        new_links = []
        created = timezone.now()

        # Delete any previous file ancestry links for the given execution
        # This overrides any file input links that were created when the execution was first queued
        FileAncestryLink.objects.filter(job_exe=job_exe).delete()

        # Not all jobs have a recipe so attempt to get one if applicable
        recipe = None
        try:
            recipe_job = RecipeJob.objects.get(job=job_exe.job)
            recipe = recipe_job.recipe
        except RecipeJob.DoesNotExist:
            pass

        # Grab ancestors for the parents
        ancestor_map = dict()
        ancestor_links = FileAncestryLink.objects.filter(descendant_id__in=parent_ids)
        for ancestor_link in ancestor_links:
            if ancestor_link.ancestor_id not in parent_ids:
                ancestor_map[ancestor_link.ancestor_id] = ancestor_link

        # Make sure all input file links are still created when no products are generated
        if not child_ids:
            child_ids = {None}

        # Create direct links by leaving the ancestor job fields as null
        for parent_id in parent_ids:
            for child_id in child_ids:

                # Set references to the current file
                link = FileAncestryLink(created=created)
                link.ancestor_id = parent_id
                link.descendant_id = child_id

                # Set references to the current execution
                link.job_exe_id = job_exe.id
                link.job = job_exe.job
                link.recipe = recipe
                new_links.append(link)

        # Create indirect links by setting the ancestor job fields
        for ancestor_link in ancestor_map.itervalues():
            for child_id in child_ids:

                # Set references to the current file
                link = FileAncestryLink(created=created)
                link.ancestor_id = ancestor_link.ancestor_id
                link.descendant_id = child_id

                # Set references to the current execution
                link.job_exe_id = job_exe.id
                link.job = job_exe.job
                link.recipe = recipe

                # Set references to the ancestor execution
                link.ancestor_job = ancestor_link.job
                link.ancestor_job_exe = ancestor_link.job_exe
                new_links.append(link)

        FileAncestryLink.objects.bulk_create(new_links)

    def get_source_ancestors(self, file_ids):
        '''Returns a list of the source file ancestors for the given file IDs. This will include any of the given files
        that are source files themselves.

        :param file_ids: The file IDs
        :type file_ids: list[int]
        :returns: The list of ancestor source files
        :rtype: list[:class:`source.models.SourceFile`]
        '''

        source_files = Q(id__in=file_ids)
        product_files = Q(descendants__descendant_id__in=file_ids)
        return SourceFile.objects.filter(source_files | product_files).distinct('file_id')


class FileAncestryLink(models.Model):
    '''Represents an ancestry link between two files where the ancestor resulted in the descendant through a series of
    one or more job executions. A direct ancestry link (parent to child) is formed when the parent is passed as input to
    a job execution and the child is created as an output of that job execution.

    :keyword ancestor: An ancestor file from which the other file is descended
    :type ancestor: :class:`django.db.models.ForeignKey`
    :keyword descendant: A product file that descended from the ancestor file
    :type descendant: :class:`django.db.models.ForeignKey`

    :keyword job_exe: The job execution that caused this link to be formed
    :type job_exe: :class:`django.db.models.ForeignKey`
    :keyword job: The job that caused this link to be formed
    :type job: :class:`django.db.models.ForeignKey`
    :keyword recipe: The recipe that caused this link to be formed. Note that not all jobs are created from a recipe and
        so this field could be null.
    :type recipe: :class:`django.db.models.ForeignKey`

    :keyword ancestor_job: The higher level job that took the ancestor as input and indirectly caused this link to be
        formed. Note that this field will be null for directly created files, where the ancestor is a parent that was
        fed as input to a job and the descendant is a child produced as output by that same job.
    :type ancestor_job: :class:`django.db.models.ForeignKey`
    :keyword ancestor_job_exe: The higher level job execution that took the ancestor as input and indirectly caused this
        link to be formed. Note that this field will be null for directly created files, where the ancestor is a parent
        that was fed as input to a job execution and the descendant is a child produced as output by that same job
        execution.
    :type ancestor_job_exe: :class:`django.db.models.ForeignKey`

    :keyword created: When the file link was created
    :type created: :class:`django.db.models.DateTimeField`
    '''

    ancestor = models.ForeignKey('storage.ScaleFile', on_delete=models.PROTECT, related_name='descendants')
    descendant = models.ForeignKey('product.ProductFile', blank=True, null=True, on_delete=models.PROTECT,
                                   related_name='ancestors')

    job_exe = models.ForeignKey('job.JobExecution', on_delete=models.PROTECT, related_name='file_links')
    job = models.ForeignKey('job.Job', on_delete=models.PROTECT, related_name='file_links')
    recipe = models.ForeignKey('recipe.Recipe', blank=True, on_delete=models.PROTECT, null=True,
                               related_name='file_links')

    ancestor_job = models.ForeignKey('job.Job', blank=True, on_delete=models.PROTECT,
                                     related_name='ancestor_file_links', null=True)
    ancestor_job_exe = models.ForeignKey('job.JobExecution', blank=True, on_delete=models.PROTECT,
                                         related_name='ancestor_file_links', null=True)

    created = models.DateTimeField(auto_now_add=True)

    objects = FileAncestryLinkManager()

    class Meta(object):
        '''meta information for the db'''
        db_table = 'file_ancestry_link'


class ProductFileManager(models.GeoManager):
    '''Provides additional methods for handling product files
    '''

    def get_products(self, started=None, ended=None, job_type_ids=None, job_type_names=None, job_type_categories=None,
                     is_operational=None, file_name=None, order=None):
        '''Returns a list of product files within the given time range.

        :param started: Query product files updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query product files updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param job_type_ids: Query product files produced by jobs with the given type identifier.
        :type job_type_ids: list[int]
        :param job_type_names: Query product files produced by jobs with the given type name.
        :type job_type_names: list[str]
        :param job_type_categories: Query product files produced by jobs with the given type category.
        :type job_type_categories: list[str]
        :param is_operational: Query product files flagged as operational or R&D only.
        :type is_operational: bool
        :param file_name: Query product files with the given file name.
        :type file_name: str
        :param order: A list of fields to control the sort order.
        :type order: list[str]
        :returns: The list of product files that match the time range.
        :rtype: list[:class:`product.models.ProductFile`]
        '''

        # Fetch a list of product files
        products = ProductFile.objects.filter(has_been_published=True)
        products = products.select_related('workspace', 'job_type').defer('workspace__json_config')
        products = products.prefetch_related('countries')

        # Apply time range filtering
        if started:
            products = products.filter(last_modified__gte=started)
        if ended:
            products = products.filter(last_modified__lte=ended)

        if job_type_ids:
            products = products.filter(job_type_id__in=job_type_ids)
        if job_type_names:
            products = products.filter(job_type__name__in=job_type_names)
        if job_type_categories:
            products = products.filter(job_type__category__in=job_type_categories)
        if is_operational is not None:
            products = products.filter(job_type__is_operational=is_operational)
        if file_name:
            products = products.filter(file_name=file_name)

        # Apply sorting
        if order:
            products = products.order_by(*order)
        else:
            products = products.order_by('last_modified')

        return products

    def populate_source_ancestors(self, products):
        '''Populates each of the given products with its source file ancestors in a field called "source_files"

        :param products: List of products
        :type products: list of :class:`product.models.ProductFile`
        '''

        product_lists = {}  # {product ID: list of source files}
        for product in products:
            product.source_files = []
            product_lists[product.id] = product.source_files

        source_files = {}  # {source file ID: source file}
        src_qry = SourceFile.objects.filter(descendants__descendant_id__in=product_lists.keys())
        src_qry = src_qry.select_related('workspace').defer('workspace__json_config').order_by('id').distinct('id')
        for source in src_qry:
            source_files[source.id] = source

        link_qry = FileAncestryLink.objects.filter(ancestor_id__in=source_files.keys())
        link_qry = link_qry.filter(descendant_id__in=product_lists.keys())
        for link in link_qry:
            product_lists[link.descendant_id].append(source_files[link.ancestor_id])

    @transaction.atomic
    def publish_products(self, job_exe_id, when):
        '''Publishes all of the products produced by the given job execution. All database changes will be made in an
        atomic transaction.

        :param job_exe_id: The ID of the job execution
        :type job_exe_id: int
        :param when: When the products were published
        :type when: :class:`datetime.datetime`
        '''

        # Acquire model lock
        product_qry = ProductFile.objects.select_for_update().filter(job_exe_id=job_exe_id).order_by('id')
        for product in product_qry:
            product.has_been_published = True
            product.is_published = True
            product.published = when
            product.save()

    def upload_files(self, upload_dir, work_dir, file_entries, input_file_ids, job_exe, workspace):
        '''Uploads the given local product files into the workspace. All database changes will be made in an atomic
        transaction. This method assumes that ScaleFileManager.setup_upload_dir() has already been called with the same
        upload and work directories.

        :param upload_dir: Absolute path to the local directory of the files to upload
        :type upload_dir: str
        :param work_dir: Absolute path to a local work directory available to assist in uploading
        :type work_dir: str
        :param file_entries: List of files where each file is a tuple of (source path relative to upload directory,
            workspace path for storing the file, media_type)
        :type file_entries: list of tuple(str, str, str)
        :param input_file_ids: List of identifiers for files used to produce the given file entries
        :type input_file_ids: list of int
        :param job_exe: The job_exe model with the related job and job_type fields
        :type job_exe: :class:`job.models.JobExecution`
        :param workspace: The workspace to use for storing the product files
        :type workspace: :class:`storage.models.Workspace`
        :returns: The list of the saved product models
        :rtype: list of :class:`product.models.ProductFile`
        '''

        # Build a list of UUIDs for the input files
        input_files = ScaleFile.objects.filter(pk__in=input_file_ids).values('uuid', 'id').order_by('uuid')
        input_file_uuids = [f['uuid'] for f in input_files]

        # Determine if any input files are non-operational products
        input_products = ProductFile.objects.filter(file__in=[f['id'] for f in input_files])
        input_products_operational = all([f.is_operational for f in input_products])

        products_to_save = []
        for entry in file_entries:
            local_path = entry[0]
            remote_path = entry[1]
            media_type = entry[2]

            product = ProductFile()
            product.job_exe = job_exe
            product.job = job_exe.job
            product.job_type = job_exe.job.job_type
            product.is_operational = input_products_operational and job_exe.job.job_type.is_operational
            product.media_type = media_type

            # Add a stable identifier based on the job type, input files, and file name
            # This is designed to remain stable across re-processing the same type of job on the same inputs
            file_name = os.path.basename(local_path)
            product.update_uuid(job_exe.job.job_type.id, file_name, *input_file_uuids)

            # Add geospatial info to product if available
            if len(entry) > 3:
                geo_metadata = entry[3]
                target_date = None
                if 'data_started' in geo_metadata:
                    product.data_started = parse_datetime(geo_metadata['data_started'])
                    target_date = product.data_started
                if 'data_ended' in geo_metadata:
                    product.data_ended = parse_datetime(geo_metadata['data_ended'])
                    if target_date is None:
                        target_date = product.data_ended
                if target_date is None:
                    target_date = product.created
                if 'geo_json' in geo_metadata:
                    geom, props = geo_utils.parse_geo_json(geo_metadata['geo_json'])
                    product.geometry = geom
                    product.meta_data = props
                    product.center_point = geo_utils.get_center_point(geom)

            products_to_save.append((product, local_path, remote_path))

        return ScaleFile.objects.upload_files(upload_dir, work_dir, workspace, products_to_save)


class ProductFile(ScaleFile):
    '''Represents a product file that has been created by Scale. This is an extension of the
    :class:`storage.models.ScaleFile` model.

    :keyword file: The corresponding ScaleFile model
    :type file: :class:`django.db.models.OneToOneField`
    :keyword job_exe: The job execution that created this product
    :type job_exe: :class:`django.db.models.ForeignKey`
    :keyword job: The job that created this product
    :type job: :class:`django.db.models.ForeignKey`
    :keyword job_type: The type of the job that created this product
    :type job_type: :class:`django.db.models.ForeignKey`
    :keyword is_operational: Whether this product was produced by an operational job type (True) or by a job type that
        is still in a research & development (R&D) phase (False)
    :type is_operational: :class:`django.db.models.BooleanField`

    :keyword has_been_published: Whether this product has ever been published. A product becomes published when its job
        execution completes successfully. A product that has been published will appear in the API call to retrieve
        product updates.
    :type has_been_published: :class:`django.db.models.BooleanField`
    :keyword is_published: Whether this product is currently published. A published product has had its job execution
        complete successfully and has not been unpublished.
    :type is_published: :class:`django.db.models.BooleanField`
    :keyword published: When this product was published (its job execution was completed)
    :type published: :class:`django.db.models.DateTimeField`
    :keyword unpublished: When this product was unpublished
    :type unpublished: :class:`django.db.models.DateTimeField`
    '''

    file = models.OneToOneField('storage.ScaleFile', primary_key=True, parent_link=True)
    job_exe = models.ForeignKey('job.JobExecution', on_delete=models.PROTECT)
    job = models.ForeignKey('job.Job', on_delete=models.PROTECT)
    job_type = models.ForeignKey('job.JobType', on_delete=models.PROTECT)
    is_operational = models.BooleanField(default=True)

    has_been_published = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    published = models.DateTimeField(blank=True, null=True)
    unpublished = models.DateTimeField(blank=True, null=True)

    objects = ProductFileManager()

    class Meta(object):
        '''meta information for the db'''
        db_table = 'product_file'
