from nydus.db import create_cluster
from nydus.contrib.ketama import Ketama
from nydus.db.routers import RoundRobinRouter, routing_params

from invenio.config import CFG_REDIS_HOSTS

_REDIS_CONN = {}


def get_redis(dbhost=None):
    """Connects to a redis using nydus

    We simlulate a redis cluster by connecting to several redis servers
    in the background and using a consistent hashing ring to choose which
    server stores the data.
    Returns a redis object that can be used like a regular redis object
    see http://redis.io/
    """
    key = dbhost
    if dbhost is None:
        dbhost = CFG_REDIS_HOSTS

    redis = _REDIS_CONN.get(key, None)
    if redis:
        return redis

    hosts_dict = {}
    for server_num, server_info in enumerate(CFG_REDIS_HOSTS):
        hosts_dict[server_num] = server_info

    redis = create_cluster({
        'backend': 'nydus.db.backends.redis.Redis',
        'router': 'invenio.redisutils.FailoverConsistentHashingRouter',
        'hosts': hosts_dict
    })
    _REDIS_CONN[key] = redis
    return redis


def get_key(args, kwargs):
    if 'key' in kwargs:
        return kwargs['key']
    elif args:
        return args[0]
    return None


class FailoverConsistentHashingRouter(RoundRobinRouter, object):
    """
    Router that returns host number based on a consistent hashing algorithm.
    The consistent hashing algorithm only works if a key argument is provided.

    If a key is not provided, then all hosts are returned.

    The first argument is assumed to be the ``key`` for routing. Keyword arguments
    are not supported.
    """

    def __init__(self, *args, **kwargs):
        self._db_num_id_map = {}
        self._down_nodes = set()
        self._copies = kwargs.get('copies', 2)
        # Filled in _setup_router
        self._ring = None
        super(FailoverConsistentHashingRouter, self).__init__(*args, **kwargs)

    def mark_connection_down(self, db_num):
        print 'marking %s as down' % db_num
        db_num = self.ensure_db_num(db_num)
        self._down_nodes.add(db_num)

        super(FailoverConsistentHashingRouter, self).mark_connection_down(db_num)

    def mark_connection_up(self, db_num):
        print 'marking %s as up' % db_num
        db_num = self.ensure_db_num(db_num)
        self._down_nodes.remove(db_num)

        super(FailoverConsistentHashingRouter, self).mark_connection_up(db_num)

    @routing_params
    def _setup_router(self, args, kwargs, **fkwargs):  # callback pylint: disable=W0613
        self._db_num_id_map = dict([(db_num, host.identifier) for db_num, host in self.cluster.hosts.iteritems()])
        self._ring = HashRing([str(i) for i in self._db_num_id_map.keys()])

        return True

    @routing_params
    def _pre_routing(self, *args, **kwargs):
        self.check_down_connections()
        return super(FailoverConsistentHashingRouter, self)._pre_routing(*args, **kwargs)

    @routing_params
    def _route(self, attr, args, kwargs, **fkwargs):  # callback pylint: disable=W0613
        """
        The first argument is assumed to be the ``key`` for routing.
        """
        key = get_key(args, kwargs)

        found = [int(node) for node in self._ring.get_multiple_nodes(key, self._copies)]
        found = [node for node in found if node not in self._down_nodes]

        print 'found', repr(found)
        if not found:
            raise self.HostListExhausted()

        return list(found)


class HashRing(Ketama):

    def get_multiple_nodes(self, key, num):
        assert num <= len(self._nodes), "Too many nodes requested"
        step = max(len(self._sorted_keys) / num, 1)
        l = len(self._sorted_keys)
        nodes = set()
        pos = self._get_node_pos(key)

        for i in xrange(num):
            for dummy in self._sorted_keys:
                node = self._hashring[self._sorted_keys[pos % l]]
                # New node found
                if node not in nodes:
                    nodes.add(node)
                    break
                pos += 1

            pos += (i * step)

        return nodes
