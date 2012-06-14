# -*- coding: utf-8 -*-  
import os, re
import shutil
import json
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render_to_response
from gitshell.feed.feed import FeedAction
from gitshell.repos.Forms import ReposForm
from gitshell.repos.githandler import GitHandler
from gitshell.repos.models import Repos, ReposManager
from gitshell.settings import PRIVATE_REPOS_PATH, PUBLIC_REPOS_PATH, GIT_BARE_REPOS_PATH

@login_required
def user_repos(request, user_name):
    return user_repos_paging(request, user_name, 0)

@login_required
def user_repos_paging(request, user_name, pagenum):
    repos_list = ReposManager.list_repos_by_userId(request.user.id, 0, 25)
    repos_commit_map = {}
    feedAction = FeedAction()
    for repos in repos_list:
        repos_commit_map[str(repos.name)] = []
        feeds = feedAction.get_repos_feeds(repos.id, 0, 4)
        for feed in feeds:
            repos_commit_map[str(repos.name)].append(feed[0])
    response_dictionary = {'user_name': user_name, 'repos_list': repos_list, 'repos_commit_map': repos_commit_map}
    return render_to_response('repos/user_repos.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def repos(request, user_name, repos_name):
    response_dictionary = {'current': 'index', 'user_name': user_name, 'repos_name': repos_name}
    return render_to_response('repos/repos.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def repos_tree(request, user_name, repos_name):
    response_dictionary = {'current': 'tree', 'user_name': user_name, 'repos_name': repos_name}
    return render_to_response('repos/repos.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def repos_commits(request, user_name, repos_name):
    response_dictionary = {'current': 'commits', 'user_name': user_name, 'repos_name': repos_name}
    return render_to_response('repos/repos.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def repos_issues(request, user_name, repos_name):
    response_dictionary = {'current': 'issues', 'user_name': user_name, 'repos_name': repos_name}
    return render_to_response('repos/repos.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def repos_network(request, user_name, repos_name):
    response_dictionary = {'current': 'network', 'user_name': user_name, 'repos_name': repos_name}
    return render_to_response('repos/repos.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def repos_branches(request, user_name, repos_name):
    response_dictionary = {'current': 'branches', 'user_name': user_name, 'repos_name': repos_name}
    return render_to_response('repos/repos.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def repos_stats(request, user_name, repos_name):
    response_dictionary = {'current': 'stats', 'user_name': user_name, 'repos_name': repos_name}
    return render_to_response('repos/repos.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def repo_refs(request, user_name, repo_name):
    repo = get_repo_by_name(user_name, repo_name)
    if repo is None:
        return HttpResponse(json.dumps({'user_name': user_name, 'repo_name': repo_name, 'branches': [], 'tags': []}), mimetype="application/json")
    parent_path = ""
    if repo.auth_type == 0:
        parent_path = PUBLIC_REPOS_PATH
    else:
        parent_path = PRIVATE_REPOS_PATH
    repopath = '%s/%s/%s.git' % (parent_path, user_name, repo_name)

    gitHandler = GitHandler()
    branches_refs = gitHandler.repo_ls_branches(repopath)
    tags_refs = gitHandler.repo_ls_tags(repopath)
    response_dictionary = {'user_name': user_name, 'repo_name': repo_name, 'branches': branches_refs, 'tags': tags_refs}
    return HttpResponse(json.dumps(response_dictionary), mimetype="application/json")

def get_repo_by_name(user_name, repo_name):
    try:
        user = User.objects.get(username=user_name)     
        return ReposManager.get_repos_by_userId_name(user.id, repo_name)
    except User.DoesNotExist:
        return None

def folder(request):
    response_dictionary = {'hello_world': 'hello world'}
    return render_to_response('repos/folder.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def file(request):
    response_dictionary = {'hello_world': 'hello world'}
    return render_to_response('repos/file.html',
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


