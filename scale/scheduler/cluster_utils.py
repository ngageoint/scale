import logging

logger = logging.getLogger(__name__)

try:
    from kazoo.client import KazooClient
    from kazoo.recipe.election import Election
    from urlparse import urlparse

    def wait_for_leader(zk_url, my_id, func, *args, **kargs):
        logger.info("Identifying scale scheduler leader")
        url = urlparse(zk_url)
        if url.scheme != 'zk':
            raise ValueError('Invalid zookeeper url: %s' % zk_url)
        path = "%s/election" % url.path
        zk = KazooClient(url.netloc)
        zk.start()
        election = Election(zk, path, my_id)
        election.run(func, *args, **kargs)

except ImportError:
    logger.warning("Zookeeper client not available, only single node operation is supported")

    def wait_for_leader(zk_url, my_id, func, *args, **kargs):
        func(*args, **kargs)

