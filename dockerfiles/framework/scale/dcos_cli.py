#!/bin/python
import pexpect, requests, os, json, time, subprocess

FRAMEWORK_NAME = os.getenv('DCOS_PACKAGE_FRAMEWORK_NAME', 'scale')
DEPLOY_DB = os.getenv('DEPLOY_DB', 'false')
DEPLOY_LOGGING = os.getenv('DEPLOY_LOGGING', 'false')
DEPLOY_WEBSERVER = os.getenv('DEPLOY_WEBSERVER', 'false')
USERNAME = os.getenv('DCOS_USER', '')
PASSWORD = os.getenv('DCOS_PASS', '')
OAUTH_TOKEN = os.getenv('DCOS_OAUTH_TOKEN', '')


def dcos_login(username, password):
    home = os.path.expanduser("~")
    with open(home + '/.dcos/dcos.toml', "r") as file:
        if 'dcos_acs_token' not in file.read():
            child = pexpect.spawn("/usr/local/bin/dcos auth login")
            i = child.expect(['.*sername:', 'Login successful.*', '.*authentication token:'])
            if i == 0:
                child.sendline(username)
                child.expect('.*assword:')
                child.sendline(password)
                response = child.read().strip().decode('utf-8')
            elif i == 1:
                response = child.read().strip().decode('utf-8')
            elif i == 2:
                child.sendline(OAUTH_TOKEN)
                response = child.read().strip().decode('utf-8')


def run():
    es_urls = os.getenv('SCALE_ELASTICSEARCH_URLS')

    # if SCALE_ELASTICSEARCH_URLS is not set, assume we are running within DCOS and attempt to query Elastic scheduler
    if not es_urls or not len(es_urls.strip()):
        es_urls = get_elasticsearch_urls()

    print("ELASTICSEARCH_URLS=" + es_urls)

    # Determine if Logging should be deployed.
    db_host = None
    db_port = None
    if DEPLOY_DB.lower() == 'true':
        app_name = '%s-db' % FRAMEWORK_NAME
        db_port = deploy_database(app_name)
        print("DB_HOST=%s.marathon.mesos" % app_name)
        print("DB_PORT=%s" % db_port)

    # Determine if Logging should be deployed.
    if DEPLOY_LOGGING.lower() == 'true':
        app_name = '%s-logstash' % FRAMEWORK_NAME
        log_port = deploy_logstash(app_name, es_urls)
        print("LOGGING_ADDRESS=tcp://%s.marathon.mesos:%s" % (app_name, log_port))

    # Determine if Web Server should be deployed.
    if DEPLOY_WEBSERVER.lower() == 'true':
        app_name = '%s-webserver' % FRAMEWORK_NAME
        deploy_webserver(app_name, es_urls, db_host, db_port)


def delete_marathon_app(appname):
    child = pexpect.spawn("/usr/local/bin/dcos marathon app remove " + appname + " --force")
    response = child.read().strip().decode('utf-8')


def deploy_marathon_app(marathon):
    f1 = open('./marathon.json', 'w+')
    f1.write(json.dumps(marathon, ensure_ascii=False))
    f1.close()
    child = pexpect.spawn("/usr/local/bin/dcos marathon app add ./marathon.json")
    response = child.read().strip().decode('utf-8')


def check_app_exists(app_name):
    if app_name in str(subprocess.check_output(["/usr/local/bin/dcos", "marathon", "app", "list"])):
        return True
    else:
        return False


def get_marathon_port(app_name, port_index):
    output = str(subprocess.check_output(["/usr/local/bin/dcos", "marathon", "task", "list", app_name])).split('\n')
    for i in output:
        if app_name in i:
            output = list(filter(''.__ne__, i.split(" ")))
    output = str(subprocess.check_output(["/usr/local/bin/dcos", "marathon", "task", "show", output[4]])).split('\n')
    return json.loads('\n'.join(output))['ports'][port_index]


def wait_app_deploy(app_name):
    while True:
        output = str(subprocess.check_output(["/usr/local/bin/dcos", "task"])).split('\n')
        for i in output:
            if app_name in i:
                output = list(filter(''.__ne__, i.split(" ")))
        if output[3] != "R":
            time.sleep(1)
        else:
            break


def wait_app_healthy(app_name):
    while True:
        output = str(subprocess.check_output(["/usr/local/bin/dcos", "marathon", "task", "list", app_name])).split('\n')
        for i in output:
            if app_name in i:
                output = list(filter(''.__ne__, i.split(" ")))
        if output[1].lower() != "true":
            time.sleep(1)
        else:
            break


def deploy_webserver(app_name, es_urls, db_host, db_port):
    # Check if scale-db is already running
    if not check_app_exists(app_name):
        # attempt to delete an old instance..if it doesn't exists it will error but we don't care so we ignore it
        delete_marathon_app(app_name)

        # Set db host and port based on environment if not passed to function
        if not db_host:
            db_host = os.getenv('SCALE_DB_HOST')

        if not db_port:
            db_port = os.getenv('SCALE_DB_PORT')

        vhost = os.getenv('SCALE_VHOST')
        workers = os.getenv('SCALE_WEBSERVER_WORKERS', 4)
        db_name = os.getenv('SCALE_DB_NAME', 'scale')
        db_user = os.getenv('SCALE_DB_USER', 'scale')
        db_pass = os.getenv('SCALE_DB_PASS', 'scale')
        docker_image = os.getenv('MARATHON_APP_DOCKER_IMAGE')
        optional_envs = ['SCALE_SECRET_KEY', 'SCALE_ALLOWED_HOSTS']

        marathon = {
            'id': app_name,
            'cpus': 2,
            'mem': 1024,
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
                "SCALE_WEBSERVER_WORKERS": str(workers),
                "SCALE_ELASTICSEARCH_URLS": es_urls
            },
            'labels': {
                "DCOS_PACKAGE_FRAMEWORK_NAME": FRAMEWORK_NAME,
                "HAPROXY_GROUP": "internal,external",
                "DCOS_SERVICE_SCHEME": "http",
                "DCOS_SERVICE_NAME": FRAMEWORK_NAME,
                "DCOS_SERVICE_PORT_INDEX": "0",
                "HAPROXY_0_VHOST": vhost
            },
            'healthChecks': [
                {
                    "path": "/api/version",
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

        deploy_marathon_app(marathon)
        wait_app_deploy(app_name)
        time.sleep(5)
        wait_app_healthy(app_name)


def deploy_database(app_name):
    # Check if scale-db is already running
    if not check_app_exists(app_name):
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
        deploy_marathon_app(marathon)
        wait_app_deploy(app_name)
        time.sleep(5)
        wait_app_healthy(app_name)
    db_port = get_marathon_port(app_name, 0)

    return db_port


def get_elasticsearch_urls():
    response = requests.get('http://elasticsearch.marathon.mesos:31105/v1/tasks')
    endpoints = ['http://%s' % x['http_address'] for x in json.loads(response.text)]
    es_urls = ','.join(endpoints)
    return es_urls


def deploy_logstash(app_name, es_urls):
    if not check_app_exists(app_name):
        # attempt to delete an old instance..if it doesn't exists it will error but we don't care so we ignore it
        delete_marathon_app(app_name)

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
                        'protocol': 'tcp'
                    },
                        {
                            'containerPort': 80,
                            'hostPort': 0,
                            'protocol': 'tcp'
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

        deploy_marathon_app(marathon)

        wait_app_deploy(app_name)
        time.sleep(5)
        wait_app_healthy(app_name)

    logstash_port = get_marathon_port(app_name, 0)

    return logstash_port



if __name__ == '__main__':
    # ensure this doesn't try and run if imported
    dcos_login(USERNAME, PASSWORD)
    run()
