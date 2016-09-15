import filecmp
import json
import os
import time
import traceback
import urllib

import requests
from requests.exceptions import RequestException

ES_TASKS = '%s/v1/tasks' % os.getenv('ELASTICSEARCH_URL', 'http://elasticsearch.marathon.mesos:31105')
SLEEP_TIME = float(os.getenv('SLEEP_TIME', 30))
TEMPLATE_URI = os.getenv('TEMPLATE_URI', None)

CONF_FILE = '/opt/watchdog/logstash.conf'

if TEMPLATE_URI:
    print('Attempting template update from %s...' % TEMPLATE_URI)
    urllib.urlretrieve(TEMPLATE_URI, '%s-template' % CONF_FILE)
    print('Template update complete.')

def update_endpoints(endpoints):
    print('ElasticSearch endpoints found: %s' % json.dumps(endpoints))
    with open('%s-template' % CONF_FILE) as in_conf:
        conf_string = in_conf.read()
        conf_string = conf_string.replace('_ES_HOSTS_', json.dumps(endpoints))
        with open('%s_tmp' % CONF_FILE, 'w') as out_conf:
            out_conf.write(conf_string)

    if not (os.path.isfile(CONF_FILE) and filecmp.cmp(CONF_FILE, '%s_tmp' % CONF_FILE)):
        print('Elastic Search endpoint change detected. Applying new config...')
        os.rename('%s_tmp' % CONF_FILE, CONF_FILE)
    else:
        print('No update needed. Present config is up-to-date.')

        

# Loop endlessly monitoring Elasticsearch cluster. Supervisor will SIGKILL us if container stops
while True:
    try:
        response = requests.get(ES_TASKS)
        endpoints = [x['http_address'] for x in json.loads(response.text)]
        update_endpoints(endpoints)
    except RequestException:
        print('Unable to get ElasticSearch tasks from %s' % ES_TASKS)
        traceback.print_exc()

    time.sleep(SLEEP_TIME)
