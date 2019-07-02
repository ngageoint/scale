#!/bin/python
from __future__ import print_function

from marathon import MarathonClient, MarathonApp
from marathon import NotFoundError

import json
import os
import sys
import time

import requests
from mesoshttp.acs import DCOSServiceAuth

APPLICATION_GROUP = os.getenv('APPLICATION_GROUP', None)
FRAMEWORK_NAME = os.getenv('DCOS_PACKAGE_FRAMEWORK_NAME', 'scale')
LOGGING_ADDRESS = os.getenv('LOGGING_ADDRESS', '')
DEPLOY_WEBSERVER = os.getenv('DEPLOY_WEBSERVER', 'true')
DEPLOY_UI = os.getenv('DEPLOY_UI', 'true')
SERVICE_SECRET = os.getenv('SERVICE_SECRET')


def dcos_login():
    # Defaults servers for both DCOS 1.10+ CE and EE.
    servers = os.getenv('MARATHON_SERVERS',
                        'http://marathon.mesos:8080,https://marathon.mesos:8443').split(',')

    if SERVICE_SECRET:
        print('Attempting token auth to Marathon...')
        client = MarathonClient(servers, auth_token=DCOSServiceAuth(json.loads(SERVICE_SECRET)).token, verify=False)
    else:
        print('Attempting unauthenticated access to Marathon...')
        client = MarathonClient(servers, verify=False)

    return client


def run(client):
    silo_admin_password = os.getenv('ADMIN_PASSWORD', 'spicy-pickles17!')
    silo_hub_org = os.getenv('SILO_HUB_ORG', 'geointseed')
    silo_url = os.getenv('SILO_URL', '')

    blocking_apps = []

    # Determine if elasticsearch should be deployed. If ELASTICSEARCH_URL is unset we need to deploy it
    es_url = os.getenv('ELASTICSEARCH_URL', '')
    if not len(es_url):
        app_name = '%s-elasticsearch' % FRAMEWORK_NAME
        deploy_elasticsearch(client, app_name)
        es_url = "http://%s.marathon.l4lb.thisdcos.directory:9200" % subdomain_gen(app_name)
        blocking_apps.append(app_name)
    print("ELASTICSEARCH_URL=%s" % (es_url))

    # Determine if rabbitmq should be deployed. If SCALE_BROKER_URL is unset we need to deploy it
    broker_url = os.getenv('SCALE_BROKER_URL', '')
    if not len(broker_url):
        app_name = '%s-rabbitmq' % FRAMEWORK_NAME
        deploy_rabbitmq(client, app_name)
        broker_url = 'amqp://guest:guest@%s.marathon.l4lb.thisdcos.directory:5672//' % subdomain_gen(app_name)
        print("BROKER_URL=%s" % broker_url)
        blocking_apps.append(app_name)

    # Determine if db should be deployed.
    db_url = os.getenv('DATABASE_URL', '')
    if not len(db_url):
        app_name = '%s-db' % FRAMEWORK_NAME
        deploy_database(client, app_name)
        db_url = "postgis://scale:scale@%s.marathon.l4lb.thisdcos.directory:5432/scale" % subdomain_gen(app_name)
        print("DATABASE_URL=%s" % db_url)
        blocking_apps.append(app_name)

    # Determine if fluentd should be deployed.
    if not len(LOGGING_ADDRESS):
        app_name = '%s-fluentd' % FRAMEWORK_NAME
        deploy_fluentd(client, app_name, es_url)
        print("LOGGING_ADDRESS=tcp://%s.marathon.l4lb.thisdcos.directory:24224" % subdomain_gen(app_name))
        print("LOGGING_HEALTH_ADDRESS=%s.marathon.l4lb.thisdcos.directory:24220" % subdomain_gen(app_name))
        blocking_apps.append(app_name)

    # Determine if Web Server should be deployed.
    if DEPLOY_WEBSERVER.lower() == 'true':
        app_name = '%s-webserver' % FRAMEWORK_NAME
        deploy_webserver(client, app_name, es_url, db_url, broker_url)
        webserver_url = 'http://%s.marathon.l4lb.thisdcos.directory:80/' % subdomain_gen(app_name)
        blocking_apps.append(app_name)

    # Determine if Web Server should be deployed.
    scan_silo = False
    if not len(silo_url):
        app_name = '%s-silo' % FRAMEWORK_NAME
        deploy_silo(client, app_name, db_url)
        silo_url = 'http://%s.marathon.l4lb.thisdcos.directory:9000/' % subdomain_gen(app_name)
        blocking_apps.append(app_name)
        scan_silo = True

    # Determine if UI should be deployed.
    if DEPLOY_UI.lower() == 'true':
        app_name = '%s-ui' % FRAMEWORK_NAME
        deploy_ui(client, app_name, webserver_url, silo_url)
        print("WEBSERVER_ADDRESS=http://%s.marathon.l4lb.thisdcos.directory:80" % (subdomain_gen(app_name)))

    # Wait for all needed apps to be healthy
    for app_name in blocking_apps:
        get_host_port_from_healthy_app(client, app_name, 0)

    # If we deployed Silo, attempt to configure a scan.
    if scan_silo:
        # Grab access token to Silo
        result = requests.post('{}login'.format(silo_url),
                               json={'username': 'admin', 'password': silo_admin_password})
        token = 'token {}'.format(result.json()['token'])
        # Add the registry org
        requests.post('{}registries/add'.format(silo_url),
                      json={'name': silo_hub_org, 'url': 'https://hub.docker.com', 'org': silo_hub_org},
                      headers={'Authorization': token})
        # Trigger scan of registry org
        requests.get('{}registries/scan'.format(silo_url),
                     headers={'Authorization': token})


def subdomain_gen(app_name):
    prefix = APPLICATION_GROUP if APPLICATION_GROUP else ""

    return "%s%s" % (prefix, app_name)


def delete_marathon_app(client, app_name, fail_on_error=False, sleep_secs=5):
    print("Attempting delete of Marathon app: %s" % app_name)
    try:
        response = client.delete_app(get_group_app_name(app_name), force=True)
        print(response, file=sys.stderr)
    except NotFoundError:
        if fail_on_error:
            raise
        else:
            print('Not found. Ignoring...')

    while (check_app_exists(client, app_name)):
        print('Waiting for delete of Marathon App: %s' % app_name)
        time.sleep(sleep_secs)


def deploy_marathon_app(client, marathon_json, sleep_secs=10, retries=3):
    app_id = marathon_json['id']

    CONFIG_URI = os.getenv('CONFIG_URI')
    if CONFIG_URI:
        marathon_json['uris'].append(CONFIG_URI)

    print("Attempting deploy Marathon app with id: %s" % app_id)
    print(marathon_json, file=sys.stderr)
    marathon_app = MarathonApp.from_json(marathon_json)

    # We are going to retry, in the case of blocked deployments
    attempt = 0
    while attempt < retries:
        try:
            try:
                client.get_app(app_id)
                response = client.update_app(app_id, marathon_app)
            except NotFoundError:
                response = client.create_app(app_id, marathon_app)
            print(response, file=sys.stderr)
            print('Deployment succeeded.')
            break
        except Exception, ex:
            attempt += 1
            print(ex.message)
            print('Failure attempting to deploy app. Retrying...')
            time.sleep(sleep_secs)


def apply_set_envs(marathon_json, env_pairs):
    # Env pairs of as follows:
    # {'source_env':'target_env'}

    # For all optional environment variable that are set pass them on.
    for env in env_pairs:
        env_value = os.getenv(env)
        if env_value:
            marathon_json['env'][env_pairs[env]] = str(env_value)


def check_app_exists(client, app_name):
    try:
        client.get_app(get_group_app_name(app_name))
        return True
    except NotFoundError:
        return False


def get_host_port_from_healthy_app(client, app_name, port_index):
    group_app_name = get_group_app_name(app_name)

    wait_app_healthy(client, group_app_name)

    return get_marathon_app_single_task_host_port(client, group_app_name, port_index)


def get_marathon_app_single_task_host_port(client, app_name, port_index):
    app = client.get_app(app_name)
    return app.tasks[0].ports[port_index]


def get_group_app_name(app_name):
    # Add in the application group, if specified
    if APPLICATION_GROUP:
        group_app_name = '/%s/%s' % (APPLICATION_GROUP, app_name)
    else:
        group_app_name = '/%s' % app_name

    return group_app_name


def initialize_app_template(template_name, app_name, image_name):
    # Load template file
    marathon_json_file = open('app-templates/%s.json' % template_name)
    marathon = json.load(marathon_json_file)
    marathon_json_file.close()

    # Update id and VIPs to reflect app_name
    marathon = search_replace(marathon, 'scale-template-%s' % template_name, get_group_app_name(app_name))

    # Set container.docker.image
    if image_name:
        marathon['container']['docker']['image'] = image_name
    return marathon


def search_replace(marathon_json, search, replace):
    stringified = json.dumps(marathon_json)
    output = stringified.replace(search, replace)

    return json.loads(output)


def wait_app_healthy(client, app_name, sleep_secs=5):
    while client.get_app(app_name).tasks_healthy < 1:
        print('Waiting for healthy app %s.' % app_name)
        time.sleep(sleep_secs)


def deploy_webserver(client, app_name, es_url, db_url, broker_url):
    # Load marathon template file
    marathon = initialize_app_template('webserver', app_name,
                                       os.getenv('MARATHON_APP_DOCKER_IMAGE'))

    vhost = os.getenv('SCALE_VHOST')
    cpu = os.getenv('SCALE_WEBSERVER_CPU', 1)
    memory = os.getenv('SCALE_WEBSERVER_MEMORY', 2048)

    # Set resources of webserver
    marathon['cpus'] = int(cpu)
    marathon['mem'] = int(memory)

    # Set attributes for secrets
    secrets_dcos_sa = os.environ.get('DCOS_SERVICE_ACCOUNT', '')
    secrets_ssl_warn = os.environ.get('SECRETS_SSL_WARNINGS', '')
    secrets_token = os.environ.get('SECRETS_TOKEN', '')
    secrets_url = os.environ.get('SECRETS_URL', '')

    # Set attributes for logging
    system_logging_level = os.environ.get('SYSTEM_LOGGING_LEVEL', 'INFO')

    env_map = {
        'SCALE_ALLOWED_HOSTS': 'SCALE_ALLOWED_HOSTS',
        'SCALE_SECRET_KEY': 'SCALE_SECRET_KEY',
        'SCALE_QUEUE_NAME': 'SCALE_QUEUE_NAME',
        'GEOAXIS_HOST': 'GEOAXIS_HOST',
        'GEOAXIS_KEY': 'GEOAXIS_KEY',
        'GEOAXIS_SECRET': 'GEOAXIS_SECRET'
    }
    apply_set_envs(marathon, env_map)

    arbitrary_env = {
        'DCOS_PACKAGE_FRAMEWORK_NAME': FRAMEWORK_NAME,
        'DCOS_SERVICE_ACCOUNT': str(secrets_dcos_sa),
        'ENABLE_WEBSERVER': 'true',
        'SCALE_BROKER_URL': broker_url,
        'DATABASE_URL': db_url,
        'SCALE_STATIC_URL': '/service/%s/static/' % FRAMEWORK_NAME,
        'SCALE_WEBSERVER_CPU': str(cpu),
        'SCALE_WEBSERVER_MEMORY': str(memory),
        'ELASTICSEARCH_URL': es_url,
        'SECRETS_SSL_WARNINGS': str(secrets_ssl_warn),
        'SECRETS_TOKEN': str(secrets_token),
        'SECRETS_URL': str(secrets_url),
        'SYSTEM_LOGGING_LEVEL': system_logging_level
    }
    # For all environment variable that are set add to marathon json.
    for env in arbitrary_env:
        marathon['env'][env] = arbitrary_env[env]

    marathon['labels']['HAPROXY_0_VHOST'] = 'api-' + vhost

    deploy_marathon_app(client, marathon)


def deploy_ui(client, app_name, webserver_url, silo_url):
    ui_docker_img_default = build_image_from_suffix('ui')

    # Load marathon template file
    marathon = initialize_app_template('ui', app_name, os.getenv(
        'UI_DOCKER_IMAGE', ui_docker_img_default))

    arbitrary_env = {
        'API_BACKEND': webserver_url,
        'SILO_BACKEND': silo_url,
        'CONTEXTS': '/service/%s' % FRAMEWORK_NAME
    }
    # For all environment variable that are set add to marathon json.
    for env in arbitrary_env:
        marathon['env'][env] = arbitrary_env[env]

    marathon['labels']['DCOS_SERVICE_NAME'] = FRAMEWORK_NAME
    marathon['labels']['HAPROXY_0_VHOST'] = os.getenv('SCALE_VHOST')

    deploy_marathon_app(client, marathon)


def deploy_silo(client, app_name, db_url):
    if not check_app_exists(client, app_name):
        # Load marathon template file
        marathon = initialize_app_template('silo', app_name,
                                           os.getenv('SILO_DOCKER_IMAGE'))

        env_map = {
            'ADMIN_PASSWORD': 'SILO_ADMIN_PASSWORD'
        }

        apply_set_envs(marathon, env_map)

        arbitrary_env = {
            'DATABASE_URL': db_url.replace('postgis', 'postgres') + '?sslmode=disable'
        }
        # For all environment variable that are set add to marathon json.
        for env in arbitrary_env:
            marathon['env'][env] = arbitrary_env[env]

        deploy_marathon_app(client, marathon)


def deploy_database(client, app_name):
    # Check if scale-db is already running
    if not check_app_exists(client, app_name):
        # Load marathon template file
        marathon = initialize_app_template('db', app_name,
                                           os.getenv('DB_DOCKER_IMAGE'))

        # Set persistence
        DB_HOST_VOL = os.environ.get('SCALE_DB_HOST_VOL', '')
        if DB_HOST_VOL != '':
            marathon['container']['volumes'] = [
                {"containerPath": "/var/lib/pgsql/data", "hostPath": DB_HOST_VOL, "mode": "RW"}]

        env_map = {}
        apply_set_envs(marathon, env_map)

        deploy_marathon_app(client, marathon)


def deploy_rabbitmq(client, app_name):
    # Check if rabbitmq is already running
    if not check_app_exists(client, app_name):
        # Load marathon template file
        marathon = initialize_app_template('rabbitmq',
                                           app_name,
                                           os.getenv('RABBITMQ_DOCKER_IMAGE'))

        deploy_marathon_app(client, marathon)


def deploy_elasticsearch(client, app_name):
    # Check if elasticsearch is already running
    if not check_app_exists(client, app_name):
        # Load marathon template file
        marathon = initialize_app_template('elasticsearch',
                                           app_name,
                                           os.getenv('ELASTICSEARCH_DOCKER_IMAGE'))

        deploy_marathon_app(client, marathon)


def build_image_from_suffix(suffix):
    # default based on MARATHON_APP_DOCKER_IMAGE with repo/scale:tag updated to repo/scale-fluentd:tag
    marathon_img_default = os.getenv('MARATHON_APP_DOCKER_IMAGE')

    docker_img_default = marathon_img_default + '-' + suffix
    if ':' in marathon_img_default:
        # Grab parts to ensure we replace on tag not port
        parts = marathon_img_default.split('/')
        last_index = len(parts) - 1
        if ':' in parts[last_index]:
            replacement = parts[last_index].replace(':', '-' + suffix + ':')
            docker_img_default = marathon_img_default.replace(parts[last_index], replacement)

    return docker_img_default


def deploy_fluentd(client, app_name, es_url):
    """
    Logic must handle 3 deployment cases when FLUENTD_DOCKER_IMAGE is unset:

    localhost:5000/geoint/scale:5.9.2
    localhost:5000/geoint/scale
    geoint/scale:5.9.2

    The most problematic is the 2nd case as we previously were improperly identifying
    the port colon as the tag colon.
    """
    fluentd_docker_img_default = build_image_from_suffix('fluentd')

    # Load marathon template file
    marathon = initialize_app_template('fluentd', app_name, os.getenv(
        'FLUENTD_DOCKER_IMAGE', fluentd_docker_img_default))

    arbitrary_env = {
        'ELASTICSEARCH_URL': es_url,
    }
    # For all environment variable that are set add to marathon json.
    for env in arbitrary_env:
        marathon['env'][env] = arbitrary_env[env]

    env_map = {
        'FLUENTD_TEMPLATE_URI': 'TEMPLATE_URI'
    }
    apply_set_envs(marathon, env_map)
    deploy_marathon_app(client, marathon)


if __name__ == '__main__':
    # ensure this doesn't try and run if imported
    client = dcos_login()
    run(client)
