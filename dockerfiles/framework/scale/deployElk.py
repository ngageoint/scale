#!/usr/bin/env python

__doc__ = """
This script executes Marathon tasks for the logging stack is meant for use with DC/OS deployments only.
"""
import requests, os, json, time

def run():
    # get the elasticsearch API endpoints
    es_url = os.environ.get('ELASTICSEARCH_URL', "http://elasticsearch.marathon.mesos:31105")
    endpoints = [x["http_address"] for x in json.loads(requests.get(es_url+"/v1/tasks").text)]

    marathon = '''
    {
      "id": "scale-logstash",
      "cmd": "logstash --allow-env --verbose -e 'input { gelf { port => \\"${PORT0}\\" } } output { stdout { } elasticsearch { hosts => [\\"${ES_HOST}\\"] } }'",
      "cpus": 0.5,
      "mem": 128,
      "disk": 256,
      "instances": 1,
      "container": {
        "docker": {
          "image": "logstash",
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
      "healthChecks": []
    }
    ''' % ('\\", \\"'.join(endpoints),)

    r = requests.post('http://marathon.mesos:8080/v2/apps/', data=marathon)
    while int(json.loads(requests.get('http://marathon.mesos:8080/v2/apps/scale-logstash').text)['app']['tasksRunning']) == 0:
        time.sleep(5)
    logstashPort = json.loads(requests.get('http://marathon.mesos:8080/v2/apps/scale-logstash').text)['app']['tasks'][0]['ports'][0]
    print("udp://scale-logstash.marathon.mesos:%s"%(logstashPort,))


if __name__ == '__main__':
    # ensure this doesn't try and run if imported
    run()
