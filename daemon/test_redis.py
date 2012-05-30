#!/usr/bin/python

import redis
import random

def main():
    feed_redis = redis.Redis('localhost', 6379, 3)
    for i in range(0, 1000):
        for ftype in ['r', 'u', 'wu', 'bwu', 'wr', 'c']:
            key = '%s:%s' % (ftype, i + 10000) 
            for j in range(0, 100):
                value = random.randint(0, 1000000)
                feed_redis.zadd(key, value, value+1)

if __name__ == '__main__':
    main()
