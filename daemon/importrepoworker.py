#!/usr/bin/python
import os, threading
import shutil
import sys, json
import beanstalkc
from subprocess import Popen
from subprocess import PIPE
from gitshell.repo.models import RepoManager
from gitshell.gsuser.models import GsuserManager
from gitshell.daemon.models import EventManager, IMPORT_REPO_TUBE_NAME
from gitshell.settings import GIT_BARE_REPO_PATH, BEANSTALK_HOST, BEANSTALK_PORT
from django.db.models.signals import post_save
from gitshell.objectscache.da import da_post_save

TOTAL_THREAD_COUNT = 10

def start():
    print '==================== START ===================='
    import_repo_threads = []
    for i in range(0, TOTAL_THREAD_COUNT):
        import_repo_threads.append(ImportRepoThread())
    for import_repo_thread in import_repo_threads:
        import_repo_thread.start()
    for import_repo_thread in import_repo_threads:
        import_repo_thread.join()
    print '==================== STOP ===================='

def stop():
    for i in range(0, TOTAL_THREAD_COUNT):
        EventManager.send_stop_event(IMPORT_REPO_TUBE_NAME)
    print 'send stop event message...'

class ImportRepoThread(threading.Thread):

    def run(self):
        beanstalk = beanstalkc.Connection(host=BEANSTALK_HOST, port=BEANSTALK_PORT)
        EventManager.switch(beanstalk, IMPORT_REPO_TUBE_NAME)
        while True:
            event_job = beanstalk.reserve()
            try:
                event = json.loads(event_job.body)
                print event
                # exit signal
                if event['type'] == -1:
                    event_job.delete()
                    sys.exit(0)
                self._do_event(event)
            except Exception, e:
                print 'do_event catch except, event: %s' % event_job.body
                print 'exception: %s' % e
            event_job.delete()

    # import from remote git url, like github
    def _do_event(self, event):
        username = event['username']
        reponame = event['reponame']
        remote_git_url = event['remote_git_url']
        local_user = GsuserManager.get_user_by_name(username)
        local_repo = RepoManager.get_repo_by_name(username, reponame)
        if local_user is None or local_repo is None or local_repo.status == 0:
            return
        local_repo_path = local_repo.get_abs_repopath()
        if os.path.exists(local_repo_path):
            return
        args = ['/bin/bash', '/opt/bin/git-import-remote-repo.sh'] + [local_repo_path, remote_git_url]
        try:
            popen = Popen(args, stdout=PIPE, shell=False, close_fds=True)
            output = popen.communicate()[0].strip()
            returncode = popen.returncode
            if returncode == 0:
                RepoManager.check_export_ok_file(local_repo)
                diff_size = long(output)
                RepoManager.update_user_repo_quote(local_user, local_repo, diff_size)
                local_repo.status = 0
                local_repo.save()
            else:
                local_repo.status = 500
                local_repo.save()
        except Exception, e:
            local_repo.status = 500
            local_repo.save()
            print e
        RepoManager.check_export_ok_file(local_repo)
    
def __cache_version_update(sender, **kwargs):
    da_post_save(kwargs['instance'])

if __name__ == '__main__':
    post_save.connect(__cache_version_update)
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

