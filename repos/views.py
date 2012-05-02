# -*- coding: utf-8 -*-  
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from gitshell.repos.Forms import ReposForm
from gitshell.repos.models import Repos
import re

@login_required
def repos(request, repos_name):
    response_dictionary = {'ii': range(0, 20)}
    return render_to_response('repos/repos.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

# TODO
@login_required
def edit(request, username, rid):
    error = u''
    repos = Repos()
    repos.user_id = request.user.id
    if rid != '0':
        try:
            repos = Repos.objects.get(id = rid, user_id = request.user.id)
        except Repos.DoesNotExist:
            pass
    reposForm = ReposForm(instance = repos)
    orgi_name = repos.name
    if request.method == 'POST':
        reposForm = ReposForm(request.POST, instance = repos)
        if reposForm.is_valid() and re.match("^\w+$", reposForm.cleaned_data['name']):
            reposForm.save()
            return HttpResponseRedirect('/' + request.user.username + '/repos/')
        else:
            error = u'输入正确的仓库名称[A-Za-z0-9_]，选择好语言和可见度'
    response_dictionary = {'reposForm': reposForm, 'rid': rid, 'error': error}
    return render_to_response('repos/edit.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

