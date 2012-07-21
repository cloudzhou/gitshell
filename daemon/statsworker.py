#!/usr/bin/python
import json
import beanstalkc

def main():
    beanstalk = beanstalkc.Connection(host='localhost', port=11300)
    beanstalk.use('stats_event')
    exit_flag = False
    while not exit_flag:
        event_job = beanstalk.reserve()
        try:
            do_stats_event(event_job.body)
        except Exception, e:
            print 'do_event catch except, event: %s' % event_job.body
            print 'exception: %s' % e
        event_job.delete()

def do_event(event_job):
    pass

if __name__ == '__main__':
    main()
