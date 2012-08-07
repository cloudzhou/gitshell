from django.http import Http404
from django.http import HttpResponseRedirect

def repo_permission_check(function):

    def wrap(request, *args, **kwargs):
        if len(args) >= 2:
            user_name = args[0]
            repo_name = args[1]
            if False:
                return HttpResponseRedirect('/error/#500')
        return function(request, *args, **kwargs)
    wrap.__doc__=function.__doc__
    wrap.__name__=function.__name__

    return wrap

def repo_source_permission_check(function):

    def wrap(request, *args, **kwargs):
        if len(args) >= 2:
            user_name = args[0]
            repo_name = args[1]
            if False:
                return HttpResponseRedirect('/error/#500')
        return function(request, *args, **kwargs)
    wrap.__doc__=function.__doc__
    wrap.__name__=function.__name__

    return wrap
