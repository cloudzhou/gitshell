# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response
from gitshell.gssettings.Form import SshpubkeyForm, ChangepasswordForm, UserprofileForm

def default(request):
    response_dictionary = {'hello_world': 'hello world'}
    return render_to_response('settings/default.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def profile(request):
    userprofileForm = UserprofileForm()
    if request.method == 'POST':
        userprofileForm = UserprofileForm(request.POST)
    response_dictionary = {'hello_world': 'hello world', 'userprofileForm': userprofileForm}
    return render_to_response('settings/profile.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def changepassword(request):
    changepasswordForm = ChangepasswordForm()
    response_dictionary = {'hello_world': 'hello world', 'changepasswordForm': changepasswordForm}
    return render_to_response('settings/changepassword.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def sshpubkey(request):
    sshpubkeyForm = SshpubkeyForm()
    response_dictionary = {'hello_world': 'hello world', 'sshpubkeyForm': sshpubkeyForm}
    return render_to_response('settings/sshpubkey.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def email(request):
    response_dictionary = {'hello_world': 'hello world'}
    return render_to_response('settings/email.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def repos(request):
    response_dictionary = {'hello_world': 'hello world'}
    return render_to_response('settings/repos.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def destroy(request):
    response_dictionary = {'hello_world': 'hello world'}
    return render_to_response('settings/destroy.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
