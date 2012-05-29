#!/usr/bin/python

import redis
from gitshell import settings


FEED_TYPE = {
    'REPOS' = 'r:'
    'USER' = 'u:'
    'WATCH_USER' = 'wu:'
    'WATCH_REPOS' = 'wr:'
    'COMM' = 'c:'
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
    def put_repos_feed(self, repos_id, timestamp, feed_id):
        pass

    def put_user_feed(self, user_id, timestamp, feed_id):
        pass

    def add_watch_user(self, user_id, timestamp, watch_user_id):
        pass

    def remove_watch_user(self, user_id, timestamp, watch_user_id):
        pass

    def add_watch_repos(self, user_id, timestamp, watch_repos_id):
        pass

    def remove_watch_repos(self, user_id, timestamp, watch_repos_id):
        pass

    def add_comm_feed(self, user_id, timestamp, feed_id):
        pass

    def remove_comm_feed(self, user_id, timestamp, feed_id):
        pass

    """ all get method """
    def get_repos_feed(self, repos_id, start, num_items):
        pass

    def get_user_feed(self, user_id, start, num_items):
        pass

    def get_watch_user(self, user_id, start, num_items)
        pass

    def get_watch_repos(self, user_id, start, num_items)
        pass

    def get_comm_feed(self, user_id, start, num_items)
        pass


