'''Defines the MetricsProcessor for tracking various usage metrics'''
import logging

from django.conf import settings
import json
from node.models import Node
import os.path
import subprocess
import threading
import urllib2


#logger = logging.getLogger(__name__)
logger = logging


class MetricsProcessor(object):
    '''This class queries and stores memory, cpu, etc. metrics tracking and trending.
    '''

    def create_metrics_file(self, filename):
        '''Create an empty rrd file with the proper metrics defined

        :param filename: The full path to the filename to create
        :type filename: str
        '''
        subprocess.call(["rrdtool", "create", filename, "--step", "60",
                                "DS:mesosMemUsed:GAUGE:120:0:U",
                                "DS:mesosSystemMemFree:GAUGE:120:0:U",
                                "RRA:AVERAGE:0.5:5:100",
                                "RRA:AVERAGE:0.5:60:720",
                                "RRA:MAX:0.5:5:100",
                                "RRA:MAX:0.5:50:720",
                                "RRA:MIN:0.5:5:100",
                                "RRA:MIN:0.5:50:720"])

    def query_metrics(self):
        '''Queries the various metrics save the stats for historical tracking
        '''
        logger.info("Querying metrics")
        nodes = Node.objects.values('hostname', 'port')
        threads = []
        for node in nodes:
            logger.info("Query %s" % node['hostname'])
            t = threading.Thread(target=self._process_node, args=(node,))
            t.daemon = True
            threads.append(t)
            logger.info('Start thread')
            t.start()
        for t in threads:
            t.join()
        logger.info('Finished query')

    def _process_node(self, node):
        try:
            node_stats = self._get_mesos_data(node['hostname'], node['port'])
            pth = os.path.join(settings.METRICS_DIR, node['hostname'].split('.')[0] + ".rrd")
            if not os.path.exists(pth):
                self.create_metrics_file(pth)
            logger.info("Write log data to %s" % pth)
            self._rrd_update(pth, node_stats)
        except Exception, e:
            # don't kill processing of other nodes if any error occurs
            logger.exception(e)

    def _get_mesos_data(self, hostname, port):
        tmp = urllib2.urlopen("http://%s:%s/slave(1)/stats.json" % (hostname, port))
        tmp = json.loads(tmp.read())
        logger.info(str(tmp))
        stats = {
                 "mesosMemUsed": str(tmp["slave/mem_used"]),
                 "mesosSystemMemFree": str(tmp["system/mem_free_bytes"])
                 }
        return stats

    def _rrd_update(self, filename, data):
        if not os.path.exists(filename):
            raise IOError('No such file or directory: %s' % filename)
        subprocess.call(["rrdtool", "update", filename, "-t"] +
                         [":".join(data.keys())] +
                         ["N:" + ":".join(data.values())])
