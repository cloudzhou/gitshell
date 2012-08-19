#!/user/bin/python
# -*- coding: utf-8 -*-  
import re, json, time
from sets import Set
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from gitshell.feed.feed import FeedAction, PositionKey
from gitshell.repo.models import RepoManager, IssuesComment
from gitshell.repo.cons import conver_issues
from gitshell.gsuser.models import GsuserManager

@login_required
def home(request):
    feedAction = FeedAction()
    goto = feedAction.get_user_position(request.user.id)
    if goto == None:
        goto = PositionKey.FEED
    if goto == PositionKey.FEED:
        return feed(request)
    elif goto == PositionKey.GIT:
        return git(request)
    elif goto == PositionKey.ISSUES:
        return issues(request, 0)
    elif goto == PositionKey.EXPLORE:
        return explore(request)

@login_required
def feed(request):
    current = 'feed'
    feedAction = FeedAction()
    feedAction.set_user_position(request.user.id, PositionKey.FEED)
    raw_watch_users = feedAction.get_watch_users(request.user.id, 0, 100)
    watch_user_ids = [int(x[0]) for x in raw_watch_users]
    watch_users = GsuserManager.list_user_by_ids(watch_user_ids)
    raw_watch_repos = feedAction.get_watch_repos(request.user.id, 0, 100)
    watch_repos_ids = [int(x[0]) for x in raw_watch_repos]
    watch_repos = RepoManager.list_repo_by_ids(watch_repos_ids)
    print watch_users, watch_repos
    response_dictionary = {'current': current}
    return render_to_response('user/feed.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
@login_required
def git(request):
    current = 'git'
    feedAction = FeedAction()
    feedAction.set_user_position(request.user.id, PositionKey.GIT)
    pri_user_feeds = feedAction.get_pri_user_feeds(request.user.id, 0, 100)
    pub_user_feeds = feedAction.get_pub_user_feeds(request.user.id, 0, 100)
    feeds_as_json = git_feeds_as_json(request, pri_user_feeds, pub_user_feeds)
    response_dictionary = {'current': current, 'feeds_as_json': feeds_as_json}
    return render_to_response('user/git.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
@login_required
def issues_default(request):
    return issues(request, 0)

@login_required
def issues(request, page):
    current = 'issues'
    feedAction = FeedAction()
    feedAction.set_user_position(request.user.id, PositionKey.ISSUES)
    page = int(page)
    page_size = 50
    offset = page*page_size
    row_count = page_size + 1
    raw_issues = RepoManager.list_assigned_issues(request.user.id, 'modify_time', offset, row_count)
    username_map = {}
    reponame_map = {}
    for raw_issue in raw_issues:
        if raw_issue.user_id not in username_map:
            username_map[raw_issue.user_id] = ''
        if raw_issue.assigned not in username_map:
            username_map[raw_issue.assigned] = ''
        if raw_issue.repo_id not in reponame_map:
            reponame_map[raw_issue.repo_id] = ''
    repos = RepoManager.list_repo_by_ids(reponame_map.keys())
    users = GsuserManager.list_user_by_ids(username_map.keys())
    reponame_map = dict([(x.id, x.name) for x in repos])
    username_map = dict([(x.id, x.username) for x in users])
    issues = conver_issues(raw_issues, username_map, reponame_map)

    hasPre = False ; hasNext = False
    if page > 0:
        hasPre = True 
    if len(issues) > page_size:
        hasNext = True
        issues.pop()
    response_dictionary = {'current': current, 'issues': issues, 'page': page, 'hasPre': hasPre, 'hasNext': hasNext}
    return render_to_response('user/issues.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
@login_required
def doissues(request):
    action = request.POST.get('action', '')
    comment = request.POST.get('comment', '')
    repo_id = request.POST.get('repo_id', '')
    issues_id = request.POST.get('issues_id', '')
    if action == '' or repo_id == '' or issues_id == '':
        response_dictionary = {'result': 'failed'}
        return HttpResponse(json.dumps(response_dictionary), mimetype="application/json")
    issues = RepoManager.get_issues(int(repo_id), int(issues_id))
    if issues is None or issues.user_id != request.user.id:
        response_dictionary = {'result': 'failed'}
        return HttpResponse(json.dumps(response_dictionary), mimetype="application/json")
    if action == 'fixed':
        issues.status = 4
    elif action == 'close':
        issues.status = 5
    elif action == 'reject':
        issues.status = 6
    if comment != '':
        issuesComment = IssuesComment() 
        issuesComment.issues_id = issues.id
        issuesComment.user_id = request.user.id
        issuesComment.content = comment
        issuesComment.save()
        issues.comment_count = issues.comment_count + 1
    issues.save()
    response_dictionary = {'result': 'sucess'}
    return HttpResponse(json.dumps(response_dictionary), mimetype="application/json")
        

@login_required
def explore(request):
    current = 'explore'
    feedAction = FeedAction()
    feedAction.set_user_position(request.user.id, PositionKey.EXPLORE)
    response_dictionary = {'current': current}
    return render_to_response('user/explore.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
@login_required
def notif(request):
    current = 'notif'
    response_dictionary = {'current': current}
    return render_to_response('user/home.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
@login_required
def feedbyids(request):
    ids_str = request.POST.get('ids_str', '')
    feeds = []
    if re.match('^\w+$', ids_str):
        feeds = get_feeds(request, ids_str)
    gravatarmap = get_gravatarmap(feeds)
    response_dictionary = {'feeds': feeds, 'gravatarmap': gravatarmap}
    return HttpResponse(json.dumps(response_dictionary), mimetype="application/json")

def get_gravatarmap(feeds):
    gravatarmap = {}
    for feed in feeds:
        username = feed['author']
        if username not in gravatarmap:
            userprofile = GsuserManager.get_userprofile_by_name(username)
            if userprofile is not None:
                gravatarmap[username] = userprofile.imgurl
                continue
            gravatarmap[username] = 'None'
    return gravatarmap
    

def get_feeds(request, ids_str):
    feeds = []
    ids = []
    max_count = 0
    for idstr in ids_str.split('_'):
        if re.match('^\d+$', idstr):
            ids.append(int(idstr))
        max_count = max_count + 1
        if max_count >= 99:
            break
    commits = RepoManager.get_commits_by_ids(ids)
    for commit in commits:
        repo_id = commit.repo_id
        repo = RepoManager.get_repo_by_id(repo_id)
        if repo is None:
            continue
        if repo.auth_type == 2 and repo.user_id != request.user.id and not RepoManager.is_repo_member(repo.id, request.user.id):
            continue
        feed = {}
        feed['id'] = commit.id
        feed['repo_name'] = commit.repo_name
        feed['commit_hash'] = commit.commit_hash
        feed['author'] = commit.author
        feed['committer_date'] = time.mktime(commit.committer_date.timetuple())
        feed['subject'] = commit.subject
        feeds.append(feed)
    return feeds

def git_feeds_as_json(request, pri_user_feeds, pub_user_feeds):
    feeds_json_val = {}
    feeds_json_val['pri_user_feeds_%s' % request.user.id] = feeds_as_json(pri_user_feeds)
    feeds_json_val['pub_user_feeds_%s' % request.user.id] = feeds_as_json(pub_user_feeds)
    return str(feeds_json_val)

def feeds_as_json(feeds):
    json_arr = []
    for feed in feeds:
        json_arr.append(list(feed))
    return json_arr
    
