#!/usr/bin/python
import re
import os, sys
import json
import beanstalkc
from subprocess import Popen
from subprocess import PIPE
from datetime import datetime
from django.contrib.auth.models import User
from gitshell.gsuser.models import Userprofile, UserprofileManager
from gitshell.repos.models import CommitHistory, Repos, ReposManager

def main():
    beanstalk = beanstalkc.Connection(host='localhost', port=11300)
    #beanstalk.use('high_priority')
    exit_flag = False
    while not exit_flag:
        event_job = beanstalk.reserve()
        do_event(event_job.body)
        event_job.delete()

# abspath is the repos hooks directory
def do_event(event_job):
    event = json.loads(event_job)
    etype = event['type']
    diff_tree_blob_size_params = []
    if etype == 0:
        abspath = event['abspath'].strip()
        if abspath.endswith('/'):
            abspath = abspath[0 : len(abspath)-1]
        (username, reposname) = get_username_reposname(abspath)
        if reposname.endswith('.git'):
            reposname = reposname[0 : len(reposname)-4]
        user = get_user(username)
        gsuser = get_gsuser(user)
        repos = get_repos(user, reposname)
        repospath = get_repospath(user, repos)
        if user is None or gsuser is None or repos is None or not os.path.exists(repospath):
            return
        rev_ref_arr = event['revrefarr']
        for rev_ref in rev_ref_arr:    
            if len(rev_ref) < 3:
                continue
            oldrev = rev_ref[0]
            newrev = rev_ref[1]
            refname = rev_ref[2]
            diff_tree_blob_size_params.extend(rev_ref)
            if refname == 'refs/heads/master': 
                bulk_create_commits(user, gsuser, repos, repospath, oldrev, newrev)
        update_quote(user, gsuser, repos, repospath, diff_tree_blob_size_params)
        return
    if etype == 1:
        return
    if etype == 2:
        return

def update_quote(user, gsuser, repos, repospath, parameters):
    args = ['/opt/run/bin/diff-tree-blob-size.sh', repospath]
    args.extend(parameters)
    popen = Popen(args, stdout=PIPE, close_fds=True)
    result = popen.communicate()[0].strip()
    diff_size = 0
    if popen.returncode == 0:
        if result.startswith('+') or result.startswith('-'):
            diff_size = int(result)
        else:
            diff_size = int(result) - repos.quote
    update_gsuser_repos_quote(gsuser, repos, diff_size)

def bulk_create_commits(user, gsuser, repos, repospath, oldrev, newrev):
    args = ['/opt/run/bin/git-pretty-log.sh', repospath, oldrev, newrev]
    popen = Popen(args, stdout=PIPE, close_fds=True)
    result = popen.communicate()[0].strip()
    commitHistorys = []
    if popen.returncode == 0:
        for line in result.split('\n'):
            items = line.split('  ', 6)
            if len(items) >= 6 and re.match('^\d+$', items[5]):
                committer_date = datetime.fromtimestamp(int(items[5])) 
                # TODO
                commitHistory = CommitHistory.create(repos.id, items[0], items[1][0:24], items[2], items[3][0:30], items[4][0:30], 0, committer_date, items[6][0:512])
                commitHistorys.append(commitHistory)
    if len(commitHistorys) > 0:
        CommitHistory.objects.bulk_create(commitHistorys)

def get_username_reposname(abspath):
    rfirst_slash_idx = abspath.rfind('/')
    rsecond_slash_idx = abspath.rfind('/', 0, rfirst_slash_idx)
    rthird_slash_idx = abspath.rfind('/', 0, rsecond_slash_idx)
    if rthird_slash_idx > 0 and rthird_slash_idx < rsecond_slash_idx and rsecond_slash_idx < rfirst_slash_idx:
        return (abspath[rthird_slash_idx+1 : rsecond_slash_idx], abspath[rsecond_slash_idx+1 : rfirst_slash_idx])
    return ('', '')

def get_user(username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = None
    if user is not None and user.is_active:
        return user
    return None

def get_gsuser(user):
    if user is None:
        return None
    return UserprofileManager.get_userprofile_by_id(user.id)

def get_repos(user, reposname):  
    if user is None:
        return None
    return ReposManager.get_repos_by_userId_name(user.id, reposname)

def get_repospath(user, repos):
    if repos.auth_type == 0:
        return ('/opt/repos/public/%s/%s.git') % (user.username, repos.name)
    else:
        return ('/opt/repos/private/%s/%s.git') % (user.username, repos.name)

def update_gsuser_repos_quote(gsuser, repos, diff_size):
    gsuser.quote = gsuser.quote + diff_size
    repos.quote = repos.quote + diff_size
    gsuser.save()
    repos.save()

if __name__ == '__main__':
    main()
