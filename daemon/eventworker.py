#!/usr/bin/python
import os, sys
import json
import beanstalkc

def main():
    beanstalk = beanstalkc.Connection(host='localhost', port=11300)
    beanstalk.use('high_priority')
    exit_flag = False
    while not exit_flag:
        event_job = beanstalk.reserve()
        do_event(event_job.body)
        event_job.delete()

def do_event(event_job):
    event = json.loads(event_job)
    etype = event['type']
    if etype == 0:
        abspath = event['abspath']
        rev_ref_arr = event['revrefarr']
        for rev_ref in rev_ref_arr:    
            if len(rev_ref) < 3:
                continue
            oldrev = rev_ref[0]
            newrev = rev_ref[1]
            refname = rev_ref[2]
            update_quote(oldrev, newrev, refname)
            if refname == 'refs/heads/master': 
                update_commits(oldrev, newrev, refname)
        return
    if etype == 1:
        return
    if etype == 2:
        return

def update_quote(oldrev, newrev, refname)
    pass

def update_commits(oldrev, newrev, refname)
    pass

if __name__ == '__main__':
    main()
