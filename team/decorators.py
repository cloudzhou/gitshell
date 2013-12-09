# -*- coding: utf-8 -*-  
from django.http import Http404
from django.http import HttpResponseRedirect
from django.utils.http import urlquote
from gitshell.gsuser.models import GsuserManager
from gitshell.team.models import TeamManager, TeamMember
from gitshell.viewtools.views import json_httpResponse, json_success, json_failed, obj2dict

def team_admin_permission_check(function):

    def wrap(request, *args, **kwargs):
        if len(args) >= 1:
            username = args[0]
            teamUser = GsuserManager.get_user_by_name(username)
            if not teamUser:
                return _response_not_admin_rights(request)
            teamMember = TeamManager.get_teamMember_by_teamUserId_userId(teamUser.id, request.user.id)
            if not teamMember or not teamMember.has_admin_rights():
                return _response_not_admin_rights(request)
        return function(request, *args, **kwargs)
    wrap.__doc__=function.__doc__
    wrap.__name__=function.__name__

    return wrap

def _response_not_admin_rights(request):
    if request.method == 'POST':
        return json_failed(403, u'没有管理员权限')
    return HttpResponseRedirect('/help/error/team_not_admin_rights/')

