import filecmp
import json
import os
import sys
import time
import urllib

import requests


ES_URLS = os.getenv('ELASTICSEARCH_URLS').split(',')
SLEEP_TIME = float(os.getenv('SLEEP_TIME', 30))
TEMPLATE_URI = os.getenv('TEMPLATE_URI', None)

CONF_FILE = '/opt/logstash/logstash.conf'


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
        
def check_for_life(endpoints):
    for endpoint in endpoints:
        response = requests.get(endpoint)
        if json.loads(response.text)['version']['number']:
            return True
            
    return False

# ensure this doesn't try and run if imported
if __name__ == '__main__':
    if TEMPLATE_URI:
        print('Attempting template update from %s...' % TEMPLATE_URI)
        urllib.urlretrieve(TEMPLATE_URI, '%s-template' % CONF_FILE)
        print('Template update complete.')

    print('Validating Elasticsearch URLs...')
    if check_for_life(ES_URLS):
        update_endpoints(ES_URLS)
    else:
        print('No valid Elasticsearch endpoints detected. Shutting down...')
        sys.exit()

    # Supervisor will SIGKILL us if container stops, so we can sleep wait forever
    while True:
        time.sleep(SLEEP_TIME)

