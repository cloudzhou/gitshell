# -*- coding: utf-8 -*-  
import random
import re
import base64, hashlib
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.mail import send_mail
from django.core.cache import cache
from django.core.validators import email_re
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate as auth_authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User, UserManager, check_password
from django.db import IntegrityError
from gitshell.gsuser.Forms import LoginForm, JoinForm0, JoinForm1, ResetpasswordForm0, ResetpasswordForm1, SkillsForm, RecommendsForm
from gitshell.gsuser.models import Userprofile, GsuserManager
from gitshell.repo.models import RepoManager
from gitshell.feed.feed import FeedAction

def user(request, user_name):
    gsuser = GsuserManager.get_user_by_name(user_name)
    if gsuser is None:
        raise Http404
    gsuserprofile = GsuserManager.get_userprofile_by_id(gsuser.id)
    recommendsForm = RecommendsForm()
    feedAction = FeedAction()
    repos = RepoManager.list_repo_by_userId(gsuser.id, 0, 10)
    recommends = GsuserManager.list_recommend_by_id(gsuser.id, 0, 20)

    raw_watch_repos = feedAction.get_watch_repos(gsuser.id, 0, 10)
    raw_watch_users = feedAction.get_watch_users(gsuser.id, 0, 10)
    raw_bewatch_users = feedAction.get_bewatch_users(gsuser.id, 0, 10)

    response_dictionary = {'mainnav': 'user', 'recommendsForm': recommendsForm, 'gsuser': gsuser, 'gsuserprofile': gsuserprofile}
    return render_to_response('user/user.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def active(request, user_name):
    gsuser = GsuserManager.get_user_by_name(user_name)
    if gsuser is None:
        raise Http404
    gsuserprofile = GsuserManager.get_userprofile_by_id(gsuser.id)
    response_dictionary = {'mainnav': 'user', 'gsuser': gsuser, 'gsuserprofile': gsuserprofile}
    return render_to_response('user/active.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def stats(request, user_name):
    gsuser = GsuserManager.get_user_by_name(user_name)
    if gsuser is None:
        raise Http404
    gsuserprofile = GsuserManager.get_userprofile_by_id(gsuser.id)
    response_dictionary = {'mainnav': 'user', 'gsuser': gsuser, 'gsuserprofile': gsuserprofile}
    return render_to_response('user/stats.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def watch_user(request, user_name):
    gsuser = GsuserManager.get_user_by_name(user_name)
    if gsuser is None:
        raise Http404
    gsuserprofile = GsuserManager.get_userprofile_by_id(gsuser.id)
    raw_watch_users = feedAction.get_watch_users(gsuser.id, 0, 10)
    raw_bewatch_users = feedAction.get_bewatch_users(gsuser.id, 0, 10)

    response_dictionary = {'mainnav': 'user', 'gsuser': gsuser, 'gsuserprofile': gsuserprofile}
    return render_to_response('user/watch_user.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def watch_repo(request, user_name):
    gsuser = GsuserManager.get_user_by_name(user_name)
    if gsuser is None:
        raise Http404
    gsuserprofile = GsuserManager.get_userprofile_by_id(gsuser.id)
    raw_watch_repos = feedAction.get_watch_repos(gsuser.id, 0, 10)
    response_dictionary = {'mainnav': 'user', 'gsuser': gsuser, 'gsuserprofile': gsuserprofile}
    return render_to_response('user/watch_repo.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def recommend(request, user_name):
    gsuser = GsuserManager.get_user_by_name(user_name)
    if gsuser is None:
        raise Http404
    gsuserprofile = GsuserManager.get_userprofile_by_id(gsuser.id)
    recommends = GsuserManager.list_recommend_by_id(gsuser.id, 0, 50)

    response_dictionary = {'mainnav': 'user', 'gsuser': gsuser, 'gsuserprofile': gsuserprofile}
    return render_to_response('user/recommend.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def network_watch(request, user_name):
    gsuser = GsuserManager.get_user_by_name(user_name)
    if gsuser is None:
        raise Http404
    response_dictionary = {'mainnav': 'user'}
    return render_to_response('user/user.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def network_unwatch(request, user_name):
    gsuser = GsuserManager.get_user_by_name(user_name)
    if gsuser is None:
        raise Http404
    response_dictionary = {'mainnav': 'user'}
    return render_to_response('user/user.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

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

def logout(request):
    auth_logout(request)
    return HttpResponseRedirect('/')

def join(request, step):
    if step is None:
        step = '0'
    error = u''
    joinForm0 = JoinForm0()
    if step == '0' and request.method == 'POST':
        joinForm0 = JoinForm0(request.POST)
        if joinForm0.is_valid():
            random_hash = '%032x' % random.getrandbits(128)
            email = joinForm0.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = None
            if user is None:
                cache.set(random_hash, email)
                active_url = 'http://www.gitshell.com/join/%s/' % random_hash
                message = u'尊敬的gitshell用户：\n感谢您选择了gitshell，请点击下面的地址激活你在gitshell的帐号：\n%s\n----------\n此邮件由gitshell系统发出，系统不接收回信，因此请勿直接回复。 如有任何疑问，请联系 support@gitshell.com。' % active_url
                send_mail('[gitshell]注册邮件', message, 'noreply@gitshell.com', [email], fail_silently=False)
                return HttpResponseRedirect('/join/1/')
            error = u'%s 已经注册，如果您是邮箱的主人，可以执行重置密码' % email
        else:
            error = u'请检查邮箱，验证码是否正确，注意大小写和前后空格。'
    joinForm1 = JoinForm1()
    if len(step) > 1 and request.method == 'POST':
        joinForm1 = JoinForm1(request.POST)
        if joinForm1.is_valid():
            email = cache.get(step)
            if email is None or not email_re.match(email):
                return HttpResponseRedirect('/join/4/')
            name = joinForm1.cleaned_data['name']
            password = joinForm1.cleaned_data['password']
            if name is not None and re.match("^\w+$", name):
                try:
                    user = User.objects.create_user(name, email, password)
                except IntegrityError:
                    user = None
                if user is not None and user.is_active:
                    user = auth_authenticate(username=user.username, password=password)
                    if user is not None and user.is_active:
                        auth_login(request, user)
                        cache.delete(step)
                        userprofile = Userprofile()
                        userprofile.id = user.id
                        userprofile.imgurl = hashlib.md5(user.email.lower()).hexdigest()
                        userprofile.save()
                        return HttpResponseRedirect('/join/3/')
                error = u'用户名 %s 或者 邮箱 %s 已经注册' % (name, email)
            else:
                error = u'请检查用户名是否规范[A-Za-z0-9_]'
        else:
            error = u'请检查用户名，密码是否正确，注意大小写和前后空格。'
    response_dictionary = {'step': step, 'error': error, 'joinForm0': joinForm0, 'joinForm1': joinForm1}
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
                active_url = 'http://www.gitshell.com/resetpassword/%s/' % random_hash
                message = u'尊敬的gitshell用户：\n如果您没有重置密码的请求，请忽略此邮件。点击下面的地址重置你在gitshell的帐号密码：\n%s\n----------\n此邮件由gitshell系统发出，系统不接收回信，因此请勿直接回复。 如有任何疑问，请联系 support@gitshell.com。' % active_url
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

# TODO note: add email unique support ! UNIQUE KEY `email` (`email`) #
