#!/usr/bin/python
import os, threading, shutil, sys, json, time
import beanstalkc
from datetime import datetime
from subprocess import Popen, PIPE
from gitshell.repo.models import RepoManager
from gitshell.gsuser.models import GsuserManager
from gitshell.daemon.models import EventManager, IMPORT_REPO_TUBE_NAME
from gitshell.settings import GIT_BARE_REPO_PATH, BEANSTALK_HOST, BEANSTALK_PORT, logger
from gitshell.objectscache.da import da_post_save
from django.db.models.signals import post_save, post_delete

STOP_FILE_FLAG = '/tmp/notifworker.exit.flag'
TIME_NEVER_COME = datetime(9999, 1, 1, 1, 1)
ROW_COUNT = 5000

def start():
    logger.info('==================== START notifworker ====================')
    while True:
        expect_notif_time = datetime.now()
        if os.path.exists(STOP_FILE_FLAG):
            break
        for i in range(0, 1000):
            notifSettings = FeedManager.list_notifsetting_by_expectNotifTime(expect_notif_time, ROW_COUNT*i, ROW_COUNT)
            if len(notifSettings) < ROW_COUNT:
                break
            for notifSetting in notifSettings:
                notifMessages = FeedManager.list_notifmessage_by_userId_notifTypes(notifSetting.user_id, notifSetting.notif_types, 0, 1000)
                send_notifMessages(notifMessages, notifSetting)
                notifSetting.last_notif_time = expect_notif_time
                notifSetting.expect_notif_time = TIME_NEVER_COME
                notifSetting.save()
        now = int(time.time())
        next_minute_left = 60 - now%60
        if next_minute_left == 0:
            next_minute_left = 1
        time.sleep(next_minute_left)
        
    logger.info('==================== STOP notifworker ====================')

def send_notifMessages(notifMessages, notifSetting):
    email = notifSetting.email
    pass

def stop():
    open(STOP_FILE_FLAG, 'a').close()

def __cache_version_update(sender, **kwargs):
    da_post_save(kwargs['instance'])

if __name__ == '__main__':
    post_save.connect(__cache_version_update)
    post_delete.connect(__cache_version_update)
    if len(sys.argv) < 2:
        print 'usage: start|stop'
        sys.exit(1)
    action = sys.argv[1]
    if action == 'start':
        start()
    elif action == 'stop':
        stop()
    else:
        print 'usage: start|stop'
        sys.exit(1)


