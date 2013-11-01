#!/usr/bin/python
import os, threading, shutil, sys, json, re
from django.contrib.auth.models import User, UserManager
from gitshell.repo.models import RepoManager, CommitHistory
from gitshell.issue.models import IssueManager, Issue
from gitshell.gsuser.models import GsuserManager, Userprofile
from gitshell.keyauth.models import KeyauthManager

def start():
    users = User.objects.all()
    for user in users:
        userprofile = GsuserManager.get_userprofile_by_id(user.id)
        if not userprofile:
            continue
        if not re.match('[a-zA-Z0-9-_]+', user.username):
            continue
        userstats = {}
        userstats['username'] = user.username
        userstats['email'] = user.email
        userstats['date_joined'] = user.date_joined.strftime('%Y/%m/%d %H:%M:%S')
        userstats['last_login'] = user.last_login.strftime('%Y/%m/%d %H:%M:%S')
        repos = RepoManager.list_repo_by_userId(user.id, 0, 1000)
        userstats['repo_total_count'] = len(repos)
        first_time_commit = None; last_time_commit = None; commits = 0; forks = 0; repo_private_count = 0
        for repo in repos:
            commits = commits + repo.commit
            if repo.auth_type != 0:
                repo_private_count = repo_private_count + 1
            if repo.fork_repo_id != 0:
                forks = forks + 1
            commitHistorys = CommitHistory.objects.filter(visibly=0).filter(repo_id=repo.id).order_by('create_time')[0:1]
            if len(commitHistorys) > 0:
                first_time_commitHistory = commitHistorys[0]
                if first_time_commit is None or first_time_commit > first_time_commitHistory.create_time:
                    first_time_commit = first_time_commitHistory.create_time
            commitHistorys = CommitHistory.objects.filter(visibly=0).filter(repo_id=repo.id).order_by('-create_time')[0:1]
            if len(commitHistorys) > 0:
                last_time_commitHistory = commitHistorys[0]
                if last_time_commit is None or last_time_commit < last_time_commitHistory.create_time:
                    last_time_commit = last_time_commitHistory.create_time
        userstats['repo_private_count'] = repo_private_count
        if first_time_commit:
            userstats['first_time_commit'] = first_time_commit.strftime('%Y/%m/%d %H:%M:%S')
        else:
            userstats['first_time_commit'] = ''
        if last_time_commit:
            userstats['last_time_commit'] = last_time_commit.strftime('%Y/%m/%d %H:%M:%S')
        else:
            userstats['last_time_commit'] = ''
        userstats['commits'] = commits
        userstats['watch_repo'] = userprofile.watchrepo
        userstats['fork_repo'] = forks
        pullrequests = RepoManager.list_pullRequest_by_pullUserId(user.id)
        userstats['pullrequests'] = len(pullrequests)
        issues = Issue.objects.filter(visibly=0).filter(creator_user_id=user.id)[0:1000]
        userstats['issues'] = len(issues)
        userpubkeys = KeyauthManager.list_userpubkey_by_userId(user.id)
        userstats['ssh_key'] = len(userpubkeys)
        csv_items = [userstats['username'], userstats['email'], userstats['date_joined'], userstats['last_login'], str(int(userstats['repo_total_count'])), str(int(userstats['repo_private_count'])), userstats['first_time_commit'], userstats['last_time_commit'], str(int(userstats['commits'])), str(int(userstats['watch_repo'])), str(int(userstats['fork_repo'])), str(int(userstats['pullrequests'])), str(int(userstats['issues'])), str(int(userstats['ssh_key']))]
        print ','.join(csv_items)

if __name__ == '__main__':
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

