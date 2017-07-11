from __future__ import unicode_literals

import datetime

import django
from django.test import TestCase
from django.utils.timezone import now

import error.test.utils as error_test_utils
import job.test.utils as job_test_utils
import node.test.utils as node_test_utils
from job.execution.job_exe import RunningJobExecution
from job.execution.metrics import FinishedJobExeMetricsOverTime, TotalJobExeMetrics


class TestTotalJobExeMetrics(TestCase):
    """Tests the TotalJobExeMetrics class"""

    def setUp(self):
        django.setup()

        self.alg_error = error_test_utils.create_error(category='ALGORITHM')
        self.data_error = error_test_utils.create_error(category='DATA')
        self.system_error = error_test_utils.create_error(category='SYSTEM')

        self.metrics = TotalJobExeMetrics(now())

    def test_init_with_database(self):
        """Tests calling init_with_database() successfully to load in job executions from the database"""

        # First block of job executions
        end_time_1 = now() - FinishedJobExeMetricsOverTime.BLOCK_LENGTH - FinishedJobExeMetricsOverTime.BLOCK_LENGTH
        node_model_1 = node_test_utils.create_node()
        job_type_1 = job_test_utils.create_job_type()
        job_type_2 = job_test_utils.create_job_type()
        job_exe_model_1 = job_test_utils.create_job_exe(job_type=job_type_1, status='COMPLETED', ended=end_time_1,
                                                        node=node_model_1)
        job_exe_model_2 = job_test_utils.create_job_exe(job_type=job_type_1, status='COMPLETED', ended=end_time_1,
                                                        node=node_model_1)
        job_exe_model_3 = job_test_utils.create_job_exe(job_type=job_type_1, status='FAILED', ended=end_time_1,
                                                        error=self.alg_error, node=node_model_1)
        job_exe_model_4 = job_test_utils.create_job_exe(job_type=job_type_1, status='FAILED', ended=end_time_1,
                                                        error=self.alg_error, node=node_model_1)
        job_exe_model_5 = job_test_utils.create_job_exe(job_type=job_type_1, status='FAILED', ended=end_time_1,
                                                        error=self.alg_error, node=node_model_1)
        job_exe_model_6 = job_test_utils.create_job_exe(job_type=job_type_1, status='FAILED', ended=end_time_1,
                                                        error=self.data_error, node=node_model_1)
        job_exe_model_7 = job_test_utils.create_job_exe(job_type=job_type_1, status='FAILED', ended=end_time_1,
                                                        error=self.system_error, node=node_model_1)
        job_exe_model_8 = job_test_utils.create_job_exe(job_type=job_type_2, status='FAILED', ended=end_time_1,
                                                        error=self.system_error, node=node_model_1)
        node_model_2 = node_test_utils.create_node()
        job_exe_model_9 = job_test_utils.create_job_exe(job_type=job_type_1, status='COMPLETED', ended=end_time_1,
                                                        node=node_model_2)
        job_exe_model_10 = job_test_utils.create_job_exe(job_type=job_type_2, status='COMPLETED', ended=end_time_1,
                                                         node=node_model_2)
        job_exe_model_11 = job_test_utils.create_job_exe(job_type=job_type_2, status='FAILED', ended=end_time_1,
                                                         error=self.data_error, node=node_model_2)
        # Second block of job executions (one time block over from first set of executions)
        end_time_2 = end_time_1 + FinishedJobExeMetricsOverTime.BLOCK_LENGTH
        job_exe_model_12 = job_test_utils.create_job_exe(job_type=job_type_2, status='FAILED', ended=end_time_2,
                                                         error=self.system_error, node=node_model_1)
        job_exe_model_13 = job_test_utils.create_job_exe(job_type=job_type_2, status='FAILED', ended=end_time_2,
                                                         error=self.system_error, node=node_model_1)
        job_exe_model_14 = job_test_utils.create_job_exe(job_type=job_type_2, status='COMPLETED', ended=end_time_2,
                                                         node=node_model_2)
        # Load all initial executions from database
        self.metrics.init_with_database()

        # Generate JSON which should include both sets of job executions
        right_now = end_time_2 + datetime.timedelta(seconds=30)
        node_list_dict = [{'id': node_model_1.id}, {'id': node_model_2.id}]
        self.metrics.generate_status_json(node_list_dict, right_now)

        # Check expected totals
        self.assertEqual(node_list_dict[0]['job_executions']['running']['total'], 0)
        self.assertEqual(node_list_dict[0]['job_executions']['completed']['total'], 2)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['total'], 8)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['algorithm']['total'], 3)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['data']['total'], 1)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['system']['total'], 4)
        self.assertEqual(node_list_dict[1]['job_executions']['running']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['completed']['total'], 3)
        self.assertEqual(node_list_dict[1]['job_executions']['failed']['total'], 1)
        self.assertEqual(node_list_dict[1]['job_executions']['failed']['algorithm']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['failed']['data']['total'], 1)
        self.assertEqual(node_list_dict[1]['job_executions']['failed']['system']['total'], 0)

        # Generate JSON which should include only second set of job executions (first set rolled off by time)
        later = end_time_1 + FinishedJobExeMetricsOverTime.TOTAL_TIME_PERIOD + datetime.timedelta(seconds=1)
        later += FinishedJobExeMetricsOverTime.BLOCK_LENGTH
        node_list_dict = [{'id': node_model_1.id}, {'id': node_model_2.id}]
        self.metrics.generate_status_json(node_list_dict, later)

        # Check expected totals
        self.assertEqual(node_list_dict[0]['job_executions']['running']['total'], 0)
        self.assertEqual(node_list_dict[0]['job_executions']['completed']['total'], 0)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['total'], 2)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['algorithm']['total'], 0)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['data']['total'], 0)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['system']['total'], 2)
        self.assertEqual(node_list_dict[1]['job_executions']['running']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['completed']['total'], 1)
        self.assertEqual(node_list_dict[1]['job_executions']['failed']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['failed']['algorithm']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['failed']['data']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['failed']['system']['total'], 0)

        # Generate JSON where all job executions should have rolled off by time
        later = later + FinishedJobExeMetricsOverTime.TOTAL_TIME_PERIOD
        node_list_dict = [{'id': node_model_1.id}, {'id': node_model_2.id}]
        self.metrics.generate_status_json(node_list_dict, later)

        # Check expected totals
        self.assertEqual(node_list_dict[0]['job_executions']['running']['total'], 0)
        self.assertEqual(node_list_dict[0]['job_executions']['completed']['total'], 0)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['total'], 0)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['algorithm']['total'], 0)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['data']['total'], 0)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['system']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['running']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['completed']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['failed']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['failed']['algorithm']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['failed']['data']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['failed']['system']['total'], 0)

    def test_running_executions(self):
        """Tests the metrics with running executions that complete"""

        node_model_1 = node_test_utils.create_node()
        node_model_2 = node_test_utils.create_node()
        job_type_1 = job_test_utils.create_job_type()
        job_type_2 = job_test_utils.create_job_type()
        job_exe_model_1 = job_test_utils.create_job_exe(job_type=job_type_1, status='RUNNING', node=node_model_1)
        job_exe_model_2 = job_test_utils.create_job_exe(job_type=job_type_1, status='RUNNING', node=node_model_1)
        job_exe_model_3 = job_test_utils.create_job_exe(job_type=job_type_1, status='RUNNING', node=node_model_1)
        job_exe_model_4 = job_test_utils.create_job_exe(job_type=job_type_2, status='RUNNING', node=node_model_1)
        job_exe_model_5 = job_test_utils.create_job_exe(job_type=job_type_1, status='RUNNING', node=node_model_2)
        job_exe_model_6 = job_test_utils.create_job_exe(job_type=job_type_1, status='RUNNING', node=node_model_2)
        job_exe_model_7 = job_test_utils.create_job_exe(job_type=job_type_2, status='RUNNING', node=node_model_2)
        job_exe_model_8 = job_test_utils.create_job_exe(job_type=job_type_2, status='RUNNING', node=node_model_2)
        job_exe_model_9 = job_test_utils.create_job_exe(job_type=job_type_2, status='RUNNING', node=node_model_2)
        job_exe_model_10 = job_test_utils.create_job_exe(job_type=job_type_2, status='RUNNING', node=node_model_2)
        job_exe_model_11 = job_test_utils.create_job_exe(job_type=job_type_2, status='RUNNING', node=node_model_2)
        job_exe_1 = RunningJobExecution('agent', job_exe_model_1)
        job_exe_2 = RunningJobExecution('agent', job_exe_model_2)
        job_exe_3 = RunningJobExecution('agent', job_exe_model_3)
        job_exe_4 = RunningJobExecution('agent', job_exe_model_4)
        job_exe_5 = RunningJobExecution('agent', job_exe_model_5)
        job_exe_6 = RunningJobExecution('agent', job_exe_model_6)
        job_exe_7 = RunningJobExecution('agent', job_exe_model_7)
        job_exe_8 = RunningJobExecution('agent', job_exe_model_8)
        job_exe_9 = RunningJobExecution('agent', job_exe_model_9)
        job_exe_10 = RunningJobExecution('agent', job_exe_model_10)
        job_exe_11 = RunningJobExecution('agent', job_exe_model_11)

        # NOTE: This unit test is about to get CRAZY. I apologize for the complexity, but this is needed for a
        # thorough testing
        self.metrics.add_running_job_exes([job_exe_1, job_exe_2, job_exe_3, job_exe_4, job_exe_5, job_exe_6, job_exe_7,
                                           job_exe_8, job_exe_9, job_exe_10, job_exe_11])
        node_list_dict = [{'id': node_model_1.id}, {'id': node_model_2.id}]
        self.metrics.generate_status_json(node_list_dict, now())

        # Check expected totals
        self.assertEqual(node_list_dict[0]['job_executions']['running']['total'], 4)
        for job_type_dict in node_list_dict[0]['job_executions']['running']['by_job_type']:
            if job_type_dict['job_type_id'] == job_type_1.id:
                self.assertEqual(job_type_dict['count'], 3)
            elif job_type_dict['job_type_id'] == job_type_2.id:
                self.assertEqual(job_type_dict['count'], 1)
            else:
                self.fail('Unexpected job type ID')
        self.assertEqual(node_list_dict[0]['job_executions']['completed']['total'], 0)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['total'], 0)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['algorithm']['total'], 0)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['data']['total'], 0)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['system']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['running']['total'], 7)
        for job_type_dict in node_list_dict[1]['job_executions']['running']['by_job_type']:
            if job_type_dict['job_type_id'] == job_type_1.id:
                self.assertEqual(job_type_dict['count'], 2)
            elif job_type_dict['job_type_id'] == job_type_2.id:
                self.assertEqual(job_type_dict['count'], 5)
            else:
                self.fail('Unexpected job type ID')
        self.assertEqual(node_list_dict[1]['job_executions']['completed']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['failed']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['failed']['algorithm']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['failed']['data']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['failed']['system']['total'], 0)

        # Finish some job executions
        end_time_1 = now()
        job_exe_1._set_finished_status('COMPLETED', end_time_1)
        job_exe_2._set_finished_status('FAILED', end_time_1, error=self.data_error)
        job_exe_4._set_finished_status('FAILED', end_time_1, error=self.alg_error)
        self.metrics.job_exe_finished(job_exe_1)
        self.metrics.job_exe_finished(job_exe_2)
        self.metrics.job_exe_finished(job_exe_4)
        node_list_dict = [{'id': node_model_1.id}, {'id': node_model_2.id}]
        self.metrics.generate_status_json(node_list_dict, end_time_1 + datetime.timedelta(seconds=1))

        # Check expected totals
        self.assertEqual(node_list_dict[0]['job_executions']['running']['total'], 1)
        self.assertEqual(len(node_list_dict[0]['job_executions']['running']['by_job_type']), 1)
        self.assertEqual(node_list_dict[0]['job_executions']['running']['by_job_type'][0]['count'], 1)
        self.assertEqual(node_list_dict[0]['job_executions']['running']['by_job_type'][0]['job_type_id'], job_type_1.id)
        self.assertEqual(node_list_dict[0]['job_executions']['completed']['total'], 1)
        self.assertEqual(len(node_list_dict[0]['job_executions']['completed']['by_job_type']), 1)
        self.assertEqual(node_list_dict[0]['job_executions']['completed']['by_job_type'][0]['count'], 1)
        self.assertEqual(node_list_dict[0]['job_executions']['completed']['by_job_type'][0]['job_type_id'],
                         job_type_1.id)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['total'], 2)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['algorithm']['total'], 1)
        self.assertEqual(len(node_list_dict[0]['job_executions']['failed']['algorithm']['by_job_type']), 1)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['algorithm']['by_job_type'][0]['count'], 1)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['algorithm']['by_job_type'][0]['job_type_id'],
                         job_type_2.id)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['data']['total'], 1)
        self.assertEqual(len(node_list_dict[0]['job_executions']['failed']['data']['by_job_type']), 1)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['data']['by_job_type'][0]['count'], 1)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['data']['by_job_type'][0]['job_type_id'],
                         job_type_1.id)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['system']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['running']['total'], 7)
        for job_type_dict in node_list_dict[1]['job_executions']['running']['by_job_type']:
            if job_type_dict['job_type_id'] == job_type_1.id:
                self.assertEqual(job_type_dict['count'], 2)
            elif job_type_dict['job_type_id'] == job_type_2.id:
                self.assertEqual(job_type_dict['count'], 5)
            else:
                self.fail('Unexpected job type ID')
        self.assertEqual(node_list_dict[1]['job_executions']['completed']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['failed']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['failed']['algorithm']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['failed']['data']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['failed']['system']['total'], 0)

        # Finish some job executions (all executions still on node 2)
        end_time_2 = end_time_1 + FinishedJobExeMetricsOverTime.BLOCK_LENGTH
        job_exe_5._set_finished_status('COMPLETED', end_time_2)
        job_exe_6._set_finished_status('COMPLETED', end_time_2)
        job_exe_7._set_finished_status('COMPLETED', end_time_2)
        job_exe_8._set_finished_status('COMPLETED', end_time_2)
        job_exe_9._set_finished_status('COMPLETED', end_time_2)
        job_exe_10._set_finished_status('COMPLETED', end_time_2)
        job_exe_11._set_finished_status('COMPLETED', end_time_2)
        self.metrics.job_exe_finished(job_exe_5)
        self.metrics.job_exe_finished(job_exe_6)
        self.metrics.job_exe_finished(job_exe_7)
        self.metrics.job_exe_finished(job_exe_8)
        self.metrics.job_exe_finished(job_exe_9)
        self.metrics.job_exe_finished(job_exe_10)
        self.metrics.job_exe_finished(job_exe_11)
        node_list_dict = [{'id': node_model_1.id}, {'id': node_model_2.id}]
        self.metrics.generate_status_json(node_list_dict, end_time_2)

        # Check expected totals
        self.assertEqual(node_list_dict[0]['job_executions']['running']['total'], 1)
        self.assertEqual(len(node_list_dict[0]['job_executions']['running']['by_job_type']), 1)
        self.assertEqual(node_list_dict[0]['job_executions']['running']['by_job_type'][0]['count'], 1)
        self.assertEqual(node_list_dict[0]['job_executions']['running']['by_job_type'][0]['job_type_id'], job_type_1.id)
        self.assertEqual(node_list_dict[0]['job_executions']['completed']['total'], 1)
        self.assertEqual(len(node_list_dict[0]['job_executions']['completed']['by_job_type']), 1)
        self.assertEqual(node_list_dict[0]['job_executions']['completed']['by_job_type'][0]['count'], 1)
        self.assertEqual(node_list_dict[0]['job_executions']['completed']['by_job_type'][0]['job_type_id'],
                         job_type_1.id)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['total'], 2)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['algorithm']['total'], 1)
        self.assertEqual(len(node_list_dict[0]['job_executions']['failed']['algorithm']['by_job_type']), 1)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['algorithm']['by_job_type'][0]['count'], 1)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['algorithm']['by_job_type'][0]['job_type_id'],
                         job_type_2.id)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['data']['total'], 1)
        self.assertEqual(len(node_list_dict[0]['job_executions']['failed']['data']['by_job_type']), 1)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['data']['by_job_type'][0]['count'], 1)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['data']['by_job_type'][0]['job_type_id'],
                         job_type_1.id)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['system']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['running']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['completed']['total'], 7)
        for job_type_dict in node_list_dict[1]['job_executions']['completed']['by_job_type']:
            if job_type_dict['job_type_id'] == job_type_1.id:
                self.assertEqual(job_type_dict['count'], 2)
            elif job_type_dict['job_type_id'] == job_type_2.id:
                self.assertEqual(job_type_dict['count'], 5)
            else:
                self.fail('Unexpected job type ID')
        self.assertEqual(node_list_dict[1]['job_executions']['failed']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['failed']['algorithm']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['failed']['data']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['failed']['system']['total'], 0)

        # Let all finished job executions roll off by time, only running remaining
        end_time_3 = end_time_2 + FinishedJobExeMetricsOverTime.TOTAL_TIME_PERIOD
        end_time_3 += FinishedJobExeMetricsOverTime.BLOCK_LENGTH + datetime.timedelta(seconds=1)
        node_list_dict = [{'id': node_model_1.id}, {'id': node_model_2.id}]
        self.metrics.generate_status_json(node_list_dict, end_time_3)

        # Check expected totals
        self.assertEqual(node_list_dict[0]['job_executions']['running']['total'], 1)
        self.assertEqual(len(node_list_dict[0]['job_executions']['running']['by_job_type']), 1)
        self.assertEqual(node_list_dict[0]['job_executions']['running']['by_job_type'][0]['count'], 1)
        self.assertEqual(node_list_dict[0]['job_executions']['running']['by_job_type'][0]['job_type_id'], job_type_1.id)
        self.assertEqual(node_list_dict[0]['job_executions']['completed']['total'], 0)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['total'], 0)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['algorithm']['total'], 0)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['data']['total'], 0)
        self.assertEqual(node_list_dict[0]['job_executions']['failed']['system']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['running']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['completed']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['failed']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['failed']['algorithm']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['failed']['data']['total'], 0)
        self.assertEqual(node_list_dict[1]['job_executions']['failed']['system']['total'], 0)
