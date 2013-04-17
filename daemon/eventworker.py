#!/usr/bin/python
import re, time
import os, sys
import json
import beanstalkc
from subprocess import Popen
from subprocess import PIPE
from datetime import datetime
from django.core.cache import cache
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from gitshell.gsuser.models import Userprofile, GsuserManager
from gitshell.repo.models import CommitHistory, Repo, RepoManager
from gitshell.feed.models import Feed, NotifMessage, FeedManager
from gitshell.feed.feed import FeedAction
from gitshell.stats.models import StatsManager
from gitshell.objectscache.models import CacheKey
from gitshell.daemon.models import EventManager, EVENT_TUBE_NAME
from gitshell.settings import REPO_PATH, BEANSTALK_HOST, BEANSTALK_PORT
from gitshell.objectscache.da import da_post_save

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
        __clear_relative_cache(user, gsuser, repo)
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
        repo.commit = repo.commit + commit_count
        update_quote(user, gsuser, repo, repopath, diff_tree_blob_size_params)
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

# git log -100 --pretty='%h  %p  %t  %an  %cn  %ct  %ce  %ae  %s'
def bulk_create_commits(user, gsuser, repo, repopath, oldrev, newrev, refname):

    # list raw commitHistorys
    raw_commitHistorys = __list_raw_commitHistorys(repo, repopath, oldrev, newrev, refname)

    # list uniq commitHistorys
    commitHistorys = __list_commitHistorys(repo, raw_commitHistorys)

    # feed action
    member_user_ids = [x.user_id for x in RepoManager.list_repomember(repo.id)]
    member_user_ids.append(repo.user_id)
    member_user = GsuserManager.list_user_by_ids(member_user_ids)
    member_username_dict = dict([(x.username, x.id) for x in member_user])
    member_email_dict = dict([(x.email, x.id) for x in member_user])

    # generate feed data
    (user_feed_key_values, total_feed_key_values) = __get_feed_data(repo, commitHistorys, member_username_dict, member_email_dict)
        
    # add feed
    feedAction = FeedAction()
    __add_user_and_repo_feed(feedAction, repo, user_feed_key_values, total_feed_key_values)

    # at somebody action
    __notif(commitHistorys, repo, member_username_dict, member_email_dict)

    # stats action
    __stats(commitHistorys, repo, member_username_dict, member_email_dict)
    
    return len(raw_commitHistorys)

def get_committer_id(repo, commitHistory, member_username_dict, member_email_dict):
    if len(member_username_dict) == 1:
        return repo.user_id
    elif commitHistory.committer in member_username_dict:
        return member_username_dict[commitHistory.committer]
    elif commitHistory.committer_email in member_email_dict:
        return member_email_dict[commitHistory.committer_email]
    return None

def get_author_id(repo, commitHistory, member_username_dict, member_email_dict):
    if len(member_username_dict) == 1:
        return repo.user_id
    elif commitHistory.author in member_username_dict:
        return member_username_dict[commitHistory.author]
    elif commitHistory.author_email in member_email_dict:
        return member_email_dict[commitHistory.author_email]
    return None

def __get_feed_data(repo, commitHistorys, member_username_dict, member_email_dict):
    user_feed_key_values = {}
    total_feed_key_values = []
    for commitHistory in commitHistorys:
        committer_id = get_committer_id(repo, commitHistory, member_username_dict, member_email_dict)
        feed = Feed.create_push_commit(committer_id, repo.id, commitHistory.id)
        feed.save()
        if committer_id is not None:
            if committer_id not in user_feed_key_values:
                user_feed_key_values[committer_id] = []
            feed_key_values = user_feed_key_values[committer_id]
            feed_key_values.append(-float(time.mktime(commitHistory.committer_date.timetuple())))
            feed_key_values.append(feed.id)
        total_feed_key_values.append(-float(time.mktime(commitHistory.committer_date.timetuple())))
        total_feed_key_values.append(feed.id)
    return (user_feed_key_values, total_feed_key_values)

def __add_user_and_repo_feed(feedAction, repo, user_feed_key_values, total_feed_key_values):
    latest_feeds  = []
    if repo.auth_type == 2:
        for user_id, feed_key_values in user_feed_key_values.items():
            feedAction.madd_pri_user_feed(user_id, feed_key_values)
    else:
        for user_id, feed_key_values in user_feed_key_values.items():
            feedAction.madd_pub_user_feed(user_id, feed_key_values)
            if len(latest_feeds) < 4:
                latest_feeds.extend(feed_key_values)
    if len(latest_feeds) > 0:
        feedAction.madd_latest_feed(latest_feeds[0:4])
    if len(total_feed_key_values) > 0:
        feedAction.madd_repo_feed(repo.id, total_feed_key_values)

def __list_raw_commitHistorys(repo, repopath, oldrev, newrev, refname):
    args = ['/opt/run/bin/git-pretty-log.sh', repopath, oldrev, newrev]
    popen = Popen(args, stdout=PIPE, shell=False, close_fds=True)
    result = popen.communicate()[0].strip()
    raw_commitHistorys = []
    if popen.returncode == 0:
        for line in result.split('\n'):
            items = line.split('______', 8)
            if len(items) >= 9 and re.match('^\d+$', items[5]):
                committer_date = datetime.fromtimestamp(int(items[5])) 
                author_name = items[3][0:30]
                committer_name = items[4][0:30]
                commitHistory = CommitHistory.create(repo.id, repo.name, items[0], items[1][0:24], items[2], author_name, committer_name, committer_date, items[8][0:512], refname[0:32], items[6], items[7])
                raw_commitHistorys.append(commitHistory)
    return raw_commitHistorys

def __list_commitHistorys(repo, raw_commitHistorys):
    commitHistorys = []
    commit_ids = [x.commit_id for x in raw_commitHistorys]
    exists_commitHistorys = RepoManager.list_commits_by_commit_ids(repo.id, commit_ids)
    exists_commit_ids_set = set([x.commit_id for x in exists_commitHistorys])
    commitHistorys = []
    for commitHistory in raw_commitHistorys:
        if commitHistory.commit_id not in exists_commit_ids_set:
            commitHistory.save()
            commitHistorys.append(commitHistory)
    return commitHistorys

def __notif(commitHistorys, repo, member_username_dict, member_email_dict):
    for commitHistory in commitHistorys:
        from_user_id = get_author_id(repo, commitHistory, member_username_dict, member_email_dict)
        if from_user_id is not None:
            FeedManager.notif_commit_at(from_user_id, commitHistory.id, commitHistory.subject)
    
def __stats(commitHistorys, repo, member_username_dict, member_email_dict):
    stats_commits = []
    for commitHistory in commitHistorys:
        committer_id = get_committer_id(repo, commitHistory, member_username_dict, member_email_dict)
        author_id = get_author_id(repo, commitHistory, member_username_dict, member_email_dict)
        if committer_id is not None and author_id is not None:
            timestamp = time.mktime(commitHistory.committer_date.timetuple())
            stats_commits.append([repo.id, committer_id, author_id, timestamp])
    StatsManager.stats(stats_commits)

def __clear_relative_cache(user, gsuser, repo):
    cache.delete(CacheKey.REFS_TAG % repo.id)
    cache.delete(CacheKey.REFS_BRANCH % repo.id)
    cache.delete(CacheKey.REFS_COMMIT_HASH % repo.id)
    
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
    gsuser = GsuserManager.get_userprofile_by_id(gsuser.id)
    gsuser.used_quote = gsuser.used_quote + diff_size
    repo.used_quote = repo.used_quote + diff_size
    gsuser.save()
    repo.save()

def stop():
    EventManager.send_stop_event(EVENT_TUBE_NAME)
    print 'send stop event message...'

def __cache_version_update(sender, **kwargs):
    da_post_save(kwargs['instance'])

if __name__ == '__main__':
    post_save.connect(__cache_version_update)
    if len(sys.argv) < 2:
        sys.exit(1)
    action = sys.argv[1]
    if action == 'start':
        start()
    elif action == 'stop':
        stop()

