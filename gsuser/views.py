# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response
from gitshell.gsuser.Forms import LoginForm

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
    response_dictionary = {'hello_world': 'hello world1'}
    return render_to_response('gsuser/join.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def resetpassword(request, step):
    response_dictionary = {'hello_world': 'hello world1'}
    return render_to_response('gsuser/join.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
