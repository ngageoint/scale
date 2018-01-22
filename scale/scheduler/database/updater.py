"""Defines the class that performs the Scale database update"""
from __future__ import unicode_literals

import logging

from django.db import connection, transaction

from batch.models import Batch
from job.execution.tasks.json.results.task_results import TaskResults
from job.models import Job, JobExecution, JobExecutionEnd, JobExecutionOutput, TaskUpdate
from recipe.models import Recipe
from util.exceptions import TerminatedCommand
from util.parse import datetime_to_string


logger = logging.getLogger(__name__)


class DatabaseUpdater(object):
    """This class manages the Scale database update. This class is thread-safe."""

    def __init__(self):
        """Constructor
        """

        self._running = True
        self._updated_job_exe = 0
        self._total_job_exe = 0
        self._updated_job = 0
        self._total_job = 0
        self._current_recipe_id = None
        self._updated_recipe = 0
        self._total_recipe = 0
        self._current_batch_id = None
        self._updated_batch = 0
        self._total_batch = 0

    def update(self):
        """Runs the database update
        """

        # Converting job execution models
        self._perform_update_init()
        while True:
            if not self._running:
                raise TerminatedCommand()

            if self._updated_job_exe >= self._total_job_exe:
                break
            self._perform_update_iteration()

        # Removing job execution duplicates
        self._perform_job_exe_dup_init()
        while True:
            if not self._running:
                raise TerminatedCommand()

            if self._updated_job >= self._total_job:
                break
            self._perform_job_exe_dup_iteration()

        # Populating new recipe fields in job models
        self._perform_recipe_field_init()
        while True:
            if not self._running:
                raise TerminatedCommand()

            if self._updated_recipe >= self._total_recipe:
                break
            self._perform_recipe_field_iteration()

        # Populating new batch fields in job and recipe models
        self._perform_batch_field_init()
        while True:
            if not self._running:
                raise TerminatedCommand()

            if self._updated_batch >= self._total_batch:
                break
            self._perform_batch_field_iteration()

    def stop(self):
        """Informs the database updater to stop running
        """

        logger.info('Scale database updater has been told to stop')
        self._running = False

    def _perform_batch_field_init(self):
        """Performs any initialization piece of the setting of batch fields on job and recipe models
        """

        logger.info('Scale is now populating the new batch fields on the job and recipe models')
        logger.info('Counting the number of batches...')
        self._total_batch = Batch.objects.all().count()
        logger.info('Found %d batches that need to be done', self._total_batch)

    def _perform_batch_field_iteration(self):
        """Performs a single iteration of the setting of batch fields on job and recipe models
        """

        # Get batch ID
        batch_qry = Batch.objects.all()
        if self._current_batch_id:
            batch_qry = batch_qry.filter(id__gt=self._current_batch_id)
        for batch in batch_qry.order_by('id').only('id')[:1]:
            batch_id = batch.id
            break

        # Populate job.recipe_id if it is missing
        qry_1 = 'UPDATE job j SET batch_id = bj.batch_id FROM batch_job bj'
        qry_1 += ' WHERE j.id = bj.job_id AND bj.batch_id = %s AND j.batch_id IS NULL'
        qry_2 = 'UPDATE recipe r SET batch_id = br.batch_id FROM batch_recipe br'
        qry_2 += ' WHERE r.id = br.recipe_id AND br.batch_id = %s AND r.batch_id IS NULL'
        with connection.cursor() as cursor:
            cursor.execute(qry_1, [str(batch_id)])
            count = cursor.rowcount
            if count:
                logger.info('%d job(s) updated with batch_id %d', count, batch_id)
            cursor.execute(qry_2, [str(batch_id)])
            count = cursor.rowcount
            if count:
                logger.info('%d recipe(s) updated with batch_id %d', count, batch_id)

        self._current_batch_id = batch_id
        self._updated_batch += 1
        if self._updated_batch > self._total_batch:
            self._updated_batch = self._total_batch
        percent = (float(self._updated_batch) / float(self._total_batch)) * 100.00
        logger.info('Completed %s of %s batches (%.1f%%)', self._updated_batch, self._total_batch, percent)

    def _perform_job_exe_dup_init(self):
        """Performs any initialization piece of the removal of job execution duplicates
        """

        logger.info('Scale is now removing duplicate job execution models')
        logger.info('Counting the number of jobs that need to be checked...')
        self._total_job = Job.objects.all().count()
        logger.info('Found %d jobs that need to be checked for duplicate executions', self._total_job)

    def _perform_job_exe_dup_iteration(self):
        """Performs a single iteration of the removal of job execution duplicates
        """

        job_batch_size = 10000

        batch_start_job_id = self._updated_job
        batch_end_job_id = batch_start_job_id + job_batch_size - 1

        # Find (job_id, exe_num) pairs that have duplicates
        job_ids_by_exe_num = {}  # {Exe num: [Job ID]}
        job_exe_ids_by_exe_num = {}  # {Exe num: [Job Exe ID]}, these are the "good" exes to keep
        qry = 'SELECT job_id, exe_num, count(*), min(id) FROM job_exe'
        qry += ' WHERE job_id BETWEEN %s AND %s GROUP BY job_id, exe_num'
        qry = 'SELECT job_id, exe_num, count, min FROM (%s) c WHERE count > 1' % qry
        with connection.cursor() as cursor:
            cursor.execute(qry, [str(batch_start_job_id), str(batch_end_job_id)])
            for row in cursor.fetchall():
                job_id = row[0]
                exe_num = row[1]
                job_exe_id = row[3]
                if exe_num not in job_ids_by_exe_num:
                    job_ids_by_exe_num[exe_num] = []
                    job_exe_ids_by_exe_num[exe_num] = []
                job_ids_by_exe_num[exe_num].append(job_id)
                job_exe_ids_by_exe_num[exe_num].append(job_exe_id)

        if job_ids_by_exe_num:
            # Find IDs of duplicate job_exes
            job_exe_ids_to_delete = []
            for exe_num in job_ids_by_exe_num:
                job_ids = job_ids_by_exe_num[exe_num]
                job_exe_ids = job_exe_ids_by_exe_num[exe_num]  # These are the "good" exes to keep
                job_exe_qry = JobExecution.objects.filter(job_id__in=job_ids, exe_num=exe_num)
                for job_exe in job_exe_qry.exclude(id__in=job_exe_ids).only('id'):
                    job_exe_ids_to_delete.append(job_exe.id)

            logger.info('Deleting %d duplicates that were found...', len(job_exe_ids_to_delete))
            TaskUpdate.objects.filter(job_exe_id__in=job_exe_ids_to_delete).delete()
            JobExecutionOutput.objects.filter(job_exe_id__in=job_exe_ids_to_delete).delete()
            JobExecutionEnd.objects.filter(job_exe_id__in=job_exe_ids_to_delete).delete()
            deleted_count = JobExecution.objects.filter(id__in=job_exe_ids_to_delete).delete()[0]
            logger.info('Deleted %d duplicates', deleted_count)
        else:
            logger.info('No duplicates found')

        self._updated_job += job_batch_size
        if self._updated_job > self._total_job:
            self._updated_job = self._total_job
        percent = (float(self._updated_job) / float(self._total_job)) * 100.00
        logger.info('Completed %s of %s jobs (%.1f%%)', self._updated_job, self._total_job, percent)

    def _perform_recipe_field_init(self):
        """Performs any initialization piece of the setting of recipe fields on job models
        """

        logger.info('Scale is now populating the new recipe fields on the job models')
        logger.info('Counting the number of recipes...')
        self._total_recipe = Recipe.objects.all().count()
        logger.info('Found %d recipes that need to be done', self._total_recipe)

    def _perform_recipe_field_iteration(self):
        """Performs a single iteration of the setting of recipe fields on job models
        """

        recipe_batch_size = 10000

        # Get recipe IDs
        recipe_qry = Recipe.objects.all()
        if self._current_recipe_id:
            recipe_qry = recipe_qry.filter(id__gt=self._current_recipe_id)
        recipe_ids = [recipe.id for recipe in recipe_qry.order_by('id').only('id')[:recipe_batch_size]]

        # Populate job.recipe_id if it is missing
        qry_1 = 'UPDATE job j SET recipe_id = rj.recipe_id FROM recipe_job rj'
        qry_1 += ' WHERE j.id = rj.job_id AND rj.recipe_id IN %s AND rj.is_original AND j.recipe_id IS NULL'
        qry_2 = 'UPDATE job j SET root_recipe_id = r.id FROM recipe_job rj'
        qry_2 += ' JOIN recipe r ON rj.recipe_id = r.id WHERE j.id = rj.job_id AND'
        qry_2 += ' r.id IN %s AND r.root_superseded_recipe_id IS NULL AND j.root_recipe_id IS NULL'
        qry_3 = 'UPDATE job j SET root_recipe_id = r.root_superseded_recipe_id FROM recipe_job rj'
        qry_3 += ' JOIN recipe r ON rj.recipe_id = r.id WHERE j.id = rj.job_id'
        qry_3 += ' AND r.id IN %s AND r.root_superseded_recipe_id IS NOT NULL AND j.root_recipe_id IS NULL'
        with connection.cursor() as cursor:
            cursor.execute(qry_1, [tuple(recipe_ids)])
            count = cursor.rowcount
            if count:
                logger.info('%d job(s) updated with recipe_id field', count)
            cursor.execute(qry_2, [tuple(recipe_ids)])
            count = cursor.rowcount
            if count:
                logger.info('%d job(s) updated with root_recipe_id field', count)
            cursor.execute(qry_3, [tuple(recipe_ids)])
            count = cursor.rowcount
            if count:
                logger.info('%d job(s) updated with root_recipe_id field', count)

        self._current_recipe_id = recipe_ids[-1]
        self._updated_recipe += recipe_batch_size
        if self._updated_recipe > self._total_recipe:
            self._updated_recipe = self._total_recipe
        percent = (float(self._updated_recipe) / float(self._total_recipe)) * 100.00
        logger.info('Completed %s of %s recipes (%.1f%%)', self._updated_recipe, self._total_recipe, percent)

    def _perform_update_init(self):
        """Performs any initialization piece of the database update
        """

        msg = 'This Scale database update converts old job_exe models into new '
        msg += 'job_exe, job_exe_end, and job_exe_output models.'
        logger.info(msg)
        logger.info('Counting the number of job executions that need to be updated...')
        self._total_job_exe = JobExecution.objects.filter(status__isnull=False).count()
        logger.info('Found %d job executions that need to be updated', self._total_job_exe)

    def _perform_update_iteration(self):
        """Performs a single iteration of the database update
        """

        # Retrieve 500 job executions that need to be updated and get job IDs
        job_ids = set()
        for job_exe in JobExecution.objects.filter(status__isnull=False).only('id', 'job_id')[:500]:
            job_ids.add(job_exe.job_id)

        # Retrieve all job executions for those jobs in sorted order
        job_exe_count = 0
        current_job_id = None
        current_exe_num = 1
        exe_num_dict = {}  # {exe_num: [job_exe.id]}
        job_exe_end_models = []
        job_exe_output_models = []
        job_exe_qry = JobExecution.objects.select_related('job').filter(job_id__in=job_ids)
        for job_exe in job_exe_qry.defer('resources', 'configuration', 'stdout', 'stderr').order_by('job_id', 'id'):
            job_exe_count += 1
            if job_exe.job_id == current_job_id:
                current_exe_num += 1
            else:
                current_job_id = job_exe.job_id
                current_exe_num = 1

            # This job_exe model needs to be updated with its exe_num
            if current_exe_num in exe_num_dict:
                exe_num_dict[current_exe_num].append(job_exe.id)
            else:
                exe_num_dict[current_exe_num] = [job_exe.id]

            if job_exe.status in ['COMPLETED', 'FAILED', 'CANCELED']:
                # Create corresponding job_exe_end model
                job_exe_end = JobExecutionEnd()
                job_exe_end.job_exe_id = job_exe.id
                job_exe_end.job_id = job_exe.job_id
                job_exe_end.job_type_id = job_exe.job.job_type_id
                job_exe_end.exe_num = current_exe_num

                # Create task results from job_exe task fields
                task_list = []
                if job_exe.pre_started:
                    pre_task_dict = {'task_id': '%s_%s' % (job_exe.get_cluster_id(), 'pre'), 'type': 'pre',
                                     'was_launched': True, 'was_started': True,
                                     'started': datetime_to_string(job_exe.pre_started)}
                    if job_exe.pre_completed:
                        pre_task_dict['ended'] = datetime_to_string(job_exe.pre_completed)
                    if job_exe.pre_exit_code is not None:
                        pre_task_dict['exit_code'] = job_exe.pre_exit_code
                    task_list.append(pre_task_dict)
                if job_exe.job_started:
                    job_task_dict = {'task_id': '%s_%s' % (job_exe.get_cluster_id(), 'job'), 'type': 'main',
                                     'was_launched': True, 'was_started': True,
                                     'started': datetime_to_string(job_exe.job_started)}
                    if job_exe.job_completed:
                        job_task_dict['ended'] = datetime_to_string(job_exe.job_completed)
                    if job_exe.job_exit_code is not None:
                        job_task_dict['exit_code'] = job_exe.job_exit_code
                    task_list.append(job_task_dict)
                if job_exe.post_started:
                    post_task_dict = {'task_id': '%s_%s' % (job_exe.get_cluster_id(), 'post'), 'type': 'post',
                                      'was_launched': True, 'was_started': True,
                                      'started': datetime_to_string(job_exe.post_started)}
                    if job_exe.post_completed:
                        post_task_dict['ended'] = datetime_to_string(job_exe.post_completed)
                    if job_exe.post_exit_code is not None:
                        post_task_dict['exit_code'] = job_exe.post_exit_code
                    task_list.append(post_task_dict)
                task_results = TaskResults({'tasks': task_list})

                job_exe_end.task_results = task_results.get_dict()
                job_exe_end.status = job_exe.status
                job_exe_end.error_id = job_exe.error_id
                job_exe_end.node_id = job_exe.node_id
                job_exe_end.queued = job_exe.queued
                job_exe_end.started = job_exe.started
                job_exe_end.ended = job_exe.ended
                job_exe_end_models.append(job_exe_end)

            if job_exe.status == 'COMPLETED':
                # Create corresponding job_exe_output model
                job_exe_output = JobExecutionOutput()
                job_exe_output.job_exe_id = job_exe.id
                job_exe_output.job_id = job_exe.job_id
                job_exe_output.job_type_id = job_exe.job.job_type_id
                job_exe_output.exe_num = current_exe_num
                job_exe_output.output = job_exe.results
                job_exe_output_models.append(job_exe_output)

        # Update/create models in an atomic transaction
        with transaction.atomic():
            for exe_num, job_exe_ids in exe_num_dict.items():
                JobExecution.objects.filter(id__in=job_exe_ids).update(exe_num=exe_num, status=None, error_id=None,
                                                                       command_arguments=None, environment=None,
                                                                       cpus_scheduled=None, mem_scheduled=None,
                                                                       disk_out_scheduled=None,
                                                                       disk_total_scheduled=None, pre_started=None,
                                                                       pre_completed=None, pre_exit_code=None,
                                                                       job_started=None, job_completed=None,
                                                                       job_exit_code=None, job_metrics=None,
                                                                       post_started=None, post_completed=None,
                                                                       post_exit_code=None, stdout=None, stderr=None,
                                                                       results_manifest=None, results=None, ended=None,
                                                                       last_modified=None)
            JobExecutionEnd.objects.bulk_create(job_exe_end_models)
            JobExecutionOutput.objects.bulk_create(job_exe_output_models)

        logger.info('Updated %d job executions', job_exe_count)
        self._updated_job_exe += job_exe_count
        percent = (float(self._updated_job_exe) / float(self._total_job_exe)) * 100.00
        print 'Completed %s of %s job executions (%.1f%%)' % (self._updated_job_exe, self._total_job_exe, percent)
