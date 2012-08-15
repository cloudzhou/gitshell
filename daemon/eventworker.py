#!/usr/bin/python
import re, time
import os, sys
import json
import beanstalkc
from subprocess import Popen
from subprocess import PIPE
from datetime import datetime
from django.contrib.auth.models import User
from gitshell.gsuser.models import Userprofile, GsuserManager
from gitshell.repo.models import CommitHistory, Repo, RepoManager
from gitshell.feed.feed import FeedAction
from gitshell.daemon.models import EventManager, EVENT_TUBE_NAME
from gitshell.settings import PRIVATE_REPO_PATH, PUBLIC_REPO_PATH, BEANSTALK_HOST, BEANSTALK_PORT

MAX_COMMIT_COUNT = 100
def start():
    print '==================== START ===================='
    beanstalk = beanstalkc.Connection(host=BEANSTALK_HOST, port=BEANSTALK_PORT)
    EventManager.switch(beanstalk, EVENT_TUBE_NAME)
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

# abspath is the repo hooks directory
def do_event(event):
    etype = event['type']
    diff_tree_blob_size_params = []
    if etype == 0:
        abspath = event['abspath'].strip()
        if abspath.endswith('/'):
            abspath = abspath[0 : len(abspath)-1]
        (username, reponame) = get_username_reponame(abspath)
        if reponame.endswith('.git'):
            reponame = reponame[0 : len(reponame)-4]
        if username == '' or reponame == '':
            return
        user = get_user(username)
        gsuser = get_gsuser(user)
        repo = get_repo(user, reponame)
        repopath = get_repopath(user, repo)
        if user is None or gsuser is None or repo is None or repopath is None or not os.path.exists(repopath):
            return
        rev_ref_arr = event['revrefarr']
        commit_count = 0
        for rev_ref in rev_ref_arr:    
            if len(rev_ref) < 3:
                continue
            oldrev = rev_ref[0]
            newrev = rev_ref[1]
            refname = rev_ref[2]
            diff_tree_blob_size_params.extend(rev_ref)
            commit_count = bulk_create_commits(user, gsuser, repo, repopath, oldrev, newrev, refname) + commit_count
            if commit_count > MAX_COMMIT_COUNT:
                break
        update_quote(user, gsuser, repo, repopath, diff_tree_blob_size_params)
        return
    if etype == 1:
        return
    if etype == 2:
        return

def update_quote(user, gsuser, repo, repopath, parameters):
    args = ['/opt/run/bin/diff-tree-blob-size.sh', repopath]
    args.extend(parameters)
    popen = Popen(args, stdout=PIPE, shell=False, close_fds=True)
    result = popen.communicate()[0].strip()
    diff_size = 0
    if popen.returncode == 0:
        if result.startswith('+') or result.startswith('-'):
            diff_size = int(result)
        else:
            diff_size = int(result) - repo.used_quote
    update_gsuser_repo_quote(gsuser, repo, diff_size)

# git log -100 --pretty='%h  %p  %t  %an  %cn  %ct  %s'
def bulk_create_commits(user, gsuser, repo, repopath, oldrev, newrev, refname):
    args = ['/opt/run/bin/git-pretty-log.sh', repopath, oldrev, newrev]
    popen = Popen(args, stdout=PIPE, shell=False, close_fds=True)
    result = popen.communicate()[0].strip()
    raw_commitHistorys = []
    if popen.returncode == 0:
        for line in result.split('\n'):
            items = line.split('  ', 6)
            if len(items) >= 6 and re.match('^\d+$', items[5]):
                committer_date = datetime.fromtimestamp(int(items[5])) 
                author_name = items[3][0:30]
                committer_name = items[4][0:30]
                commitHistory = CommitHistory.create(repo.id, repo.name, items[0], items[1][0:24], items[2], author_name, committer_name, committer_date, items[6][0:512], refname[0:32])
                raw_commitHistorys.append(commitHistory)
    length = len(raw_commitHistorys)
    commit_ids = [commitHistory.commit_id for x in raw_commitHistorys]
    exists_commitHistorys = RepoManager.list_commits_by_commit_ids(repo.id, commit_ids)
    exists_commit_ids_set = set([x.commit_id for x in exists_commitHistorys])
    commitHistorys = []
    for commitHistory in raw_commitHistorys:
        if commitHistory.commit_id not in exists_commit_ids_set:
            commitHistory.save()
            commitHistorys.append(commitHistory)
    # TODO commiter and author Map list_member
    # feed action
    feedAction = FeedAction()
    feed_key_values = []
    for commitHistory in commitHistorys:
        feed_key_values.append(-float(time.mktime(commitHistory.committer_date.timetuple())))
        feed_key_values.append(commitHistory.id)
    # total private repo the feed is private
    if repo.auth_type == 2:
        feedAction.madd_pri_user_feed(user.id, feed_key_values)
    else:
        feedAction.madd_pub_user_feed(user.id, feed_key_values)
    feedAction.madd_repo_feed(repo.id, feed_key_values)

    # stats action
    __stats(commitHistorys)
    
    return length

def __stats(commitHistorys):
    pass

def get_username_reponame(abspath):
    rfirst_slash_idx = abspath.rfind('/')
    rsecond_slash_idx = abspath.rfind('/', 0, rfirst_slash_idx)
    rthird_slash_idx = abspath.rfind('/', 0, rsecond_slash_idx)
    if rthird_slash_idx > 0 and rthird_slash_idx < rsecond_slash_idx and rsecond_slash_idx < rfirst_slash_idx:
        return (abspath[rthird_slash_idx+1 : rsecond_slash_idx], abspath[rsecond_slash_idx+1 : rfirst_slash_idx])
    return ('', '')

def get_user(username):
    return GsuserManager.get_user_by_name(username)

def get_gsuser(user):
    if user is None:
        return None
    return GsuserManager.get_userprofile_by_id(user.id)

def get_repo(user, reponame):  
    if user is None:
        return None
    return RepoManager.get_repo_by_userId_name(user.id, reponame)

def get_repopath(user, repo):
    if user is None or repo is None:
        return None
    return repo.get_abs_repopath(user.username)

def update_gsuser_repo_quote(gsuser, repo, diff_size):
    gsuser.used_quote = gsuser.used_quote + diff_size
    repo.used_quote = repo.used_quote + diff_size
    gsuser.save()
    repo.save()

def stop():
    EventManager.send_stop_event(EVENT_TUBE_NAME)
    print 'send stop event message...'

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(1)
    action = sys.argv[1]
    if action == 'start':
        start()
    elif action == 'stop':
        stop()
