#!/usr/bin/python

import redis
from gitshell import settings


FEED_TYPE = {
    """ feed, sorted sets """
    'REPOS' : 'r',
    'USER' : 'u',
    'WATCH_USER' : 'wu',
    'BEWATCH_USER' : 'bwu',
    'WATCH_REPOS' : 'wr',
    'COMM' : 'c',
    """ random identify hashes keys r, u, wu, bwu, wr, c """
    'IDENTIFY_CHECK' : 'ic',
}

""" all method about feed and redis """
class FeedAction():
    """ feed aciton by redis """
    def __init__(self):
        self.redis = redis.Redis(
            host = settings.REDIS_HOST,
            port = settings.REDIS_PORT,
            socket_timeout = settings.REDIS_SOCKET_TIMEOUT
        )

    """ all modify method """
    def add_repos_feed(self, repos_id, timestamp, feed_id):
        madd_repos_feed(repos_id, -timestamp, feed_id)

    def add_user_feed(self, user_id, timestamp, feed_id):
        madd_user_feed(user_id, -timestamp, feed_id)

    def madd_repos_feed(self, repos_id, *args, **kwargs):
        key = '%s:%s' % (FEED_TYPE['REPOS'], repos_id)
        self.redis.zadd(key, args, kwargs)
        self.redis.zremrangebyrank(key, 100, 200)

    def madd_user_feed(self, user_id, *args, **kwargs):
        key = '%s:%s' % (FEED_TYPE['USER'], user_id)
        self.redis.zadd(key, args, kwargs)
        self.redis.zremrangebyrank(key, 100, 200)

    def add_watch_user(self, user_id, timestamp, watch_user_id):
        key = '%s:%s' % (FEED_TYPE['WATCH_USER'], user_id)
        self.redis.zadd(key, -timestamp, watch_user_id)
        self.redis.zremrangebyrank(key, 100, 200)

    def remove_watch_user(self, user_id, watch_user_id):
        key = '%s:%s' % (FEED_TYPE['WATCH_USER'], user_id)
        self.redis.zrem(key, watch_user_id)

    def add_bewatch_user(self, user_id, timestamp, bewatch_user_id):
        key = '%s:%s' % (FEED_TYPE['BEWATCH_USER'], user_id)
        self.redis.zadd(key, -timestamp, bewatch_user_id)
        self.redis.zremrangebyrank(key, 100, 200)

    def remove_bewatch_user(self, user_id, bewatch_user_id):
        key = '%s:%s' % (FEED_TYPE['BEWATCH_USER'], user_id)
        self.redis.zrem(key, bewatch_user_id)

    def add_watch_repos(self, user_id, timestamp, watch_repos_id):
        key = '%s:%s' % (FEED_TYPE['WATCH_REPOS'], user_id)
        self.redis.zadd(key, -timestamp, watch_repos_id)
        self.redis.zremrangebyrank(key, 100, 200)

    def remove_watch_repos(self, user_id, watch_repos_id):
        key = '%s:%s' % (FEED_TYPE['WATCH_REPOS'], user_id)
        self.redis.zrem(key, watch_repos_id)

    def add_comm_feed(self, user_id, timestamp, feed_id):
        key = '%s:%s' % (FEED_TYPE['COMM'], user_id)
        self.redis.zadd(key, -timestamp, feed_id)
        self.redis.zremrangebyrank(key, 100, 200)

    def remove_comm_feed(self, user_id, feed_id):
        key = '%s:%s' % (FEED_TYPE['COMM'], user_id)
        self.redis.zrem(key, feed_id)

    """ all get method """
    def get_repos_feed(self, repos_id, start, num_items):
        key = '%s:%s' % (FEED_TYPE['REPOS'], repos_id)
        self.redis.zrange(key, 0, 100)

    def get_user_feed(self, user_id, start, num_items):
        key = '%s:%s' % (FEED_TYPE['USER'], user_id)
        self.redis.zrange(key, 0, 100)

    def get_watch_user(self, user_id, start, num_items)
        key = '%s:%s' % (FEED_TYPE['WATCH_USER'], user_id)
        self.redis.zrange(key, 0, 100)

    def get_bewatch_user(self, user_id, start, num_items)
        key = '%s:%s' % (FEED_TYPE['BEWATCH_USER'], user_id)
        self.redis.zrange(key, 0, 100)

    def get_watch_repos(self, user_id, start, num_items)
        key = '%s:%s' % (FEED_TYPE['WATCH_REPOS'], user_id)
        self.redis.zrange(key, 0, 100)

    def get_comm_feed(self, user_id, start, num_items)
        key = '%s:%s' % (FEED_TYPE['COMM'], user_id)
        self.redis.zrange(key, 0, 100)

