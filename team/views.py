#!/bin/python
# -*- coding: utf-8 -*-  
import re, json, time, copy, random
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
from gitshell.feed.mailUtils import Mailer
from gitshell.repo.models import RepoManager, Repo
from gitshell.issue.models import IssueManager, Issue, IssueComment
from gitshell.issue.cons import conver_issues
from gitshell.gsuser.models import GsuserManager, UserViaRef, REF_TYPE
from gitshell.gsuser.views import get_feeds_as_json
from gitshell.gssettings.Form import TeamprofileForm
from gitshell.team.models import TeamManager, TeamMember
from gitshell.todolist.views import todo
from gitshell.viewtools.views import json_httpResponse, obj2dict

@login_required
def dashboard(request, username):
    (teamUser, teamUserprofile) = _get_team_user_userprofile(request, username)
    feedAction = FeedAction()
    goto = feedAction.get_user_position(teamUser.id)
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
    (teamUser, teamUserprofile) = _get_team_user_userprofile(request, username)
    current = 'timeline'; title = u'%s / 动态' % (teamUser.username)
    feedAction = FeedAction()
    feedAction.set_user_position(teamUser.id, PositionKey.TIMELINE)
    pri_user_feeds = feedAction.get_pri_user_feeds(teamUser.id, 0, 100)
    pub_user_feeds = feedAction.get_pub_user_feeds(teamUser.id, 0, 100)
    feeds_as_json = get_feeds_as_json(request, pri_user_feeds, pub_user_feeds)
    response_dictionary = {'current': current, 'title': title, 'feeds_as_json': feeds_as_json}
    response_dictionary.update(_get_common_team_dict(request, teamUser, teamUserprofile))
    return render_to_response('team/timeline.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def pull_merge(request, username):
    (teamUser, teamUserprofile) = _get_team_user_userprofile(request, username)
    current = 'pull'; title = u'%s / 需要我处理的合并请求' % (teamUser.username)
    feedAction = FeedAction()
    feedAction.set_user_position(teamUser.id, PositionKey.PULL)
    pullRequests = RepoManager.list_pullRequest_by_teamUserId_mergeUserId(teamUser.id, request.user.id)
    response_dictionary = {'current': current, 'title': title, 'pullRequests': pullRequests}
    response_dictionary.update(_get_common_team_dict(request, teamUser, teamUserprofile))
    return render_to_response('team/pull_merge.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
@login_required
def pull_request(request, username):
    (teamUser, teamUserprofile) = _get_team_user_userprofile(request, username)
    current = 'pull'; title = u'%s / 我创建的合并请求' % (teamUser.username)
    feedAction = FeedAction()
    feedAction.set_user_position(teamUser.id, PositionKey.PULL)
    pullRequests = RepoManager.list_pullRequest_by_teamUserId_pullUserId(teamUser.id, request.user.id)
    response_dictionary = {'current': current, 'title': title, 'pullRequests': pullRequests}
    response_dictionary.update(_get_common_team_dict(request, teamUser, teamUserprofile))
    return render_to_response('team/pull_request.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def issues_default(request, username):
    return issues(request, username, 0)

@login_required
def issues(request, username, page):
    (teamUser, teamUserprofile) = _get_team_user_userprofile(request, username)
    current = 'issues'; title = u'%s / 问题' % (teamUser.username)
    feedAction = FeedAction()
    feedAction.set_user_position(teamUser.id, PositionKey.ISSUES)
    page = int(page); page_size = 50; offset = page*page_size; row_count = page_size + 1
    raw_issues = IssueManager.list_issues_by_teamUserId_assigned(teamUser.id, request.user.id, 'modify_time', offset, row_count)
    issues = conver_issues(raw_issues)

    hasPre = False ; hasNext = False
    if page > 0:
        hasPre = True 
    if len(issues) > page_size:
        hasNext = True
        issues.pop()
    response_dictionary = {'current': current, 'title': title, 'issues': issues, 'page': page, 'hasPre': hasPre, 'hasNext': hasNext}
    response_dictionary.update(_get_common_team_dict(request, teamUser, teamUserprofile))
    return render_to_response('team/issues.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def notif(request, username):
    (teamUser, teamUserprofile) = _get_team_user_userprofile(request, username)
    current = 'notif'; title = u'%s / 我的通知' % (teamUser.username)
    feedAction = FeedAction()
    feedAction.set_user_position(teamUser.id, PositionKey.NOTIF)
    notifMessages = FeedManager.list_notifmessage_by_toUserId_teamUserId(request.user.id, teamUser.id, 0, 500)
    response_dictionary = {'current': current, 'title': title, 'notifMessages': notifMessages}
    response_dictionary.update(_get_common_team_dict(request, teamUser, teamUserprofile))
    return render_to_response('team/notif.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def repo(request, username):
    (teamUser, teamUserprofile) = _get_team_user_userprofile(request, username)
    current = 'repo'; title = u'%s / 仓库列表' % (teamUser.username)
    teamMember = TeamManager.get_teamMember_by_userId_teamUserId(request.user.id, teamUser.id)
    repos = []
    # is team member
    if teamMember:
        repos = RepoManager.list_repo_by_userId(teamUser.id, 0, 1000)
    else:
        repos = RepoManager.list_unprivate_repo_by_userId(teamUser.id, 0, 1000)
    response_dictionary = {'current': current, 'title': title, 'repos': repos}
    response_dictionary.update(_get_common_team_dict(request, teamUser, teamUserprofile))
    return render_to_response('team/repo.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def settings(request, username):
    return profile(request, username)

@login_required
def profile(request, username):
    (teamUser, teamUserprofile) = _get_team_user_userprofile(request, username)
    current = 'settings'; sub_nav = 'profile'; title = u'%s / 设置 / 信息' % (teamUser.username)
    teamprofileForm = TeamprofileForm(instance = teamUserprofile)
    if request.method == 'POST':
        teamprofileForm = TeamprofileForm(request.POST, instance = teamUserprofile)
        new_teamUserprofile = teamprofileForm.save(commit=False)
        new_teamUserprofile.username = userprofile.username
        new_teamUserprofile.save()
        return HttpResponseRedirect('/%s/-/settings/profile/' % username)
    response_dictionary = {'current': current, 'title': title, 'sub_nav': sub_nav, 'teamUser': teamUser, 'teamUserprofile': teamUserprofile, 'teamprofileForm': teamprofileForm}
    response_dictionary.update(_get_common_team_dict(request, teamUser, teamUserprofile))
    return render_to_response('team/profile.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def members(request, username):
    (teamUser, teamUserprofile) = _get_team_user_userprofile(request, username)
    current = 'settings'; sub_nav = 'members'; title = u'%s / 设置 / 成员' % (teamUser.username)
    teamMembers = TeamManager.list_teamMember_by_teamUserId(teamUser.id)
    response_dictionary = {'current': current, 'title': title, 'sub_nav': sub_nav, 'teamMembers': teamMembers}
    response_dictionary.update(_get_common_team_dict(request, teamUser, teamUserprofile))
    return render_to_response('team/members.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
@require_http_methods(["POST"])
def add_member(request, username):
    (teamUser, teamUserprofile) = _get_team_user_userprofile(request, username)
    teamMember = TeamManager.get_teamMember_by_userId_teamUserId(request.user.id, teamUser.id)
    if not teamMember or not teamMember.has_admin_rights():
        return _response_not_manage_rights(request)
    teamMember = None
    username_or_email = request.POST.get('username_or_email', '')
    if '@' in username_or_email:
        user = GsuserManager.get_user_by_email(username_or_email)
        if not user:
            ref_hash = '%032x' % random.getrandbits(128)
            ref_message = u'用户 %s 邀请您注册Gitshell，成为团队 %s 的成员' % (request.user.username, username)
            userViaRef = UserViaRef(email=username_or_email, ref_type=REF_TYPE.VIA_TEAM_MEMBER, ref_hash=ref_hash, ref_message=ref_message, first_refid = teamUser.id, first_refname = teamUser.username)
            userViaRef.save()
            join_url = 'https://gitshell.com/join/ref/%s/' % ref_hash
            Mailer().send_join_via_team_addmember(request.user, teamUser, username_or_email, join_url)
            return json_httpResponse({'code': 301, 'result': 'failed', 'message': u'邮箱 %s 未注册，已经发送邮件邀请对方注册' % username_or_email})
        teamMember = TeamManager.add_teamMember_by_email(teamUser, username_or_email)
    else:
        teamMember = TeamManager.add_teamMember_by_username(teamUser, username_or_email)
    if not teamMember:
        return json_httpResponse({'code': 404, 'message': u'没有相关用户，不能是团队帐号'})
    return json_httpResponse({'code': 200, 'message': u'成功添加用户'})

@login_required
@require_http_methods(["POST"])
def member_leave(request, username):
    (teamUser, teamUserprofile) = _get_team_user_userprofile(request, username)
    teamMember = TeamManager.get_teamMember_by_userId_teamUserId(request.user.id, teamUser.id)
    if not teamMember:
        return _response_not_manage_rights(request)
    teamMembers = TeamManager.list_teamMember_by_teamUserId(teamMember.team_user_id)
    if _has_other_admin_teamMember(request, teamMember, teamMembers):
        teamMember.visibly = 1
        teamMember.save()
        return json_httpResponse({'code': 200, 'message': u'用户退出成功'})
    return json_httpResponse({'code': 500, 'message': u'用户退出失败，一个团队帐号至少需要保留一个管理员'})

@login_required
@require_http_methods(["POST"])
def remove_member(request, username):
    (manage_teamMember, teamMember) = _get_teamMember_by_manageTeamMemberId(request)
    if not teamMember or not teamMember.has_admin_rights():
        return _response_not_manage_rights(request)
    teamMembers = TeamManager.list_teamMember_by_teamUserId(teamMember.team_user_id)
    if _has_other_admin_teamMember(request, manage_teamMember, teamMembers):
        manage_teamMember.visibly = 1
        manage_teamMember.save()
        return json_httpResponse({'code': 200, 'message': u'删除用户成功'})
    return json_httpResponse({'code': 500, 'message': u'删除用户失败，一个团队帐号至少需要保留一个管理员'})

@login_required
@require_http_methods(["POST"])
def grant_admin(request, username):
    (manage_teamMember, teamMember) = _get_teamMember_by_manageTeamMemberId(request)
    if not teamMember or not teamMember.has_admin_rights():
        return _response_not_manage_rights(request)
    manage_teamMember.is_admin = 1
    manage_teamMember.save()
    return json_httpResponse({'code': 200, 'message': u'赋予管理员权限'})

@login_required
@require_http_methods(["POST"])
def cancal_admin(request, username):
    (manage_teamMember, teamMember) = _get_teamMember_by_manageTeamMemberId(request)
    if not teamMember or not teamMember.has_admin_rights():
        return _response_not_manage_rights(request)
    teamMembers = TeamManager.list_teamMember_by_teamUserId(teamMember.team_user_id)
    if _has_other_admin_teamMember(request, manage_teamMember, teamMembers):
        manage_teamMember.is_admin = 0
        manage_teamMember.save()
        return json_httpResponse({'code': 200, 'message': u'赋予管理员权限'})
    return json_httpResponse({'code': 500, 'message': u'解除管理员失败，一个团队帐号至少需要保留一个管理员'})

@login_required
def destroy(request, username):
    (teamUser, teamUserprofile) = _get_team_user_userprofile(request, username)
    teamMember = TeamManager.get_teamMember_by_userId_teamUserId(request.user.id, teamUser.id)
    if not teamMember or not teamMember.has_admin_rights():
        return _response_not_manage_rights(request)
    current = 'settings'; sub_nav = 'destroy'; title = u'%s / 设置 / 删除帐号' % (teamUser.username)
    response_dictionary = {'current': current, 'title': title, 'sub_nav': sub_nav}
    response_dictionary.update(_get_common_team_dict(request, teamUser, teamUserprofile))
    return render_to_response('team/destroy.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
@require_http_methods(["POST"])
def destroy_confirm(request, username):
    (teamUser, teamUserprofile) = _get_team_user_userprofile(request, username)
    teamMember = TeamManager.get_teamMember_by_userId_teamUserId(request.user.id, teamUser.id)
    if not teamMember or not teamMember.has_admin_rights():
        return _response_not_manage_rights(request)
    teamRepos = RepoManager.list_repo_by_userId(teamUser.id, 0, 1000)
    for teamRepo in teamRepos:
        RepoManager.delete_repo(teamUser, teamUserprofile, teamRepo)
    teamMembers = TeamManager.list_teamMember_by_teamUserId(teamUser.id)
    for teamMember in teamMembers:
        teamMember.visibly = 1
        teamMember.save()
    teamUser.delete()
    teamUserprofile.visibly = 1
    teamUserprofile.save()
    return json_httpResponse({'code': 200, 'message': u'已经删除了团队帐号'})

def _get_teamMember_by_manageTeamMemberId(request):
    teamMember_id = int(request.POST.get('teamMember_id', 0))
    manage_teamMember = TeamManager.get_teamMember_by_id(teamMember_id)
    if not manage_teamMember:
        return None
    teamMember = TeamManager.get_teamMember_by_userId_teamUserId(request.user.id, manage_teamMember.team_user_id)
    if not teamMember or not teamMember.has_admin_rights():
        return (None, None)
    return (manage_teamMember, teamMember)

def _has_other_admin_teamMember(request, manage_teamMember, teamMembers):
    for teamMember in teamMembers:
        if teamMember.id != manage_teamMember.id and teamMember.has_admin_rights():
            return True
    return False

def _response_not_manage_rights(request):
    return json_httpResponse({'code': 403, 'message': u'没有管理员权限'})

def _get_common_team_dict(request, teamUser, teamUserprofile):
    has_admin_rights = False
    teamMember = TeamManager.get_teamMember_by_userId_teamUserId(request.user.id, teamUser.id)
    if teamMember and teamMember.has_admin_rights():
        has_admin_rights = True
    return {'teamUser': teamUser, 'teamUserprofile': teamUserprofile, 'has_admin_rights': has_admin_rights}

def _get_team_user_userprofile(request, username):
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


