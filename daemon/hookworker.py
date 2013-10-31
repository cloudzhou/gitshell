#!/usr/bin/python
import re, time, os, sys, json, httplib, urllib
from urlparse import urlparse
import beanstalkc
from subprocess import Popen
from subprocess import PIPE
from datetime import datetime
from django.core.cache import cache
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete
from gitshell.gsuser.models import Userprofile, GsuserManager
from gitshell.repo.models import RepoManager, Repo, WebHookURL, CommitHistory
from gitshell.repo.githandler import GitHandler
from gitshell.daemon.models import EventManager, HOOK_TUBE_NAME
from gitshell.settings import REPO_PATH, BEANSTALK_HOST, BEANSTALK_PORT, logger
from gitshell.objectscache.da import da_post_save

ACCEPT = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36'
MAX_COMMIT_COUNT = 100
def start():
    logger.info('==================== START eventworker ====================')
    beanstalk = beanstalkc.Connection(host=BEANSTALK_HOST, port=BEANSTALK_PORT)
    EventManager.switch(beanstalk, HOOK_TUBE_NAME)
    while True:
        event_job = beanstalk.reserve()
        try:
            event = json.loads(event_job.body)
            # exit signal
            if event['type'] == -1:
                event_job.delete()
                sys.exit(0)
            do_event(event)
        except Exception, e:
            logger.error('do_event catch except, event: %s' % event_job.body)
            logger.exception(e)
        event_job.delete()
    logger.info('==================== STOP eventworker ====================')

# abspath is the repo hooks directory
def do_event(event):
    etype = event['type']
    if etype == 0:
        abspath = event['abspath'].strip()
        (username, reponame) = get_username_reponame(abspath)
        if username == '' or reponame == '':
            return
        (user, userprofile, repo, abs_repo_path) = get_attrs(username, reponame)
        if user is None or userprofile is None or repo is None or abs_repo_path is None or not os.path.exists(abs_repo_path):
            return
        gitHandler = GitHandler()
        webHookURLs = RepoManager.list_webHookURL_by_repoId(repo.id)
        rev_ref_arr = event['revrefarr']
        for rev_ref in rev_ref_arr:
            if len(rev_ref) < 3:
                continue
            oldrev = rev_ref[0]
            newrev = rev_ref[1]
            refname = rev_ref[2]
            for webHookURL in webHookURLs:
                if webHookURL.status != 0:
                    continue
                handle_push_webHookURL(gitHandler, abs_repo_path, user, repo, oldrev, newrev, refname, webHookURL)

def handle_push_webHookURL(gitHandler, abs_repo_path, user, repo, oldrev, newrev, refname, webHookURL):
    raw_commits = gitHandler.repo_log_file(abs_repo_path, oldrev, newrev, 500, '.')
    payload = {}
    payload['before'] = oldrev
    payload['after'] = newrev
    payload['compare'] = 'https://gitshell.com/%s/%s/compare/%s...%s' % (repo.username, repo.name, newrev, oldrev)
    payload['created'] = (oldrev.startswith('0000000') and not newrev.startswith('0000000'))
    payload['deleted'] = (not oldrev.startswith('0000000') and newrev.startswith('0000000'))
    commits = []
    for raw_commit in raw_commits:
        commit = commit_as_view(repo, raw_commit)
        commits.append(commit)
    head_commit = commits[len(commits)-1]
    repository = repo_as_view(user, repo)
    payload['commits'] = commits
    payload['head_commit'] = head_commit
    payload['repository'] = repository
    payload['ref'] = refname
    payload_json = json.dumps(payload)
    post_payload(webHookURL, payload_json)

def commit_as_view(repo, commit):
    commit_view = {}
    commit_view['id'] = commit['commit_hash']
    commit_view['timestamp'] = long(commit['committer_date'])
    commit_view['message'] = commit['commit_message']
    commit_view['url'] = 'https://gitshell.com/%s/%s/commit/%s/' % (repo.username, repo.name, commit['commit_hash'])
    author = {'name': commit['author_name'], 'email': commit['author_email']}
    author['username'] = get_gitshell_username(commit['author_name'], commit['author_email'])
    committer = {'name': commit['committer_name'], 'email': commit['committer_email']}
    committer['username'] = get_gitshell_username(commit['committer_name'], commit['committer_email'])
    commit_view['author'] = author
    commit_view['committer'] = committer
    return commit_view

NAME_CACHE = {}
EMAIL_CACHE = {}
def get_gitshell_username(name, email):
    global NAME_CACHE, EMAIL_CACHE
    if email in EMAIL_CACHE:
        return EMAIL_CACHE[email]
    if name in NAME_CACHE:
        return NAME_CACHE[name]
    user = GsuserManager.get_user_by_email(email)
    if user:
        EMAIL_CACHE[email] = user.username
        return user.username
    user = GsuserManager.get_user_by_name(name)
    if user:
        NAME_CACHE[name] = user.username
        return user.username

def repo_as_view(user, repo):
    repository = {}
    repository['created_at'] = time.mktime(repo.create_time.timetuple())
    repository['description'] = repo.desc
    repository['fork'] = (repo.fork_repo_id != 0)
    repository['forks'] = repo.fork
    repository['has_downloads'] = False
    repository['has_issues'] = True
    repository['has_wiki'] = False
    repository['homepage'] = ''
    repository['id'] = repo.id
    repository['language'] = repo.lang
    repository['master_branch'] = 'master'
    repository['name'] = repo.name
    #repository['open_issues'] = 
    owner = {'name': user.username, 'email': user.email}
    repository['owner'] = owner
    repository['private'] = (repo.auth_type != 0)
    # TODO pushed_at is wrong
    repository['pushed_at'] = time.mktime(repo.last_push_time.timetuple())
    repository['size'] = repo.used_quote
    repository['stargazers'] = repo.star
    repository['url'] = 'https://gitshell.com/%s/%s/' % (repo.username, repo.name)
    repository['watchers'] = repo.watch
    return repository
    
def post_payload(webHookURL, payload):
    connection = None
    url = webHookURL.url
    try:
        parseResult = urlparse(url)
        scheme = parseResult.scheme; hostname = parseResult.hostname; port = parseResult.port; path = parseResult.path
        if not port:
            port = 80
        if scheme == 'https':
            connection = httplib.HTTPSConnection(hostname, port, timeout=10)
        else:
            connection = httplib.HTTPConnection(hostname, port, timeout=10)
        params = urllib.urlencode({'payload': payload})
        headers = {'Content-type': 'application/x-www-form-urlencoded', 'Accept': ACCEPT, 'User-Agent': USER_AGENT}
        connection.request('POST', path, params, headers)
        response = connection.getresponse()
        if webHookURL.last_return_code != response.status:
            webHookURL.last_return_code = response.status
            webHookURL.save()
        if response.status == 200:
            return True
    except Exception, e:
        logger.exception(e)
    finally:
       if connection: connection.close()
    return False
            
def get_username_reponame(abspath):
    if abspath.endswith('/'):
        abspath = abspath[0 : len(abspath)-1]
    rfirst_slash_idx = abspath.rfind('/')
    rsecond_slash_idx = abspath.rfind('/', 0, rfirst_slash_idx)
    rthird_slash_idx = abspath.rfind('/', 0, rsecond_slash_idx)
    if rthird_slash_idx > 0 and rthird_slash_idx < rsecond_slash_idx and rsecond_slash_idx < rfirst_slash_idx:
        (username, reponame) = (abspath[rthird_slash_idx+1 : rsecond_slash_idx], abspath[rsecond_slash_idx+1 : rfirst_slash_idx])
        if reponame.endswith('.git'):
            reponame = reponame[0 : len(reponame)-4]
        return (username, reponame)
    return ('', '')

def return_all_none():
    return (None, None, None, None)
    
def get_attrs(username, reponame):
    user = GsuserManager.get_user_by_name(username)
    if not user:
        return_all_none()
    userprofile = GsuserManager.get_userprofile_by_id(user.id)
    if not userprofile:
        return_all_none()
    repo = RepoManager.get_repo_by_userId_name(user.id, reponame)
    if not repo:
        return_all_none()
    abs_repo_path = repo.get_abs_repopath()
    return (user, userprofile, repo, abs_repo_path)

def stop():
    EventManager.send_stop_event(HOOK_TUBE_NAME)

def __cache_version_update(sender, **kwargs):
    da_post_save(kwargs['instance'])

if __name__ == '__main__':
    post_save.connect(__cache_version_update)
    post_delete.connect(__cache_version_update)
    if len(sys.argv) < 2:
        sys.exit(1)
    action = sys.argv[1]
    if action == 'start':
        start()
    elif action == 'stop':
        stop()

