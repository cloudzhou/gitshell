#!/usr/bin/python
import os, shutil, sys, json
import random, re, json, time
import httplib, urllib, hashlib
from datetime import datetime
import base64, hashlib, urlparse
from subprocess import Popen
from subprocess import PIPE

SECRET_KEY = ''
REMOTE_HOST = 'gitshell.com'
REMOTE_PORT = 443

def start():
    print '==================== START ===================='
    gitshell_connection = None
    try:
        gitshell_connection = httplib.HTTPSConnection(REMOTE_HOST, REMOTE_PORT, timeout=10)
        headers = {'Accept': 'application/json'}
        gitshell_connection.request('GET', '/gitshell/list_latest_push_repo/1y/?secret_key='+SECRET_KEY, '', headers)
        response = gitshell_connection.getresponse()
        if response.status == 200:
            json_str = response.read()
            repos = json.loads(json_str)
            for repo in repos:
                do_repo(repo)
    except Exception, e:
        print 'exception: %s' % e
    finally:
        if gitshell_connection: gitshell_connection.close()
    print '==================== END ===================='

def do_repo(repo):
    id = repo['id']
    username = repo['username']
    name = repo['name']
    dropbox_sync = repo['dropbox_sync']
    visibly = repo['visibly']
    args = ['/bin/bash', '/opt/bin/dropbox_sync_repo.sh', id, username, name, dropbox_sync, visibly]
    popen = Popen(args, stdout=PIPE, shell=False, close_fds=True)
    result = popen.communicate()[0].strip()

if __name__ == '__main__':
    start()


