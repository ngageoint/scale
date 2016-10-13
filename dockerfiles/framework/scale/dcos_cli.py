#!/bin/python
import pexpect, sys, requests, os, json, time, subprocess

def get_env_vars():
    globals()['deploy_logging'] = os.getenv('DEPLOY_LOGGING', 'false')
    globals()['username'] = os.getenv('DCOS_USER', '')
    globals()['password'] = os.getenv('DCOS_PASS', '')
    globals()['oauth_token'] = os.getenv('DCOS_OAUTH_TOKEN', '')
    globals()['deploy_db'] = os.getenv('DEPLOY_DB', 'false')

def dcos_login(username, password):
  home = os.path.expanduser("~")
  with open(home+'/.dcos/dcos.toml', "r") as file:
    if 'dcos_acs_token' not in file.read():
      child = pexpect.spawn("/usr/local/bin/dcos auth login")
      i = child.expect (['.*sername:', 'Login successful.*', '.*authentication token:'])
      if i==0:
        child.sendline(username)
        child.expect('.*assword:')
        child.sendline(password)
        response = child.read().strip().decode('utf-8')
      elif i==1:
        response = child.read().strip().decode('utf-8')
      elif i==2:
        child.sendline(oauth_token)
        response = child.read().strip().decode('utf-8')

def run():
  # Determine if Logging should be deployed.
  if deploy_db.lower() == 'true':
    deploy_database()
  # Determine if Logging should be deployed.
  if deploy_logging.lower() == 'true':
    deploy_logstash()

def delete_marathon_app(appname):
  child = pexpect.spawn("/usr/local/bin/dcos marathon app remove "+appname+" --force")
  response = child.read().strip().decode('utf-8')

def deploy_marathon_app(marathon):
  f1=open('./marathon.json', 'w+')
  f1.write(json.dumps(marathon, ensure_ascii=False))
  f1.close()
  child = pexpect.spawn("/usr/local/bin/dcos marathon app add ./marathon.json")
  response = child.read().strip().decode('utf-8')

def check_app_exists(appname):
  if appname in str(subprocess.check_output(["/usr/local/bin/dcos", "marathon", "app", "list"])):
    return True
  else:
    return False

def get_marathon_port(appname, port_index):
  output = str(subprocess.check_output(["/usr/local/bin/dcos", "marathon", "task", "list", appname])).split('\n')
  for i in output:
    if appname in i:
      output = list(filter(('').__ne__, i.split(" ")))
  output = str(subprocess.check_output(["/usr/local/bin/dcos", "marathon", "task", "show", output[4]])).split('\n')
  return json.loads('\n'.join(output))['ports'][port_index]

def wait_app_deploy(appname):
  while True:
    output = str(subprocess.check_output(["/usr/local/bin/dcos", "task"])).split('\n')
    for i in output:
      if appname in i:
        output = list(filter(('').__ne__, i.split(" ")))
    if output[3] != "R":
      time.sleep(1)
    else:
      break

def wait_app_healthy(appname):  
  while True:
    output = str(subprocess.check_output(["/usr/local/bin/dcos", "marathon", "task", "list", appname])).split('\n')
    for i in output:
      if appname in i:
        output = list(filter(('').__ne__, i.split(" ")))
    if output[1].lower() != "true":
      time.sleep(1)
    else:
      break

def deploy_database():
  # Check if scale-db is already running
  if not check_app_exists('scale-db'):
    cfg = {
        'scaleDBName': os.environ.get('SCALE_DB_NAME', 'scale'),
        'scaleDBHost': os.environ.get('SCALE_DB_HOST', 'scale-db.marathon.slave.mesos').split(".")[0],
        'scaleDBUser': os.environ.get('SCALE_DB_USER', 'scale'),
        'scaleDBPass': os.environ.get('SCALE_DB_PASS', 'scale'),
        'db_docker_image': os.environ.get('DB_DOCKER_IMAGE', 'mdillon/postgis'),
        'dbHostVol': os.environ.get('SCALE_DB_HOST_VOL', '')
    }
    if cfg['dbHostVol'] == '':
        cfg['volumes'] = []
    else:
        cfg['volumes'] = [{"containerPath": "/var/lib/pgsql/data","hostPath": "cfg['dbHostVol']","mode": "RW"}]
    marathon = {
      'id': 'scale-db',
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
    wait_app_deploy('scale-db')
    time.sleep(5)
    wait_app_healthy('scale-db') 
  db_port = get_marathon_port('scale-db', 0)
  print("DB_PORT="+str(db_port))

def get_elasticsearch_urls():
  response = requests.get('http://elasticsearch.marathon.mesos:31105/v1/tasks')
  endpoints = ['http://%s' % x['http_address'] for x in json.loads(response.text)]
  es_urls = ','.join(endpoints)
  return es_urls

def deploy_logstash():
  es_urls = os.getenv('SCALE_ELASTICSEARCH_URL')
  # if ELASTICSEARCH_URL is not set, assume we are running within DCOS and attempt to query Elastic scheduler
  if not es_urls or not len(es_urls.strip()):
    es_urls = get_elasticsearch_urls()

  if not check_app_exists('scale-logstash'):
    # attempt to delete an old instance..if it doesn't exists it will error but we don't care so we ignore it
    #delete_marathon_app('scale-logstash')

    # get the Logstash container API endpoints
    logstash_image = os.getenv('LOGSTASH_DOCKER_IMAGE', 'geoint/logstash-elastic-ha')
    marathon = {
      'id': 'scale-logstash',
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
    
    wait_app_deploy('scale-logstash')
    time.sleep(5)
    wait_app_healthy('scale-logstash')
    
  print("ELASTICSEARCH_URL="+es_urls)
  db_port = get_marathon_port('scale-logstash', 0)
  print("LOGGING_ADDRESS=tcp://scale-logstash.marathon.mesos:"+str(db_port))


if __name__ == '__main__':
    # ensure this doesn't try and run if imported
    get_env_vars()
    dcos_login(username, password)
    run()

