#!/usr/bin/python
import sys, json
import beanstalkc
from subprocess import Popen
from subprocess import PIPE
from gitshell.daemon.models import EventManager, FORK_TUBE_NAME
from gitshell.settings import PRIVATE_REPO_PATH, PUBLIC_REPO_PATH, BEANSTALK_HOST, BEANSTALK_PORT

def start():
    print '==================== START ===================='
    beanstalk = beanstalkc.Connection(host=BEANSTALK_HOST, port=BEANSTALK_PORT)
    EventManager.switch(beanstalk, FORK_TUBE_NAME)
    while True:
        event_job = beanstalk.reserve()
        try:
            event = json.loads(event_job.body)
            # exit signal
            if event['type'] == -1:
                event_job.delete()
                print '==================== STOP ===================='
                sys.exit(0)
            do_event(event)
        except Exception, e:
            print 'do_event catch except, event: %s' % event_job.body
            print 'exception: %s' % e
        event_job.delete()

# git gc and file copy, nothing more
def do_event(event):
    from_repo_id = event['from_repo_id']
    to_repo_id = event['to_repo_id']
    from_repo = RepoManager.get_repo_by_id(from_repo_id)
    to_repo = RepoManager.get_repo_by_id(to_repo_id)
    if from_repo is None or to_repo is None:
        return
    from_repo_path = from_repo.get_abs_repopath()
    to_repo_path = to_repo.get_abs_repopath()
    if not os.path.exists(from_repo_path):
        print 'from_repo_path: %s is not exists, clone failed' % from_repo_path
        return
    if self.chdir(from_repo_path) is False:
        print 'chdir to from_repo_path: %s is False, clone failed' % from_repo_path
        return
    if os.path.exists(to_repo_path):
        print 'to_repo_path: %s already exists, clone failed' % to_repo_path
        return
    args = ['/usr/bin/git gc']
    popen = Popen(args, stdout=PIPE, shell=False, close_fds=True)
    result = popen.communicate()[0].strip()
    to_repo_dirname = os.path.dirname(to_repo_path)
    if not os.path.exists(to_repo_dirname):
        os.makedirs(to_repo_dirname)
    shutil.copytree(from_repo_path, to_repo_path) 
    update_repo_status(to_repo)

def update_repo_status(to_repo):
    to_repo.status = 0
    to_repo.save()

def stop():
    stop_event = {'type': -1}
    EventManager.sendevent(FORK_TUBE_NAME, json.dumps(stop_event))
    print 'send stop event message...'

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'usage: start|stop'
        sys.exit(1)
    action = sys.argv[1]
    if action == 'start':
        start()
    elif action == 'stop':
        stop()
