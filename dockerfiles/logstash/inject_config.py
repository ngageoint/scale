import filecmp
import json
import os
import sys
import urllib
import urllib2
import urlparse


ES_URLS = os.getenv('ELASTICSEARCH_URLS').split(',')
TEMPLATE_URI = os.getenv('TEMPLATE_URI', None)

CONF_FILE = '/opt/logstash/logstash.conf'


def update_endpoints(endpoints):
    with open('%s-template' % CONF_FILE) as in_conf:
        conf_string = in_conf.read()

        endpoints, credentials = sanitize_endpoints(endpoints)

        print('Valid elasticSearch endpoints found: %s' % json.dumps(endpoints))

        conf_string = conf_string.replace('_ES_HOSTS_', json.dumps(endpoints))

        logstash_user = ''
        logstash_password = ''
        if credentials:
            logstash_user = 'user => %s' % credentials[0]
            logstash_password = 'password => %s' % credentials[1]

        conf_string = conf_string.replace('_ES_USER_', logstash_user)
        conf_string = conf_string.replace('_ES_PASSWORD_', logstash_password)

        with open('%s_tmp' % CONF_FILE, 'w') as out_conf:
            out_conf.write(conf_string)

    if not (os.path.isfile(CONF_FILE) and filecmp.cmp(CONF_FILE, '%s_tmp' % CONF_FILE)):
        print('Elastic Search endpoint change detected. Applying new config...')
        os.rename('%s_tmp' % CONF_FILE, CONF_FILE)
    else:
        print('No update needed. Present config is up-to-date.')


def sanitize_endpoints(endpoints):
    final_credentials = None
    for i in range(len(endpoints)):
        endpoints[i], credentials = extract_credentials(endpoints[i])
        if credentials and not final_credentials:
            final_credentials = credentials

    return (endpoints, final_credentials)


def extract_credentials(endpoint):
    url = urlparse.urlparse(endpoint)
    username = url.username
    password = url.password
    if username and password:
        print('Detected credentials for user %s' % (username))

        endpoint = endpoint.replace('%s:%s@' % (username, password), '')

    return (endpoint, (username, password))


def check_for_life(endpoints):
    for endpoint in endpoints:
        print endpoint
        response = urllib.urlopen(endpoint)
        if json.load(response.fp)['version']['number']:
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

