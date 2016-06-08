#!/usr/bin/env python
import requests, os, json, time
r = requests.get('http://marathon.mesos:8080/v2/apps/')
scaleDBName = os.environ.get('SCALE_DB_NAME', 'scale')
scaleDBHost = os.environ.get('SCALE_DB_HOST', 'scale-db.marathon.slave.mesos').split(".")[0]
scaleDBUser = os.environ.get('SCALE_DB_USER', 'scale')
scaleDBPass = os.environ.get('SCALE_DB_PASS', 'scale')
nfsPostgresUid = os.environ.get('NFS_POSTGRES_UID', '26')
nfsPostgresGid = os.environ.get('NFS_POSTGRES_GID', '26')
dockerImage = os.environ.get('DB_DOCKER_IMAGE', 'docker.io/droessne/dcos-scale-db')
dbHostVol = os.environ.get('SCALE_DB_HOST_VOL', '')
if dbHostVol == '':
  volumes=''
else:
  volumes='{"containerPath": "/var/lib/pgsql/data","hostPath": "'+dbHostVol+'","mode": "RW"}'
marathon='{"id": "/'+scaleDBHost+'","instances": 1,"constraints": [["hostname","UNIQUE"]],"container": {"docker": {"forcePullImage": true,"image": "'+dockerImage+'","network": "BRIDGE","portMappings": [{"containerPort": 5432, "hostPort": 0}],"privileged": false},"type": "DOCKER","volumes": ['+volumes+']},"cpus": 2,"disk": 0,"env": {"SCALE_DB_NAME": "'+scaleDBName+'","SCALE_DB_USER": "'+scaleDBUser+'","SCALE_DB_PASS": "'+scaleDBPass+'","NFS_POSTGRES_UID": "'+nfsPostgresUid+'","NFS_POSTGRES_GID": "'+nfsPostgresGid+'"},"healthChecks": [{"gracePeriodSeconds": 300,"ignoreHttp1xx": false,"intervalSeconds": 20,"maxConsecutiveFailures": 3,"portIndex": 0,"protocol": "TCP","timeoutSeconds": 20}],"labels": {},"mem": 1024,"ports": [5432]}'
r = requests.post('http://marathon.mesos:8080/v2/apps/', data=marathon)
#if "already exists" in r.text:
#  print "Already in Marathon."
while json.loads(requests.get('http://marathon.mesos:8080/v2/apps/'+scaleDBHost).text)['app']['tasksHealthy'] == 0:
  #print "Waiting for Healthy DB!"
  time.sleep(5)
dbPort = json.loads(requests.get('http://marathon.mesos:8080/v2/apps/'+scaleDBHost).text)['app']['tasks'][0]['ports'][0]
os.putenv('SCALE_DB_PORT',str(dbPort))
print dbPort
exit()

