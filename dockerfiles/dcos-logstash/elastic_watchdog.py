import filecmp
import json
import os
import time
import traceback
import urllib

import requests
from requests.exceptions import RequestException


ES_URLS = os.getenv('ELASTICSEARCH_URLS').split(',')
SLEEP_TIME = float(os.getenv('SLEEP_TIME', 30))
TEMPLATE_URI = os.getenv('TEMPLATE_URI', None)

CONF_FILE = '/opt/watchdog/logstash.conf'


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

# ensure this doesn't try and run if imported
if __name__ == '__main__':
    if TEMPLATE_URI:
        print('Attempting template update from %s...' % TEMPLATE_URI)
        urllib.urlretrieve(TEMPLATE_URI, '%s-template' % CONF_FILE)
        print('Template update complete.')

    # Loop endlessly monitoring Elasticsearch cluster. Supervisor will SIGKILL us if container stops
    while True:
        try:
            es_service = '_nodes/_all/http,settings'
            response = requests.get('%s/%s' % (ES_URLS[0], es_service))
            endpoints = []
            for key, node in json.loads(response.text)['nodes'].iteritems():
                if node['settings']['node']['data'] == 'true':
                    endpoints.append(node['http_address'])
                else:
                    print('Non-data node filtered out: %s' % node['http_address'])
            update_endpoints(endpoints)
        except RequestException:
            print('Unable to get ElasticSearch tasks from %s' % ES_URLS[0])
            traceback.print_exc()
            print('Rotating ElasticSearch endpoints for next try')
            ES_URLS = ES_URLS[1:] + ES_URLS[:1]

        time.sleep(SLEEP_TIME)
