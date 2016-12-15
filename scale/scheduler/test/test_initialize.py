#@PydevCodeAnalysisIgnore
import django

from django.test.testcases import TransactionTestCase

from job.models import Job, JobType
from scheduler.initialize import initialize_system

class TestInitializeSystem(TransactionTestCase):

    fixtures = [u'basic_system_job_types.json']

    def setUp(self):
        django.setup()

    def test_create_clock_job(self):
        """Tests creating the Scale clock job"""

        clock_job_type = JobType.objects.get_clock_job_type()
        count = Job.objects.filter(job_type_id=clock_job_type.id).count()
        self.assertEqual(count, 0)

        initialize_system()
        count = Job.objects.filter(job_type_id=clock_job_type.id).count()
        self.assertEqual(count, 1)

        # Make sure it only creates one job
        initialize_system()
        count = Job.objects.filter(job_type_id=clock_job_type.id).count()
        self.assertEqual(count, 1)
