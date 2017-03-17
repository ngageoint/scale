# Classes needed to shim migrations based on abandoned external packages

from django.contrib.postgres.fields import JSONField


class JSONStringField(JSONField):
    
    def db_type(self, connection):
        return 'json'