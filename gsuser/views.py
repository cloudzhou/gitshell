# Create your views here.
# -*- coding: utf-8 -*-  
import random
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.mail import send_mail
from django.core.cache import cache
from django.core.validators import email_re
from django.contrib.auth import authenticate as auth_authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User, UserManager, check_password
from gitshell.gsuser.Forms import LoginForm, JoinForm0, JoinForm1, ResetpasswordForm0, ResetpasswordForm1

def user(request, user_name):
    response_dictionary = {'hello_world': 'hello world1'}
    return render_to_response('home.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def repos(request, user_name):
    response_dictionary = {'hello_world': 'hello world1'}
    return render_to_response('home.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def settings(request):
    response_dictionary = {'hello_world': 'hello world1'}
    return render_to_response('home.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def login(request):
    loginForm = LoginForm()
    if request.method == 'POST':
        loginForm = LoginForm(request.POST)
        if loginForm.is_valid():
            email = loginForm.cleaned_data['email']
            password = loginForm.cleaned_data['password']
            rememberme = loginForm.cleaned_data['rememberme']
            if rememberme:
                request.session.set_expiry(2592000)
            user = User.objects.get(email=email)
            if user is not None and user.check_password(password):
                user = auth_authenticate(username=user.username, password=password)
                if user is not None and user.is_active:
                    auth_login(request, user)
                    return HttpResponseRedirect('/home/')
    response_dictionary = {'loginForm': loginForm}
    return render_to_response('gsuser/login.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def logout(request):
    auth_logout(request)
    return HttpResponseRedirect('/')

def join(request, step):
    if step is None:
        step = '0'
    joinForm0 = JoinForm0()
    if step == '0' and request.method == 'POST':
        joinForm0 = JoinForm0(request.POST)
        if joinForm0.is_valid():
            random_hash = '%032x' % random.getrandbits(128)
            email = joinForm0.cleaned_data['email']
            cache.set(random_hash, email)
            active_url = 'http://www.gitshell.com/join/%s/' % random_hash
            message = '尊敬的gitshell用户：\n感谢您选择了gitshell，请点击下面的地址激活你在gitshell的帐号：\n%s\n----------\n此邮件由gitshell系统发出，系统不接收回信，因此请勿直接回复。 如有任何疑问，请联系 support@gitshell.com。' % active_url
            send_mail('[gitshell]注册邮件', message, 'noreply@gitshell.com', [email], fail_silently=False)
            return HttpResponseRedirect('/join/1/')
    joinForm1 = JoinForm1()
    if len(step) > 1 and request.method == 'POST':
        joinForm1 = JoinForm1(request.POST)
        if joinForm1.is_valid():
            email = cache.get(step)
            if email is not None and email_re.match(email):
                name = joinForm1.cleaned_data['name']
                password = joinForm1.cleaned_data['password']
                user = User.objects.create_user(name, email, password)
                if user is not None and user.is_active:
                    user = auth_authenticate(username=user.username, password=password)
                    if user is not None and user.is_active:
                        auth_login(request, user)
                        cache.delete(step)
                        return HttpResponseRedirect('/join/3/')
            return HttpResponseRedirect('/join/4/')
    response_dictionary = {'step': step, 'joinForm0': joinForm0, 'joinForm1': joinForm1}
    return render_to_response('gsuser/join.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def resetpassword(request, step):
    if step is None:
        step = '0'
    resetpasswordForm0 = ResetpasswordForm0()
    if step == '0' and request.method == 'POST':
        resetpasswordForm0 = ResetpasswordForm0(request.POST)
        if resetpasswordForm0.is_valid():
            random_hash = '%032x' % random.getrandbits(128)
            email = resetpasswordForm0.cleaned_data['email']
            user = User.objects.get(email=email)
            if user is not None and user.is_active:
                cache.set(random_hash, email)
                active_url = 'http://www.gitshell.com/resetpassword/%s/' % random_hash
                message = '尊敬的gitshell用户：\n如果您没有重置密码的请求，请忽略此邮件。点击下面的地址重置你在gitshell的帐号密码：\n%s\n----------\n此邮件由gitshell系统发出，系统不接收回信，因此请勿直接回复。 如有任何疑问，请联系 support@gitshell.com。' % active_url
                send_mail('[gitshell]重置密码邮件', message, 'noreply@gitshell.com', [email], fail_silently=False)
                return HttpResponseRedirect('/resetpassword/1/')
    resetpasswordForm1 = ResetpasswordForm1()
    if len(step) > 1 and request.method == 'POST':
        resetpasswordForm1 = ResetpasswordForm1(request.POST)
        if resetpasswordForm1.is_valid():
            email = cache.get(step)
            if email is not None and email_re.match(email):
                password = resetpasswordForm1.cleaned_data['password']
                user = User.objects.get(email=email)
                if user is not None and user.is_active:
                    user.set_password(password)
                    user.save()
                    user = auth_authenticate(username=user.username, password=password)
                    auth_login(request, user)
                    cache.delete(step)
                    return HttpResponseRedirect('/resetpassword/3/')
            return HttpResponseRedirect('/resetpassword/4/')
    response_dictionary = {'step': step, 'resetpasswordForm0': resetpasswordForm0, 'resetpasswordForm1': resetpasswordForm1}
    return render_to_response('gsuser/resetpassword.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

# note: add email unique support ! UNIQUE KEY `email` (`email`) #
