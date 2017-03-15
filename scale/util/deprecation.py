# Classes needed to shim migrations based on abandoned external packages

class JSONStringField(JSONField):
    
    def db_type(self, connection):
        return 'json'