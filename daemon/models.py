from django.db import models
import json, beanstalkc
from gitshell.objectscache.models import BaseModel
from gitshell.settings import BEANSTALK_HOST, BEANSTALK_PORT

EVENT_TUBE_NAME = 'commit_event'
FORK_TUBE_NAME = 'fork_event'

class EventManager():

    @classmethod
    def send_fork_event(self, from_repo_id, to_repo_id):
        fork_event = {'type': 0, 'from_repo_id': from_repo_id, 'to_repo_id': to_repo_id}
        EventManager.sendevent(FORK_TUBE_NAME, json.dumps(fork_event))

    @classmethod
    def sendevent(self, tube, event):
        beanstalk = beanstalkc.Connection(host=BEANSTALK_HOST, port=BEANSTALK_PORT)
        self.switch(beanstalk, tube)
        beanstalk.put(event) 

    @classmethod
    def switch(self, beanstalk, tube):
        beanstalk.use(tube)
        beanstalk.watch(tube)
        beanstalk.ignore('default')
