#!/usr/bin/env python

__doc__ = """
This script executes Marathon tasks for the logging stack is meant for use with DC/OS deployments only.
"""
import requests, os, json, time


def run():
    # get the elasticsearch API endpoints
    es_url = os.environ.get('SCALE_ELASTICSEARCH_URL', 'http://elasticsearch.marathon.mesos:31105')
    config_uri = os.environ.get('CONFIG_URI', '')
    if config_uri:
        config_uri = '"' + config_uri + '"'  # Config URI needs quotes to be inserted into JSON string
    endpoints = [x['http_address'] for x in json.loads(requests.get(es_url+'/v1/tasks').text)]

    # attempt to delete an old instance..if it doesn't exists it will error but we don't care so we ignore it
    requests.delete('http://marathon.mesos:8080/v2/apps/scale-logstash')

    marathon = '''
    {
      "id": "scale-logstash",
      "cmd": "logstash --allow-env --verbose -e 'input { gelf { port => \\"${PORT0}\\" } } output { elasticsearch { hosts => [\\"${ES_HOST}\\"] } }'",
      "cpus": 0.5,
      "mem": 1024,
      "disk": 256,
      "instances": 1,
      "container": {
        "docker": {
          "image": "%s",
          "network": "HOST"
        },
        "type": "DOCKER",
        "volumes": []
      },
      "portDefinitions": [
        {
          "port": 12201,
          "protocol": "udp"
        }
      ],
      "env": {
          "ES_HOST": "%s"
      },
      "labels": {},
      "healthChecks": [],
      "uris": [%s]
    }
    ''' % (os.environ.get('LOGSTASH_DOCKER_IMAGE', 'logstash'), endpoints[0], config_uri)

    r = requests.post('http://marathon.mesos:8080/v2/apps/', data=marathon)
    while int(json.loads(requests.get('http://marathon.mesos:8080/v2/apps/scale-logstash').text)['app']['tasksRunning']) == 0:
        time.sleep(5)
    logstashPort = json.loads(requests.get('http://marathon.mesos:8080/v2/apps/scale-logstash').text)['app']['tasks'][0]['ports'][0]
    print('udp://scale-logstash.marathon.mesos:%s'%(logstashPort,))
    print('http://%s' % endpoints[0])


if __name__ == '__main__':
    # ensure this doesn't try and run if imported
    run()
