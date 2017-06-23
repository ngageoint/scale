#!/bin/python
from __future__ import print_function

import requests, os, json, time, sys

from marathon import MarathonClient, MarathonApp
from marathon import NotFoundError

FRAMEWORK_NAME = os.getenv('DCOS_PACKAGE_FRAMEWORK_NAME', 'scale')
SCALE_DB_HOST = os.getenv('SCALE_DB_HOST', '')
SCALE_LOGGING_ADDRESS = os.getenv('SCALE_LOGGING_ADDRESS', '')
DEPLOY_WEBSERVER = os.getenv('DEPLOY_WEBSERVER', 'true')


def dcos_login():
    # Defaults servers for both DCOS 1.7 and 1.8. 1.8 added HTTPS within DCOS EE clusters.
    servers = os.getenv('MARATHON_SERVERS', 'http://marathon.mesos:8080,https://marathon.mesos:8443').split(',')
    oauth_token = os.getenv('DCOS_OAUTH_TOKEN', '').strip()
    username = os.getenv('DCOS_USER', '').strip()
    password = os.getenv('DCOS_PASS', '').strip()

    if len(oauth_token):
        print('Attempting token auth to Marathon...')
        client = MarathonClient(servers, auth_token=oauth_token)
    elif len(username) and len(password):
        print('Attempting basic auth to Marathon...')
        client = MarathonClient(servers, username=username, password=password)
    else:
        print('Attempting unauthenticated access to Marathon...')
        client = MarathonClient(servers)

    return client


def run(client):
    es_urls = os.getenv('SCALE_ELASTICSEARCH_URLS')

    # if SCALE_ELASTICSEARCH_URLS is not set, assume we are running within DCOS and attempt to query Elastic scheduler
    if not es_urls or not len(es_urls.strip()):
        es_urls = get_elasticsearch_urls()

    print("ELASTICSEARCH_URLS=" + es_urls)
    rabbitmq_app_name = '%s-rabbitmq' % FRAMEWORK_NAME
    log_app_name = '%s-logstash' % FRAMEWORK_NAME
    db_app_name = '%s-db' % FRAMEWORK_NAME

    # Determine if rabbitmq should be deployed. If SCALE_BROKER_URL is unset we need to deploy it
    broker_url = os.getenv('SCALE_BROKER_URL', '')
    if not len(broker_url):
        deploy_rabbitmq(client, rabbitmq_app_name)

    # Determine if db should be deployed.
    db_host = os.getenv('SCALE_DB_HOST', '')
    db_port = os.getenv('SCALE_DB_PORT', '')
    if not len(db_host):
        deploy_database(client, db_app_name)

    # Determine if logstash should be deployed.
    if not len(SCALE_LOGGING_ADDRESS):
        deploy_logstash(client, log_app_name, es_urls)

    # Wait for all needed apps to be healthy
    if not len(broker_url):
        rabbitmq_port = get_host_port_from_healthy_app(client, rabbitmq_app_name, 0)
        broker_url = 'amqp://guest:guest@%s.marathon.mesos:%s//' % (rabbitmq_app_name, rabbitmq_port)
        print("BROKER_URL=%s" % broker_url)

    if not len(db_host):
        db_port = get_host_port_from_healthy_app(client,db_app_name, 0)
        db_host = "%s.marathon.mesos" % db_app_name
        print("DB_HOST=%s" % db_host)
        print("DB_PORT=%s" % db_port)

    if not len(SCALE_LOGGING_ADDRESS):
        log_port = get_host_port_from_healthy_app(client, log_app_name, 0)
        print("LOGGING_ADDRESS=tcp://%s.marathon.mesos:%s" % (log_app_name, log_port))
        print("LOGGING_HEALTH_ADDRESS=%s.marathon.l4lb.thisdcos.directory:80" % log_app_name)

    # Determine if Web Server should be deployed.
    if DEPLOY_WEBSERVER.lower() == 'true':
        app_name = '%s-webserver' % FRAMEWORK_NAME
        webserver_port = deploy_webserver(client, app_name, es_urls, db_host, db_port)
        print("WEBSERVER_ADDRESS=http://%s.marathon.mesos:%s" % (app_name, webserver_port))


def delete_marathon_app(client, app_name, fail_on_error=False, sleep_secs=5):
    print("Attempting delete of Marathon app: %s" % app_name)
    try:
        response = client.delete_app(app_name, force=True)
        print(response, file=sys.stderr)
    except NotFoundError:
        if fail_on_error:
            raise
        else:
            print('Not found. Ignoring...')

    while(check_app_exists(client, app_name)):
        print('Waiting for delete of Marathon App: %s' % app_name)
        time.sleep(sleep_secs)


def deploy_marathon_app(client, marathon_json, sleep_secs=10, retries=3):
    app_id = marathon_json['id']
    print("Attempting deploy Marathon app with id: %s" % app_id)
    print(marathon_json, file=sys.stderr)
    marathon_app = MarathonApp.from_json(marathon_json)
    
    # We are going to retry, in the case of blocked deployments
    attempt = 0
    while attempt < retries:
        try:
            response = client.create_app(app_id, marathon_app)
            print(response, file=sys.stderr)
            print('Deployment succeeded.')
            break
        except Exception, ex:
            attempt += 1
            print(ex.message)
            print('Failure attempting to deploy app. Retrying...')
            time.sleep(sleep_secs)


def check_app_exists(client, app_name):
    try:
        client.get_app(app_name)
        return True
    except NotFoundError:
        return False


def get_host_port_from_healthy_app(client, app_name, port_index):
    wait_app_healthy(client, app_name)

    return get_marathon_app_single_task_host_port(client, app_name, port_index)


def get_marathon_app_single_task_host_port(client, app_name, port_index):
    app = client.get_app(app_name)
    return app.tasks[0].ports[port_index]


def wait_app_healthy(client, app_name, sleep_secs=5):
    while client.get_app(app_name).tasks_healthy < 1:
        print('Waiting for healthy app %s.' % app_name)
        time.sleep(sleep_secs)


def deploy_webserver(client, app_name, es_urls, db_host, db_port):
    # attempt to delete an old instance..if it doesn't exists it will error but we don't care so we ignore it
    delete_marathon_app(client, app_name)

    vhost = os.getenv('SCALE_VHOST')
    cpu = os.getenv('SCALE_WEBSERVER_CPU', 1)
    memory = os.getenv('SCALE_WEBSERVER_MEMORY', 2048)
    db_name = os.getenv('SCALE_DB_NAME', 'scale')
    db_user = os.getenv('SCALE_DB_USER', 'scale')
    db_pass = os.getenv('SCALE_DB_PASS', 'scale')
    docker_image = os.getenv('MARATHON_APP_DOCKER_IMAGE')
    optional_envs = ['SCALE_SECRET_KEY', 'SCALE_ALLOWED_HOSTS']

    marathon = {
        'id': app_name,
        'cpus': int(cpu),
        'mem': int(memory),
        'disk': 0,
        'instances': 1,
        'container': {
            'docker': {
                'image': docker_image,
                'network': 'BRIDGE',
                'portMappings': [{
                    'containerPort': 80,
                    'hostPort': 0
                }
                ],
                'forcePullImage': True
            },
            'type': 'DOCKER'
        },
        'env': {
            "DCOS_PACKAGE_FRAMEWORK_NAME": FRAMEWORK_NAME,
            "ENABLE_WEBSERVER": 'true',
            "SCALE_DB_HOST": db_host,
            "SCALE_DB_NAME": db_name,
            "SCALE_DB_PORT": str(db_port),
            "SCALE_DB_USER": db_user,
            "SCALE_DB_PASS": db_pass,
            "SCALE_STATIC_URL": "/service/%s/static/" % FRAMEWORK_NAME,
            "SCALE_WEBSERVER_CPU": str(cpu),
            "SCALE_WEBSERVER_MEMORY": str(memory),
            "SCALE_ELASTICSEARCH_URLS": es_urls
        },
        'labels': {
            "HAPROXY_GROUP": "internal,external",
            "DCOS_SERVICE_SCHEME": "http",
            "DCOS_SERVICE_NAME": FRAMEWORK_NAME,
            "DCOS_SERVICE_PORT_INDEX": "0",
            "HAPROXY_0_VHOST": vhost,
            "HAPROXY_0_BACKEND_HTTP_OPTIONS": "http-request set-header X-HAPROXY 1\n"
                                              "rspadd Access-Control-Allow-Methods:\\ GET,\\ POST,\\ PUT,\\ PATCH,\\ OPTIONS,\\ DELETE\n"
                                              "rspadd Access-Control-Allow-Headers:\\ Origin,\\ X-Requested-With,\\ Content-Type,\\ Accept,\\ Authorization\n"
        },
        'healthChecks': [
            {
                "path": "/api/v4/version/",
                "protocol": "TCP",
                "gracePeriodSeconds": 300,
                "intervalSeconds": 20,
                "portIndex": 0,
                "timeoutSeconds": 20,
                "maxConsecutiveFailures": 3
            },
        ],
        'uris': []
    }
    CONFIG_URI = os.getenv('CONFIG_URI')
    if CONFIG_URI:
        marathon['uris'].append(CONFIG_URI)
    # For all optional environment variable that are set pass them on.
    for env in optional_envs:
        env_value = os.getenv(env)
        if env_value:
            marathon['env'][env] = env_value

    deploy_marathon_app(client, marathon)
    wait_app_healthy(client, app_name)

    webserver_port = get_marathon_app_single_task_host_port(client, app_name, 0)

    return webserver_port


def deploy_database(client, app_name):
    # Check if scale-db is already running
    if not check_app_exists(client, app_name):
        cfg = {
            'scaleDBName': os.environ.get('SCALE_DB_NAME', 'scale'),
            'scaleDBHost': '%s.marathon.mesos' % app_name,
            'scaleDBUser': os.environ.get('SCALE_DB_USER', 'scale'),
            'scaleDBPass': os.environ.get('SCALE_DB_PASS', 'scale'),
            'db_docker_image': os.environ.get('DB_DOCKER_IMAGE', 'mdillon/postgis'),
            'dbHostVol': os.environ.get('SCALE_DB_HOST_VOL', '')
        }
        if cfg['dbHostVol'] == '':
            cfg['volumes'] = []
        else:
            cfg['volumes'] = [{"containerPath": "/var/lib/pgsql/data", "hostPath": "cfg['dbHostVol']", "mode": "RW"}]
        marathon = {
            'id': app_name,
            'cpus': 2,
            'mem': 1024,
            'disk': 0,
            'instances': 1,
            'container': {
                'docker': {
                    'image': cfg['db_docker_image'],
                    'network': 'BRIDGE',
                    'portMappings': [{
                        'containerPort': 5432,
                        'hostPort': 0
                    }
                    ],
                    'forcePullImage': True
                },
                'type': 'DOCKER',
                'volumes': cfg['volumes']
            },
            'env': {
                "POSTGRES_DB": cfg['scaleDBName'],
                "POSTGRES_USER": cfg['scaleDBUser'],
                "POSTGRES_PASSWORD": cfg['scaleDBPass']
            },
            'labels': {},
            'healthChecks': [
                {
                    "protocol": "TCP",
                    "gracePeriodSeconds": 300,
                    "intervalSeconds": 20,
                    "portIndex": 0,
                    "timeoutSeconds": 20,
                    "maxConsecutiveFailures": 3
                },
            ],
            'uris': []
        }

        CONFIG_URI = os.getenv('CONFIG_URI')
        if CONFIG_URI:
            marathon['uris'].append(CONFIG_URI)
        deploy_marathon_app(client, marathon)


def get_elasticsearch_urls():
    response = requests.get('http://elasticsearch.marathon.mesos:31105/v1/tasks')
    endpoints = ['http://%s' % x['http_address'] for x in json.loads(response.text)]
    es_urls = ','.join(endpoints)
    return es_urls

def deploy_rabbitmq(client, app_name):
    # Check if scale-db is already running
    if not check_app_exists(client, app_name):
        rabbitmq_image = os.getenv('RABBITMQ_DOCKER_IMAGE', 'rabbitmq:3.6-management')
        
        marathon = {
            "id": app_name,
            "cpus": 1,
            "mem": 512,
            "disk": 0,
            "instances": 1,
            "container": {
                "docker": {
                    "image": rabbitmq_image,
                    "forcePullImage": True,
                    "privileged": False,
                    "portMappings": [
                        {
                            "containerPort": 5672,
                            "hostPort": 5672,
                            "protocol": "tcp",
                            "labels": {
                                "VIP_0": "/%s:5672" % app_name
                            }
                        },
                        {
                            "containerPort": 15672,
                            "protocol": "tcp",
                            "servicePort": 0,
                            "labels": {
                                "VIP_1": "/%s:15672" % app_name
                            }
                        }
                    ],
                    "network": "BRIDGE"
                }
            },
            "healthChecks": [
                {
                    "protocol": "TCP",
                    "gracePeriodSeconds": 300,
                    "intervalSeconds": 60,
                    "timeoutSeconds": 20,
                    "maxConsecutiveFailures": 3,
                    "portIndex": 0
                }
            ],
            'uris': []
        }


        # Support uri passing for protected Docker Registries
        CONFIG_URI = os.getenv('CONFIG_URI')
        if CONFIG_URI:
            marathon['uris'].append(CONFIG_URI)

        deploy_marathon_app(client, marathon)

def deploy_logstash(client, app_name, es_urls):
    # attempt to delete an old instance..if it doesn't exists it will error but we don't care so we ignore it
    delete_marathon_app(client, app_name)

    # get the Logstash container API endpoints
    logstash_image = os.getenv('LOGSTASH_DOCKER_IMAGE', 'geoint/logstash-elastic-ha')
    marathon = {
        'id': app_name,
        'cpus': 0.5,
        'mem': 1024,
        'disk': 256,
        'instances': 1,
        'container': {
            'docker': {
                'image': logstash_image,
                'network': 'BRIDGE',
                'portMappings': [{
                    'containerPort': 8000,
                    'hostPort': 9229,
                    'protocol': 'tcp',
                    'labels': {
                        'VIP_0': '%s:8000' % app_name
                    }
                },
                    {
                        'containerPort': 80,
                        'hostPort': 0,
                        'protocol': 'tcp',
                        'labels': {
                            'VIP_1': '%s:80' % app_name
                        }
                    }
                ],
                'forcePullImage': True
            },
            'type': 'DOCKER',
            'volumes': []
        },
        'env': {
            'LOGSTASH_ARGS': '-w 1',
            'ELASTICSEARCH_URLS': es_urls
        },
        'labels': {},
        'healthChecks': [
            {
                "protocol": "HTTP",
                "path": "/",
                "gracePeriodSeconds": 5,
                "intervalSeconds": 10,
                "portIndex": 1,
                "timeoutSeconds": 10,
                "maxConsecutiveFailures": 3
            },
        ],
        'uris': []
    }

    # Capture any passed-in environment variables that are relevant to Logstash container.
    CONFIG_URI = os.getenv('CONFIG_URI')
    SLEEP_TIME = os.getenv('LOGSTASH_WATCHDOG_SLEEP_TIME')
    TEMPLATE_URI = os.getenv('LOGSTASH_TEMPLATE_URI')
    if SLEEP_TIME:
        marathon['env']['SLEEP_TIME'] = SLEEP_TIME
    if TEMPLATE_URI:
        marathon['env']['TEMPLATE_URI'] = TEMPLATE_URI
    if CONFIG_URI:
        marathon['uris'].append(CONFIG_URI)

    deploy_marathon_app(client, marathon)


if __name__ == '__main__':
    # ensure this doesn't try and run if imported
    client = dcos_login()
    run(client)
