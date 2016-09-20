#!/usr/bin/env python

__doc__ = """
This script executes a Marathon tasks for the postgis database and is meant for use with DC/OS deployments only.
"""
import requests, os, json, time

def run():
    cfg = {
        'scaleDBName': os.environ.get('SCALE_DB_NAME', 'scale'),
        'scaleDBHost': os.environ.get('SCALE_DB_HOST', 'scale-db.marathon.slave.mesos').split(".")[0],
        'scaleDBUser': os.environ.get('SCALE_DB_USER', 'scale'),
        'scaleDBPass': os.environ.get('SCALE_DB_PASS', 'scale'),
        'nfsPostgresUid': os.environ.get('NFS_POSTGRES_UID', '26'),
        'nfsPostgresGid': os.environ.get('NFS_POSTGRES_GID', '26'),
        'dockerImage': os.environ.get('DB_DOCKER_IMAGE', 'mdillon/postgis'),
        'dbHostVol': os.environ.get('SCALE_DB_HOST_VOL', '')
    }
    if cfg['dbHostVol'] == '':
        cfg['volumes'] = ''
    else:
        cfg['volumes'] = '{"containerPath": "/var/lib/pgsql/data","hostPath": "%(dbHostVol)s","mode": "RW"}' % cfg

    marathon = '''{"id": "/%(scaleDBHost)s",
                 "instances": 1,
                 "constraints": [["hostname","UNIQUE"]],
                 "container": {"docker": {"forcePullImage": true,
                                          "image": "%(dockerImage)s",
                                          "network": "BRIDGE",
                                          "portMappings": [{"containerPort": 5432, "hostPort": 0}],
                                          "privileged": false},
                               "type": "DOCKER",
                               "volumes": [%(volumes)s]},
                 "cpus": 2,
                 "disk": 0,
                 "env": {
                     "POSTGRES_DB": "%(scaleDBName)s",
                     "POSTGRES_USER": "%(scaleDBUser)s",
                     "POSTGRES_PASSWORD": "%(scaleDBPass)s",
                     "NFS_POSTGRES_UID": "%(nfsPostgresUid)s",
                     "NFS_POSTGRES_GID": "%(nfsPostgresGid)s"},
                 "healthChecks": [{"gracePeriodSeconds": 300,
                                   "ignoreHttp1xx": false,
                                   "intervalSeconds": 20,
                                   "maxConsecutiveFailures": 3,
                                   "portIndex": 0,
                                   "protocol": "TCP",
                                   "timeoutSeconds": 20}],
                 "labels": {},
                 "mem": 1024,
                 "ports": [5432]}''' % cfg
    r = requests.post('http://marathon.mesos:8080/v2/apps/', data=marathon)
    while json.loads(requests.get('http://marathon.mesos:8080/v2/apps/'+cfg['scaleDBHost']).text)['app']['tasksHealthy'] == 0:
        #print "Waiting for Healthy DB!"
        time.sleep(5)
    dbPort = json.loads(requests.get('http://marathon.mesos:8080/v2/apps/'+cfg['scaleDBHost']).text)['app']['tasks'][0]['ports'][0]
    os.putenv('SCALE_DB_PORT', str(dbPort))
    print(dbPort)
    exit()


if __name__ == '__main__':
    # ensure this doesn't try and run if imported
    run()
