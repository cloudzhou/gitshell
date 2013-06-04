# -*- coding: utf-8 -*-  
import random, re, json, time
import httplib, urllib
from datetime import datetime
import base64, hashlib
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.mail import send_mail
from django.core.cache import cache
from django.core.validators import email_re
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate as auth_authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User, UserManager, check_password
from django.db import IntegrityError
from gitshell.gsuser.Forms import LoginForm, JoinForm, ResetpasswordForm0, ResetpasswordForm1, SkillsForm, RecommendsForm
from gitshell.gsuser.models import Recommend, Userprofile, GsuserManager, ThirdpartyUser, COMMON_EMAIL_DOMAIN
from gitshell.gsuser.middleware import MAIN_NAVS
from gitshell.repo.models import RepoManager
from gitshell.stats.models import StatsManager
from gitshell.feed.feed import FeedAction
from gitshell.stats import timeutils
from gitshell.feed.views import get_feeds_as_json
from gitshell.viewtools.views import json_httpResponse
from gitshell.thirdparty.views import github_oauth_access_token, github_get_thirdpartyUser, github_authenticate, github_list_repo

def user(request, user_name):
    gsuser = GsuserManager.get_user_by_name(user_name)
    if gsuser is None:
        raise Http404
    gsuserprofile = GsuserManager.get_userprofile_by_id(gsuser.id)
    recommendsForm = RecommendsForm()
    repos = RepoManager.list_unprivate_repo_by_userId(gsuser.id, 0, 10)
    raw_recommends = GsuserManager.list_recommend_by_userid(gsuser.id, 0, 20)
    recommends = __conver_to_recommends_vo(raw_recommends)

    feedAction = FeedAction()
    raw_watch_repos = feedAction.get_watch_repos(gsuser.id, 0, 10)
    raw_watch_users = feedAction.get_watch_users(gsuser.id, 0, 10)
    raw_bewatch_users = feedAction.get_bewatch_users(gsuser.id, 0, 10)
    watch_repo_ids = [int(x[0]) for x in raw_watch_repos]
    watch_user_ids = [int(x[0]) for x in raw_watch_users]
    bewatch_user_ids = [int(x[0]) for x in raw_bewatch_users]
    watch_repos_map = RepoManager.merge_repo_map(watch_repo_ids)
    watch_users_map = GsuserManager.map_users(watch_user_ids)
    bewatch_users_map = GsuserManager.map_users(bewatch_user_ids)
    watch_repos = [watch_repos_map[x] for x in watch_repo_ids if x in watch_repos_map]
    watch_users = [watch_users_map[x] for x in watch_user_ids if x in watch_users_map]
    bewatch_users = [bewatch_users_map[x] for x in bewatch_user_ids if x in bewatch_users_map]

    now = datetime.now()
    last30days = timeutils.getlast30days(now)
    last30days_commit = get_last30days_commit(gsuser)

    feedAction = FeedAction()
    pri_user_feeds = feedAction.get_pri_user_feeds(gsuser.id, 0, 10)
    pub_user_feeds = feedAction.get_pub_user_feeds(gsuser.id, 0, 10)
    feeds_as_json = get_feeds_as_json(request, pri_user_feeds, pub_user_feeds)

    response_dictionary = {'mainnav': 'user', 'recommendsForm': recommendsForm, 'repos': repos, 'watch_repos': watch_repos, 'watch_users': watch_users, 'bewatch_users': bewatch_users, 'last30days': last30days, 'last30days_commit': last30days_commit, 'feeds_as_json': feeds_as_json, 'recommends': recommends}
    response_dictionary.update(get_common_user_dict(request, gsuser, gsuserprofile))
    return render_to_response('user/user.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def active(request, user_name):
    gsuser = GsuserManager.get_user_by_name(user_name)
    if gsuser is None:
        raise Http404
    gsuserprofile = GsuserManager.get_userprofile_by_id(gsuser.id)
    feedAction = FeedAction()
    pri_user_feeds = feedAction.get_pri_user_feeds(gsuser.id, 0, 50)
    pub_user_feeds = feedAction.get_pub_user_feeds(gsuser.id, 0, 50)
    feeds_as_json = get_feeds_as_json(request, pri_user_feeds, pub_user_feeds)
    response_dictionary = {'mainnav': 'user', 'feeds_as_json': feeds_as_json}
    response_dictionary.update(get_common_user_dict(request, gsuser, gsuserprofile))
    return render_to_response('user/active.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def stats(request, user_name):
    gsuser = GsuserManager.get_user_by_name(user_name)
    if gsuser is None:
        raise Http404
    gsuserprofile = GsuserManager.get_userprofile_by_id(gsuser.id)
    now = datetime.now()
    last30days = timeutils.getlast30days(now)
    last30days_commit = get_last30days_commit(gsuser)
    response_dictionary = {'mainnav': 'user', 'last30days': last30days, 'last30days_commit': last30days_commit}
    response_dictionary.update(get_common_user_dict(request, gsuser, gsuserprofile))
    return render_to_response('user/stats.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def watch_user(request, user_name):
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

    response_dictionary = {'mainnav': 'user', 'watch_users': watch_users, 'bewatch_users': bewatch_users}
    response_dictionary.update(get_common_user_dict(request, gsuser, gsuserprofile))
    return render_to_response('user/watch_user.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def watch_repo(request, user_name):
    gsuser = GsuserManager.get_user_by_name(user_name)
    if gsuser is None:
        raise Http404
    gsuserprofile = GsuserManager.get_userprofile_by_id(gsuser.id)

    feedAction = FeedAction()
    raw_watch_repos = feedAction.get_watch_repos(gsuser.id, 0, 100)
    watch_repo_ids = [int(x[0]) for x in raw_watch_repos]
    watch_repos_map = RepoManager.merge_repo_map_ignore_visibly(watch_repo_ids)
    watch_repos = [watch_repos_map[x] for x in watch_repo_ids if x in watch_repos_map]

    response_dictionary = {'mainnav': 'user', 'watch_repos': watch_repos}
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
    if username is not None and re.match("^\w+$", username) and username != request.user.username and username not in MAIN_NAVS:
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
            random_hash = '%032x' % random.getrandbits(128)
            cache.set(random_hash + '_email', email)
            active_url = 'https://gitshell.com/settings/validate_email/%s/' % random_hash
            message = u'尊敬的gitshell用户：\n请点击下面的地址更改您在gitshell的登录邮箱：\n%s\n----------\n此邮件由gitshell系统发出，系统不接收回信，因此请勿直接回复。 如有任何疑问，请联系 support@gitshell.com。' % active_url
            send_mail('[gitshell]更改邮件地址', message, 'noreply@gitshell.com', [email], fail_silently=False)
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
    response_dictionary = {'result': 'success'}
    recommend = GsuserManager.get_recommend_by_id(recommend_id)
    if recommend.user_id == request.user.id:
        recommend.visibly = 1
        recommend.save()
    return json_httpResponse(response_dictionary)

@login_required
@require_http_methods(["POST"])
def network_watch(request, user_name):
    response_dictionary = {'result': 'success'}
    gsuserprofile = GsuserManager.get_userprofile_by_name(user_name)
    if gsuserprofile is None:
        message = u'用户不存在'
        return json_httpResponse({'result': 'failed', 'message': message})
    if not RepoManager.watch_user(request.userprofile, gsuserprofile):
        message = u'关注失败，关注数量超过限制或者用户不允许关注'
        return json_httpResponse({'result': 'failed', 'message': message})
    return json_httpResponse(response_dictionary)

@login_required
@require_http_methods(["POST"])
def network_unwatch(request, user_name):
    response_dictionary = {'result': 'success'}
    gsuserprofile = GsuserManager.get_userprofile_by_name(user_name)
    if gsuserprofile is None:
        message = u'用户不存在'
        return json_httpResponse({'result': 'failed', 'message': message})
    if not RepoManager.unwatch_user(request.userprofile, gsuserprofile):
        message = u'取消关注失败，可能用户未被关注'
        return json_httpResponse({'result': 'failed', 'message': message})
    return json_httpResponse(response_dictionary)

def login(request):
    loginForm = LoginForm()
    error = u''
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
                    url_next = '/home/'
                    if request.GET.get('next') is not None:
                        url_next = request.GET.get('next')
                    return HttpResponseRedirect(url_next)
            if user is None:
                error = u'%s 还没有注册' % email
            else:
                error = u'密码不正确'
        else:
            error = u'请检查邮箱密码，验证码是否正确，注意大小写和前后空格。'
    response_dictionary = {'error': error, 'loginForm': loginForm}
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
    return HttpResponseRedirect('/home/')

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
        return HttpResponseRedirect('/%s/repo/create/?%s#via-github' % (request.user.username, urllib.urlencode({'apply_error': error.encode('utf8')})))
    thirdpartyUser.user_type = ThirdpartyUser.GITHUB
    thirdpartyUser.access_token = access_token
    thirdpartyUser.id = request.user.id
    thirdpartyUser.init = 1
    thirdpartyUser.save()
    return HttpResponseRedirect('/%s/repo/create/#via-github' % request.user.username)

def logout(request):
    auth_logout(request)
    return HttpResponseRedirect('/')

def join(request, step):
    if step is None:
        step = '0'
    error = u''
    joinForm = JoinForm()
    if step == '0' and request.method == 'POST':
        joinForm = JoinForm(request.POST)
        if joinForm.is_valid():
            random_hash = '%032x' % random.getrandbits(128)
            email = joinForm.cleaned_data['email']
            username = joinForm.cleaned_data['username']
            password = joinForm.cleaned_data['password']
            user_by_email = GsuserManager.get_user_by_email(email)
            user_by_username = GsuserManager.get_user_by_name(username)
            if user_by_email is None and user_by_username is None:
                cache.set(random_hash + '_email', email)
                cache.set(random_hash + '_username', username)
                cache.set(random_hash + '_password', password)
                active_url = 'https://gitshell.com/join/%s/' % random_hash
                message = u'尊敬的gitshell用户：\n感谢您选择了gitshell，请点击下面的地址激活您在gitshell的帐号：\n%s\n----------\n此邮件由gitshell系统发出，系统不接收回信，因此请勿直接回复。 如有任何疑问，请联系 support@gitshell.com。' % active_url
                send_mail('[gitshell]注册邮件', message, 'noreply@gitshell.com', [email], fail_silently=False)
                goto = ''
                email_suffix = email.split('@')[-1]
                if email_suffix in COMMON_EMAIL_DOMAIN:
                    goto = COMMON_EMAIL_DOMAIN[email_suffix]
                return HttpResponseRedirect('/join/1/?goto=' + goto)
            error = u'email: %s 或者 name: %s 已经注册，如果您是邮箱的主人，可以执行重置密码' % (email, username)
        else:
            error = u'请检查邮箱，验证码是否正确，注意大小写和前后空格。'
    if len(step) > 1:
        email = cache.get(step + '_email')
        username = cache.get(step + '_username')
        password = cache.get(step + '_password')
        if email is None or username is None or password is None or not email_re.match(email) or not re.match("^\w+$", username) or username in MAIN_NAVS:
            return HttpResponseRedirect('/join/4/')
        user = None
        try:
            user = User.objects.create_user(username, email, password)
        except IntegrityError:
            print 'user IntegrityError'
        if user is not None and user.is_active:
            user = auth_authenticate(username=user.username, password=password)
            if user is not None and user.is_active:
                auth_login(request, user)
                cache.delete(step + '_email')
                cache.delete(step + '_username')
                cache.delete(step + '_password')
                userprofile = Userprofile()
                userprofile.id = user.id
                userprofile.username = user.username
                userprofile.email = user.email
                userprofile.imgurl = hashlib.md5(user.email.lower()).hexdigest()
                userprofile.save()
                return HttpResponseRedirect('/join/3/')
        else:
            error = u'请检查用户名，密码是否正确，注意大小写和前后空格。'
    response_dictionary = {'step': step, 'error': error, 'joinForm': joinForm}
    return render_to_response('user/join.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def resetpassword(request, step):
    if step is None:
        step = '0'
    error = u''
    resetpasswordForm0 = ResetpasswordForm0()
    if step == '0' and request.method == 'POST':
        resetpasswordForm0 = ResetpasswordForm0(request.POST)
        if resetpasswordForm0.is_valid():
            random_hash = '%032x' % random.getrandbits(128)
            email = resetpasswordForm0.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = None
            if user is not None and user.is_active:
                cache.set(random_hash, email)
                active_url = 'https://gitshell.com/resetpassword/%s/' % random_hash
                message = u'尊敬的gitshell用户：\n如果您没有重置密码的请求，请忽略此邮件。点击下面的地址重置您在gitshell的帐号密码：\n%s\n----------\n此邮件由gitshell系统发出，系统不接收回信，因此请勿直接回复。 如有任何疑问，请联系 support@gitshell.com。' % active_url
                send_mail('[gitshell]重置密码邮件', message, 'noreply@gitshell.com', [email], fail_silently=False)
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
    response_dictionary = {'step': step, 'error': error, 'resetpasswordForm0': resetpasswordForm0, 'resetpasswordForm1': resetpasswordForm1}
    return render_to_response('user/resetpassword.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def get_common_user_dict(request, gsuser, gsuserprofile):
    is_watched_user = False
    if request.user.is_authenticated():
        is_watched_user = RepoManager.is_watched_user(request.user.id, gsuser.id)
    return {'gsuser': gsuser, 'gsuserprofile': gsuserprofile, 'is_watched_user': is_watched_user}

def get_last30days_commit(gsuser):
    now = datetime.now()
    last30days = timeutils.getlast30days(now)
    raw_last30days_commit = StatsManager.list_user_stats(gsuser.id, 'day', datetime.fromtimestamp(last30days[-1]), datetime.fromtimestamp(last30days[0]))
    last30days_commit = dict([(time.mktime(x.date.timetuple()), int(x.count)) for x in raw_last30days_commit])
    return last30days_commit

def __conver_to_recommends_vo(raw_recommends):
    user_ids = [x.from_user_id for x in raw_recommends]
    users_map = GsuserManager.map_users(user_ids)
    recommends_vo = [x.to_recommend_vo(users_map) for x in raw_recommends]
    return recommends_vo

# TODO note: add email unique support ! UNIQUE KEY `email` (`email`) #
