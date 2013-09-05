# -*- coding: utf-8 -*-  
import os, threading, shutil, sys, json, time
import beanstalkc
from datetime import datetime
from subprocess import Popen, PIPE
from gitshell.repo.models import RepoManager
from gitshell.gsuser.models import GsuserManager
from gitshell.daemon.models import EventManager, IMPORT_REPO_TUBE_NAME
from gitshell.settings import GIT_BARE_REPO_PATH, BEANSTALK_HOST, BEANSTALK_PORT, logger
from gitshell.objectscache.da import da_post_save
from gitshell.feed.models import FeedManager
from gitshell.feed.mailUtils import Mailer
from django.db.models.signals import post_save, post_delete

STOP_FILE_FLAG = '/tmp/notifworker.exit.flag'
TIME_NEVER_COME = datetime(9999, 1, 1, 1, 1)
ROW_COUNT = 5000

def start():
    logger.info('==================== START notifworker ====================')
    while True:
        expect_notif_time = datetime.now()
        #print expect_notif_time
        if os.path.exists(STOP_FILE_FLAG):
            os.remove(STOP_FILE_FLAG)
            break
        for i in range(0, 1000):
            notifSettings = FeedManager.list_notifsetting_by_expectNotifTime(expect_notif_time, ROW_COUNT*i, ROW_COUNT)
            #print len(notifSettings)
            for notifSetting in notifSettings:
                #print notifSetting.id
                from_time = notifSetting.last_notif_time
                to_time = expect_notif_time
                #print from_time, to_time
                if from_time >= to_time:
                    notifSetting.expect_notif_time = TIME_NEVER_COME
                    notifSetting.save()
                    continue
                notifMessages = FeedManager.list_notifmessage_by_userId_betweenTime_notifTypes(notifSetting.user_id, from_time, to_time, notifSetting.notif_types, 0, 1000)
                #print len(notifMessages)
                _send_notifMessages(notifMessages, notifSetting)
                notifSetting.last_notif_time = expect_notif_time
                notifSetting.expect_notif_time = TIME_NEVER_COME
                notifSetting.save()
            if len(notifSettings) < ROW_COUNT:
                break
        now = int(time.time())
        next_minute_left = 60 - now%60
        if next_minute_left == 0:
            next_minute_left = 60
        #print next_minute_left
        time.sleep(next_minute_left)
        
    logger.info('==================== STOP notifworker ====================')

def _send_notifMessages(notifMessages, notifSetting):
    userprofile = GsuserManager.get_userprofile_by_id(notifSetting.user_id)
    header = u'来自Gitshell的 %s 个通知' % len(notifMessages)
    html = FeedManager.render_notifMessages_as_html(userprofile, header, notifMessages)
    Mailer().send_html_mail(header, html, None, [notifSetting.email])

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


