#!/usr/bin/python
import json
import beanstalkc
from subprocess import Popen
from subprocess import PIPE

def main():
    beanstalk = beanstalkc.Connection(host='localhost', port=11300)
    beanstalk.use('clone_event')
    while True:
        event_job = beanstalk.reserve()
        try:
            do_stats_event(event_job.body)
        except Exception, e:
            print 'do_event catch except, event: %s' % event_job.body
            print 'exception: %s' % e
        event_job.delete()

# git gc and file copy, nothing more
def do_event(event_job):
    event = json.loads(event_job)
    from_repo_path = event['from_repo_path']
    to_repo_path = event['to_repo_path']
    to_repo_id = event['to_repo_id']
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

def update_repo_status(to_repo_id):
    pass

if __name__ == '__main__':
    main()
