import django
from django.test import TestCase

from error.handlers import DatabaseLogHandler


class TestGetDatabaseModel(TestCase):

    def setUp(self):
        django.setup()
        self.obj_under_test = DatabaseLogHandler()

    def test_get_model(self):
        model = self.obj_under_test.get_model('error.models.LogEntry')
        if model is None:
            self.fail("Failed to get the model")
