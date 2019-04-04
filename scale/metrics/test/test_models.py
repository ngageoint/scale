from __future__ import absolute_import

import datetime

import django
from django.test import TestCase
from django.utils.timezone import utc

import error.test.utils as error_test_utils
import ingest.test.utils as ingest_test_utils
import job.test.utils as job_test_utils
import source.test.utils as source_test_utils
import metrics.test.utils as metrics_test_utils
from job.execution.tasks.json.results.task_results import TaskResults
from metrics.models import MetricsError, MetricsIngest, MetricsJobType
from metrics.registry import MetricsTypeColumn
from util.parse import datetime_to_string


class TestMetricsError(TestCase):
    """Tests the MetricsError model logic."""

    def setUp(self):
        django.setup()

    def test_calculate_none(self):
        """Tests generating metrics when there are no matching errors."""
        MetricsError.objects.calculate(datetime.date(2015, 1, 1))
        entries = MetricsError.objects.filter(occurred=datetime.date(2015, 1, 1))

        self.assertEqual(len(entries), 0)

    def test_calculate_filtered(self):
        """Tests generating metrics with only certain errors."""
        job_test_utils.create_job(status='FAILED')
        job_test_utils.create_job(status='COMPLETED')

        error1 = error_test_utils.create_error(is_builtin=True)
        job1 = job_test_utils.create_job(error=error1, status='FAILED', ended=datetime.datetime(2015, 1, 1, tzinfo=utc))
        job_test_utils.create_job_exe(job=job1, error=error1, status=job1.status, ended=job1.ended)

        error2 = error_test_utils.create_error()
        job2 = job_test_utils.create_job(error=error2, status='FAILED', ended=datetime.datetime(2015, 1, 1, tzinfo=utc))
        job_test_utils.create_job_exe(error=error2, status=job2.status, ended=job2.ended)

        job3 = job_test_utils.create_job(status='COMPLETED', ended=datetime.datetime(2015, 1, 1, tzinfo=utc))
        job_test_utils.create_job_exe(job=job3, status=job3.status, ended=job3.ended)

        MetricsError.objects.calculate(datetime.date(2015, 1, 1))
        entries = MetricsError.objects.filter(occurred=datetime.date(2015, 1, 1))

        self.assertEqual(len(entries), 1)

    def test_calculate_repeated(self):
        """Tests regenerating metrics for a date that already has metrics."""
        error = error_test_utils.create_error(is_builtin=True)
        job = job_test_utils.create_job(status='FAILED', error=error, ended=datetime.datetime(2015, 1, 1, tzinfo=utc))
        job_test_utils.create_job_exe(job=job, error=error, status=job.status, ended=job.ended)

        MetricsError.objects.calculate(datetime.date(2015, 1, 1))
        MetricsError.objects.calculate(datetime.date(2015, 1, 1))
        entries = MetricsError.objects.filter(occurred=datetime.date(2015, 1, 1))

        self.assertEqual(len(entries), 1)

    def test_calculate_stats(self):
        """Tests calculating individual statistics for a metrics entry."""
        error = error_test_utils.create_error(is_builtin=True)
        job1 = job_test_utils.create_job(error=error, status='FAILED', ended=datetime.datetime(2015, 1, 1, tzinfo=utc))
        job_test_utils.create_job_exe(
            job=job1, error=error, status=job1.status,
            queued=datetime.datetime(2015, 1, 1, tzinfo=utc),
            started=datetime.datetime(2015, 1, 1, 0, 10, 2, tzinfo=utc),
            ended=datetime.datetime(2015, 1, 1, 6, 0, 16, tzinfo=utc),
        )
        job2 = job_test_utils.create_job(error=error, status='FAILED', ended=datetime.datetime(2015, 1, 1, tzinfo=utc))
        job_test_utils.create_job_exe(
            job=job2, error=error, status=job2.status,
            queued=datetime.datetime(2015, 1, 1, tzinfo=utc),
            started=datetime.datetime(2015, 1, 1, 2, 10, 2, tzinfo=utc),
            ended=datetime.datetime(2015, 1, 1, 16, 0, 58, tzinfo=utc),
        )

        sys_error = error_test_utils.create_error(category='SYSTEM', is_builtin=True)
        job3a = job_test_utils.create_job(error=sys_error, status='FAILED', ended=datetime.datetime(2015, 1, 1,
                                                                                                    tzinfo=utc))
        job_test_utils.create_job_exe(job=job3a, status=job3a.status, ended=job3a.ended, error=sys_error)

        data_error = error_test_utils.create_error(category='DATA', is_builtin=True)
        job3b = job_test_utils.create_job(error=data_error, status='FAILED', ended=datetime.datetime(2015, 1, 1,
                                                                                                     tzinfo=utc))
        job_test_utils.create_job_exe(job=job3b, status=job3b.status, ended=job3b.ended, error=data_error)

        algo_error = error_test_utils.create_error(category='ALGORITHM', is_builtin=True)
        job3c = job_test_utils.create_job(error=algo_error, status='FAILED', ended=datetime.datetime(2015, 1, 1,
                                                                                                     tzinfo=utc))
        job_test_utils.create_job_exe(job=job3c, status=job3c.status, ended=job3c.ended, error=algo_error)

        MetricsError.objects.calculate(datetime.date(2015, 1, 1))

        entries = MetricsError.objects.filter(occurred=datetime.date(2015, 1, 1))
        self.assertEqual(len(entries), 4)

        for entry in entries:
            self.assertEqual(entry.occurred, datetime.date(2015, 1, 1))
            if entry.error == error:
                self.assertEqual(entry.total_count, 2)
            else:
                self.assertEqual(entry.total_count, 1)

    def test_get_metrics_type(self):
        """Tests getting the metrics type."""
        metrics_type = MetricsError.objects.get_metrics_type()

        self.assertEqual(metrics_type.name, 'errors')
        self.assertEqual(len(metrics_type.filters), 2)
        self.assertListEqual(metrics_type.choices, [])

    def test_get_metrics_type_choices(self):
        """Tests getting the metrics type with choices."""
        error_test_utils.create_error(is_builtin=True)
        metrics_type = MetricsError.objects.get_metrics_type(include_choices=True)

        self.assertEqual(metrics_type.name, 'errors')
        self.assertEqual(len(metrics_type.filters), 2)
        self.assertEqual(len(metrics_type.choices), 1)

    def test_get_plot_data(self):
        """Tests getting the metrics plot data."""
        metrics_test_utils.create_error(total_count=1)
        plot_data = MetricsError.objects.get_plot_data()

        self.assertEqual(len(plot_data), 1)

    def test_get_plot_data_filtered(self):
        """Tests getting the metrics plot data with filters."""
        error = error_test_utils.create_error(is_builtin=True)
        metrics_test_utils.create_error(error=error, occurred=datetime.date(2015, 1, 1), total_count=1)
        metrics_test_utils.create_error(error=error, occurred=datetime.date(2015, 1, 20), total_count=1)
        metrics_test_utils.create_error(occurred=datetime.date(2015, 1, 1), total_count=1)

        plot_data = MetricsError.objects.get_plot_data(started=datetime.date(2015, 1, 1),
                                                       ended=datetime.date(2015, 1, 10),
                                                       choice_ids=[error.id],
                                                       columns=[MetricsTypeColumn('total_count')])

        self.assertEqual(len(plot_data), 1)
        self.assertEqual(len(plot_data[0].values), 1)


class TestMetricsIngest(TestCase):
    """Tests the MetricsIngest model logic."""

    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

    def test_calculate_none(self):
        """Tests generating metrics when there are no matching executions."""
        MetricsIngest.objects.calculate(datetime.date(2015, 1, 1))
        entries = MetricsIngest.objects.filter(occurred=datetime.date(2015, 1, 1))

        self.assertEqual(len(entries), 0)

    def test_calculate_filtered(self):
        """Tests generating metrics with only certain ingests."""
        ingest_test_utils.create_ingest(status='TRANSFERRING')
        ingest_test_utils.create_ingest(status='TRANSFERRED')
        ingest_test_utils.create_ingest(status='DEFERRED')
        ingest_test_utils.create_ingest(status='QUEUED')
        ingest_test_utils.create_ingest(status='INGESTING')
        ingest_test_utils.create_ingest(status='INGESTED')
        ingest_test_utils.create_ingest(status='ERRORED')
        ingest_test_utils.create_ingest(status='DUPLICATE')

        ingest_test_utils.create_ingest(strike=ingest_test_utils.create_strike(), status='DEFERRED',
                                        ingest_ended=datetime.datetime(2015, 1, 1, tzinfo=utc))
        ingest_test_utils.create_ingest(strike=ingest_test_utils.create_strike(), status='INGESTED',
                                        ingest_ended=datetime.datetime(2015, 1, 1, tzinfo=utc))
        ingest_test_utils.create_ingest(strike=ingest_test_utils.create_strike(), status='ERRORED',
                                        ingest_ended=datetime.datetime(2015, 1, 1, tzinfo=utc))
        ingest_test_utils.create_ingest(strike=ingest_test_utils.create_strike(), status='DUPLICATE',
                                        ingest_ended=datetime.datetime(2015, 1, 1, tzinfo=utc))

        MetricsIngest.objects.calculate(datetime.date(2015, 1, 1))
        entries = MetricsIngest.objects.filter(occurred=datetime.date(2015, 1, 1))

        self.assertEqual(len(entries), 4)

    def test_calculate_strike_is_none(self):
        """Tests generating metrics for a date that has ingests with None in Strike field (Scan parent ingest)."""
        scan = ingest_test_utils.create_scan()
        ingest_test_utils.create_ingest(scan=scan, status='INGESTED',
                                        ingest_ended=datetime.datetime(2015, 1, 1, tzinfo=utc))

        MetricsIngest.objects.calculate(datetime.date(2015, 1, 1))
        entries = MetricsIngest.objects.filter(occurred=datetime.date(2015, 1, 1))

        self.assertEqual(len(entries), 0)

    def test_calculate_repeated(self):
        """Tests regenerating metrics for a date that already has metrics."""
        strike = ingest_test_utils.create_strike()
        ingest_test_utils.create_ingest(strike=strike, status='INGESTED', ingest_ended=datetime.datetime(2015, 1, 1,
                                                                                                         tzinfo=utc))

        MetricsIngest.objects.calculate(datetime.date(2015, 1, 1))
        MetricsIngest.objects.calculate(datetime.date(2015, 1, 1))
        entries = MetricsIngest.objects.filter(occurred=datetime.date(2015, 1, 1))

        self.assertEqual(len(entries), 1)

    def test_calculate_stats(self):
        """Tests calculating individual statistics for a metrics entry."""
        strike = ingest_test_utils.create_strike()
        source_file = source_test_utils.create_source(file_size=200)
        ingest_test_utils.create_ingest(strike=strike, source_file=source_file, status='INGESTED',
                                        transfer_started=datetime.datetime(2015, 1, 1, tzinfo=utc),
                                        transfer_ended=datetime.datetime(2015, 1, 1, 0, 10, tzinfo=utc),
                                        ingest_started=datetime.datetime(2015, 1, 1, tzinfo=utc),
                                        ingest_ended=datetime.datetime(2015, 1, 1, 1, tzinfo=utc))
        ingest_test_utils.create_ingest(strike=strike, status='INGESTED',
                                        transfer_started=datetime.datetime(2015, 1, 1, tzinfo=utc),
                                        transfer_ended=datetime.datetime(2015, 1, 1, 0, 20, tzinfo=utc),
                                        ingest_started=datetime.datetime(2015, 1, 1, tzinfo=utc),
                                        ingest_ended=datetime.datetime(2015, 1, 1, 2, tzinfo=utc))
        ingest_test_utils.create_ingest(strike=strike, status='ERRORED',
                                        transfer_started=datetime.datetime(2015, 1, 1, tzinfo=utc),
                                        transfer_ended=datetime.datetime(2015, 1, 1, 0, 30, tzinfo=utc),
                                        ingest_started=datetime.datetime(2015, 1, 1, tzinfo=utc),
                                        ingest_ended=datetime.datetime(2015, 1, 1, 3, tzinfo=utc))
        ingest_test_utils.create_ingest(strike=strike, status='DEFERRED',
                                        transfer_started=datetime.datetime(2015, 1, 1, tzinfo=utc),
                                        transfer_ended=datetime.datetime(2015, 1, 1, 0, 40, tzinfo=utc),
                                        ingest_started=datetime.datetime(2015, 1, 1, tzinfo=utc),
                                        ingest_ended=datetime.datetime(2015, 1, 1, 4, tzinfo=utc))
        ingest_test_utils.create_ingest(strike=strike, status='DUPLICATE',
                                        transfer_started=datetime.datetime(2015, 1, 1, tzinfo=utc),
                                        transfer_ended=datetime.datetime(2015, 1, 1, 0, 50, tzinfo=utc),
                                        ingest_started=datetime.datetime(2015, 1, 1, tzinfo=utc),
                                        ingest_ended=datetime.datetime(2015, 1, 1, 5, tzinfo=utc))

        MetricsIngest.objects.calculate(datetime.date(2015, 1, 1))

        entries = MetricsIngest.objects.filter(occurred=datetime.date(2015, 1, 1))
        self.assertEqual(len(entries), 1)

        entry = entries.first()
        self.assertEqual(entry.occurred, datetime.date(2015, 1, 1))
        self.assertEqual(entry.deferred_count, 1)
        self.assertEqual(entry.ingested_count, 2)
        self.assertEqual(entry.errored_count, 1)
        self.assertEqual(entry.duplicate_count, 1)
        self.assertEqual(entry.total_count, 5)

        self.assertEqual(entry.file_size_sum, 600)
        self.assertEqual(entry.file_size_min, 100)
        self.assertEqual(entry.file_size_max, 200)
        self.assertEqual(entry.file_size_avg, 120)

        self.assertEqual(entry.transfer_time_sum, 9000)
        self.assertEqual(entry.transfer_time_min, 600)
        self.assertEqual(entry.transfer_time_max, 3000)
        self.assertEqual(entry.transfer_time_avg, 1800)

        self.assertEqual(entry.ingest_time_sum, 10800)
        self.assertEqual(entry.ingest_time_min, 3600)
        self.assertEqual(entry.ingest_time_max, 7200)
        self.assertEqual(entry.ingest_time_avg, 5400)

    def test_calculate_stats_partial(self):
        """Tests individual statistics are null when information is unavailable."""
        strike = ingest_test_utils.create_strike()
        ingest1 = ingest_test_utils.create_ingest(strike=strike, status='ERRORED',
                                                  ingest_ended=datetime.datetime(2015, 1, 1, tzinfo=utc))
        ingest1.file_size = None
        ingest1.save()

        ingest2 = ingest_test_utils.create_ingest(strike=strike, status='DUPLICATE',
                                                  ingest_ended=datetime.datetime(2015, 1, 1, tzinfo=utc))
        ingest2.file_size = None
        ingest2.save()

        MetricsIngest.objects.calculate(datetime.date(2015, 1, 1))

        entries = MetricsIngest.objects.filter(occurred=datetime.date(2015, 1, 1))
        self.assertEqual(len(entries), 1)

        entry = entries.first()
        self.assertEqual(entry.occurred, datetime.date(2015, 1, 1))
        self.assertEqual(entry.deferred_count, 0)
        self.assertEqual(entry.ingested_count, 0)
        self.assertEqual(entry.errored_count, 1)
        self.assertEqual(entry.duplicate_count, 1)
        self.assertEqual(entry.total_count, 2)

        self.assertIsNone(entry.file_size_sum)
        self.assertIsNone(entry.file_size_min)
        self.assertIsNone(entry.file_size_max)
        self.assertIsNone(entry.file_size_avg)

        self.assertIsNone(entry.transfer_time_sum)
        self.assertIsNone(entry.transfer_time_min)
        self.assertIsNone(entry.transfer_time_max)
        self.assertIsNone(entry.transfer_time_avg)

        self.assertIsNone(entry.ingest_time_sum)
        self.assertIsNone(entry.ingest_time_min)
        self.assertIsNone(entry.ingest_time_max)
        self.assertIsNone(entry.ingest_time_avg)

    def test_get_metrics_type(self):
        """Tests getting the metrics type."""
        metrics_type = MetricsIngest.objects.get_metrics_type()

        self.assertEqual(metrics_type.name, 'ingests')
        self.assertEqual(len(metrics_type.filters), 1)
        self.assertListEqual(metrics_type.choices, [])

    def test_get_metrics_type_choices(self):
        """Tests getting the metrics type with choices."""
        ingest_test_utils.create_strike()
        metrics_type = MetricsIngest.objects.get_metrics_type(include_choices=True)

        self.assertEqual(metrics_type.name, 'ingests')
        self.assertEqual(len(metrics_type.filters), 1)
        self.assertEqual(len(metrics_type.choices), 1)

    def test_get_plot_data(self):
        """Tests getting the metrics plot data."""
        metrics_test_utils.create_ingest(ingested_count=1)
        plot_data = MetricsIngest.objects.get_plot_data()

        self.assertGreater(len(plot_data), 1)

    def test_get_plot_data_filtered(self):
        """Tests getting the metrics plot data with filters."""
        strike = ingest_test_utils.create_strike()
        metrics_test_utils.create_ingest(strike=strike, occurred=datetime.datetime(2015, 1, 1, tzinfo=utc),
                                         ingested_count=1)
        metrics_test_utils.create_ingest(strike=strike, occurred=datetime.datetime(2015, 1, 20, tzinfo=utc),
                                         ingested_count=1)
        metrics_test_utils.create_ingest(occurred=datetime.datetime(2015, 1, 1, tzinfo=utc), ingested_count=1)

        plot_data = MetricsIngest.objects.get_plot_data(started=datetime.date(2015, 1, 1),
                                                        ended=datetime.date(2015, 1, 10),
                                                        choice_ids=[strike.id],
                                                        columns=[MetricsTypeColumn('ingested_count')])

        self.assertEqual(len(plot_data), 1)
        self.assertEqual(len(plot_data[0].values), 1)


class TestMetricsJobType(TestCase):
    """Tests the MetricsJobType model logic."""

    def setUp(self):
        django.setup()

    def test_calculate_none(self):
        """Tests generating metrics when there are no matching executions."""
        MetricsJobType.objects.calculate(datetime.date(2015, 1, 1))
        entries = MetricsJobType.objects.filter(occurred=datetime.date(2015, 1, 1))

        self.assertEqual(len(entries), 0)

    def test_calculate_filtered(self):
        """Tests generating metrics with only certain job executions."""
        job_test_utils.create_job(status='QUEUED')
        job_test_utils.create_job(status='RUNNING')
        job_test_utils.create_job(status='FAILED')
        job_test_utils.create_job(status='COMPLETED')
        job_test_utils.create_job(status='CANCELED')

        job1 = job_test_utils.create_job(status='QUEUED', ended=datetime.datetime(2015, 1, 1, tzinfo=utc))
        job_test_utils.create_job_exe(job=job1, status=job1.status, ended=job1.ended)
        job2 = job_test_utils.create_job(status='RUNNING', ended=datetime.datetime(2015, 1, 1, tzinfo=utc))
        job_test_utils.create_job_exe(job=job2, status=job2.status, ended=job2.ended)

        job3 = job_test_utils.create_job(status='FAILED', ended=datetime.datetime(2015, 1, 1, tzinfo=utc))
        job_test_utils.create_job_exe(job=job3, status=job3.status, ended=job3.ended)
        job4 = job_test_utils.create_job(status='COMPLETED', ended=datetime.datetime(2015, 1, 1, tzinfo=utc))
        job_test_utils.create_job_exe(job=job4, status=job4.status, ended=job4.ended)
        job5 = job_test_utils.create_job(status='CANCELED', ended=datetime.datetime(2015, 1, 1, tzinfo=utc))
        job_test_utils.create_job_exe(job=job5, status=job5.status, ended=job5.ended)

        MetricsJobType.objects.calculate(datetime.date(2015, 1, 1))
        entries = MetricsJobType.objects.filter(occurred=datetime.date(2015, 1, 1))

        self.assertEqual(len(entries), 3)

    def test_calculate_repeated(self):
        """Tests regenerating metrics for a date that already has metrics."""
        job = job_test_utils.create_job(status='COMPLETED', ended=datetime.datetime(2015, 1, 1, tzinfo=utc))
        job_test_utils.create_job_exe(job=job, status=job.status, ended=job.ended)

        MetricsJobType.objects.calculate(datetime.date(2015, 1, 1))
        MetricsJobType.objects.calculate(datetime.date(2015, 1, 1))
        entries = MetricsJobType.objects.filter(occurred=datetime.date(2015, 1, 1))

        self.assertEqual(len(entries), 1)

    def test_calculate_stats(self):
        """Tests calculating individual statistics for a metrics entry."""
        job_type = job_test_utils.create_seed_job_type()
        job1 = job_test_utils.create_job(job_type=job_type, status='COMPLETED', ended=datetime.datetime(2015, 1, 1, tzinfo=utc))
        task_results_dict = {'version': '1.0',
                             'tasks': [{'task_id': '1', 'type': 'pre', 'was_launched': True,
                                        'started': datetime_to_string(datetime.datetime(2015, 1, 1, 0, 30, 4, tzinfo=utc)),
                                        'ended': datetime_to_string(datetime.datetime(2015, 1, 1, 1, 6, tzinfo=utc))},
                                       {'task_id': '2', 'type': 'main', 'was_launched': True,
                                        'started': datetime_to_string(datetime.datetime(2015, 1, 1, 1, 40, 8, tzinfo=utc)),
                                        'ended': datetime_to_string(datetime.datetime(2015, 1, 1, 2, 30, 10, tzinfo=utc))},
                                       {'task_id': '3', 'type': 'post', 'was_launched': True,
                                        'started': datetime_to_string(datetime.datetime(2015, 1, 1, 3, 30, 12, tzinfo=utc)),
                                        'ended': datetime_to_string(datetime.datetime(2015, 1, 1, 4, 40, 14, tzinfo=utc))}]}
        job_test_utils.create_job_exe(
            job=job1, status=job1.status,
            queued=datetime.datetime(2015, 1, 1, tzinfo=utc),
            started=datetime.datetime(2015, 1, 1, 0, 10, 2, tzinfo=utc),
            # pre_started=datetime.datetime(2015, 1, 1, 0, 30, 4, tzinfo=utc),
            # pre_completed=datetime.datetime(2015, 1, 1, 1, 6, tzinfo=utc),
            # job_started=datetime.datetime(2015, 1, 1, 1, 40, 8, tzinfo=utc),
            # job_completed=datetime.datetime(2015, 1, 1, 2, 30, 10, tzinfo=utc),
            # post_started=datetime.datetime(2015, 1, 1, 3, 30, 12, tzinfo=utc),
            # post_completed=datetime.datetime(2015, 1, 1, 4, 40, 14, tzinfo=utc),
            ended=datetime.datetime(2015, 1, 1, 6, 0, 16, tzinfo=utc),
            task_results=TaskResults(task_results_dict)
        )
        job2 = job_test_utils.create_job(job_type=job_type, status='COMPLETED', ended=datetime.datetime(2015, 1, 1, tzinfo=utc))
        task_results_dict = {'version': '1.0',
                             'tasks': [{'task_id': '1', 'type': 'pre', 'was_launched': True,
                                        'started': datetime_to_string(datetime.datetime(2015, 1, 1, 4, 30, 4, tzinfo=utc)),
                                        'ended': datetime_to_string(datetime.datetime(2015, 1, 1, 6, 0, 8, tzinfo=utc))},
                                       {'task_id': '2', 'type': 'main', 'was_launched': True,
                                        'started': datetime_to_string(datetime.datetime(2015, 1, 1, 8, 40, 14, tzinfo=utc)),
                                        'ended': datetime_to_string(datetime.datetime(2015, 1, 1, 10, 30, 22, tzinfo=utc))},
                                       {'task_id': '3', 'type': 'post', 'was_launched': True,
                                        'started': datetime_to_string(datetime.datetime(2015, 1, 1, 12, 30, 32, tzinfo=utc)),
                                        'ended': datetime_to_string(datetime.datetime(2015, 1, 1, 14, 40, 44, tzinfo=utc))}]}
        job_test_utils.create_job_exe(
            job=job2, status=job2.status,
            queued=datetime.datetime(2015, 1, 1, tzinfo=utc),
            started=datetime.datetime(2015, 1, 1, 2, 10, 2, tzinfo=utc),
            # pre_started=datetime.datetime(2015, 1, 1, 4, 30, 4, tzinfo=utc),
            # pre_completed=datetime.datetime(2015, 1, 1, 6, 0, 8, tzinfo=utc),
            # job_started=datetime.datetime(2015, 1, 1, 8, 40, 14, tzinfo=utc),
            # job_completed=datetime.datetime(2015, 1, 1, 10, 30, 22, tzinfo=utc),
            # post_started=datetime.datetime(2015, 1, 1, 12, 30, 32, tzinfo=utc),
            # post_completed=datetime.datetime(2015, 1, 1, 14, 40, 44, tzinfo=utc),
            ended=datetime.datetime(2015, 1, 1, 16, 0, 58, tzinfo=utc),
            task_results=TaskResults(task_results_dict)
        )

        sys_error = error_test_utils.create_error(category='SYSTEM')
        job3a = job_test_utils.create_job(job_type=job_type, status='FAILED', ended=datetime.datetime(2015, 1, 1, tzinfo=utc),
                                          error=sys_error)
        job_test_utils.create_job_exe(job=job3a, status=job3a.status, ended=job3a.ended, error=sys_error)

        data_error = error_test_utils.create_error(category='DATA')
        job3b = job_test_utils.create_job(job_type=job_type, status='FAILED', ended=datetime.datetime(2015, 1, 1, tzinfo=utc),
                                          error=data_error)
        job_test_utils.create_job_exe(job=job3b, status=job3b.status, ended=job3b.ended, error=data_error)

        algo_error = error_test_utils.create_error(category='ALGORITHM')
        job3c = job_test_utils.create_job(job_type=job_type, status='FAILED', ended=datetime.datetime(2015, 1, 1, tzinfo=utc),
                                          error=algo_error)
        job_test_utils.create_job_exe(job=job3c, status=job3c.status, ended=job3c.ended, error=algo_error)

        job4 = job_test_utils.create_job(job_type=job_type, status='CANCELED', ended=datetime.datetime(2015, 1, 1, tzinfo=utc))
        job_test_utils.create_job_exe(job=job4, status=job4.status, ended=job4.ended)

        MetricsJobType.objects.calculate(datetime.date(2015, 1, 1))

        entries = MetricsJobType.objects.filter(occurred=datetime.date(2015, 1, 1))
        self.assertEqual(len(entries), 1)

        entry = entries.first()
        self.assertEqual(entry.occurred, datetime.date(2015, 1, 1))
        self.assertEqual(entry.completed_count, 2)
        self.assertEqual(entry.failed_count, 3)
        self.assertEqual(entry.canceled_count, 1)
        self.assertEqual(entry.total_count, 6)

        self.assertEqual(entry.error_system_count, 1)
        self.assertEqual(entry.error_data_count, 1)
        self.assertEqual(entry.error_algorithm_count, 1)

        self.assertEqual(entry.queue_time_sum, 8404)
        self.assertEqual(entry.queue_time_min, 602)
        self.assertEqual(entry.queue_time_max, 7802)
        self.assertEqual(entry.queue_time_avg, 4202)

        self.assertEqual(entry.pre_time_sum, 7560)
        self.assertEqual(entry.pre_time_min, 2156)
        self.assertEqual(entry.pre_time_max, 5404)
        self.assertEqual(entry.pre_time_avg, 3780)

        self.assertEqual(entry.job_time_sum, 9610)
        self.assertEqual(entry.job_time_min, 3002)
        self.assertEqual(entry.job_time_max, 6608)
        self.assertEqual(entry.job_time_avg, 4805)

        self.assertEqual(entry.post_time_sum, 12014)
        self.assertEqual(entry.post_time_min, 4202)
        self.assertEqual(entry.post_time_max, 7812)
        self.assertEqual(entry.post_time_avg, 6007)

        self.assertEqual(entry.run_time_sum, 70870)
        self.assertEqual(entry.run_time_min, 21014)
        self.assertEqual(entry.run_time_max, 49856)
        self.assertEqual(entry.run_time_avg, 35435)

        self.assertEqual(entry.stage_time_sum, 41686)
        self.assertEqual(entry.stage_time_min, 11654)
        self.assertEqual(entry.stage_time_max, 30032)
        self.assertEqual(entry.stage_time_avg, 20843)

    def test_calculate_stats_partial(self):
        """Tests individual statistics are null when information is unavailable."""
        job_type = job_test_utils.create_seed_job_type()
        job_test_utils.create_job(job_type=job_type, status='FAILED', ended=datetime.datetime(2015, 1, 1, tzinfo=utc))
        job_test_utils.create_job(job_type=job_type, status='CANCELED', ended=datetime.datetime(2015, 1, 1, tzinfo=utc))

        MetricsJobType.objects.calculate(datetime.date(2015, 1, 1))

        entries = MetricsJobType.objects.filter(occurred=datetime.date(2015, 1, 1))
        self.assertEqual(len(entries), 1)

        entry = entries.first()
        self.assertEqual(entry.occurred, datetime.date(2015, 1, 1))
        self.assertEqual(entry.completed_count, 0)
        self.assertEqual(entry.failed_count, 1)
        self.assertEqual(entry.canceled_count, 1)
        self.assertEqual(entry.total_count, 2)

        self.assertEqual(entry.error_system_count, 0)
        self.assertEqual(entry.error_data_count, 0)
        self.assertEqual(entry.error_algorithm_count, 0)

        self.assertIsNone(entry.queue_time_sum)
        self.assertIsNone(entry.queue_time_min)
        self.assertIsNone(entry.queue_time_max)
        self.assertIsNone(entry.queue_time_avg)

        self.assertIsNone(entry.pre_time_sum)
        self.assertIsNone(entry.pre_time_min)
        self.assertIsNone(entry.pre_time_max)
        self.assertIsNone(entry.pre_time_avg)

        self.assertIsNone(entry.job_time_sum)
        self.assertIsNone(entry.job_time_min)
        self.assertIsNone(entry.job_time_max)
        self.assertIsNone(entry.job_time_avg)

        self.assertIsNone(entry.post_time_sum)
        self.assertIsNone(entry.post_time_min)
        self.assertIsNone(entry.post_time_max)
        self.assertIsNone(entry.post_time_avg)

        self.assertIsNone(entry.run_time_sum)
        self.assertIsNone(entry.run_time_min)
        self.assertIsNone(entry.run_time_max)
        self.assertIsNone(entry.run_time_avg)

        self.assertIsNone(entry.stage_time_sum)
        self.assertIsNone(entry.stage_time_min)
        self.assertIsNone(entry.stage_time_max)
        self.assertIsNone(entry.stage_time_avg)

    def test_calculate_negative_times(self):
        """Tests calculating times when machine clocks are out of sync."""
        job_type = job_test_utils.create_seed_job_type()
        job = job_test_utils.create_job(job_type=job_type, status='COMPLETED', ended=datetime.datetime(2015, 1, 1, tzinfo=utc))
        job_test_utils.create_job_exe(
            job=job, status=job.status,
            queued=datetime.datetime(2015, 1, 1, 1, 10, tzinfo=utc),
            started=datetime.datetime(2015, 1, 1, 1, 5, tzinfo=utc),
            ended=datetime.datetime(2015, 1, 1, tzinfo=utc),
        )

        MetricsJobType.objects.calculate(datetime.date(2015, 1, 1))

        entries = MetricsJobType.objects.filter(occurred=datetime.date(2015, 1, 1))
        self.assertEqual(len(entries), 1)

        entry = entries.first()
        self.assertEqual(entry.queue_time_min, 0)
        self.assertEqual(entry.queue_time_max, 0)

    def test_get_metrics_type(self):
        """Tests getting the metrics type."""
        metrics_type = MetricsJobType.objects.get_metrics_type()

        self.assertEqual(metrics_type.name, 'job-types')
        self.assertEqual(len(metrics_type.filters), 2)
        self.assertListEqual(metrics_type.choices, [])

    def test_get_metrics_type_choices(self):
        """Tests getting the metrics type with choices."""
        job_test_utils.create_seed_job_type()
        metrics_type = MetricsJobType.objects.get_metrics_type(include_choices=True)

        self.assertEqual(metrics_type.name, 'job-types')
        self.assertEqual(len(metrics_type.filters), 2)
        self.assertEqual(len(metrics_type.choices), 1)

    def test_get_plot_data(self):
        """Tests getting the metrics plot data."""
        metrics_test_utils.create_job_type(completed_count=1)
        plot_data = MetricsJobType.objects.get_plot_data()

        self.assertGreater(len(plot_data), 1)

    def test_get_plot_data_filtered(self):
        """Tests getting the metrics plot data with filters."""
        job_type = job_test_utils.create_seed_job_type()
        metrics_test_utils.create_job_type(job_type=job_type, occurred=datetime.date(2015, 1, 1), completed_count=1)
        metrics_test_utils.create_job_type(job_type=job_type, occurred=datetime.date(2015, 1, 20), completed_count=1)
        metrics_test_utils.create_job_type(occurred=datetime.date(2015, 1, 1), completed_count=1)

        plot_data = MetricsJobType.objects.get_plot_data(started=datetime.date(2015, 1, 1),
                                                         ended=datetime.date(2015, 1, 10),
                                                         choice_ids=[job_type.id],
                                                         columns=[MetricsTypeColumn('completed_count')])

        self.assertEqual(len(plot_data), 1)
        self.assertEqual(len(plot_data[0].values), 1)
