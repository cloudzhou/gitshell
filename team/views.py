___user/bin/python
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
from gitshell.issue.cons import conver_issues
from gitshell.gsuser.models import GsuserManager
from gitshell.gsuser.views import get_feeds_as_json
from gitshell.team.models import TeamManager
from gitshell.todolist.views import todo
from gitshell.viewtools.views import json_httpResponse, obj2dict

@login_required
def dashboard(request, username):
    (user, userprofile) = _get_user_userprofile(request, username)
    feedAction = FeedAction()
    goto = feedAction.get_user_position(user.id)
    if goto == None:
        goto = PositionKey.TIMELINE
    if goto == PositionKey.TIMELINE:
        return timeline(request, username)
    elif goto == PositionKey.PULL:
        return pull_merge(request, username)
    elif goto == PositionKey.ISSUES:
        return issues(request, username, 0)
    elif goto == PositionKey.NOTIF:
        return notif(request, username)
    return timeline(request, username)

@login_required
def timeline(request, username):
    (user, userprofile) = _get_user_userprofile(request, username)
    current = 'timeline'
    feedAction = FeedAction()
    feedAction.set_user_position(user.id, PositionKey.TIMELINE)
    pri_user_feeds = feedAction.get_pri_user_feeds(user.id, 0, 100)
    pub_user_feeds = feedAction.get_pub_user_feeds(user.id, 0, 100)
    feeds_as_json = get_feeds_as_json(request, pri_user_feeds, pub_user_feeds)
    response_dictionary = {'current': current, 'feeds_as_json': feeds_as_json}
    return render_to_response('team/timeline.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def pull_merge(request, username):
    (user, userprofile) = _get_user_userprofile(request, username)
    current = 'pull'
    feedAction = FeedAction()
    feedAction.set_user_position(user.id, PositionKey.PULL)
    pullRequests = RepoManager.list_pullRequest_by_teamUserId_mergeUserId(user.id, request.user.id)
    response_dictionary = {'current': current, 'pullRequests': pullRequests}
    return render_to_response('team/pull_merge.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
@login_required
def pull_request(request, username):
    (user, userprofile) = _get_user_userprofile(request, username)
    current = 'pull'
    feedAction = FeedAction()
    feedAction.set_user_position(user.id, PositionKey.PULL)
    pullRequests = RepoManager.list_pullRequest_by_teamUserId_pullUserId(user.id, request.user.id)
    response_dictionary = {'current': current, 'pullRequests': pullRequests}
    return render_to_response('team/pull_request.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def issues_default(request, username):
    return issues(request, username, 0)

@login_required
def issues(request, username, page):
    (user, userprofile) = _get_user_userprofile(request, username)
    current = 'issues'
    feedAction = FeedAction()
    feedAction.set_user_position(user.id, PositionKey.ISSUES)
    page = int(page), page_size = 50, offset = page*page_size, row_count = page_size + 1
    raw_issues = IssueManager.list_issues_by_teamUserId_assigned(user.id, request.user.id, 'modify_time', offset, row_count)
    issues = conver_issues(raw_issues)

    hasPre = False ; hasNext = False
    if page > 0:
        hasPre = True 
    if len(issues) > page_size:
        hasNext = True
        issues.pop()
    response_dictionary = {'current': current, 'issues': issues, 'page': page, 'hasPre': hasPre, 'hasNext': hasNext}
    return render_to_response('team/issues.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def notif(request, username):
    (user, userprofile) = _get_user_userprofile(request, username)
    current = 'notif'
    feedAction = FeedAction()
    feedAction.set_user_position(user.id, PositionKey.NOTIF)
    notifMessages = FeedManager.list_notifmessage_by_toUserId_teamUserId(request.user.id, user.id, 0, 500)
    if userprofile.unread_message != 0:
        userprofile.unread_message = 0
        userprofile.save()
    response_dictionary = {'current': current, 'notifMessages': notifMessages}
    return render_to_response('team/notif.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def _get_user_userprofile(request, username):
    current_user = GsuserManager.get_user_by_name(username)
    if not current_user:
        return (request.user, request.userprofile)
    teamMember = TeamManager.get_teamMember_by_userId_teamUserId(request.user.id, current_user.id)
    if not teamMember:
        return (request.user, request.userprofile)
    current_userprofile = GsuserManager.get_userprofile_by_id(current_user.id)
    if current_userprofile:
        return (current_user, current_userprofile)
    return (request.user, request.userprofile)


