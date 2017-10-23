class ProductFileMetadata(object):
    def __init__(self, output_name, local_path, media_type=None, remote_path=None, data_start=None, data_end=None,
                 geojson=None):

        self.data_start = data_start
        self.data_end = data_end
        self.geojson = geojson
        self.local_path = local_path
        self.media_type = media_type
        self.output_name = output_name
        self.remote_path = remote_path