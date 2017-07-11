import filecmp
import json
import os
import sys
import time
import traceback
import urllib

import requests
from requests.exceptions import RequestException


ES_LB = os.getenv('ELASTICSEARCH_LB', 'false').lower() in ['true', '1', 't']
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

    # If behind a load balancer, we can skip all the ES cluster settings retrieval and just apply given endpoints
    if ES_LB:
        print('Starting up load balancer mode. No changes will be made to the given URLs...')
        if check_for_life(ES_URLS):
            update_endpoints(ES_URLS)
        else:
            print('No valid elasticsearch endpoints detected. Shutting down...')
            sys.exit()
        
        # Supervisor will SIGKILL us if container stops, so we can sleep wait forever
        while True:
            time.sleep(SLEEP_TIME)
            
    print('Starting up in HA sniffing mode. We will be regularly inspecting _nodes API for additional nodes...')

    # Loop endlessly monitoring Elasticsearch cluster. Supervisor will SIGKILL us if container stops
    while True:
        try:
            es_service = '_nodes/_all/http,settings'
            # Only query the first ES from the first node in the list... if it goes sideways, we rotate list anyway
            response = requests.get('%s/%s' % (ES_URLS[0], es_service))
            endpoints = []
            for key, node in json.loads(response.text)['nodes'].iteritems():
                if node['settings']['node']['data'] == 'true':
                    address = node['http_address']
                    # Handle case where http_address contains both node name and ip address
                    # Prefer IP address with port by grabbing value after the slash
                    if '/' in address:
                        address = address.split('/')[1]
                    endpoints.append(address)
                else:
                    print('Non-data node filtered out: %s' % node['http_address'])
            ES_URLS = ['http://%s' % x for x in endpoints]
            update_endpoints(endpoints)
        except RequestException:
            print('Unable to get ElasticSearch nodes from %s' % ES_URLS[0])
            traceback.print_exc()
            print('Rotating ElasticSearch endpoints for next try...')
            ES_URLS = ES_URLS[1:] + ES_URLS[:1]

        # If the config file hasn't been written yet, it means there was a failure in all previous bootstrap attempts
        # We will skip the sleep until the configuration file has been written. This will only apply for the first
        # 5 seconds, as once Logstash starts it will SIGKILL supervisor and halt everything if a config file was not
        # ever written.
        if os.path.isfile(CONF_FILE):
            time.sleep(SLEEP_TIME)
        else:
            # While attempting to bootstrap retry every 0.5 seconds
            time.sleep(0.5)
