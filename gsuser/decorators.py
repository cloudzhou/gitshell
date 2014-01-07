# -*- coding: utf-8 -*-  
from django.http import Http404
from django.http import HttpResponseRedirect
from django.utils.http import urlquote
from gitshell.feed.feed import FeedAction
from gitshell.repo.models import RepoManager, REPO_PERMISSION
from gitshell.viewtools.views import json_httpResponse, json_success, json_failed

def repo_view_permission_check(function):

    def wrap(request, *args, **kwargs):
        if len(args) >= 2:
            user_name = args[0]; repo_name = args[1]
            repo = RepoManager.get_repo_by_name(user_name, repo_name)
            if repo is None:
                return HttpResponseRedirect('/help/error/repo_not_found/')
            if repo.auth_type == 2 and not request.user.is_authenticated():
                return HttpResponseRedirect('/login/?next=' + urlquote(request.path))
            # half private, code is keep
            is_allowed_access_repo = RepoManager.is_allowed_access_repo(repo, request.user, REPO_PERMISSION.WEB_VIEW)
            if not is_allowed_access_repo:
                if request.method == 'POST':
                    return json_failed(403, u'没有管理权限')
                return HttpResponseRedirect('/help/error/repo_permission_denied/')
        if request.user.is_authenticated():
            feedAction = FeedAction()
            feedAction.add_recently_view_repo_now(request.user.id, repo.id)
        return function(request, *args, **kwargs)
    wrap.__doc__=function.__doc__
    wrap.__name__=function.__name__

    return wrap

def repo_admin_permission_check(function):

    def wrap(request, *args, **kwargs):
        if len(args) >= 2:
            user_name = args[0]; repo_name = args[1]
            repo = RepoManager.get_repo_by_name(user_name, repo_name)
            if repo is None:
                return HttpResponseRedirect('/help/error/repo_not_found/')
            if not request.user.is_authenticated():
                return HttpResponseRedirect('/login/?next=' + urlquote(request.path))
            is_allowed_access_repo = RepoManager.is_allowed_access_repo(repo, request.user, REPO_PERMISSION.ADMIN)
            if not is_allowed_access_repo:
                if request.method == 'POST':
                    return json_failed(403, u'没有管理权限')
                return HttpResponseRedirect('/help/error/repo_permission_denied/')
        if request.user.is_authenticated():
            feedAction = FeedAction()
            feedAction.add_recently_view_repo_now(request.user.id, repo.id)
        return function(request, *args, **kwargs)
    wrap.__doc__=function.__doc__
    wrap.__name__=function.__name__

    return wrap

def repo_source_permission_check(function):

    def wrap(request, *args, **kwargs):
        if len(args) >= 2:
            user_name = args[0]; repo_name = args[1]
            repo = RepoManager.get_repo_by_name(user_name, repo_name)
            if repo is None:
                return HttpResponseRedirect('/help/error/repo_not_found/')
            if repo.auth_type != 0 and not request.user.is_authenticated():
                return HttpResponseRedirect('/login/?next=' + urlquote(request.path))
            is_allowed_access_repo = RepoManager.is_allowed_access_repo(repo, request.user, REPO_PERMISSION.READ_ONLY)
            if not is_allowed_access_repo:
                if request.method == 'POST':
                    return json_failed(403, u'没有管理权限')
                return HttpResponseRedirect('/help/error/repo_permission_denied/')
        if request.user.is_authenticated():
            feedAction = FeedAction()
            feedAction.add_recently_view_repo_now(request.user.id, repo.id)
        return function(request, *args, **kwargs)
    wrap.__doc__=function.__doc__
    wrap.__name__=function.__name__

    return wrap

