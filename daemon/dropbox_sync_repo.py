#!/usr/bin/python
import os, shutil, sys, json
import random, re, json, time
import httplib, urllib, hashlib
from datetime import datetime
import base64, hashlib, urlparse
from subprocess import Popen
from subprocess import PIPE
from gitshell.settings import logger

SECRET_KEY = 'git424953shell'
REMOTE_HOST = 'gitshell.com'
REMOTE_PORT = 443

def start():
    logger.info('==================== START dropbox_sync_repo ====================')
    gitshell_connection = None
    try:
        gitshell_connection = httplib.HTTPSConnection(REMOTE_HOST, REMOTE_PORT, timeout=10)
        headers = {'Accept': 'application/json'}
        gitshell_connection.request('GET', '/gitshell/list_latest_push_repo/2M/?secret_key='+SECRET_KEY, '', headers)
        response = gitshell_connection.getresponse()
        if response.status == 200:
            json_str = response.read()
            json_response = json.loads(json_str)
            result = json_response['result']
            repos = json_response['latest_push_repos']
            if result == 'success':
                for repo in repos:
                    do_repo(repo)
    except Exception, e:
        logger.exception(e)
    finally:
        if gitshell_connection: gitshell_connection.close()
    logger.info('==================== END dropbox_sync_repo ====================')

def do_repo(repo):
    id = str(repo['id'])
    username = repo['username']
    name = repo['name']
    dropbox_sync = str(repo['dropbox_sync'])
    visibly = str(repo['visibly'])
    args = ['/bin/bash', '/opt/bin/dropbox_sync_repo.sh', id, username, name, dropbox_sync, visibly]
    popen = Popen(args, stdout=PIPE, shell=False, close_fds=True)
    result = popen.communicate()[0].strip()

if __name__ == '__main__':
    start()


