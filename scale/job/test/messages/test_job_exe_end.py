from __future__ import unicode_literals

import django
from django.utils.timezone import now
from django.test import TransactionTestCase

import job.test.utils as job_test_utils
from error.models import reset_error_cache
from job.messages.job_exe_end import CreateJobExecutionEnd
from job.models import JobExecutionEnd
from job.tasks.update import TaskStatusUpdate


class TestCreateJobExecutionEnd(TransactionTestCase):

    fixtures = ['basic_errors.json', 'basic_job_errors.json']

    def setUp(self):
        django.setup()

        # Clear error cache so tests work correctly
        reset_error_cache()

    def test_json(self):
        """Tests coverting a CreateJobExecutionEnd message to and from JSON"""

        job_exe_1 = job_test_utils.create_running_job_exe()
        job_exe_2 = job_test_utils.create_running_job_exe()
        job_exe_3 = job_test_utils.create_running_job_exe()
        job_exe_4 = job_test_utils.create_running_job_exe()
        job_exe_5 = job_test_utils.create_running_job_exe()
        job_exe_ids = [job_exe_1.id, job_exe_2.id, job_exe_3.id, job_exe_4.id, job_exe_5.id]

        # Execution that was immediately canceled
        job_exe_1.execution_canceled(now())

        # Execution that was canceled after a task launched
        task_2 = job_exe_2.start_next_task()
        task_2.launch(now())
        job_exe_2.execution_canceled(now())
        update = job_test_utils.create_task_status_update(task_2.id, task_2.agent_id, TaskStatusUpdate.KILLED, now())
        task_2.update(update)
        job_exe_2.task_update(update)

        # Execution where a task timed out
        task_3 = job_exe_3.start_next_task()
        task_3.launch(now())
        job_exe_3.execution_timed_out(task_3, now())
        update = job_test_utils.create_task_status_update(task_3.id, task_3.agent_id, TaskStatusUpdate.KILLED, now())
        task_3.update(update)
        job_exe_3.task_update(update)

        # Execution where a task failed
        task_4 = job_exe_4.start_next_task()
        task_4.launch(now())
        update = job_test_utils.create_task_status_update(task_4.id, task_4.agent_id, TaskStatusUpdate.FAILED, now())
        task_4.update(update)
        job_exe_4.task_update(update)

        # Execution that completed
        while not job_exe_5.is_finished():
            task_5 = job_exe_5.start_next_task()
            task_5.launch(now())
            update = job_test_utils.create_task_status_update(task_5.id, task_5.agent_id, TaskStatusUpdate.RUNNING,
                                                              now())
            task_5.update(update)
            job_exe_5.task_update(update)
            update = job_test_utils.create_task_status_update(task_5.id, task_5.agent_id, TaskStatusUpdate.FINISHED,
                                                              now())
            task_5.update(update)
            job_exe_5.task_update(update)

        # Add models to message
        message = CreateJobExecutionEnd()
        if message.can_fit_more():
            message.add_job_exe_end(job_exe_1.create_job_exe_end_model())
        if message.can_fit_more():
            message.add_job_exe_end(job_exe_2.create_job_exe_end_model())
        if message.can_fit_more():
            message.add_job_exe_end(job_exe_3.create_job_exe_end_model())
        if message.can_fit_more():
            message.add_job_exe_end(job_exe_4.create_job_exe_end_model())
        if message.can_fit_more():
            message.add_job_exe_end(job_exe_5.create_job_exe_end_model())

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = CreateJobExecutionEnd.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        job_exe_ends = JobExecutionEnd.objects.filter(job_exe_id__in=job_exe_ids).order_by('job_exe_id')
        self.assertEqual(len(job_exe_ends), 5)
        self.assertEqual(job_exe_ends[0].status, 'CANCELED')
        self.assertEqual(job_exe_ends[1].status, 'CANCELED')
        self.assertEqual(job_exe_ends[2].status, 'FAILED')
        self.assertEqual(job_exe_ends[3].status, 'FAILED')
        self.assertEqual(job_exe_ends[4].status, 'COMPLETED')

    def test_execute(self):
        """Tests calling CreateJobExecutionEnd.execute() successfully"""

        # Add 3 job_exe_end models to messages 1, 2, and 3
        message_1 = CreateJobExecutionEnd()
        message_2 = CreateJobExecutionEnd()
        message_3 = CreateJobExecutionEnd()
        job_exe_ids = []
        for _ in range(3):
            job_exe = job_test_utils.create_running_job_exe()
            job_exe_ids.append(job_exe.id)
            while not job_exe.is_finished():
                task = job_exe.start_next_task()
                task.launch(now())
                update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING,
                                                                  now())
                task.update(update)
                job_exe.task_update(update)
                update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FINISHED,
                                                                  now())
                task.update(update)
                job_exe.task_update(update)
            message_1.add_job_exe_end(job_exe.create_job_exe_end_model())
            message_1.add_job_exe_end(job_exe.create_job_exe_end_model())  # Test having duplicate models
            message_2.add_job_exe_end(job_exe.create_job_exe_end_model())
            message_3.add_job_exe_end(job_exe.create_job_exe_end_model())

        # Execute message 1 with 3 job_exe_end models
        message_1.execute()
        self.assertEqual(JobExecutionEnd.objects.filter(job_exe_id__in=job_exe_ids).count(), 3)

        # Add more job_exe_end models to messages 1 and 2
        while message_2.can_fit_more():
            job_exe = job_test_utils.create_running_job_exe()
            job_exe_ids.append(job_exe.id)
            while not job_exe.is_finished():
                task = job_exe.start_next_task()
                task.launch(now())
                update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING,
                                                                  now())
                task.update(update)
                job_exe.task_update(update)
                update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FINISHED,
                                                                  now())
                task.update(update)
                job_exe.task_update(update)
            message_2.add_job_exe_end(job_exe.create_job_exe_end_model())
            message_3.add_job_exe_end(job_exe.create_job_exe_end_model())

        # Execute message 2 with same 3 job_exe_end models from before, plus new ones
        # Old models should not cause an error and only new ones should get created
        message_2.execute()
        self.assertEqual(JobExecutionEnd.objects.filter(job_exe_id__in=job_exe_ids).count(), len(job_exe_ids))

        # Execute message 3 with all old models
        # Old models should not cause an error and no new ones should get created
        message_3.execute()
        self.assertEqual(JobExecutionEnd.objects.filter(job_exe_id__in=job_exe_ids).count(), len(job_exe_ids))
