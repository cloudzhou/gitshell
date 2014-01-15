# -*- coding: utf-8 -*-  
import random, re, json, time
import httplib, urllib
from datetime import datetime
import base64, hashlib
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.cache import cache
from django.core.validators import email_re
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate as auth_authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User, UserManager, check_password
from django.db import IntegrityError
from gitshell.objectscache.models import CacheKey
from gitshell.gsuser.Forms import LoginForm, JoinForm, ResetpasswordForm0, ResetpasswordForm1, SkillsForm, RecommendsForm
from gitshell.gsuser.models import UserEmail, Recommend, Userprofile, GsuserManager, ThirdpartyUser, REF_TYPE, COMMON_EMAIL_DOMAIN
from gitshell.gsuser.middleware import MAIN_NAVS
from gitshell.gsuser.utils import UrlRouter
from gitshell.repo.models import RepoManager
from gitshell.team.models import TeamManager
from gitshell.stats.models import StatsManager
from gitshell.feed.feed import FeedAction
from gitshell.feed.mailUtils import Mailer
from gitshell.stats import timeutils
from gitshell.stats.models import StatsManager
from gitshell.settings import logger
from gitshell.feed.views import get_feeds_as_json
from gitshell.viewtools.views import json_httpResponse, json_success, json_failed
from gitshell.thirdparty.views import github_oauth_access_token, github_get_thirdpartyUser, github_authenticate, github_list_repo

def user(request, user_name):
    title = u'%s / 概括' % user_name
    gsuser = GsuserManager.get_user_by_name(user_name)
    if gsuser is None:
        raise Http404
    gsuserprofile = GsuserManager.get_userprofile_by_id(gsuser.id)
    if gsuserprofile.is_team_account == 1 and TeamManager.is_teamMember(gsuser.id, request.user.id):
        return HttpResponseRedirect('/%s/-/dashboard/' % user_name)
    recommendsForm = RecommendsForm()
    repos = []
    if gsuser.id == request.user.id:
        repos = RepoManager.list_repo_by_userId(gsuser.id, 0, 100)
    else:
        repos = RepoManager.list_unprivate_repo_by_userId(gsuser.id, 0, 100)

    now = datetime.now()
    last30days = timeutils.getlast30days(now)
    last30days_commit = get_last30days_commit(gsuser)

    feedAction = FeedAction()

    raw_watch_repos = feedAction.get_watch_repos(gsuser.id, 0, 10)
    watch_repo_ids = [int(x[0]) for x in raw_watch_repos]
    watch_repos_map = RepoManager.merge_repo_map(watch_repo_ids)
    watch_repos = [watch_repos_map[x] for x in watch_repo_ids if x in watch_repos_map]

    pri_user_feeds = feedAction.get_pri_user_feeds(gsuser.id, 0, 10)
    pub_user_feeds = feedAction.get_pub_user_feeds(gsuser.id, 0, 10)
    feeds_as_json = get_feeds_as_json(request, pri_user_feeds, pub_user_feeds)

    star_repos = RepoManager.list_star_repo(gsuser.id, 0, 20)

    response_dictionary = {'mainnav': 'user', 'title': title, 'recommendsForm': recommendsForm, 'repos': repos, 'watch_repos': watch_repos, 'star_repos': star_repos, 'last30days': last30days, 'last30days_commit': last30days_commit, 'feeds_as_json': feeds_as_json}
    response_dictionary.update(get_common_user_dict(request, gsuser, gsuserprofile))
    return render_to_response('user/user.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def active(request, user_name):
    title = u'%s / 动态' % user_name
    gsuser = GsuserManager.get_user_by_name(user_name)
    if gsuser is None:
        raise Http404
    gsuserprofile = GsuserManager.get_userprofile_by_id(gsuser.id)
    feedAction = FeedAction()
    pri_user_feeds = feedAction.get_pri_user_feeds(gsuser.id, 0, 50)
    pub_user_feeds = feedAction.get_pub_user_feeds(gsuser.id, 0, 50)
    feeds_as_json = get_feeds_as_json(request, pri_user_feeds, pub_user_feeds)
    response_dictionary = {'mainnav': 'user', 'title': title, 'feeds_as_json': feeds_as_json}
    response_dictionary.update(get_common_user_dict(request, gsuser, gsuserprofile))
    return render_to_response('user/active.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def stats(request, user_name):
    title = u'%s / 统计' % user_name
    gsuser = GsuserManager.get_user_by_name(user_name)
    if gsuser is None:
        raise Http404
    gsuserprofile = GsuserManager.get_userprofile_by_id(gsuser.id)
    now = datetime.now()
    last30days = timeutils.getlast30days(now)
    last30days_commit = get_last30days_commit(gsuser)
    response_dictionary = {'mainnav': 'user', 'title': title, 'last30days': last30days, 'last30days_commit': last30days_commit}
    response_dictionary.update(get_common_user_dict(request, gsuser, gsuserprofile))
    return render_to_response('user/stats.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def watch_user(request, user_name):
    title = u'%s / 关注的用户' % user_name
    gsuser = GsuserManager.get_user_by_name(user_name)
    if gsuser is None:
        raise Http404
    gsuserprofile = GsuserManager.get_userprofile_by_id(gsuser.id)

    feedAction = FeedAction()
    raw_watch_users = feedAction.get_watch_users(gsuser.id, 0, 100)
    watch_user_ids = [int(x[0]) for x in raw_watch_users]
    watch_users_map = GsuserManager.map_users(watch_user_ids)
    watch_users = [watch_users_map[x] for x in watch_user_ids if x in watch_users_map]

    raw_bewatch_users = feedAction.get_bewatch_users(gsuser.id, 0, 100)
    bewatch_user_ids = [int(x[0]) for x in raw_bewatch_users]
    bewatch_users_map = GsuserManager.map_users(bewatch_user_ids)
    bewatch_users = [bewatch_users_map[x] for x in bewatch_user_ids if x in bewatch_users_map]
    # fixed on detect
    need_fix = False
    if len(watch_users) != gsuserprofile.watch:
        gsuserprofile.watch = len(watch_users)
        need_fix = True
    if len(bewatch_users) < 100 and len(bewatch_users) != gsuserprofile.be_watched:
        gsuserprofile.be_watched = len(bewatch_users) 
        need_fix = True
    if need_fix:
        gsuserprofile.save()

    response_dictionary = {'mainnav': 'user', 'title': title, 'watch_users': watch_users, 'bewatch_users': bewatch_users}
    response_dictionary.update(get_common_user_dict(request, gsuser, gsuserprofile))
    return render_to_response('user/watch_user.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def star_repo(request, user_name):
    title = u'%s / 标星的仓库' % user_name
    gsuser = GsuserManager.get_user_by_name(user_name)
    if gsuser is None:
        raise Http404
    gsuserprofile = GsuserManager.get_userprofile_by_id(gsuser.id)
    star_repos = RepoManager.list_star_repo(gsuser.id, 0, 500)
    response_dictionary = {'mainnav': 'user', 'title': title, 'star_repos': star_repos}
    response_dictionary.update(get_common_user_dict(request, gsuser, gsuserprofile))
    return render_to_response('user/star_repo.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def watch_repo(request, user_name):
    title = u'%s / 关注的仓库' % user_name
    gsuser = GsuserManager.get_user_by_name(user_name)
    if gsuser is None:
        raise Http404
    gsuserprofile = GsuserManager.get_userprofile_by_id(gsuser.id)

    feedAction = FeedAction()
    raw_watch_repos = feedAction.get_watch_repos(gsuser.id, 0, 100)
    watch_repo_ids = [int(x[0]) for x in raw_watch_repos]
    watch_repos_map = RepoManager.merge_repo_map_ignore_visibly(watch_repo_ids)
    watch_repos = [watch_repos_map[x] for x in watch_repo_ids if x in watch_repos_map]

    response_dictionary = {'mainnav': 'user', 'title': title, 'watch_repos': watch_repos}
    # fixed on detect
    if len(watch_repos) != gsuserprofile.watchrepo:
        gsuserprofile.watchrepo = len(watch_repos)
        gsuserprofile.save()

    response_dictionary.update(get_common_user_dict(request, gsuser, gsuserprofile))
    return render_to_response('user/watch_repo.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def recommend(request, user_name):
    gsuser = GsuserManager.get_user_by_name(user_name)
    if gsuser is None:
        raise Http404
    if request.method == 'POST':
        recommendsForm = RecommendsForm(request.POST)
        if recommendsForm.is_valid() and request.user.is_authenticated():
            content = recommendsForm.cleaned_data['content'].strip()
            if content != '':
                recommend = Recommend()
                recommend.user_id = gsuser.id
                recommend.content = content
                recommend.from_user_id = request.user.id
                recommend.save()
    gsuserprofile = GsuserManager.get_userprofile_by_id(gsuser.id)
    raw_recommends = GsuserManager.list_recommend_by_userid(gsuser.id, 0, 50)
    recommends = __conver_to_recommends_vo(raw_recommends)

    response_dictionary = {'mainnav': 'user', 'recommends': recommends}
    response_dictionary.update(get_common_user_dict(request, gsuser, gsuserprofile))
    return render_to_response('user/recommend.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@require_http_methods(["POST"])
def find(request):
    user = None
    is_user_exist = False
    username = request.POST.get('username')
    if username is not None:
        if username in MAIN_NAVS:
            is_user_exist = True
        user = GsuserManager.get_user_by_name(username)
    email = request.POST.get('email')
    if email is not None:
        user = GsuserManager.get_user_by_email(email)
    if user is not None:
        is_user_exist = True
    response_dictionary = { 'is_user_exist': is_user_exist }
    return json_httpResponse(response_dictionary)

@login_required
@require_http_methods(["POST"])
def change(request):
    thirdpartyUser = GsuserManager.get_thirdpartyUser_by_id(request.user.id)
    user = None
    is_user_exist = True
    is_exist_repo = False
    username = request.POST.get('username')
    if username is not None and re.match("^[a-zA-Z0-9_-]+$", username) and username != request.user.username and username not in MAIN_NAVS and not username.startswith('-'):
        repo_count = RepoManager.count_repo_by_userId(request.user.id)
        if repo_count > 0:
            return json_httpResponse({'is_exist_repo': True})
        user = GsuserManager.get_user_by_name(username)
        if user is None:
            request.user.username = username
            request.userprofile.username = username
            request.user.save()
            request.userprofile.save()
            for repo in RepoManager.list_repo_by_userId(request.user.id, 0, 100):
                repo.username = username
                repo.save()
            is_user_exist = False
    goto = ''
    email = request.POST.get('email')
    if email is not None and email_re.match(email):
        user = GsuserManager.get_user_by_email(email)
        if user is None:
            Mailer().send_change_email(request.user, email)
            email_suffix = email.split('@')[-1]
            if email_suffix in COMMON_EMAIL_DOMAIN:
                goto = COMMON_EMAIL_DOMAIN[email_suffix]
            is_user_exist = False
    if thirdpartyUser is not None:
        thirdpartyUser.init = 1
        thirdpartyUser.save()
    if username == request.user.username:
        is_user_exist = False
    response_dictionary = { 'is_exist_repo': is_exist_repo, 'is_user_exist': is_user_exist, 'goto': goto, 'new_username': username, 'new_email': email }
    return json_httpResponse(response_dictionary)

@login_required
@require_http_methods(["POST"])
def recommend_delete(request, user_name, recommend_id):
    gsuser = GsuserManager.get_user_by_name(user_name)
    if gsuser is None:
        raise Http404
    recommend = GsuserManager.get_recommend_by_id(recommend_id)
    if recommend.user_id == request.user.id:
        recommend.visibly = 1
        recommend.save()
    return json_success(u'成功删除评论')

@login_required
@require_http_methods(["POST"])
def watch(request, user_name):
    gsuserprofile = GsuserManager.get_userprofile_by_name(user_name)
    if gsuserprofile is None:
        message = u'用户不存在'
        return json_failed(404, message)
    if not RepoManager.watch_user(request.userprofile, gsuserprofile):
        message = u'关注失败，关注数量超过限制或者用户不允许关注'
        return json_failed(500, message)
    return json_success(u'成功关注用户 %s' % user_name)

@login_required
@require_http_methods(["POST"])
def unwatch(request, user_name):
    gsuserprofile = GsuserManager.get_userprofile_by_name(user_name)
    if gsuserprofile is None:
        message = u'用户不存在'
        return json_failed(404, message)
    if not RepoManager.unwatch_user(request.userprofile, gsuserprofile):
        message = u'取消关注失败，可能用户未被关注'
        return json_failed(500, message)
    return json_success(u'成功取消关注用户 %s' % user_name)

@login_required
def switch(request, user_name, current_user_id):
    current_user_id = int(current_user_id)
    new_current_user_id = request.user.id
    if current_user_id != request.user.id:
        teamMember = TeamManager.get_teamMember_by_teamUserId_userId(current_user_id, request.user.id)
        if teamMember:
            new_current_user_id = current_user_id
    request.userprofile.current_user_id = new_current_user_id
    request.userprofile.save()
    return HttpResponseRedirect(request.urlRouter.route('/dashboard/'))

def login(request):
    loginForm = LoginForm()
    error = u''; title = u'登录'
    if request.method == 'POST':
        loginForm = LoginForm(request.POST)
        if loginForm.is_valid():
            email = loginForm.cleaned_data['email']
            password = loginForm.cleaned_data['password']
            rememberme = loginForm.cleaned_data['rememberme']
            if rememberme:
                request.session.set_expiry(2592000)
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = None
            if user is not None and user.check_password(password):
                user = auth_authenticate(username=user.username, password=password)
                if user is not None and user.is_active:
                    auth_login(request, user)
                    url_next = '/dashboard/'
                    if request.GET.get('next') is not None:
                        url_next = request.GET.get('next')
                    return HttpResponseRedirect(url_next)
            if user is None:
                error = u'%s 还没有注册' % email
            else:
                error = u'密码不正确'
        else:
            error = u'请检查邮箱密码，验证码是否正确，注意大小写和前后空格。'
    response_dictionary = {'error': error, 'title': title, 'loginForm': loginForm}
    return render_to_response('user/login.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def login_github(request):
    code = request.GET.get('code')
    if request.GET.get('code') is None:
        return HttpResponseRedirect('/login/')
    access_token = github_oauth_access_token(code)
    if access_token == '':
        return HttpResponseRedirect('/login/')
    thirdpartyUser = github_get_thirdpartyUser(access_token)
    if thirdpartyUser is None or thirdpartyUser.tp_id is None or thirdpartyUser.tp_username is None:
        return HttpResponseRedirect('/login/')
    user = github_authenticate(thirdpartyUser)
    if user is not None:
        request.session.set_expiry(2592000)
        user.backend='django.contrib.auth.backends.ModelBackend'
        auth_login(request, user)
        thirdpartyUser = GsuserManager.get_thirdpartyUser_by_id(user.id)
    if thirdpartyUser.init == 0:
        return HttpResponseRedirect('/settings/change_username_email/')
    return HttpResponseRedirect('/dashboard/')

@login_required
def login_github_apply(request):
    error = u''
    code = request.GET.get('code')
    if code is None:
        error = u'GitHub 关联失败，没有相关 code'
    access_token = github_oauth_access_token(code)
    if access_token == '':
        error = u'GitHub 关联失败，获取不到 access_token，请再次重试'
    thirdpartyUser = github_get_thirdpartyUser(access_token)
    if thirdpartyUser is None or thirdpartyUser.tp_id is None or thirdpartyUser.tp_username is None:
        error = u'获取不到 GitHub 信息，请再次重试'
    thirdpartyUser_find = GsuserManager.get_thirdpartyUser_by_type_tpId(ThirdpartyUser.GITHUB, thirdpartyUser.tp_id)
    if thirdpartyUser_find is not None:
        error = u'该 GitHub 账户已经关联 Gitshell，请直接使用 GitHub 账户登录'
    if error != '':
        return HttpResponseRedirect('/%s/-/repo/create/?%s#via-github' % (request.user.username, urllib.urlencode({'apply_error': error.encode('utf8')})))
    thirdpartyUser.user_type = ThirdpartyUser.GITHUB
    thirdpartyUser.access_token = access_token
    thirdpartyUser.id = request.user.id
    thirdpartyUser.init = 1
    thirdpartyUser.save()
    return HttpResponseRedirect('/%s/-/repo/create/#via-github' % request.user.username)

@login_required
@require_http_methods(["POST"])
def login_github_relieve(request):
    thirdpartyUser_find = GsuserManager.get_thirdpartyUser_by_id(request.user.id)
    if thirdpartyUser_find is not None:
        thirdpartyUser_find.delete()
    response_dictionary = {'code': 200, 'result': 'success'}
    return json_httpResponse(response_dictionary)

def logout(request):
    auth_logout(request)
    return HttpResponseRedirect('/')

def join(request, step):
    joinForm = JoinForm()
    return _join(request, joinForm, 'base', '', step)

def join_via_ref(request, ref_hash):
    joinForm = JoinForm()
    joinForm.fields['ref_hash'].initial = ref_hash
    userViaRef = GsuserManager.get_userViaRef_by_refhash(ref_hash)
    tip = ''
    if userViaRef:
        tip = userViaRef.ref_message
    if userViaRef and userViaRef.email:
        joinForm.fields['email'].initial = userViaRef.email
        joinForm.fields['username'].initial = userViaRef.email.split('@')[0]
    if userViaRef and userViaRef.username:
        joinForm.fields['username'].initial = userViaRef.username
    return _join(request, joinForm, 'ref', tip, '0')

def _join(request, joinForm, joinVia, tip, step):
    if step is None:
        step = '0'
    error = u''; title = u'注册'
    if step == '0' and request.method == 'POST':
        joinForm = JoinForm(request.POST)
        if joinForm.is_valid():
            email = joinForm.cleaned_data['email']
            username = joinForm.cleaned_data['username']
            password = joinForm.cleaned_data['password']
            ref_hash = joinForm.cleaned_data['ref_hash']
            user_by_email = GsuserManager.get_user_by_email(email)
            user_by_username = GsuserManager.get_user_by_name(username)
            if user_by_email is None and user_by_username is None:
                if ref_hash:
                    userViaRef = GsuserManager.get_userViaRef_by_refhash(ref_hash)
                    if userViaRef and _create_user_and_authenticate(request, username, email, password, ref_hash, True):
                        return HttpResponseRedirect('/join/3/')
                client_ip = _get_client_ip(request)
                cache_join_client_ip_count = cache.get(CacheKey.JOIN_CLIENT_IP % client_ip)
                if cache_join_client_ip_count is None:
                    cache_join_client_ip_count = 0
                cache_join_client_ip_count = cache_join_client_ip_count + 1
                cache.set(CacheKey.JOIN_CLIENT_IP % client_ip, cache_join_client_ip_count)
                if cache_join_client_ip_count < 10 and _create_user_and_authenticate(request, username, email, password, ref_hash, False):
                    return HttpResponseRedirect('/join/3/')
                Mailer().send_verify_account(email, username, password, ref_hash)
                goto = ''
                email_suffix = email.split('@')[-1]
                if email_suffix in COMMON_EMAIL_DOMAIN:
                    goto = COMMON_EMAIL_DOMAIN[email_suffix]
                return HttpResponseRedirect('/join/1/?goto=' + goto)
            error = u'欢迎回来, email: %s 或者 name: %s 已经注册过了, 您只需要直接登陆就行。' % (email, username)
        else:
            error = u'啊? 邮箱或验证码有误输入。注意大小写和前后空格。'
    if len(step) > 1:
        email = cache.get(step + '_email')
        username = cache.get(step + '_username')
        password = cache.get(step + '_password')
        ref_hash = cache.get(step + '_ref_hash')
        if email is None or username is None or password is None or not email_re.match(email) or not re.match("^[a-zA-Z0-9_-]+$", username) or username.startswith('-') or username in MAIN_NAVS:
            return HttpResponseRedirect('/join/4/')
        if _create_user_and_authenticate(request, username, email, password, ref_hash, True):
            return HttpResponseRedirect('/join/3/')
        else:
            error = u'啊? 用户名或密码有误输入，注意大小写和前后空格。'
    response_dictionary = {'step': step, 'error': error, 'title': title, 'joinForm': joinForm, 'joinVia': joinVia, 'tip': tip}
    return render_to_response('user/join.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def resetpassword(request, step):
    if step is None:
        step = '0'
    error = u''; title = u'重置密码'
    resetpasswordForm0 = ResetpasswordForm0()
    if step == '0' and request.method == 'POST':
        resetpasswordForm0 = ResetpasswordForm0(request.POST)
        if resetpasswordForm0.is_valid():
            email = resetpasswordForm0.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = None
            if user is not None and user.is_active:
                Mailer().send_resetpassword(email)
                return HttpResponseRedirect('/resetpassword/1/')
            error = u'邮箱 %s 还没有注册' % email
        else:
            error = u'请检查邮箱，验证码是否正确'
    resetpasswordForm1 = ResetpasswordForm1()
    if len(step) > 1 and request.method == 'POST':
        resetpasswordForm1 = ResetpasswordForm1(request.POST)
        if resetpasswordForm1.is_valid():
            email = cache.get(step)
            if email is not None and email_re.match(email):
                password = resetpasswordForm1.cleaned_data['password']
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    user = None
                if user is not None and user.is_active:
                    user.set_password(password)
                    user.save()
                    user = auth_authenticate(username=user.username, password=password)
                    auth_login(request, user)
                    cache.delete(step)
                    return HttpResponseRedirect('/resetpassword/3/')
            return HttpResponseRedirect('/resetpassword/4/')
    response_dictionary = {'step': step, 'error': error, 'title': title, 'resetpasswordForm0': resetpasswordForm0, 'resetpasswordForm1': resetpasswordForm1}
    return render_to_response('user/resetpassword.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def bind(request, ref_hash):
    userViaRef = None
    if ref_hash:
        userViaRef = GsuserManager.get_userViaRef_by_refhash(ref_hash)
        GsuserManager.handle_user_via_refhash(request.user, ref_hash)
    if userViaRef:
        is_verify = 1
        if userViaRef.ref_type == REF_TYPE.VIA_REPO_MEMBER:
            GsuserManager.add_useremail(request.user, userViaRef.email, is_verify)
            return HttpResponseRedirect('/%s/%s/' % (userViaRef.first_refname, userViaRef.second_refname))
        elif userViaRef.ref_type == REF_TYPE.VIA_TEAM_MEMBER:
            GsuserManager.add_useremail(request.user, userViaRef.email, is_verify)
            return HttpResponseRedirect('/%s/' % (userViaRef.first_refname))
    return HttpResponseRedirect('/dashboard/')

def get_common_user_dict(request, gsuser, gsuserprofile):
    feedAction = FeedAction()
    raw_watch_users = feedAction.get_watch_users(gsuser.id, 0, 10)
    raw_bewatch_users = feedAction.get_bewatch_users(gsuser.id, 0, 10)
    watch_user_ids = [int(x[0]) for x in raw_watch_users]
    bewatch_user_ids = [int(x[0]) for x in raw_bewatch_users]
    watch_users_map = GsuserManager.map_users(watch_user_ids)
    bewatch_users_map = GsuserManager.map_users(bewatch_user_ids)
    watch_users = [watch_users_map[x] for x in watch_user_ids if x in watch_users_map]
    bewatch_users = [bewatch_users_map[x] for x in bewatch_user_ids if x in bewatch_users_map]
    raw_recommends = GsuserManager.list_recommend_by_userid(gsuser.id, 0, 20)
    recommends = __conver_to_recommends_vo(raw_recommends)

    is_watched_user = False
    if request.user.is_authenticated():
        is_watched_user = RepoManager.is_watched_user(request.user.id, gsuser.id)
    return {'gsuser': gsuser, 'gsuserprofile': gsuserprofile, 'watch_users': watch_users, 'bewatch_users': bewatch_users, 'recommends': recommends, 'is_watched_user': is_watched_user, 'show_common': True}

def get_last30days_commit(gsuser):
    now = datetime.now()
    last30days = timeutils.getlast30days(now)
    raw_last30days_commit = StatsManager.list_user_stats(gsuser.id, 'day', datetime.fromtimestamp(last30days[-1]), datetime.fromtimestamp(last30days[0]))
    last30days_commit = dict([(time.mktime(x.date.timetuple()), int(x.count)) for x in raw_last30days_commit])
    return last30days_commit

def stats(request, user_name):
    user = GsuserManager.get_user_by_name(user_name)
    if user is None:
        raise Http404
    stats_dict = get_stats_dict(request, user)
    gsuserprofile = GsuserManager.get_userprofile_by_id(user.id)
    response_dictionary = {'title': u'%s / 最近统计' % (user.username), 'gsuserprofile': gsuserprofile}
    response_dictionary.update(stats_dict)
    return render_to_response('user/stats.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def get_stats_dict(request, user):
    now = datetime.now()
    last12hours = timeutils.getlast12hours(now)
    last7days = timeutils.getlast7days(now)
    last30days = timeutils.getlast30days(now)
    last12months = timeutils.getlast12months(now)
    raw_last12hours_commit = StatsManager.list_user_stats(user.id, 'hour', datetime.fromtimestamp(last12hours[-1]), datetime.fromtimestamp(last12hours[0]))
    last12hours_commit = dict([(time.mktime(x.date.timetuple()), int(x.count)) for x in raw_last12hours_commit])
    raw_last30days_commit = StatsManager.list_user_stats(user.id, 'day', datetime.fromtimestamp(last30days[-1]), datetime.fromtimestamp(last30days[0]))
    last30days_commit = dict([(time.mktime(x.date.timetuple()), int(x.count)) for x in raw_last30days_commit])
    last7days_commit = {}
    for x in last7days:
        if x in last30days_commit:
            last7days_commit[x] = last30days_commit[x]
    raw_last12months_commit = StatsManager.list_user_stats(user.id, 'month', datetime.fromtimestamp(last12months[-1]), datetime.fromtimestamp(last12months[0]))
    last12months_commit = dict([(time.mktime(x.date.timetuple()), int(x.count)) for x in raw_last12months_commit])

    round_week = timeutils.get_round_week(now)
    round_month = timeutils.get_round_month(now)
    round_year = timeutils.get_round_year(now)

    raw_per_last_week_commits = StatsManager.list_user_repo_stats(user.id, 'week', round_week)
    raw_per_last_month_commits = StatsManager.list_user_repo_stats(user.id, 'month', round_month)
    raw_per_last_year_commits = StatsManager.list_user_repo_stats(user.id, 'year', round_year)

    raw_week_repo_ids = [x.repo_id for x in raw_per_last_week_commits]
    raw_month_repo_ids = [x.repo_id for x in raw_per_last_month_commits]
    raw_year_repo_ids = [x.repo_id for x in raw_per_last_year_commits]
    uniq_repo_ids = list(set(raw_week_repo_ids + raw_month_repo_ids + raw_year_repo_ids))
    repo_dict = RepoManager.merge_repo_map(uniq_repo_ids)

    is_yourself = False
    if request.user.is_authenticated() and user.id == request.user.id:
        is_yourself = True

    per_repo_week_commits = _list_repo_count_dict(raw_per_last_week_commits, repo_dict, is_yourself)
    per_repo_month_commits = _list_repo_count_dict(raw_per_last_month_commits, repo_dict, is_yourself)
    per_repo_year_commits = _list_repo_count_dict(raw_per_last_year_commits, repo_dict, is_yourself)
    round_week_tip = u'%s 以来参与项目' % round_week.strftime('%y/%m/%d')
    round_month_tip = u'%s 以来参与项目' %  round_month.strftime('%y/%m/%d')
    round_year_tip = u'%s 以来参与项目' %  round_year.strftime('%y/%m/%d')
    per_repo_commits = []
    if len(per_repo_week_commits) > 0:
        per_repo_commits.append({'commits': per_repo_week_commits, 'tip': round_week_tip})
    if len(per_repo_month_commits) > 0:
        per_repo_commits.append({'commits': per_repo_month_commits, 'tip': round_month_tip})
    if len(per_repo_year_commits) > 0:
        per_repo_commits.append({'commits': per_repo_year_commits, 'tip': round_year_tip})

    stats_dict = {'last12hours': last12hours, 'last7days': last7days, 'last30days': last30days, 'last12months': last12months, 'last12hours_commit': last12hours_commit, 'last7days_commit': last7days_commit, 'last30days_commit': last30days_commit, 'last12months_commit': last12months_commit, 'per_repo_commits': per_repo_commits}
    return stats_dict

def _list_repo_count_dict(raw_per_commit, repo_dict, is_yourself):
    per_commits = []
    total_count = 0
    for x in raw_per_commit:
        repo_id = x.repo_id
        if repo_id not in repo_dict or (repo_dict[repo_id]['auth_type'] != 0 and not is_yourself):
            continue
        total_count = total_count + int(x.count)
        per_commits.append({'name': repo_dict[repo_id]['name'], 'count': int(x.count)})
    for x in per_commits:
        ratio = x['count']*100/total_count
        if ratio == 0:
            ratio = 1
        x['ratio'] = ratio
    return per_commits

def __conver_to_recommends_vo(raw_recommends):
    user_ids = [x.from_user_id for x in raw_recommends]
    users_map = GsuserManager.map_users(user_ids)
    recommends_vo = [x.to_recommend_vo(users_map) for x in raw_recommends]
    return recommends_vo

def _create_user_and_authenticate(request, username, email, password, ref_hash, is_verify):
    user = None
    try:
        user = User.objects.create_user(username, email, password)
        if user is None or not user.is_active:
            return False
    except IntegrityError, e:
        logger.exception(e)
        return False
    user = auth_authenticate(username=user.username, password=password)
    auth_login(request, user)
    userprofile = Userprofile(id = user.id, username = user.username, email = user.email, imgurl = hashlib.md5(user.email.lower()).hexdigest())
    userprofile.save()
    userEmail = UserEmail(user_id = user.id, email = user.email, is_verify = is_verify, is_primary = 1, is_public = 1)
    userEmail.save()
    if ref_hash:
        GsuserManager.handle_user_via_refhash(user, ref_hash)
    return True

def _get_client_ip(request):
    x_forwarded_for = request.META.get('X-Forwarded-For')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# Note: add email unique support ! UNIQUE KEY `email` (`email`) #
