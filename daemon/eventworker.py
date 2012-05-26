#!/usr/bin/python
import os, sys
import json
import beanstalkc
from subprocess import Popen
from subprocess import PIPE

def main():
    beanstalk = beanstalkc.Connection(host='localhost', port=11300)
    #beanstalk.use('high_priority')
    exit_flag = False
    while not exit_flag:
        event_job = beanstalk.reserve()
        do_event(event_job.body)
        print event_job.body
        event_job.delete()

def do_event(event_job):
    event = json.loads(event_job)
    etype = event['type']
    diff_tree_blob_size_params = []
    if etype == 0:
        abspath = event['abspath']
        rev_ref_arr = event['revrefarr']
        for rev_ref in rev_ref_arr:    
            if len(rev_ref) < 3:
                continue
            oldrev = rev_ref[0]
            newrev = rev_ref[1]
            refname = rev_ref[2]
            diff_tree_blob_size_params.extend(rev_ref)
            if refname == 'refs/heads/master': 
                update_commits(oldrev, newrev, refname)
        update_quote(abspath, diff_tree_blob_size_params)
        return
    if etype == 1:
        return
    if etype == 2:
        return

def update_quote(abspath, parameters):
    args = ['/opt/run/bin/diff-tree-blob-size.sh', abspath]
    args.extend(parameters)
    print args
    result = Popen(args, stdout=PIPE, close_fds=True).communicate()[0]
    print result

def update_commits(oldrev, newrev, refname):
    pass

if __name__ == '__main__':
    main()
