# -*- coding: utf-8 -*-  
import os, re
import shutil
import json
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render_to_response
from django.utils.html import escape
from gitshell.feed.feed import FeedAction
from gitshell.repo.Forms import RepoForm, RepoIssuesForm, RepoIssuesCommentForm
from gitshell.repo.githandler import GitHandler
from gitshell.repo.models import Repo, RepoManager, Issues
from gitshell.repo.cons import TRACKERS, STATUSES, PRIORITIES, ISSUES_ATTRS
from gitshell.gsuser.models import UserprofileManager
from gitshell.settings import PRIVATE_REPO_PATH, PUBLIC_REPO_PATH, GIT_BARE_REPO_PATH

@login_required
def user_repo(request, user_name):
    return user_repo_paging(request, user_name, 0)

@login_required
def user_repo_paging(request, user_name, pagenum):
    repo_list = RepoManager.list_repo_by_userId(request.user.id, 0, 25)
    repo_commit_map = {}
    feedAction = FeedAction()
    for repo in repo_list:
        repo_commit_map[str(repo.name)] = []
        feeds = feedAction.get_repo_feeds(repo.id, 0, 4)
        for feed in feeds:
            repo_commit_map[str(repo.name)].append(feed[0])
    response_dictionary = {'user_name': user_name, 'repo_list': repo_list, 'repo_commit_map': repo_commit_map}
    return render_to_response('repo/user_repo.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def repo(request, user_name, repo_name):
    refs = 'master'; path = '.'; current = 'index'
    return repo_ls_tree(request, user_name, repo_name, refs, path, current)

def repo_default_tree(request, user_name, repo_name):
    refs = 'master'; path = '.'; current = 'tree'
    return repo_ls_tree(request, user_name, repo_name, refs, path, current)
    
def repo_tree(request, user_name, repo_name, refs, path):
    current = 'tree'
    return repo_ls_tree(request, user_name, repo_name, refs, path, current)

def repo_raw_tree(request, user_name, repo_name, refs, path):
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None or path.endswith('/'):
        raise Http404
    gitHandler = GitHandler()
    abs_repopath = repo.get_abs_repopath(user_name)
    commit_hash = gitHandler.get_commit_hash(abs_repopath, refs)
    blob = gitHandler.repo_cat_file(abs_repopath, commit_hash, path)
    return HttpResponse(blob, content_type="text/plain")

lang_suffix = {'applescript': 'AppleScript', 'as3': 'AS3', 'bash': 'Bash', 'sh': 'Bash', 'cfm': 'ColdFusion', 'cfc': 'ColdFusion', 'cpp': 'Cpp', 'cxx': 'Cpp', 'c': 'Cpp', 'h': 'Cpp', 'cs': 'CSharp', 'css': 'Css', 'dpr': 'Delphi', 'dfm': 'Delphi', 'pas': 'Delphi', 'diff': 'Diff', 'patch': 'Diff', 'erl': 'Erlang', 'groovy': 'Groovy', 'fx': 'JavaFX', 'jfx': 'JavaFX', 'java': 'Java', 'js': 'JScript', 'pl': 'Perl', 'py': 'Python', 'php': 'Php', 'psl': 'PowerShell', 'rb': 'Ruby', 'sass': 'Sass', 'scala': 'Scala', 'sql': 'Sql', 'vb': 'Vb', 'xml': 'Xml', 'xhtml': 'Xml', 'html': 'Xml', 'htm': 'Xml'}
brush_aliases = {'AppleScript': 'applescript', 'AS3': 'actionscript3', 'Bash': 'shell', 'ColdFusion': 'coldfusion', 'Cpp': 'cpp', 'CSharp': 'csharp', 'Css': 'css', 'Delphi': 'delphi', 'Diff': 'diff', 'Erlang': 'erlang', 'Groovy': 'groovy', 'JavaFX': 'javafx', 'Java': 'java', 'JScript': 'javascript', 'Perl': 'perl', 'Php': 'php', 'Plain': 'plain', 'PowerShell': 'powershell', 'Python': 'python', 'Ruby': 'ruby', 'Sass': 'sass', 'Scala': 'scala', 'Sql': 'sql', 'Vb': 'vb', 'Xml': 'xml'}
def repo_ls_tree(request, user_name, repo_name, refs, path, current):
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    if path is None or path == '':
        path = '.'
    gitHandler = GitHandler()
    abs_repopath = repo.get_abs_repopath(user_name)
    commit_hash = gitHandler.get_commit_hash(abs_repopath, refs)
    is_tree = True ; tree = {} ; blob = ''; lang = 'Plain'; brush = 'plain'
    if path == '.' or path.endswith('/'):
        tree = gitHandler.repo_ls_tree(abs_repopath, commit_hash, path)
    else:
        is_tree = False
        paths = path.split('.')
        if len(paths) > 0:
            suffix = paths[-1]
            if suffix in lang_suffix and lang_suffix[suffix] in brush_aliases:
                lang = lang_suffix[suffix]
                brush = brush_aliases[lang]
        blob = gitHandler.repo_cat_file(abs_repopath, commit_hash, path)
    response_dictionary = {'current': current, 'repo': repo, 'user_name': user_name, 'repo_name': repo_name, 'refs': refs, 'path': path, 'tree': tree, 'blob': blob, 'is_tree': is_tree, 'lang': lang, 'brush': brush}
    return render_to_response('repo/tree.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def repo_default_commits(request, user_name, repo_name):
    refs = 'master'; path = '.'
    return repo_commits(request, user_name, repo_name, refs, path)
    
def repo_commits(request, user_name, repo_name, refs, path):
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    if path is None or path == '':
        path = '.'
    gitHandler = GitHandler()
    abs_repopath = repo.get_abs_repopath(user_name)
    commit_hash = gitHandler.get_commit_hash(abs_repopath, refs)
    commits = gitHandler.repo_log_file(abs_repopath, commit_hash, path)
    response_dictionary = {'current': 'commits', 'repo': repo, 'user_name': user_name, 'repo_name': repo_name, 'refs': refs, 'path': path, 'commits': commits}
    return render_to_response('repo/commits.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def repo_diff(request, user_name, repo_name, pre_commit_hash, commit_hash, path):
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    if path is None or path == '':
        path = '.'
    gitHandler = GitHandler()
    abs_repopath = repo.get_abs_repopath(user_name)
    diff = gitHandler.repo_diff(abs_repopath, pre_commit_hash, commit_hash, path)
    return HttpResponse(json.dumps({'diff': escape(diff)}), mimetype="application/json")

def repo_issues(request, user_name, repo_name):
    return repo_list_issues(request, user_name, repo_name, None, TRACKERS[0].value, STATUSES[0].value, PRIORITIES[0].value, 'modify_time', 0)
 
def repo_list_issues(request, user_name, repo_name, assigned, tracker, status, priority, orderby, page):
    refs = 'master'; path = '.'; current = 'issues'
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    user_id = request.user.id
    user_ids = [o.user_id for o in RepoManager.list_repomember(repo.id)]
    user_ids.insert(0, repo.user_id)
    if user_id != repo.user_id and user_id in user_ids:
        user_ids.remove(user_id)
        user_ids.insert(0, user_id)
    assigneds = [o.username for o in UserprofileManager.list_user_by_ids(user_ids)]
    if assigned is None:
        assigned = assigneds[0]
    tracker = int(tracker); status = int(status); priority = int(priority); page = int(page)
    current_attrs = { "assigned": str(assigned), "tracker": tracker, "status": status, "priority": priority, "orderby": str(orderby), "page": page }
    response_dictionary = {'current': current, 'user_name': user_name, 'repo_name': repo_name, 'refs': refs, 'path': path, 'assigneds': assigneds, 'assigned': assigned, 'tracker': tracker, 'status': status, 'priority': priority, 'orderby': orderby, 'page': page, 'current_attrs': current_attrs}
    response_dictionary.update(ISSUES_ATTRS)
    return render_to_response('repo/issues.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def repo_create_issues(request, user_name, repo_name):
    refs = 'master'; path = '.'; current = 'issues'
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    repoIssuesForm = RepoIssuesForm()
    repoIssuesForm.fill_assigned(repo)
    error = ''
    if request.method == 'POST':
        issues = Issues()
        issues.user_id = request.user.id
        issues.repo_id = repo.id
        repoIssuesForm = RepoIssuesForm(request.POST, instance = issues)
        repoIssuesForm.fill_assigned(repo)
        if repoIssuesForm.is_valid():
            repoIssuesForm.save()
            return HttpResponseRedirect('/%s/%s/issues/' % (user_name, repo_name))
        else:
            error = u'issues 内容不能为空'
    response_dictionary = {'current': current, 'user_name': user_name, 'repo_name': repo_name, 'refs': refs, 'path': path, 'repoIssuesForm': repoIssuesForm, 'error': error}
    response_dictionary.update(ISSUES_ATTRS)
    return render_to_response('repo/create_issues.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def repo_delete_issues(request, user_name, repo_name, issue_id):
    refs = 'master'; path = '.'; current = 'issues'
    response_dictionary = {'current': current, 'user_name': user_name, 'repo_name': repo_name, 'refs': refs, 'path': path}
    response_dictionary.update(ISSUES_ATTRS)
    return render_to_response('repo/issues.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def repo_create_comment(request, user_name, repo_name, issues_id):
    refs = 'master'; path = '.'; current = 'issues'
    repoIssuesCommentForm = RepoIssuesCommentForm()
    response_dictionary = {'current': current, 'user_name': user_name, 'repo_name': repo_name, 'refs': refs, 'path': path, 'repoIssuesCommentForm': repoIssuesCommentForm}
    response_dictionary.update(ISSUES_ATTRS)
    return render_to_response('repo/create_comment.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def repo_delete_comment(request, user_name, repo_name, comment_id):
    refs = 'master'; path = '.'; current = 'issues'
    response_dictionary = {'current': current, 'user_name': user_name, 'repo_name': repo_name, 'refs': refs, 'path': path}
    response_dictionary.update(ISSUES_ATTRS)
    return render_to_response('repo/issues.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def repo_network(request, user_name, repo_name):
    refs = 'master'; path = '.'; current = 'network'
    response_dictionary = {'current': current, 'user_name': user_name, 'repo_name': repo_name, 'refs': refs, 'path': path}
    return render_to_response('repo/repo.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def repo_clone_branches(request, user_name, repo_name):
    refs = 'master'; path = '.'; current = 'branches'
    response_dictionary = {'current': current, 'user_name': user_name, 'repo_name': repo_name, 'refs': refs, 'path': path}
    return render_to_response('repo/repo.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def repo_stats(request, user_name, repo_name):
    refs = 'master'; path = '.'; current = 'stats'
    response_dictionary = {'current': 'stats', 'user_name': user_name, 'repo_name': repo_name, 'refs': refs, 'path': path}
    return render_to_response('repo/repo.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def repo_refs(request, user_name, repo_name):
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        return HttpResponse(json.dumps({'user_name': user_name, 'repo_name': repo_name, 'branches': [], 'tags': []}), mimetype="application/json")
    repopath = repo.get_abs_repopath(user_name)

    gitHandler = GitHandler()
    branches_refs = gitHandler.repo_ls_branches(repopath)
    tags_refs = gitHandler.repo_ls_tags(repopath)
    response_dictionary = {'user_name': user_name, 'repo_name': repo_name, 'branches': branches_refs, 'tags': tags_refs}
    return HttpResponse(json.dumps(response_dictionary), mimetype="application/json")

def folder(request):
    response_dictionary = {'hello_world': 'hello world'}
    return render_to_response('repo/folder.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def file(request):
    response_dictionary = {'hello_world': 'hello world'}
    return render_to_response('repo/file.html',
                          response_dictionary,
                          context_instance=RequestContext(request))						  
# TODO
@login_required
def edit(request, rid):
    error = u''
    repo = Repo()
    if rid != '0':
        try:
            repo = Repo.objects.get(id = rid, user_id = request.user.id)
        except Repo.DoesNotExist:
            pass
    repoForm = RepoForm(instance = repo)
    repo.user_id = request.user.id
    if request.method == 'POST':
        repoForm = RepoForm(request.POST, instance = repo)
        if repoForm.is_valid() and re.match("^\w+$", repoForm.cleaned_data['name']):
            fulfill_gitrepo(request.user.username, repoForm.cleaned_data['name'], repoForm.cleaned_data['auth_type'])
            repoForm.save()
            return HttpResponseRedirect('/' + request.user.username + '/repo/')
        else:
            error = u'输入正确的仓库名称[A-Za-z0-9_]，选择好语言和可见度'
    response_dictionary = {'repoForm': repoForm, 'rid': rid, 'error': error}
    return render_to_response('repo/edit.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def get_commits_by_ids(ids):
    return RepoManager.get_commits_by_ids(ids)

def fulfill_gitrepo(username, reponame, auth_type):
    for base_repo_path in [PUBLIC_REPO_PATH, PRIVATE_REPO_PATH]:
        user_repo_path = '%s/%s' % (base_repo_path, username)
        if not os.path.exists(user_repo_path):
            os.makedirs(user_repo_path)
    pub_repo_path = ('%s/%s/%s.git' % (PUBLIC_REPO_PATH, username, reponame))
    pri_repo_path = ('%s/%s/%s.git' % (PRIVATE_REPO_PATH, username, reponame))
    if auth_type == '0': 
        if not os.path.exists(pub_repo_path):
            if os.path.exists(pri_repo_path):
                shutil.move(pri_repo_path, pub_repo_path)
            else:
                shutil.copytree(GIT_BARE_REPO_PATH, pub_repo_path)             
    else:
        if not os.path.exists(pri_repo_path):
            if os.path.exists(pub_repo_path):
                shutil.move(pub_repo_path, pri_repo_path)
            else:
                shutil.copytree(GIT_BARE_REPO_PATH, pri_repo_path)             


