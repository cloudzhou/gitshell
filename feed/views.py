#!/user/bin/python
# -*- coding: utf-8 -*-  
import re, json, time, copy
from sets import Set
from django.template import RequestContext
from django.forms.models import model_to_dict
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.views.decorators.http import require_http_methods
from gitshell.feed.feed import FeedAction, PositionKey, AttrKey
from gitshell.feed.models import Feed, FeedManager
from gitshell.repo.models import RepoManager, Repo
from gitshell.issue.models import IssueManager, Issue, IssueComment
from gitshell.gsuser.models import GsuserManager
from gitshell.todolist.views import todo
from gitshell.viewtools.views import json_httpResponse, json_success, json_failed, obj2dict

def index(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect('/dashboard/')
    return render_to_response('index.html',
                          {},
                          context_instance=RequestContext(request))

@login_required
def dashboard(request):
    feedAction = FeedAction()
    goto = feedAction.get_user_position(request.user.id)
    if goto == None:
        goto = PositionKey.FEED
    if goto == PositionKey.FEED:
        return feed(request)
    elif goto == PositionKey.TIMELINE:
        return timeline(request)
    elif goto == PositionKey.TODO:
        return todo(request)
    elif goto == PositionKey.PULL:
        return pull_merge(request)
    elif goto == PositionKey.ISSUES:
        return issues(request, 0)
    elif goto == PositionKey.EXPLORE:
        return explore(request)
    elif goto == PositionKey.NOTIF:
        return notif(request)
    return feed(request)

@login_required
def feed(request):
    current = 'feed'; title = u'%s / 动态' % (request.user.username)
    feedAction = FeedAction()
    feedAction.set_user_position(request.user.id, PositionKey.FEED)
    recently_timestamp = feedAction.get_recently_timestamp(request.user.id, AttrKey.RECENTLY_TIME_FEED)
    raw_watch_users = feedAction.get_watch_users(request.user.id, 0, 100)
    watch_user_ids = [int(x[0]) for x in raw_watch_users]
    watch_user_ids.append(request.user.id)
    raw_watch_repos = feedAction.get_watch_repos(request.user.id, 0, 100)
    watch_repo_ids = [int(x[0]) for x in raw_watch_repos]

    feeds_as_json = multi_feeds_as_json(request, feedAction, watch_user_ids, watch_repo_ids)
    feedAction.set_recently_timestamp_now(request.user.id, AttrKey.RECENTLY_TIME_FEED)
    response_dictionary = {'current': current, 'title': title, 'feeds_as_json' : feeds_as_json, 'recently_timestamp': recently_timestamp}
    return render_to_response('user/feed.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
@login_required
def timeline(request):
    current = 'timeline'; title = u'%s / 我的动态' % (request.user.username)
    feedAction = FeedAction()
    feedAction.set_user_position(request.user.id, PositionKey.TIMELINE)
    recently_timestamp = feedAction.get_recently_timestamp(request.user.id, AttrKey.RECENTLY_TIME_TIMELINE)
    pri_user_feeds = feedAction.get_pri_user_feeds(request.user.id, 0, 100)
    pub_user_feeds = feedAction.get_pub_user_feeds(request.user.id, 0, 100)
    feeds_as_json = get_feeds_as_json(request, pri_user_feeds, pub_user_feeds)
    feedAction.set_recently_timestamp_now(request.user.id, AttrKey.RECENTLY_TIME_TIMELINE)
    response_dictionary = {'current': current, 'title': title, 'feeds_as_json': feeds_as_json, 'recently_timestamp': recently_timestamp}
    return render_to_response('user/timeline.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def pull_merge(request):
    current = 'pull'; title = u'%s / 需要我处理的合并请求' % (request.user.username)
    feedAction = FeedAction()
    feedAction.set_user_position(request.user.id, PositionKey.PULL)
    recently_timestamp_astime = feedAction.get_recently_timestamp_astime(request.user.id, AttrKey.RECENTLY_TIME_PULL)
    pullRequests = RepoManager.list_pullRequest_by_mergeUserId(request.user.id)
    feedAction.set_recently_timestamp_now(request.user.id, AttrKey.RECENTLY_TIME_PULL)
    response_dictionary = {'current': current, 'title': title, 'pullRequests': pullRequests, 'recently_timestamp_astime': recently_timestamp_astime}
    return render_to_response('user/pull_merge.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
@login_required
def pull_request(request):
    current = 'pull'; title = u'%s / 我创建的合并请求' % (request.user.username)
    feedAction = FeedAction()
    feedAction.set_user_position(request.user.id, PositionKey.PULL)
    pullRequests = RepoManager.list_pullRequest_by_pullUserId(request.user.id)
    response_dictionary = {'current': current, 'title': title, 'pullRequests': pullRequests}
    return render_to_response('user/pull_request.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def issues_default(request):
    return issues(request, 0)

@login_required
def issues(request, page):
    current = 'issues'; title = u'%s / 问题' % (request.user.username)
    feedAction = FeedAction()
    feedAction.set_user_position(request.user.id, PositionKey.ISSUES)
    recently_timestamp = feedAction.get_recently_timestamp(request.user.id, AttrKey.RECENTLY_TIME_ISSUES)
    page = int(page)
    page_size = 50
    offset = page*page_size
    row_count = page_size + 1
    issues = IssueManager.list_assigned_issues(request.user.id, 'modify_time', offset, row_count)

    hasPre = False ; hasNext = False
    if page > 0:
        hasPre = True 
    if len(issues) > page_size:
        hasNext = True
        issues.pop()
    feedAction.set_recently_timestamp_now(request.user.id, AttrKey.RECENTLY_TIME_ISSUES)
    response_dictionary = {'current': current, 'title': title, 'issues': issues, 'page': page, 'hasPre': hasPre, 'hasNext': hasNext, 'recently_timestamp': recently_timestamp}
    return render_to_response('user/issues.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def explore(request):
    current = 'explore'
    feedAction = FeedAction()
    feedAction.set_user_position(request.user.id, PositionKey.EXPLORE)
    latest_feeds = feedAction.get_latest_feeds(0, 100)
    feeds_as_json = latest_feeds_as_json(request, latest_feeds)
    response_dictionary = {'current': current, 'feeds_as_json': feeds_as_json}
    return render_to_response('user/explore.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
@login_required
def notif(request):
    current = 'notif'; title = u'%s / 我的通知' % (request.user.username)
    feedAction = FeedAction()
    feedAction.set_user_position(request.user.id, PositionKey.NOTIF)
    recently_timestamp_astime = feedAction.get_recently_timestamp_astime(request.user.id, AttrKey.RECENTLY_TIME_NOTIF)
    notifMessages = FeedManager.list_notifmessage_by_userId(request.user.id, 0, 500)
    if request.userprofile.unread_message != 0:
        request.userprofile.unread_message = 0
        request.userprofile.save()
    feedAction.set_recently_timestamp_now(request.user.id, AttrKey.RECENTLY_TIME_NOTIF)
    response_dictionary = {'current': current, 'title': title, 'notifMessages': notifMessages, 'recently_timestamp_astime': recently_timestamp_astime}
    return render_to_response('user/notif.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def feed_by_ids(request):
    ids_str = request.POST.get('ids_str', '')
    feeds = []
    if re.match('^\w+$', ids_str):
        feeds = _list_feeds(request, ids_str)
    _fillwith_push_revref(request, feeds)
    _fillwith_commit_message(request, feeds)
    _fillwith_issue_event(request, feeds)
    _fillwith_pull_event(request, feeds)
    response_dictionary = {'feeds': feeds}
    return json_httpResponse(response_dictionary)

def _list_feeds(request, ids_str):
    ids = _get_feed_ids(ids_str)
    feeds = FeedManager.list_feed_by_ids(ids)
    return feeds

def _fillwith_push_revref(request, feeds):
    revref_dict = {}
    for feed in feeds:
        if not feed.is_push_revref():
            continue
        push_revref = RepoManager.get_pushrevref_by_id(feed.relative_id)
        if not push_revref:
            continue
        repo = RepoManager.get_repo_by_id(push_revref.repo_id)
        if repo and repo.auth_type == 2:
            if not request.user.is_authenticated() or not RepoManager.is_allowed_view_access_repo(repo, request.user):
                continue
        push_revref.commits = RepoManager.list_commit_by_repoId_pushrevrefId(push_revref.repo_id, push_revref.id, 0, 10)
        feed.relative_obj = push_revref

def _fillwith_commit_message(request, feeds):
    commit_ids = []
    for feed in feeds:
        if feed.is_commit_message():
            commit_ids.append(feed.relative_id)
    if len(commit_ids) == 0:
        return
    commit_dict = _convert_to_commit_dict(request, commit_ids)
    for feed in feeds:
        if feed.is_commit_message() and feed.relative_id in commit_dict:
            feed.relative_obj = commit_dict[feed.relative_id]

def _convert_to_commit_dict(request, commit_ids):
    commit_dict = {}
    allowed_view_access_repoId_set = Set()
    commits = RepoManager.list_commits_by_ids(commit_ids)
    repos = RepoManager.list_repo_by_ids(list(Set([x.repo_id for x in commits])))
    for repo in repos:
        if repo.auth_type == 2:
            if not request.user.is_authenticated() or not RepoManager.is_allowed_view_access_repo(repo, request.user):
                continue
        allowed_view_access_repoId_set.add(repo.id)
    for commit in commits:
        if commit.repo_id in allowed_view_access_repoId_set:
            commit_dict[commit.id] = commit
    return commit_dict

def _fillwith_issue_event(request, feeds):
    for feed in feeds:
        if not feed.is_issue_event():
            continue
        issue = IssueManager.get_issue_by_id(feed.relative_id)
        feed.relative_obj = issue

def _fillwith_pull_event(request, feeds):
    for feed in feeds:
        if not feed.is_pull_event():
            continue
        pullRequest = RepoManager.get_pullRequest_by_id(feed.relative_id)
        if pullRequest is None or pullRequest.source_repo is None or pullRequest.desc_repo is None:
            continue
        feed.relative_obj = pullRequest

def _get_feed_ids(ids_str):
    ids = []
    max_count = 0
    for idstr in ids_str.split('_'):
        if re.match('^\d+$', idstr):
            ids.append(int(idstr))
        max_count = max_count + 1
        if max_count >= 99:
            break
    return ids

def multi_feeds_as_json(request, feedAction, watch_user_ids, watch_repo_ids):
    feeds_json_val = {}
    for user_id in watch_user_ids:
        pub_user_feeds = feedAction.get_pub_user_feeds(user_id, 0, 50)
        if request.user.is_authenticated() and user_id == request.user.id:
            pri_user_feeds = feedAction.get_pri_user_feeds(user_id, 0, 50)
            pub_user_feeds = pub_user_feeds + pri_user_feeds
        if pub_user_feeds is not None and len(pub_user_feeds) > 0:
            feeds_json_val['uf_%s' % user_id] = feeds_as_json(pub_user_feeds)
    for repo_id in watch_repo_ids:
        repo_feeds = feedAction.get_repo_feeds(repo_id, 0, 50)
        if repo_feeds is not None and len(repo_feeds) > 0:
            feeds_json_val['rf_%s' % repo_id] = feeds_as_json(repo_feeds)
    return str(feeds_json_val)

def get_feeds_as_json(request, pri_user_feeds, pub_user_feeds):
    feeds_json_val = {}
    feeds_json_val['pri_user_feeds_%s' % request.user.id] = feeds_as_json(pri_user_feeds)
    feeds_json_val['pub_user_feeds_%s' % request.user.id] = feeds_as_json(pub_user_feeds)
    return str(feeds_json_val)

def latest_feeds_as_json(request, latest_feeds):
    feeds_json_val = {}
    feeds_json_val['latest_feeds'] = feeds_as_json(latest_feeds)
    return str(feeds_json_val)
    
def feeds_as_json(feeds):
    json_arr = []
    for feed in feeds:
        json_arr.append(list(feed))
    return json_arr


