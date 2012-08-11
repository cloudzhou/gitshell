from django.http import Http404
from django.http import HttpResponseRedirect
from gitshell.repo.models import RepoManager

def repo_permission_check(function):

    def wrap(request, *args, **kwargs):
        if len(args) >= 2:
            user_name = args[0]
            repo_name = args[1]
            repo = RepoManager.get_repo_by_name(user_name, repo_name)
            if repo is None:
                return HttpResponseRedirect('/help/error/')
            # half private, code is keep
            if repo.auth_type == 2:
                if not RepoManager.is_repo_member(repo, request.user):
                    return HttpResponseRedirect('/help/error/')
        return function(request, *args, **kwargs)
    wrap.__doc__=function.__doc__
    wrap.__name__=function.__name__

    return wrap

def repo_source_permission_check(function):

    def wrap(request, *args, **kwargs):
        if len(args) >= 2:
            user_name = args[0]
            repo_name = args[1]
        return function(request, *args, **kwargs)
    wrap.__doc__=function.__doc__
    wrap.__name__=function.__name__

    return wrap
