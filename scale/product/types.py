class ProductFileMetadata(object):
    def __init__(self, output_name, local_path, media_type=None, remote_path=None, data_start=None, data_end=None,
                 geojson=None, source_started=None, source_ended=None, source_sensor_class=None, source_sensor=None,
                 source_collection=None, source_task=None, url=None, job_name=None, job_version=None,
                 package_version=None):

        self.data_start = data_start
        self.data_end = data_end
        self.geojson = geojson
        self.local_path = local_path
        self.media_type = media_type
        self.output_name = output_name
        self.remote_path = remote_path

        # source metadata
        self.source_started = source_started
        self.source_ended = source_ended
        self.source_sensor_class = source_sensor_class
        self.source_sensor = source_sensor
        self.source_collection = source_collection
        self.source_task = source_task

        # Execution context
        self.url = url
        self.job_name = job_name
        self.job_version = job_version
        self.package_version = package_version