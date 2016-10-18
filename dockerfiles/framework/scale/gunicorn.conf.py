import os

bind = '0.0.0.0:8000'
workers = os.getenv('SCALE_WEBSERVER_WORKERS', 4)
