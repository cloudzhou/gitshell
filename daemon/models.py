from django.db import models
import json, beanstalkc
from gitshell.objectscache.models import BaseModel
from gitshell.settings import BEANSTALK_HOST, BEANSTALK_PORT

EVENT_TUBE_NAME = 'commit_event'
FORK_TUBE_NAME = 'fork_event'
IMPORT_REPO_TUBE_NAME = 'import_repo_event'

class EventManager():

    @classmethod
    def sendevent(self, tube, event):
        beanstalk = beanstalkc.Connection(host=BEANSTALK_HOST, port=BEANSTALK_PORT)
        self.switch(beanstalk, tube)
        beanstalk.put(str(event))

    @classmethod
    def send_stop_event(self, tube):
        stop_event = {'type': -1}
        self.sendevent(tube, json.dumps(stop_event))

    @classmethod
    def switch(self, beanstalk, tube):
        beanstalk.use(tube)
        beanstalk.watch(tube)
        beanstalk.ignore('default')

    # ======== send event ========
    @classmethod
    def send_fork_event(self, from_repo_id, to_repo_id):
        fork_event = {'type': 0, 'from_repo_id': from_repo_id, 'to_repo_id': to_repo_id}
        self.sendevent(FORK_TUBE_NAME, json.dumps(fork_event))

    @classmethod
    def send_import_repo_event(self, username, reponame, remote_git_url, remote_username, remote_password):
        import_repo_event = {'type': 0, 'username': username, 'reponame': reponame, 'remote_git_url': remote_git_url, 'remote_username': remote_username, 'remote_password': remote_password}
        self.sendevent(IMPORT_REPO_TUBE_NAME, json.dumps(import_repo_event))

