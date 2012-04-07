# Create your views here.
# -*- coding: utf-8 -*-  
import random
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.mail import send_mail
from django.core.cache import cache
from gitshell.gsuser.Forms import LoginForm, JoinForm0, JoinForm1

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
            return HttpResponseRedirect('/home/')
    response_dictionary = {'loginForm': loginForm}
    return render_to_response('gsuser/login.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

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
            if email is not None:
                name = joinForm1.cleaned_data['name']
                password = joinForm1.cleaned_data['password']
                print name
                print password
                return HttpResponseRedirect('/join/3/')
    response_dictionary = {'step': step, 'joinForm0': joinForm0, 'joinForm1': joinForm1}
    return render_to_response('gsuser/join.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def resetpassword(request, step):
    response_dictionary = {'hello_world': 'hello world1'}
    return render_to_response('gsuser/join.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
