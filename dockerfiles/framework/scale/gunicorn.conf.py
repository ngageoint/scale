import os

bind = '0.0.0.0:8000'

# Using GUnicorn recommended worker computation based on resources allocated
workers = int(os.getenv('SCALE_WEBSERVER_CPU', 1)) * 2 + 1
