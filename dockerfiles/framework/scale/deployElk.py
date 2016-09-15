#!/usr/bin/env python

__doc__ = """
This script executes Marathon tasks for the logging stack is meant for use with DC/OS deployments only.
"""
import requests, os, json, time


def run():
    # get the Logstash container API endpoints
    logstash_image = os.getenv('LOGSTASH_DOCKER_IMAGE', 'appliedis/dcos-logstash:2.4')
    marathon = {
      'id': 'scale-logstash',
      'cpus': 0.5,
      'mem': 1024,
      'disk': 256,
      'instances': 1,
      'container': {
        'docker': {
          'image': logstash_image,
          'network': 'HOST',
          'forcePullImage': True
        },
        'type': 'DOCKER',
        'volumes': []
      },
      'portDefinitions': [
        {
          'port': 12201,
          'protocol': 'udp'
        }
      ],
      'env': {},
      'labels': {},
      'healthChecks': [],
      'uris': []
    }

    # Capture any passed-in environment variables that are relevant to Logstash container.
    CONFIG_URI = os.getenv('CONFIG_URI')
    ELASTICSEARCH_URL = os.getenv('SCALE_ELASTICSEARCH_URL')
    SLEEP_TIME = os.getenv('LOGSTASH_WATCHDOG_SLEEP_TIME')
    TEMPLATE_URI = os.getenv('LOGSTASH_TEMPLATE_URI')

    if ELASTICSEARCH_URL:
        marathon['env']['ELASTICSEARCH_URL'] = ELASTICSEARCH_URL

    if SLEEP_TIME:
        marathon['env']['SLEEP_TIME'] = SLEEP_TIME

    if TEMPLATE_URI:
        marathon['env']['TEMPLATE_URI'] = TEMPLATE_URI

    if CONFIG_URI:
        marathon['uris'].append(CONFIG_URI)

    r = requests.post('http://marathon.mesos:8080/v2/apps/', json=marathon)
    if r.status_code >= 400:
        print(r.text)
    while int(json.loads(requests.get('http://marathon.mesos:8080/v2/apps/scale-logstash').text)['app']['tasksRunning']) == 0:
        time.sleep(5)
    logstashPort = json.loads(requests.get('http://marathon.mesos:8080/v2/apps/scale-logstash').text)['app']['tasks'][0]['ports'][0]
    print('udp://scale-logstash.marathon.mesos:%s'%(logstashPort,))


if __name__ == '__main__':
    # ensure this doesn't try and run if imported
    run()
