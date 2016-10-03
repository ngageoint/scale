#!/bin/python
import pexpect, sys, requests, os, json, time, subprocess

allowed_args = ['--username', '--password', '--deploy_logging', '--deploy_db']

def check_env_vars():
  try:
    os.environ['DEPLOY_LOGGING']
  except KeyError:
    pass
  else:
    globals()['deploy_logging'] = os.environ.get('DEPLOY_LOGGING')
  try:
    os.environ['DCOS_USER']
  except KeyError:
    pass
  else:
    globals()['username'] = os.environ.get('DCOS_USER')
  try:
    os.environ['DCOS_PASS']
  except KeyError:
    pass
  else:
    globals()['password'] = os.environ.get('DCOS_PASS')
  try:
    os.environ['DEPLOY_DB']
  except KeyError:
    pass
  else:
    globals()['deploy_db'] = os.environ.get('DEPLOY_DB')


def check_login_required():
  breakLoop = False
  while breakLoop != True:
    output = str(subprocess.check_output(["/usr/local/bin/dcos", "--version"])).split('\n')
    for i in output:
      if "dcos.version" in i:
        print i
        if "open" in i:
          login = False
          breakLoop = True
        else:
          login = True
          breakLoop = True
  breakLoop = True
  return login

def dcos_login(username, password):
  try:
    username
    password
  except NameError:
    home = os.path.expanduser("~")
    if 'dcos_acs_token' not in open(home+'/.dcos/dcos.toml').read():
      print("Not Autherized")
      exit(1)
    else:
      pass
  else:
    home = os.path.expanduser("~")
    if 'dcos_acs_token' not in open(home+'/.dcos/dcos.toml').read():
      child = pexpect.spawn("/usr/local/bin/dcos auth login")
      child.expect('.*sername:')
      child.sendline(username)
      child.expect('.*assword:')
      child.sendline(password)
      response = child.read().strip().decode('utf-8')
      #print(response)
    else:
      #print("Already Logged in")
      pass

def dcos_logout():
  child = pexpect.spawn("/usr/local/bin/dcos auth logout")
  response = child.read().strip().decode('utf-8')
  #print(response)

def get_args():
  arguments = sys.argv[1:]
  for i in arguments:
    arg = i.split('=')[0]
    val = i.split('=')[1]
    if arg not in allowed_args:
      print('Invalid Argument: '+arg)
      exit(1)
    else:
      for l in allowed_args:
        if arg == l:
          globals()[l.strip('--')] = val

def run_args():
  # Determine if Logging should be deployed.
  try:
    deploy_db
  except NameError:
    pass
  else:
    if deploy_db.lower() == 'true':
      deploy_database()
  # Determine if Logging should be deployed.
  try:
    deploy_logging
  except NameError:
    pass
  else:
    if deploy_logging.lower() == 'true':
      deploy_logstash()

def delete_marathon_app(appname):
  child = pexpect.spawn("/usr/local/bin/dcos marathon app remove "+appname+" --force")
  response = child.read().strip().decode('utf-8')

def deploy_marathon_app(marathon):
  f1=open('./logstash.json', 'w+')
  f1.write(json.dumps(marathon, ensure_ascii=False))
  f1.close()
  child = pexpect.spawn("/usr/local/bin/dcos marathon app add ./logstash.json")
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
  #print("Waiting for "+appname+" to deploy")
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
  #print("Waiting for "+appname+" to become Healthy")
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
    #print("Deploying scale-db")
    cfg = {
        'scaleDBName': os.environ.get('SCALE_DB_NAME', 'scale'),
        'scaleDBHost': os.environ.get('SCALE_DB_HOST', 'scale-db.marathon.slave.mesos').split(".")[0],
        'scaleDBUser': os.environ.get('SCALE_DB_USER', 'scale'),
        'scaleDBPass': os.environ.get('SCALE_DB_PASS', 'scale'),
        'nfsPostgresUid': os.environ.get('NFS_POSTGRES_UID', '26'),
        'nfsPostgresGid': os.environ.get('NFS_POSTGRES_GID', '26'),
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
        "POSTGRES_PASSWORD": cfg['scaleDBPass'],
        "NFS_POSTGRES_UID": cfg['nfsPostgresUid'],
        "NFS_POSTGRES_GID": cfg['nfsPostgresGid']
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
    #print("Deploying scale-logstash") 
  
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
            'protocol': 'udp'
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
          "timeoutSeconds": 2,
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
  print("LOGGING_ADDRESS=udp://scale-logstash.marathon.mesos:"+str(db_port))


if __name__ == '__main__':
    # ensure this doesn't try and run if imported
    check_env_vars()
    get_args()
    if check_login_required():
      dcos_login(username, password)
    run_args()

