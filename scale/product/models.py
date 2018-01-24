"""Defines the database model for product files"""
from __future__ import unicode_literals

import logging
import os

import django.contrib.gis.db.models as models
import django.utils.timezone as timezone
from django.db import transaction

import storage.geospatial_utils as geo_utils
from recipe.models import Recipe
from storage.brokers.broker import FileUpload
from storage.models import ScaleFile
from util.parse import parse_datetime


logger = logging.getLogger(__name__)


class FileAncestryLinkManager(models.Manager):
    """Provides additional methods for handling ancestry links for files used in jobs
    """

    @transaction.atomic
    def create_file_ancestry_links(self, parent_ids, child_ids, job, job_exe_id):
        """Creates the appropriate file ancestry links for the given parent and child files. All database changes are
        made in an atomic transaction.

        :param parent_ids: Set of parent file IDs
        :type parent_ids: set of int
        :param child_ids: Set of child file IDs. Passing None can be used to link input files to jobs and recipes
            without any derived products.
        :type child_ids: set of int
        :param job: The job that is creating the file links
        :type job: :class:`job.models.Job`
        :param job_exe_id: The job execution that is creating the file links
        :type job_exe_id: int
        """

        new_links = []
        created = timezone.now()

        # Delete any previous file ancestry links for the given job
        # This overrides any file input links that were created when the job first received its input data
        FileAncestryLink.objects.filter(job_id=job.id).delete()

        # Convert parent IDs to source file ancestors
        parent_ids = self.get_source_ancestor_ids(parent_ids)

        # Not all jobs have a recipe so attempt to get one if applicable
        job_recipe = Recipe.objects.get_recipe_for_job(job.id)

        # See if this job is in a batch
        from batch.models import BatchJob
        try:
            batch_id = BatchJob.objects.get(job_id=job.id).batch_id
        except BatchJob.DoesNotExist:
            batch_id = None

        # Make sure all input file links are still created when no products are generated
        if not child_ids:
            child_ids = {None}

        # Create direct links (from source to product) by leaving the ancestor job fields as null
        for parent_id in parent_ids:
            for child_id in child_ids:

                # Set references to the current file
                link = FileAncestryLink(created=created)
                link.ancestor_id = parent_id
                link.descendant_id = child_id

                # Set references to the current execution
                link.job_exe_id = job_exe_id
                link.job_id = job.id
                link.batch_id = batch_id
                new_links.append(link)

                if job_recipe:
                    link.recipe_id = job_recipe.recipe_id
                else:
                    link.recipe = None

        FileAncestryLink.objects.bulk_create(new_links)

    def get_source_ancestor_ids(self, file_ids):
        """Returns a list of the source file ancestor IDs for the given file IDs. This will include any of the given
        files that are source files themselves.

        :param file_ids: The file IDs
        :type file_ids: list
        :returns: The list of ancestor source file IDs
        :rtype: list
        """

        potential_src_file_ids = set(file_ids)
        # Get all ancestors to include as possible source files
        for ancestor_link in self.filter(descendant_id__in=file_ids).iterator():
            potential_src_file_ids.add(ancestor_link.ancestor_id)
        source_file_query = ScaleFile.objects.filter(id__in=list(potential_src_file_ids), file_type='SOURCE').only('id')
        return [src_file.id for src_file in source_file_query]

    def get_source_ancestors(self, file_ids):
        """Returns a list of the source file ancestors for the given file IDs. This will include any of the given files
        that are source files themselves.

        :param file_ids: The file IDs
        :type file_ids: list[int]
        :returns: The list of ancestor source files
        :rtype: list[:class:`storage.models.ScaleFile`]
        """

        potential_src_file_ids = set(file_ids)
        # Get all ancestors to include as possible source files
        for ancestor_link in self.filter(descendant_id__in=file_ids).iterator():
            potential_src_file_ids.add(ancestor_link.ancestor_id)
        return ScaleFile.objects.filter(id__in=list(potential_src_file_ids), file_type='SOURCE')


# TODO: this model and its manager can be removed once all of the remaining views that rely on it are removed
class FileAncestryLink(models.Model):
    """Represents an ancestry link between two files where the ancestor resulted in the descendant through a series of
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
        so this field could be None.
    :type recipe: :class:`django.db.models.ForeignKey`
    :keyword batch: The batch associated with this link's job/recipe, possibly None
    :type batch: :class:`django.db.models.ForeignKey`

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
    """

    ancestor = models.ForeignKey('storage.ScaleFile', on_delete=models.PROTECT, related_name='descendants')
    descendant = models.ForeignKey('storage.ScaleFile', blank=True, null=True, on_delete=models.PROTECT,
                                   related_name='ancestors')

    job_exe = models.ForeignKey('job.JobExecution', blank=True, null=True, on_delete=models.PROTECT,
                                related_name='job_exe_file_links')
    job = models.ForeignKey('job.Job', on_delete=models.PROTECT, related_name='job_file_links')
    recipe = models.ForeignKey('recipe.Recipe', blank=True, on_delete=models.PROTECT, null=True,
                               related_name='recipe_file_links')
    batch = models.ForeignKey('batch.Batch', blank=True, on_delete=models.PROTECT, null=True)

    ancestor_job = models.ForeignKey('job.Job', blank=True, on_delete=models.PROTECT,
                                     related_name='ancestor_job_file_links', null=True)
    ancestor_job_exe = models.ForeignKey('job.JobExecution', blank=True, on_delete=models.PROTECT,
                                         related_name='ancestor_job_exe_file_links', null=True)

    created = models.DateTimeField(auto_now_add=True)

    objects = FileAncestryLinkManager()

    class Meta(object):
        """meta information for the db"""
        db_table = 'file_ancestry_link'


class ProductFileManager(models.GeoManager):
    """Provides additional methods for handling product files
    """

    def filter_products(self, started=None, ended=None, time_field=None, job_type_ids=None, job_type_names=None,
                        job_type_categories=None, job_ids=None, is_operational=None, is_published=None, 
                        is_superseded=None, file_name=None, job_output=None, recipe_ids=None, recipe_type_ids=None, 
                        recipe_job=None, batch_ids=None, order=None):
        """Returns a query for product models that filters on the given fields. The returned query includes the related
        workspace, job_type, and job fields, except for the workspace.json_config field. The related countries are set
        to be pre-fetched as part of the query.

        :param started: Query product files updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query product files updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :keyword time_field: The time field to use for filtering.
        :type time_field: string
        :param job_type_ids: Query product files produced by jobs with the given type identifier.
        :type job_type_ids: list[int]
        :param job_type_names: Query product files produced by jobs with the given type name.
        :type job_type_names: list[str]
        :param job_type_categories: Query product files produced by jobs with the given type category.
        :type job_type_categories: list[str]
        :keyword job_ids: Query product files produced by a given job id
        :type job_ids: list[int]
        :param is_operational: Query product files flagged as operational or R&D only.
        :type is_operational: bool
        :param is_published: Query product files flagged as currently exposed for publication.
        :type is_published: bool
        :param is_superseded: Query product files that have/have not been superseded.
        :type is_superseded: bool
        :param file_name: Query product files with the given file name.
        :type file_name: str
        :keyword job_output: Query product files with the given job output
        :type job_output: str
        :keyword recipe_ids: Query product files produced by a given recipe id
        :type recipe_ids: list[int]
        :keyword recipe_job: Query product files produced by a given recipe name
        :type recipe_job: str
        :keyword recipe_type_ids: Query product files produced by a given recipe types
        :type recipe_type_ids: list[int]
        :keyword batch_ids: Query product files produced by batches with the given identifiers.
        :type batch_ids: list[int]
        :param order: A list of fields to control the sort order.
        :type order: list[str]
        :returns: The product file query
        :rtype: :class:`django.db.models.QuerySet`
        """

        # Fetch a list of product files
        products = ScaleFile.objects.filter(file_type='PRODUCT', has_been_published=True)
        products = products.select_related('workspace', 'job_type', 'job', 'job_exe', 'recipe', 'recipe_type', 'batch')
        products = products.defer('workspace__json_config', 'job__input', 'job__output', 'job_exe__environment',
                                  'job_exe__configuration', 'job_exe__job_metrics', 'job_exe__stdout',
                                  'job_exe__stderr', 'job_exe__results', 'job_exe__results_manifest',
                                  'job_type__interface', 'job_type__docker_params', 'job_type__configuration',
                                  'job_type__error_mapping', 'recipe__input', 'recipe_type__definition',
                                  'batch__definition')
        products = products.prefetch_related('countries')

        # Apply time range filtering
        if started:
            if time_field == 'source':
                products = products.filter(source_started__gte=started)
            elif time_field == 'data':
                products = products.filter(data_started__gte=started)
            else:
                products = products.filter(last_modified__gte=started)
        if ended:
            if time_field == 'source':
                products = products.filter(source_ended__lte=ended)
            elif time_field == 'data':
                products = products.filter(data_ended__lte=ended)
            else:
                products = products.filter(last_modified__lte=ended)

        if job_type_ids:
            products = products.filter(job_type_id__in=job_type_ids)
        if job_type_names:
            products = products.filter(job_type__name__in=job_type_names)
        if job_type_categories:
            products = products.filter(job_type__category__in=job_type_categories)
        if job_ids:
            products = products.filter(job_id__in=job_type_ids)
        if is_operational is not None:
            products = products.filter(job_type__is_operational=is_operational)
        if is_published is not None:
            products = products.filter(is_published=is_published)
        if is_superseded is not None:
            products = products.filter(is_superseded=is_superseded)
        if file_name:
            products = products.filter(file_name=file_name)
        if job_output:
            products = products.filter(job_output=job_output)
        if recipe_ids:
            products = products.filter(recipe_id__in=recipe_ids)
        if recipe_job:
            products = products.filter(recipe_job=recipe_job)
        if recipe_type_ids:
            products = products.filter(recipe_type__in=recipe_type_ids)
        if batch_ids:
            products = products.filter(batch_id__in=batch_ids)

        # Apply sorting
        if order:
            products = products.order_by(*order)
        else:
            products = products.order_by('last_modified')

        return products

    def get_products(self, started=None, ended=None, time_field=None, job_type_ids=None, job_type_names=None,
                     job_type_categories=None, job_ids=None, is_operational=None, is_published=None,
                     file_name=None, job_output=None, recipe_ids=None, recipe_type_ids=None, recipe_job=None,
                     batch_ids=None, order=None):
        """Returns a list of product files within the given time range.

        :param started: Query product files updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query product files updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :keyword time_field: The time field to use for filtering.
        :type time_field: string
        :param job_type_ids: Query product files produced by jobs with the given type identifier.
        :type job_type_ids: list[int]
        :param job_type_names: Query product files produced by jobs with the given type name.
        :type job_type_names: list[str]
        :param job_type_categories: Query product files produced by jobs with the given type category.
        :type job_type_categories: list[str]
        :keyword job_ids: Query product files produced by a given job id
        :type job_ids: list[int]
        :param is_operational: Query product files flagged as operational or R&D only.
        :type is_operational: bool
        :param is_published: Query product files flagged as currently exposed for publication.
        :type is_published: bool
        :param file_name: Query product files with the given file name.
        :type file_name: str
        :keyword job_output: Query product files with the given job output
        :type job_output: str
        :keyword recipe_ids: Query product files produced by a given recipe id
        :type recipe_ids: list[int]
        :keyword recipe_job: Query product files produced by a given recipe name
        :type recipe_job: str
        :keyword recipe_type_ids: Query product files produced by a given recipe types
        :type recipe_type_ids: list[int]
        :keyword batch_ids: Query product files produced by batches with the given identifiers.
        :type batch_ids: list[int]
        :param order: A list of fields to control the sort order.
        :type order: list[str]
        :returns: The list of product files that match the time range.
        :rtype: list[:class:`storage.models.ScaleFile`]
        """

        return self.filter_products(started=started, ended=ended, time_field=time_field, job_type_ids=job_type_ids,
                                    job_type_names=job_type_names, job_type_categories=job_type_categories,
                                    job_ids=None, is_operational=is_operational, is_published=is_published,
                                    is_superseded=False, file_name=file_name, job_output=job_output,
                                    recipe_ids=recipe_ids, recipe_type_ids=recipe_type_ids, recipe_job=recipe_job,
                                    batch_ids=batch_ids, order=order)

    def get_product_sources(self, product_file_id, started=None, ended=None, time_field=None, is_parsed=None, 
                            file_name=None, order=None):
        """Returns a query for the list of sources that produced the given product file ID.

        :param product_file_id: The product file ID.
        :type product_file_id: int
        :param started: Query source files updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query source files updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param time_field: The time field to use for filtering.
        :type time_field: string
        :param is_parsed: Query source files flagged as successfully parsed.
        :type is_parsed: bool
        :param file_name: Query source files with the given file name.
        :type file_name: str
        :param order: A list of fields to control the sort order.
        :type order: list[str]
        :returns: The list of source files that match the time range.
        :rtype: list[:class:`storage.models.ScaleFile`]
        """

        from source.models import SourceFile
        sources = SourceFile.objects.filter_sources(started=started, ended=ended, time_field=time_field,
                                                    is_parsed=is_parsed, file_name=file_name, order=order)
        sources = sources.filter(descendants__descendant_id=product_file_id)

        return sources

    def get_details(self, product_id):
        """Gets additional details for the given product model

        :param product_id: The unique identifier of the product.
        :type product_id: int
        :returns: The product file model with related workspace
        :rtype: :class:`storage.models.ScaleFile`

        :raises :class:`storage.models.ScaleFile.DoesNotExist`: If the file does not exist
        """

        return ScaleFile.objects.all().select_related('workspace').get(pk=product_id, file_type='PRODUCT')

    # TODO: remove when REST API v5 is removed
    def get_details_v5(self, product_id):
        """Gets additional details for the given product model based on related model attributes.

        :param product_id: The unique identifier of the product.
        :type product_id: int
        :returns: The product with extra related attributes: sources, ancestor/descendant products.
        :rtype: :class:`storage.models.ScaleFile`

        :raises :class:`storage.models.ScaleFile.DoesNotExist`: If the file does not exist
        """

        # Attempt to fetch the requested product
        product = ScaleFile.objects.all().select_related('workspace')
        product = product.get(pk=product_id, file_type='PRODUCT')

        # Attempt to fetch all ancestor files
        sources = []
        products = []
        ancestors = ScaleFile.objects.filter(descendants__descendant_id=product.id)
        ancestors = ancestors.select_related('job_type', 'workspace').defer('workspace__json_config')
        ancestors = ancestors.prefetch_related('countries').order_by('created')
        for ancestor in ancestors:
            if ancestor.file_type == 'SOURCE':
                sources.append(ancestor)
            elif ancestor.file_type == 'PRODUCT':
                products.append(ancestor)
        product.sources = sources
        product.ancestor_products = products

        # Attempt to fetch all descendant products
        descendants = ScaleFile.objects.filter(ancestors__ancestor_id=product.id)
        descendants = descendants.select_related('job_type', 'workspace').defer('workspace__json_config')
        descendants = descendants.prefetch_related('countries').order_by('created')
        product.descendant_products = descendants

        return product

    def populate_source_ancestors(self, products):
        """Populates each of the given products with its source file ancestors in a field called "source_files"

        :param products: List of products
        :type products: list of :class:`storage.models.ScaleFile`
        """

        product_lists = {}  # {product ID: list of source files}
        for product in products:
            product.source_files = []
            product_lists[product.id] = product.source_files

        source_files = {}  # {source file ID: source file}
        ancestor_ids = set()
        for link in FileAncestryLink.objects.filter(descendant_id__in=product_lists).only('ancestor_id'):
            ancestor_ids.add(link.ancestor_id)
        src_qry = ScaleFile.objects.filter(file_type='SOURCE', id__in=ancestor_ids)
        src_qry = src_qry.select_related('workspace').defer('workspace__json_config')
        for source in src_qry:
            source_files[source.id] = source

        link_qry = FileAncestryLink.objects.filter(ancestor_id__in=source_files.keys())
        link_qry = link_qry.filter(descendant_id__in=product_lists.keys())
        for link in link_qry:
            product_lists[link.descendant_id].append(source_files[link.ancestor_id])

    @transaction.atomic
    def publish_products(self, job_exe_id, job, when):
        """Publishes all of the products produced by the given job execution. All database changes will be made in an
        atomic transaction.

        :param job_exe_id: The job execution ID
        :type job_exe_id: int
        :param job: The locked job model
        :type job: :class:`job.models.Job`
        :param when: When the products were published
        :type when: :class:`datetime.datetime`
        """

        # Don't publish products if the job is already superseded
        if job.is_superseded:
            return

        # Unpublish any products created by jobs that are superseded by this job
        if job.root_superseded_job_id:
            self.unpublish_products(job.root_superseded_job_id, when)

        # Grab UUIDs from new products to be published
        uuids = []
        for product_file in self.filter(job_exe_id=job_exe_id):
            uuids.append(product_file.uuid)

        # Supersede products with the same UUIDs (a given UUID should only appear once in the product API calls)
        if uuids:
            query = self.filter(uuid__in=uuids, has_been_published=True)
            query.update(is_published=False, is_superseded=True, superseded=when, last_modified=timezone.now())

        # Publish this job execution's products
        self.filter(job_exe_id=job_exe_id).update(has_been_published=True, is_published=True, published=when,
                                                  last_modified=timezone.now())

    def unpublish_products(self, root_job_id, when):
        """Unpublishes all of the published products created by the superseded jobs with the given root ID

        :param root_job_id: The root superseded job ID
        :type root_job_id: int
        :param when: When the products were unpublished
        :type when: :class:`datetime.datetime`
        """

        last_modified = timezone.now()
        query = self.filter(job__root_superseded_job_id=root_job_id, is_published=True)
        query.update(is_published=False, unpublished=when, last_modified=last_modified)
        query = self.filter(job_id=root_job_id, is_published=True)
        query.update(is_published=False, unpublished=when, last_modified=last_modified)

    def upload_files(self, file_entries, input_file_ids, job_exe, workspace):
        """Uploads the given local product files into the workspace.

        :param file_entries: List of files where each file is a tuple of (absolute local path, workspace path for
            storing the file, media_type, output_name)
        :type file_entries: list of tuple(str, str, str, str)
        :param input_file_ids: List of identifiers for files used to produce the given file entries
        :type input_file_ids: list of int
        :param job_exe: The job_exe model with the related job and job_type fields
        :type job_exe: :class:`job.models.JobExecution`
        :param workspace: The workspace to use for storing the product files
        :type workspace: :class:`storage.models.Workspace`
        :returns: The list of the saved product models
        :rtype: list of :class:`storage.models.ScaleFile`
        """

        # Build a list of UUIDs for the input files
        input_files = ScaleFile.objects.filter(pk__in=input_file_ids).values('uuid', 'id').order_by('uuid')
        input_file_uuids = [f['uuid'] for f in input_files]

        # Get property names and values as strings
        properties = job_exe.job.get_job_data().get_all_properties()

        # Product UUID will be based in part on input data (UUIDs of input files and name/value pairs of input
        # properties)
        input_strings = input_file_uuids
        input_strings.extend(properties)

        # Determine if any input files are non-operational products
        input_products = ScaleFile.objects.filter(id__in=[f['id'] for f in input_files], file_type='PRODUCT')
        input_products_operational = all([f.is_operational for f in input_products])

        source_started = job_exe.job.source_started
        source_ended = job_exe.job.source_ended
        if not source_started:
            # Compute the overall start and stop times for all file_entries
            source_files = FileAncestryLink.objects.get_source_ancestors([f['id'] for f in input_files])
            start_times = [f.data_started for f in source_files]
            end_times = [f.data_ended for f in source_files]
            start_times.sort()
            end_times.sort(reverse=True)
            if start_times:
                source_started = start_times[0]
            if end_times:
                source_ended = end_times[0]

        products_to_save = []
        for entry in file_entries:
            local_path = entry[0]
            remote_path = entry[1]
            media_type = entry[2]
            output_name = entry[3]

            product = ProductFile.create()
            product.job_exe = job_exe
            product.job = job_exe.job
            product.job_type = job_exe.job.job_type
            product.is_operational = input_products_operational and job_exe.job.job_type.is_operational
            file_name = os.path.basename(local_path)
            file_size = os.path.getsize(local_path)
            product.set_basic_fields(file_name, file_size, media_type)
            product.file_path = remote_path
            product.job_output = output_name

            # Add a stable identifier based on the job type, input files, input properties, and file name
            # This is designed to remain stable across re-processing the same type of job on the same inputs
            product.update_uuid(job_exe.job.job_type.id, file_name, *input_strings)

            # Add geospatial info to product if available
            if len(entry) > 4:
                geo_metadata = entry[4]
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
                    if props:
                        product.meta_data = props
                    product.center_point = geo_utils.get_center_point(geom)

            # Add recipe info to product if available.
            job_recipe = Recipe.objects.get_recipe_for_job(job_exe.job_id)
            if job_recipe:
                product.recipe_id = job_recipe.recipe.id
                product.recipe_type = job_recipe.recipe.recipe_type
                product.recipe_job = job_recipe.job_name

                # Add batch info to product if available.
                try:
                    from batch.models import BatchJob
                    product.batch_id = BatchJob.objects.get(job_id=job_exe.job_id).batch_id
                except BatchJob.DoesNotExist:
                    product.batch_id = None

            product.source_started = source_started
            product.source_ended = source_ended

            products_to_save.append(FileUpload(product, local_path))

        return ScaleFile.objects.upload_files(workspace, products_to_save)


class ProductFile(ScaleFile):
    """Represents a product file that has been created by Scale. This is a proxy model of the
    :class:`storage.models.ScaleFile` model. It has the same set of fields, but a different manager that provides
    functionality specific to product files.
    """

    VALID_TIME_FIELDS = ['source', 'data', 'last_modified']

    @classmethod
    def create(cls):
        """Creates a new product file

        :returns: The new product file
        :rtype: :class:`product.models.ProductFile`
        """

        product_file = ProductFile()
        product_file.file_type = 'PRODUCT'
        return product_file

    objects = ProductFileManager()

    class Meta(object):
        """meta information for the db"""
        proxy = True
