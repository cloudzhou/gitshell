# -*- coding: utf-8 -*-  
import os, re
import shutil
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render_to_response
from gitshell.repos.Forms import ReposForm
from gitshell.repos.models import Repos, ReposManager
from gitshell.settings import PRIVATE_REPOS_PATH, PUBLIC_REPOS_PATH, GIT_BARE_REPOS_PATH

@login_required
def repos(request, user_name):
    repos_list = ReposManager.list_repos_by_userId(request.user.id, 0, 20)
    response_dictionary = {'user_name': user_name, 'repos_list': repos_list }
    return render_to_response('repos/repos.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def user_repos(request, user_name, repos_name):
    response_dictionary = {'ii': range(0, 20)}
    return render_to_response('repos/repos.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
# TODO
@login_required
def edit(request, rid):
    error = u''
    repos = Repos()
    if rid != '0':
        try:
            repos = Repos.objects.get(id = rid, user_id = request.user.id)
        except Repos.DoesNotExist:
            pass
    reposForm = ReposForm(instance = repos)
    repos.user_id = request.user.id
    if request.method == 'POST':
        reposForm = ReposForm(request.POST, instance = repos)
        if reposForm.is_valid() and re.match("^\w+$", reposForm.cleaned_data['name']):
            fulfill_gitrepos(request.user.username, reposForm.cleaned_data['name'], reposForm.cleaned_data['auth_type'])
            reposForm.save()
            return HttpResponseRedirect('/' + request.user.username + '/repos/')
        else:
            error = u'输入正确的仓库名称[A-Za-z0-9_]，选择好语言和可见度'
    response_dictionary = {'reposForm': reposForm, 'rid': rid, 'error': error}
    return render_to_response('repos/edit.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def get_commits_by_ids(ids):
    return ReposManager.get_commits_by_ids(ids)

def fulfill_gitrepos(username, reposname, auth_type):
    for base_repos_path in [PUBLIC_REPOS_PATH, PRIVATE_REPOS_PATH]:
        user_repos_path = '%s/%s' % (base_repos_path, username)
        if not os.path.exists(user_repos_path):
            os.makedirs(user_repos_path)
    pub_repos_path = ('%s/%s/%s.git' % (PUBLIC_REPOS_PATH, username, reposname))
    pri_repos_path = ('%s/%s/%s.git' % (PRIVATE_REPOS_PATH, username, reposname))
    if auth_type == '0': 
        if not os.path.exists(pub_repos_path):
            if os.path.exists(pri_repos_path):
                shutil.move(pri_repos_path, pub_repos_path)
            else:
                shutil.copytree(GIT_BARE_REPOS_PATH, pub_repos_path)             
    else:
        if not os.path.exists(pri_repos_path):
            if os.path.exists(pub_repos_path):
                shutil.move(pub_repos_path, pri_repos_path)
            else:
                shutil.copytree(GIT_BARE_REPOS_PATH, pri_repos_path)             


