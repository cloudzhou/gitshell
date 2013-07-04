# -*- coding: utf-8 -*-  
import os, re
import json, time, urllib
import shutil, copy, random
from datetime import datetime, timedelta
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.shortcuts import render_to_response
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.utils.html import escape
from django.forms.models import model_to_dict
from gitshell.feed.feed import FeedAction
from gitshell.feed.models import FeedManager
from gitshell.repo.Forms import RepoForm, RepoMemberForm
from gitshell.repo.githandler import GitHandler
from gitshell.repo.models import Repo, RepoManager, PullRequest, PULL_STATUS
from gitshell.gsuser.models import GsuserManager
from gitshell.gsuser.decorators import repo_permission_check, repo_source_permission_check
from gitshell.stats import timeutils
from gitshell.stats.models import StatsManager
from gitshell.settings import SECRET_KEY, REPO_PATH, GIT_BARE_REPO_PATH, DELETE_REPO_PATH, PULLREQUEST_REPO_PATH
from gitshell.daemon.models import EventManager
from gitshell.viewtools.views import json_httpResponse
from gitshell.gsuser.middleware import KEEP_REPO_NAME
from gitshell.thirdparty.views import github_oauth_access_token, github_get_thirdpartyUser, github_authenticate, github_list_repo, dropbox_share_direct

@login_required
def user_repo(request, user_name):
    return user_repo_paging(request, user_name, 0)

@login_required
def user_repo_paging(request, user_name, pagenum):
    user = GsuserManager.get_user_by_name(user_name)
    userprofile = GsuserManager.get_userprofile_by_name(user_name)
    if user is None:
        raise Http404
    raw_repo_list = RepoManager.list_repo_by_userId(user.id, 0, 100)
    repo_list = raw_repo_list
    if user.id != request.user.id:
        repo_list = [x for x in raw_repo_list if x.auth_type != 2]
    repo_feed_map = {}
    feedAction = FeedAction()
    i = 0
    for repo in repo_list:
        repo_feed_map[str(repo.name)] = []
        feeds = feedAction.get_repo_feeds(repo.id, 0, 4)
        for feed in feeds:
            repo_feed_map[str(repo.name)].append(feed[0])
        i = i + 1
        if i > 10:
            break
    # fix on error detect
    pubrepo = 0
    for repo in raw_repo_list:
        if repo.auth_type == 0 or repo.auth_type == 1:
            pubrepo = pubrepo + 1
    prirepo = len(raw_repo_list) - pubrepo
    if pubrepo != userprofile.pubrepo or prirepo != userprofile.prirepo:
        userprofile.pubrepo = pubrepo
        userprofile.prirepo = prirepo
        userprofile.save()

    response_dictionary = {'mainnav': 'repo', 'user_name': user_name, 'repo_list': repo_list, 'repo_feed_map': repo_feed_map}
    return render_to_response('repo/user_repo.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@repo_permission_check
def repo(request, user_name, repo_name):
    refs = 'master'; path = '.'; current = 'index'
    return ls_tree(request, user_name, repo_name, refs, path, current)

@repo_permission_check
def tree_default(request, user_name, repo_name):
    refs = 'master'; path = '.'; current = 'tree'
    return ls_tree(request, user_name, repo_name, refs, path, current)
    
@repo_permission_check
def tree(request, user_name, repo_name, refs, path):
    current = 'tree'
    return ls_tree(request, user_name, repo_name, refs, path, current)

@repo_permission_check
@repo_source_permission_check
def raw_blob(request, user_name, repo_name, refs, path):
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None or path.endswith('/'):
        raise Http404
    gitHandler = GitHandler()
    abs_repopath = repo.get_abs_repopath()
    commit_hash = gitHandler.get_commit_hash(repo, abs_repopath, refs)
    blob = gitHandler.repo_cat_file(abs_repopath, commit_hash, path)
    return HttpResponse(blob, content_type="text/plain")

lang_suffix = {'applescript': 'AppleScript', 'as3': 'AS3', 'bash': 'Bash', 'sh': 'Bash', 'cfm': 'ColdFusion', 'cfc': 'ColdFusion', 'cpp': 'Cpp', 'cxx': 'Cpp', 'c': 'Cpp', 'h': 'Cpp', 'cs': 'CSharp', 'css': 'Css', 'dpr': 'Delphi', 'dfm': 'Delphi', 'pas': 'Delphi', 'diff': 'Diff', 'patch': 'Diff', 'erl': 'Erlang', 'groovy': 'Groovy', 'fx': 'JavaFX', 'jfx': 'JavaFX', 'java': 'Java', 'js': 'JScript', 'pl': 'Perl', 'py': 'Python', 'php': 'Php', 'psl': 'PowerShell', 'rb': 'Ruby', 'sass': 'Sass', 'scala': 'Scala', 'sql': 'Sql', 'vb': 'Vb', 'xml': 'Xml', 'xhtml': 'Xml', 'html': 'Xml', 'htm': 'Xml', 'go': 'Go'}
brush_aliases = {'AppleScript': 'applescript', 'AS3': 'actionscript3', 'Bash': 'shell', 'ColdFusion': 'coldfusion', 'Cpp': 'cpp', 'CSharp': 'csharp', 'Css': 'css', 'Delphi': 'delphi', 'Diff': 'diff', 'Erlang': 'erlang', 'Groovy': 'groovy', 'JavaFX': 'javafx', 'Java': 'java', 'JScript': 'javascript', 'Perl': 'perl', 'Php': 'php', 'Plain': 'plain', 'PowerShell': 'powershell', 'Python': 'python', 'Ruby': 'ruby', 'Sass': 'sass', 'Scala': 'scala', 'Sql': 'sql', 'Vb': 'vb', 'Xml': 'xml', 'Go': 'go'}
@repo_permission_check
def ls_tree(request, user_name, repo_name, refs, path, current):
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    if path is None or path == '':
        path = '.'
    abs_repopath = repo.get_abs_repopath()
    gitHandler = GitHandler()
    commit_hash = gitHandler.get_commit_hash(repo, abs_repopath, refs)
    tree = {}
    if repo.auth_type == 0 or RepoManager.is_repo_member(repo, request.user):
        if path == '.' or path.endswith('/'):
            tree = gitHandler.repo_ls_tree(abs_repopath, commit_hash, path)
    readme_md = None
    if 'README.md' in tree:
        readme_md = gitHandler.repo_cat_file(abs_repopath, commit_hash, path + '/README.md')
    response_dictionary = {'mainnav': 'repo', 'current': current, 'path': path, 'tree': tree, 'readme_md': readme_md}
    response_dictionary.update(get_common_repo_dict(request, repo, user_name, repo_name, refs))
    return render_to_response('repo/tree.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@repo_permission_check
def blob(request, user_name, repo_name, refs, path):
    current = 'tree'
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None or path is None or path == '':
        raise Http404
    abs_repopath = repo.get_abs_repopath()
    gitHandler = GitHandler()
    commit_hash = gitHandler.get_commit_hash(repo, abs_repopath, refs)
    blob = u''; lang = 'Plain'; brush = 'plain'
    if repo.auth_type == 0 or RepoManager.is_repo_member(repo, request.user):
        paths = path.split('.')
        if len(paths) > 0:
            suffix = paths[-1]
            if suffix in lang_suffix and lang_suffix[suffix] in brush_aliases:
                lang = lang_suffix[suffix]
                brush = brush_aliases[lang]
        blob = gitHandler.repo_cat_file(abs_repopath, commit_hash, path)
    is_markdown = path.endswith('.markdown') or path.endswith('.md') or path.endswith('.mkd')
    response_dictionary = {'mainnav': 'repo', 'current': current, 'path': path, 'blob': blob, 'lang': lang, 'brush': brush, 'is_markdown': is_markdown}
    response_dictionary.update(get_common_repo_dict(request, repo, user_name, repo_name, refs))
    return render_to_response('repo/blob.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
    
@repo_permission_check
def commits_default(request, user_name, repo_name):
    refs = 'master'; path = '.'
    return commits(request, user_name, repo_name, refs, path)
    
@repo_permission_check
def commits(request, user_name, repo_name, refs, path):
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    if path is None or path == '':
        path = '.'
    gitHandler = GitHandler()
    abs_repopath = repo.get_abs_repopath()
    commit_hash = gitHandler.get_commit_hash(repo, abs_repopath, refs)
    commits = gitHandler.repo_log_file(abs_repopath, '0000000', commit_hash, path)
    response_dictionary = {'mainnav': 'repo', 'current': 'commits', 'path': path, 'commits': commits}
    response_dictionary.update(get_common_repo_dict(request, repo, user_name, repo_name, refs))
    return render_to_response('repo/commits.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@repo_permission_check
def commits_log(request, user_name, repo_name, from_commit_hash, to_commit_hash):
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    gitHandler = GitHandler()
    abs_repopath = repo.get_abs_repopath()
    orgi_from_commit_hash = from_commit_hash
    orgi_to_commit_hash = to_commit_hash
    from_commit_hash = gitHandler.get_commit_hash(repo, abs_repopath, from_commit_hash)
    to_commit_hash = gitHandler.get_commit_hash(repo, abs_repopath, to_commit_hash)
    commits = gitHandler.repo_log_file(abs_repopath, from_commit_hash, to_commit_hash, '.')
    response_dictionary = {'mainnav': 'repo', 'current': 'commits', 'orgi_from_commit_hash': orgi_from_commit_hash, 'orgi_to_commit_hash': orgi_to_commit_hash, 'from_commit_hash': from_commit_hash, 'to_commit_hash': to_commit_hash, 'commits': commits}
    return json_httpResponse(response_dictionary)

@repo_permission_check
def branches_default(request, user_name, repo_name):
    return branches(request, user_name, repo_name, 'master')

@repo_permission_check
def branches(request, user_name, repo_name, refs):
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    response_dictionary = {'mainnav': 'repo', 'current': 'branches'}
    response_dictionary.update(get_common_repo_dict(request, repo, user_name, repo_name, refs))
    return render_to_response('repo/branches.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@repo_permission_check
def tags_default(request, user_name, repo_name):
    return tags(request, user_name, repo_name, 'master')

@repo_permission_check
def tags(request, user_name, repo_name, refs):
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    response_dictionary = {'mainnav': 'repo', 'current': 'tags'}
    response_dictionary.update(get_common_repo_dict(request, repo, user_name, repo_name, refs))
    return render_to_response('repo/tags.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@repo_permission_check
def compare_default(request, user_name, repo_name):
    return compare_master(request, user_name, repo_name, 'master')

@repo_permission_check
def compare_master(request, user_name, repo_name, refs):
    return compare_commit(request, user_name, repo_name, refs, 'master')

@repo_permission_check
def compare_commit(request, user_name, repo_name, from_refs, to_refs):
    refs = from_refs
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    gitHandler = GitHandler()
    abs_repopath = repo.get_abs_repopath()
    from_commit_hash = gitHandler.get_commit_hash(repo, abs_repopath, from_refs)
    to_commit_hash = gitHandler.get_commit_hash(repo, abs_repopath, to_refs)
    refs_meta = gitHandler.repo_ls_refs(repo, abs_repopath)
    response_dictionary = {'mainnav': 'repo', 'current': 'compare', 'from_refs': from_refs, 'to_refs': to_refs, 'refs_meta': refs_meta}
    response_dictionary.update(get_common_repo_dict(request, repo, user_name, repo_name, refs))
    return render_to_response('repo/compare.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@repo_permission_check

@repo_permission_check
def pulls(request, user_name, repo_name):
    refs = 'master'; path = '.'
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    pullRequests = RepoManager.list_pullRequest_by_descRepoId(repo.id)
    response_dictionary = {'mainnav': 'repo', 'current': 'pull', 'path': path, 'pullRequests': pullRequests}
    response_dictionary.update(get_common_repo_dict(request, repo, user_name, repo_name, refs))
    return render_to_response('repo/pulls.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
@repo_permission_check
def pull_new_default(request, user_name, repo_name):
    source_username = user_name
    source_refs = 'master'
    desc_username = user_name
    desc_refs = 'master'
    if user_name != request.user.username:
        repo = RepoManager.get_repo_by_name(user_name, repo_name)
        if repo is None:
            raise Http404
        child_repo = RepoManager.get_childrepo_by_user_forkrepo(request.user, repo)
        if child_repo is not None:
            source_username = child_repo.username
            source_refs = 'master'
    return pull_new(request, user_name, repo_name, source_username, source_refs, desc_username, desc_refs)

@login_required
@repo_permission_check
def pull_new(request, user_name, repo_name, source_username, source_refs, desc_username, desc_refs):
    refs = 'master'; path = '.'
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    source_repo = RepoManager.get_repo_by_forkrepo(source_username, repo)
    desc_repo = RepoManager.get_repo_by_forkrepo(desc_username, repo)
    if repo is None or source_repo is None or desc_repo is None:
        raise Http404

    # pull action
    if request.method == 'POST':
        source_repo = request.POST.get('source_repo', '')
        source_refs = request.POST.get('source_refs', '')
        desc_repo = request.POST.get('desc_repo', '')
        desc_refs = request.POST.get('desc_refs', '')
        title = request.POST.get('title', '')
        desc = request.POST.get('desc', '')
        if source_repo == '' or source_refs == '' or desc_repo == '' or desc_refs == '' or title == '' or '/' not in source_repo or '/' not in desc_repo:
            return pull_new(request, user_name, repo_name, source_username, source_refs, desc_username, desc_refs)
        if not RepoManager.is_allowed_refsname_pattern(source_refs) or not RepoManager.is_allowed_refsname_pattern(desc_refs):
            return pull_new(request, user_name, repo_name, source_username, source_refs, desc_username, desc_refs)
        (source_username, source_reponame) = source_repo.split('/', 1)
        (desc_username, desc_reponame) = desc_repo.split('/', 1)
        source_pull_repo = RepoManager.get_repo_by_name(source_username, source_reponame)
        desc_pull_repo = RepoManager.get_repo_by_name(desc_username, desc_reponame)
        if not _has_pull_right(request, source_pull_repo, desc_pull_repo):
            return pull_new(request, user_name, repo_name, source_username, source_refs, desc_username, desc_refs)
        pullRequest = PullRequest.create(request.user.id, desc_pull_repo.user_id, source_pull_repo.user_id, source_pull_repo.id, source_refs, desc_pull_repo.user_id, desc_pull_repo.id, desc_refs, title, desc, 0, PULL_STATUS.NEW)
        pullRequest.save()
        pullRequest.fillwith()
        FeedManager.notif_pull_request_status(pullRequest, pullRequest.status)
        FeedManager.feed_pull_change(pullRequest, pullRequest.status)
        return HttpResponseRedirect('/%s/%s/pulls/' % (desc_username, desc_reponame))

    pull_repo_list = _list_pull_repo(request, repo)
    response_dictionary = {'mainnav': 'repo', 'current': 'pull', 'path': path, 'source_username': source_username, 'source_refs': source_refs, 'desc_username': desc_username, 'desc_refs': desc_refs, 'source_repo': source_repo, 'desc_repo': desc_repo, 'pull_repo_list': pull_repo_list}
    response_dictionary.update(get_common_repo_dict(request, repo, user_name, repo_name, refs))
    return render_to_response('repo/pull_new.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@repo_permission_check
def pull_show(request, user_name, repo_name, pullRequest_id):
    refs = 'master'; path = '.'
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    pullRequest = RepoManager.get_pullRequest_by_repoId_id(repo.id, pullRequest_id)
    
    response_dictionary = {'mainnav': 'repo', 'current': 'pull', 'path': path, 'pullRequest': pullRequest}
    response_dictionary.update(get_common_repo_dict(request, repo, user_name, repo_name, refs))
    return render_to_response('repo/pull_show.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@repo_permission_check
@require_http_methods(["POST"])
def pull_commit(request, user_name, repo_name, pullRequest_id):
    refs = 'master'; path = '.'
    args = _get_repo_pull_args(user_name, repo_name, pullRequest_id)
    if args is None:
        return json_httpResponse({'commits': commits, 'result': 'failed'})
    (repo, pullRequest, source_repo, desc_repo, pullrequest_repo_path) = tuple(args)

    gitHandler = GitHandler()
    # prepare pullrequest
    gitHandler.prepare_pull_request(pullRequest, source_repo, desc_repo)

    source_repo_refs_commit_hash = gitHandler.get_commit_hash(source_repo, source_repo.get_abs_repopath(), pullRequest.source_refname)
    desc_repo_refs_commit_hash = gitHandler.get_commit_hash(desc_repo, desc_repo.get_abs_repopath(), pullRequest.desc_refname)
    commits = gitHandler.repo_log_file(pullrequest_repo_path, desc_repo_refs_commit_hash, source_repo_refs_commit_hash, path)
    return json_httpResponse({'commits': commits, 'source_repo_refs_commit_hash': source_repo_refs_commit_hash, 'desc_repo_refs_commit_hash': desc_repo_refs_commit_hash, 'result': 'success'})
    
@repo_permission_check
@require_http_methods(["POST"])
def pull_diff(request, user_name, repo_name, pullRequest_id):
    refs = 'master'; path = '.'
    args = _get_repo_pull_args(user_name, repo_name, pullRequest_id)
    if args is None:
        return json_httpResponse({'commits': commits, 'result': 'failed'})
    (repo, pullRequest, source_repo, desc_repo, pullrequest_repo_path) = tuple(args)

    gitHandler = GitHandler()
    # prepare pullrequest
    gitHandler.prepare_pull_request(pullRequest, source_repo, desc_repo)

    source_repo_refs_commit_hash = gitHandler.get_commit_hash(source_repo, source_repo.get_abs_repopath(), pullRequest.source_refname)
    desc_repo_refs_commit_hash = gitHandler.get_commit_hash(desc_repo, desc_repo.get_abs_repopath(), pullRequest.desc_refname)
    diff = u'+++没有源代码、二进制文件，或者没有查看源代码权限，半公开和私有项目需要申请成为成员才能查看源代码'
    if repo.auth_type == 0 or RepoManager.is_repo_member(repo, request.user):
        diff = gitHandler.repo_diff(pullrequest_repo_path, desc_repo_refs_commit_hash, source_repo_refs_commit_hash, 3, path)
    return json_httpResponse({'diff': diff, 'source_repo_refs_commit_hash': source_repo_refs_commit_hash, 'desc_repo_refs_commit_hash': desc_repo_refs_commit_hash, 'result': 'success'})

@repo_permission_check
@login_required
@require_http_methods(["POST"])
def pull_merge(request, user_name, repo_name, pullRequest_id):
    refs = 'master'; path = '.'
    args = _get_repo_pull_args(user_name, repo_name, pullRequest_id)
    if args is None:
        return json_httpResponse({'commits': commits, 'result': 'failed'})
    (repo, pullRequest, source_repo, desc_repo, pullrequest_repo_path) = tuple(args)
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None or repo.user_id != request.user.id:
        return json_httpResponse({'result': 'failed'})
    source_refs = pullRequest.source_refname
    desc_refs = pullRequest.desc_refname
    gitHandler = GitHandler()
    pullrequest_user = GsuserManager.get_user_by_id(pullRequest.pull_user_id)
    (returncode, output) = gitHandler.merge_pull_request(pullRequest, source_repo, desc_repo, source_refs, desc_refs, pullrequest_user)
    pullRequest.status = PULL_STATUS.MERGED
    if returncode != 0:
        pullRequest.status = PULL_STATUS.MERGED_FAILED
    pullRequest.save()
    FeedManager.notif_pull_request_status(pullRequest, pullRequest.status)
    FeedManager.feed_pull_change(pullRequest, pullRequest.status)
    merge_output_split = '----------- starting merge -----------'
    if merge_output_split in output:
        output = output.split(merge_output_split)[1].strip()
    RepoManager.delete_repo_commit_version(repo)
    return json_httpResponse({'returncode': returncode, 'output': output, 'result': 'success'})

@repo_permission_check
@login_required
@require_http_methods(["POST"])
def pull_reject(request, user_name, repo_name, pullRequest_id):
    refs = 'master'; path = '.'
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None or repo.user_id != request.user.id:
        return json_httpResponse({'result': 'failed'})
    pullRequest = RepoManager.get_pullRequest_by_repoId_id(repo.id, pullRequest_id)
    if pullRequest is None:
        return json_httpResponse({'result': 'failed'})
    pullRequest.status = PULL_STATUS.REJECTED
    pullRequest.save()
    FeedManager.notif_pull_request_status(pullRequest, pullRequest.status)
    FeedManager.feed_pull_change(pullRequest, pullRequest.status)
    return json_httpResponse({'result': 'success'})

@repo_permission_check
@login_required
@require_http_methods(["POST"])
def pull_close(request, user_name, repo_name, pullRequest_id):
    refs = 'master'; path = '.'
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None or repo.user_id != request.user.id:
        return json_httpResponse({'result': 'failed'})
    pullRequest = RepoManager.get_pullRequest_by_repoId_id(repo.id, pullRequest_id)
    if pullRequest is None:
        return json_httpResponse({'result': 'failed'})
    pullRequest.status = PULL_STATUS.CLOSE
    pullRequest.save()
    FeedManager.notif_pull_request_status(pullRequest, pullRequest.status)
    FeedManager.feed_pull_change(pullRequest, pullRequest.status)
    return json_httpResponse({'result': 'success'})

def _get_repo_pull_args(user_name, repo_name, pullRequest_id):
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        return None
    pullRequest = RepoManager.get_pullRequest_by_repoId_id(repo.id, pullRequest_id)
    if pullRequest is None:
        return None
    source_repo = RepoManager.get_repo_by_id(pullRequest.source_repo_id)
    desc_repo = RepoManager.get_repo_by_id(pullRequest.desc_repo_id)
    if source_repo is None or desc_repo is None:
        return None
    pullrequest_repo_path = '%s/%s/%s' % (PULLREQUEST_REPO_PATH, desc_repo.username, desc_repo.name)
    return [repo, pullRequest, source_repo, desc_repo, pullrequest_repo_path]
    
@repo_permission_check
@require_http_methods(["POST"])
def diff_default(request, user_name, repo_name, pre_commit_hash, commit_hash, context):
    return diff(request, user_name, repo_name, pre_commit_hash, commit_hash, context, '.')

@repo_permission_check
@require_http_methods(["POST"])
def diff(request, user_name, repo_name, from_commit_hash, to_commit_hash, context, path):
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    if path is None or path == '':
        path = '.'
    diff = u'+++没有源代码、二进制文件，或者没有查看源代码权限，半公开和私有项目需要申请成为成员才能查看源代码'
    gitHandler = GitHandler()
    abs_repopath = repo.get_abs_repopath()
    orgi_from_commit_hash = from_commit_hash
    orgi_to_commit_hash = to_commit_hash
    from_commit_hash = gitHandler.get_commit_hash(repo, abs_repopath, from_commit_hash)
    to_commit_hash = gitHandler.get_commit_hash(repo, abs_repopath, to_commit_hash)
    if repo.auth_type == 0 or RepoManager.is_repo_member(repo, request.user):
        diff = gitHandler.repo_diff(abs_repopath, from_commit_hash, to_commit_hash, context, path)
    diff['orgi_from_commit_hash'] = orgi_from_commit_hash
    diff['orgi_to_commit_hash'] = orgi_to_commit_hash
    diff['from_commit_hash'] = from_commit_hash
    diff['to_commit_hash'] = to_commit_hash
    return json_httpResponse({'diff': diff})

@repo_permission_check
def network(request, user_name, repo_name):
    refs = 'master'; path = '.'; current = 'network'
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    error = u''
    repoMemberForm = RepoMemberForm()
    if request.method == 'POST' and request.user.is_authenticated():
        repoMemberForm = RepoMemberForm(request.POST)
        if repoMemberForm.is_valid():
            username = repoMemberForm.cleaned_data['username'].strip()
            action = repoMemberForm.cleaned_data['action']
            if action == 'add_member':
                length = len(RepoManager.list_repomember(repo.id))
                if length < 10:
                    RepoManager.add_member(repo.id, username)
                else:
                    error = u'成员数目不得超过10位'
            if action == 'remove_member':
                RepoManager.remove_member(repo.id, username)
    user_id = request.user.id
    member_ids = [o.user_id for o in RepoManager.list_repomember(repo.id)]
    member_ids.insert(0, repo.user_id)
    if user_id != repo.user_id and user_id in member_ids:
        member_ids.remove(user_id)
        member_ids.insert(0, user_id)
    merge_user_map = GsuserManager.map_users(member_ids)
    members_vo = [merge_user_map[o] for o in member_ids]
    response_dictionary = {'mainnav': 'repo', 'current': current, 'path': path, 'members_vo': members_vo, 'repoMemberForm': repoMemberForm}
    response_dictionary.update(get_common_repo_dict(request, repo, user_name, repo_name, refs))
    return render_to_response('repo/network.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@repo_permission_check
def clone_watch_star(request, user_name, repo_name):
    refs = 'master'; path = '.'; current = 'clone'
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    raw_fork_repos_tree = []
    fork_repo_id = repo.fork_repo_id
    if fork_repo_id != 0:
        fork_repo = RepoManager.get_repo_by_id(fork_repo_id)
        if fork_repo is not None:
            raw_fork_repos_tree.append([fork_repo])
    else:
        raw_fork_repos_tree.append([])
    raw_fork_repos_tree.append([repo])
    fork_me_repos = RepoManager.list_fork_repo(repo.id)
    raw_fork_repos_tree.append(fork_me_repos)
    fork_repos_tree = change_to_vo(raw_fork_repos_tree)
    star_users = RepoManager.list_star_user(repo.id, 0, 20)
    watch_users = RepoManager.list_watch_user(repo.id)
    response_dictionary = {'mainnav': 'repo', 'current': current, 'path': path, 'fork_repos_tree': fork_repos_tree, 'star_users': star_users, 'watch_users': watch_users}
    response_dictionary.update(get_common_repo_dict(request, repo, user_name, repo_name, refs))
    return render_to_response('repo/clone_watch_star.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@repo_permission_check
def stats(request, user_name, repo_name):
    refs = 'master'; path = '.'; current = 'stats'
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    userprofile = GsuserManager.get_userprofile_by_id(repo.user_id)
    now = datetime.now()
    last12hours = timeutils.getlast12hours(now)
    last7days = timeutils.getlast7days(now)
    last30days = timeutils.getlast30days(now)
    last12months = timeutils.getlast12months(now)
    raw_last12hours_commit = StatsManager.list_repo_stats(repo.id, 'hour', datetime.fromtimestamp(last12hours[-1]), datetime.fromtimestamp(last12hours[0]))
    last12hours_commit = dict([(time.mktime(x.date.timetuple()), int(x.count)) for x in raw_last12hours_commit])
    raw_last30days_commit = StatsManager.list_repo_stats(repo.id, 'day', datetime.fromtimestamp(last30days[-1]), datetime.fromtimestamp(last30days[0]))
    last30days_commit = dict([(time.mktime(x.date.timetuple()), int(x.count)) for x in raw_last30days_commit])
    last7days_commit = {}
    for x in last7days:
        if x in last30days_commit:
            last7days_commit[x] = last30days_commit[x]
    raw_last12months_commit = StatsManager.list_repo_stats(repo.id, 'month', datetime.fromtimestamp(last12months[-1]), datetime.fromtimestamp(last12months[0]))
    last12months_commit = dict([(time.mktime(x.date.timetuple()), int(x.count)) for x in raw_last12months_commit])

    round_week = timeutils.get_round_week(now)
    round_month = timeutils.get_round_month(now)
    round_year = timeutils.get_round_year(now)
    raw_per_last_week_commit = StatsManager.list_repo_user_stats(repo.id, 'week', round_week)
    raw_per_last_month_commit = StatsManager.list_repo_user_stats(repo.id, 'month', round_month)
    raw_per_last_year_commit = StatsManager.list_repo_user_stats(repo.id, 'year', round_year)
    per_last_week_commit = [int(x.count) for x in raw_per_last_week_commit]
    per_last_month_commit = [int(x.count) for x in raw_per_last_month_commit]
    per_last_year_commit = [int(x.count) for x in raw_per_last_year_commit]
    raw_per_user_week_commit = [x.user_id for x in raw_per_last_week_commit]
    raw_per_user_month_commit = [x.user_id for x in raw_per_last_month_commit]
    raw_per_user_year_commit = [x.user_id for x in raw_per_last_year_commit]
    mergedlist = list(set(raw_per_user_week_commit + raw_per_user_month_commit + raw_per_user_year_commit))
    user_dict = GsuserManager.map_users(mergedlist)
    per_user_week_commit = [str(user_dict[x]['username']) if x in user_dict else 'unknow' for x in raw_per_user_week_commit]
    per_user_month_commit = [str(user_dict[x]['username']) if x in user_dict else 'unknow' for x in raw_per_user_month_commit]
    per_user_year_commit = [str(user_dict[x]['username']) if x in user_dict else 'unknow' for x in raw_per_user_year_commit]

    quotes = {'used_quote': int(repo.used_quote), 'total_quote': int(userprofile.quote)}
    response_dictionary = {'mainnav': 'repo', 'current': 'stats', 'path': path, 'last12hours': last12hours, 'last7days': last7days, 'last30days': last30days, 'last12months': last12months, 'last12hours_commit': last12hours_commit, 'last7days_commit': last7days_commit, 'last30days_commit': last30days_commit, 'last12months_commit': last12months_commit, 'quotes': quotes, 'round_week': round_week, 'round_month': round_month, 'round_year': round_year, 'per_last_week_commit': per_last_week_commit, 'per_last_month_commit': per_last_month_commit, 'per_last_year_commit': per_last_year_commit, 'per_user_week_commit': per_user_week_commit, 'per_user_month_commit': per_user_month_commit, 'per_user_year_commit': per_user_year_commit}
    response_dictionary.update(get_common_repo_dict(request, repo, user_name, repo_name, refs))
    return render_to_response('repo/stats.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@repo_permission_check
@login_required
def settings(request, user_name, repo_name):
    refs = 'master'; path = '.'; current = 'settings'
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None or repo.user_id != request.user.id:
        raise Http404
    if repo.dropbox_sync == 1 and (repo.dropbox_url is None or repo.dropbox_url == ''):
        dropbox_url = dropbox_share_direct('repositories/%s/%s_%s.git' % (repo.username, repo.id, repo.name))
        if dropbox_url is not None and dropbox_url != '':
            repo.dropbox_url = dropbox_url
            repo.save()
    response_dictionary = {'mainnav': 'repo', 'current': current, 'path': path}
    response_dictionary.update(get_common_repo_dict(request, repo, user_name, repo_name, refs))
    return render_to_response('repo/settings.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@repo_permission_check
@login_required
@require_http_methods(["POST"])
def generate_deploy_url(request, user_name, repo_name):
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None or repo.user_id != request.user.id:
        return json_httpResponse({'result': 'failed'})
    random_hash = '%032x' % random.getrandbits(128)
    repo.deploy_url = random_hash
    repo.save()
    return json_httpResponse({'result': 'success'})

@repo_permission_check
@login_required
@require_http_methods(["POST"])
def forbid_dploy_url(request, user_name, repo_name):
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None or repo.user_id != request.user.id:
        return json_httpResponse({'result': 'failed'})
    repo.deploy_url = ''
    repo.save()
    return json_httpResponse({'result': 'success'})

@repo_permission_check
@login_required
@require_http_methods(["POST"])
def enable_dropbox_sync(request, user_name, repo_name):
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None or repo.user_id != request.user.id:
        return json_httpResponse({'result': 'failed'})
    repo.dropbox_sync = 1
    repo.last_push_time = datetime.now()
    if repo.dropbox_url is None or repo.dropbox_url == '':
        dropbox_url = dropbox_share_direct('repositories/%s/%s_%s.git' % (repo.username, repo.id, repo.name))
        repo.dropbox_url = dropbox_url
    repo.save()
    return json_httpResponse({'result': 'success'})

@repo_permission_check
@login_required
@require_http_methods(["POST"])
def disable_dropbox_sync(request, user_name, repo_name):
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None or repo.user_id != request.user.id:
        return json_httpResponse({'result': 'failed'})
    repo.dropbox_sync = 0
    repo.last_push_time = datetime.now()
    repo.save()
    return json_httpResponse({'result': 'success'})

def list_latest_push_repo(request, last_push_time_str):
    secret_key = request.GET.get('secret_key')
    if secret_key != SECRET_KEY:
        return json_httpResponse({'result': 'failed'})
    timedelta_value = 0
    if re.match('\d+[sMdwmy]', last_push_time_str):
        timedelta_value = int(last_push_time_str[0:-1])
    if last_push_time_str.endswith('s'):
        push_timedelta = timedelta(seconds=-timedelta_value)
    elif last_push_time_str.endswith('M'):
        push_timedelta = timedelta(minutes=-timedelta_value)
    elif last_push_time_str.endswith('d'):
        push_timedelta = timedelta(days=-timedelta_value)
    elif last_push_time_str.endswith('w'):
        push_timedelta = timedelta(weeks=-timedelta_value)
    elif last_push_time_str.endswith('m'):
        push_timedelta = timedelta(days=-timedelta_value*30)
    elif last_push_time_str.endswith('y'):
        push_timedelta = timedelta(days=-timedelta_value*365)
    last_push_time = datetime.now() + push_timedelta
    repos = RepoManager.list_repo_by_last_push_time(last_push_time)
    repos_as_view = []
    for repo in repos:
        repo_as_view = {}
        repo_as_view['id'] = repo.id
        repo_as_view['username'] = repo.username
        repo_as_view['name'] = repo.name
        repo_as_view['dropbox_sync'] = repo.dropbox_sync
        repo_as_view['visibly'] = repo.visibly
        repos_as_view.append(repo_as_view)
    return json_httpResponse({'result': 'success', 'latest_push_repos': repos_as_view})

def change_to_vo(raw_fork_repos_tree):
    user_ids = []
    for raw_fork_repos in raw_fork_repos_tree:
        for raw_fork_repo in raw_fork_repos:
            user_ids.append(raw_fork_repo.user_id)
    fork_repos_tree = []
    user_map = GsuserManager.map_users(user_ids)
    for raw_fork_repos in raw_fork_repos_tree:
        fork_repos_tree.append(_conver_repos(raw_fork_repos, user_map))
    return fork_repos_tree

@repo_permission_check
@require_http_methods(["POST"])
def log_graph(request, user_name, repo_name, refs):
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    abs_repopath = repo.get_abs_repopath()
    gitHandler = GitHandler()
    refs_meta = gitHandler.repo_ls_refs(repo, abs_repopath)

    orgi_commit_hash = refs
    commit_hash = gitHandler.get_commit_hash(repo, abs_repopath, refs)
    log_graph = gitHandler.repo_log_graph(abs_repopath, commit_hash)
    log_graph['orgi_commit_hash'] = orgi_commit_hash
    log_graph['commit_hash'] = commit_hash
    log_graph['refs_meta'] = refs_meta
    response_dictionary = {'user_name': user_name, 'repo_name': repo_name}
    response_dictionary.update(log_graph)
    return json_httpResponse(response_dictionary)
    
@repo_permission_check
def refs_graph(request, user_name, repo_name, refs):
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    response_dictionary = {'mainnav': 'repo', 'current': 'refs_graph'}
    response_dictionary.update(get_common_repo_dict(request, repo, user_name, repo_name, refs))
    return render_to_response('repo/refs_graph.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@repo_permission_check
@require_http_methods(["POST"])
def refs(request, user_name, repo_name):
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        return json_httpResponse({'user_name': user_name, 'repo_name': repo_name, 'branches': [], 'tags': []})
    repopath = repo.get_abs_repopath()

    gitHandler = GitHandler()
    refs_meta = gitHandler.repo_ls_refs(repo, repopath)
    response_dictionary = {'mainnav': 'repo', 'user_name': user_name, 'repo_name': repo_name, 'refs_meta': refs_meta}
    return json_httpResponse(response_dictionary)

@repo_permission_check
@login_required
@require_http_methods(["POST"])
def fork(request, user_name, repo_name):
    response_dictionary = {'mainnav': 'repo', 'user_name': user_name, 'repo_name': repo_name}
    has_error = False
    message = 'success'
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        message = u'仓库不存在'
        return json_httpResponse({'result': 'failed', 'message': message})
    userprofile = request.userprofile
    if (userprofile.pubrepo + userprofile.prirepo) >= 100:
        message = u'您的仓库总数量已经超过限制'
        has_error = True
    if (userprofile.used_quote + repo.used_quote) >= userprofile.quote:
        message = u'您剩余空间不足，总空间 %s kb，剩余 %s kb' % (userprofile.quote, userprofile.used_quote)
        has_error = True
    fork_repo = RepoManager.get_repo_by_name(request.user.username, repo.name);
    if fork_repo is not None:
        message = u'您已经有一个名字相同的仓库: %s' % (repo.name)
        has_error = True
    if has_error:
        return json_httpResponse({'result': 'failed', 'message': message})
    fork_repo = Repo.create(request.user.id, repo.id, request.user.username, repo.name, repo.desc, repo.lang, repo.auth_type, repo.used_quote)
    fork_repo.status = 1
    fork_repo.save()
    userprofile.used_quote = userprofile.used_quote + repo.used_quote
    userprofile.save()
    
    # fork event, clone...
    EventManager.send_fork_event(repo.id, fork_repo.id)
    response_dictionary.update({'result': 'success', 'message': 'fork done, start copy repo tree...'})
    return json_httpResponse(response_dictionary)

@repo_permission_check
@login_required
@require_http_methods(["POST"])
def watch(request, user_name, repo_name):
    response_dictionary = {'result': 'success'}
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        message = u'仓库不存在'
        return json_httpResponse({'result': 'failed', 'message': message})
    if not RepoManager.watch_repo(request.userprofile, repo):
        message = u'关注失败，关注数量超过限制或者仓库不允许关注'
        return json_httpResponse({'result': 'failed', 'message': message})
    return json_httpResponse(response_dictionary)

@repo_permission_check
@login_required
@require_http_methods(["POST"])
def unwatch(request, user_name, repo_name):
    response_dictionary = {'result': 'success'}
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        message = u'仓库不存在'
        return json_httpResponse({'result': 'failed', 'message': message})
    if not RepoManager.unwatch_repo(request.userprofile, repo):
        message = u'取消关注失败，可能仓库未被关注'
        return json_httpResponse({'result': 'failed', 'message': message})
    return json_httpResponse(response_dictionary)

@repo_permission_check
@login_required
@require_http_methods(["POST"])
def star(request, user_name, repo_name):
    response_dictionary = {'result': 'success'}
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        message = u'仓库不存在'
        return json_httpResponse({'result': 'failed', 'message': message})
    if not RepoManager.star_repo(request.user.id, repo.id):
        message = u'标星失败，标星数量超过限制或者仓库不允许标星'
        return json_httpResponse({'result': 'failed', 'message': message})
    return json_httpResponse(response_dictionary)

@repo_permission_check
@login_required
@require_http_methods(["POST"])
def unstar(request, user_name, repo_name):
    response_dictionary = {'result': 'success'}
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        message = u'仓库不存在'
        return json_httpResponse({'result': 'failed', 'message': message})
    if not RepoManager.unstar_repo(request.user.id, repo.id):
        message = u'取消标星失败，可能仓库未被标星'
        return json_httpResponse({'result': 'failed', 'message': message})
    return json_httpResponse(response_dictionary)

@login_required
def find(request):
    repo = None
    is_repo_exist = True
    name = request.POST.get('name')
    if RepoManager.is_allowed_reponame_pattern(name):
        repo = RepoManager.get_repo_by_name(request.user.username, name)
        is_repo_exist = (repo is not None)
    return json_httpResponse({'is_repo_exist': is_repo_exist, 'name': name})

@login_required
def create(request, user_name):
    error = u''
    if user_name != request.user.username:
        raise Http404
    thirdpartyUser = GsuserManager.get_thirdpartyUser_by_id(request.user.id)
    repo = Repo()
    repo.user_id = request.user.id
    repo.username = request.user.username
    repoForm = RepoForm(instance = repo)
    response_dictionary = {'mainnav': 'repo', 'repoForm': repoForm, 'error': error, 'thirdpartyUser': thirdpartyUser, 'apply_error': request.GET.get('apply_error')}
    if request.method == 'POST':
        repoForm = RepoForm(request.POST, instance = repo)
        userprofile = request.userprofile
        if (userprofile.pubrepo + userprofile.prirepo) >= 100:
            error = u'您拥有的仓库数量已经达到 100 的限制。'
            return __response_create_repo_error(request, response_dictionary, error)
        if not repoForm.is_valid():
            error = u'输入正确的仓库名称[a-zA-Z0-9_-]，不能 - 开头，选择好语言和可见度，active、watch、recommend、repo是保留的名称。'
            return __response_create_repo_error(request, response_dictionary, error)
        name = repoForm.cleaned_data['name']
        if not RepoManager.is_allowed_reponame_pattern(name):
            error = u'输入正确的仓库名称[a-zA-Z0-9_-]，不能 - 开头，active、watch、recommend、repo是保留的名称。'
            return __response_create_repo_error(request, response_dictionary, error)
        dest_repo = RepoManager.get_repo_by_userId_name(request.user.id, name)
        if dest_repo is not None:
            error = u'仓库名称已经存在。'
            return __response_create_repo_error(request, response_dictionary, error)
        if userprofile.used_quote > userprofile.quote:
            error = u'您剩余空间不足，总空间 %s kb，剩余 %s kb' % (userprofile.quote, userprofile.used_quote)
            return __response_create_repo_error(request, response_dictionary, error)
        remote_git_url = request.POST.get('remote_git_url', '').strip()
        remote_username = request.POST.get('remote_username', '').strip()
        remote_password = request.POST.get('remote_password', '').strip()
        create_repo = repoForm.save()
        if create_repo.auth_type == 0:
            userprofile.pubrepo = userprofile.pubrepo + 1
        else:
            userprofile.prirepo = userprofile.prirepo + 1
        userprofile.save()
        remote_git_url = __validate_get_remote_git_url(remote_git_url, remote_username, remote_password)
        if remote_git_url is not None and remote_git_url != '':
            create_repo.status = 2
            create_repo.save()
        fulfill_gitrepo(create_repo, remote_git_url)
        return HttpResponseRedirect('/%s/%s/' % (request.user.username, name))
    return render_to_response('repo/create.html', response_dictionary, context_instance=RequestContext(request))

def __response_create_repo_error(request, response_dictionary, error):
    response_dictionary['error'] = error
    return render_to_response('repo/create.html', response_dictionary, context_instance=RequestContext(request))

def __validate_get_remote_git_url(remote_git_url, remote_username, remote_password):
    if remote_git_url != '' and not re.match('[a-zA-Z0-9_\.\-\/:]+', remote_git_url):
        return ''
    if remote_git_url.startswith('git://'):
        remote_git_url_as_http = 'http://' + remote_git_url[len('git://'):]
        if __is_url_valid(remote_git_url_as_http):
            return remote_git_url
        return ''
    if remote_username is None or remote_username == '':
        remote_username = 'remote_username'
    if remote_password is None or remote_password == '':
        remote_password = 'remote_password'
    remote_username = urllib.quote_plus(remote_username)
    remote_password = urllib.quote_plus(remote_password)
    if not __is_url_valid(remote_git_url):
        return ''
    protocol = ''
    remote_git_url_without_protocol = ''
    for protocol in ['http://', 'https://']:
        if remote_git_url.startswith(protocol):
            remote_git_url_without_protocol = remote_git_url[len(protocol):]
            return '%s%s:%s@%s' % (protocol, remote_username, remote_password, remote_git_url_without_protocol)
    return ''

def __is_url_valid(url):
    validator = URLValidator(verify_exists=False)
    try:
        validator(url)
        return True
    except ValidationError, e:
        print e
    return False
    
@repo_permission_check
@login_required
def edit(request, user_name, repo_name):
    error = u''
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    repoForm = RepoForm(instance = repo)
    response_dictionary = {'mainnav': 'repo', 'repoForm': repoForm, 'error': error}
    if request.method == 'POST':
        repoForm = RepoForm(request.POST, instance = repo)
        if not repoForm.is_valid():
            error = u'输入正确的仓库名称[a-zA-Z0-9_-]，不能 - 开头，选择好语言和可见度，active、watch、recommend、repo是保留的名称。'
            return __response_edit_repo_error(request, response_dictionary, error)
        name = repoForm.cleaned_data['name']
        if not RepoManager.is_allowed_reponame_pattern(name):
            error = u'输入正确的仓库名称[a-zA-Z0-9_-]，不能 - 开头，active、watch、recommend、repo是保留的名称。'
            return __response_edit_repo_error(request, response_dictionary, error)
        repo = repoForm.save()
        RepoManager.check_export_ok_file(repo)
        return HttpResponseRedirect('/%s/%s/' % (repo.username, repo.name))
    return render_to_response('repo/edit.html', response_dictionary, context_instance=RequestContext(request))

def __response_edit_repo_error(request, response_dictionary, error):
    response_dictionary['error'] = error
    return render_to_response('repo/edit.html', response_dictionary, context_instance=RequestContext(request))

@repo_permission_check
@login_required
def delete(request, user_name, repo_name):
    error = u''
    if user_name != request.user.username:
        raise Http404
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    gsuser = GsuserManager.get_userprofile_by_id(request.user.id)
    if request.method == 'POST':
        repo.visibly = 1
        repo.last_push_time = datetime.now()
        gsuser.used_quote = gsuser.used_quote - repo.used_quote
        if gsuser.used_quote < 0:
            gsuser.used_quote = 0
        gsuser.save()
        repo.save()
        delete_path = '%s/%s' % (DELETE_REPO_PATH, repo.id)
        abs_repopath = repo.get_abs_repopath()
        if os.path.exists(abs_repopath):
            shutil.move(abs_repopath, delete_path)
        feedAction = FeedAction()
        feedAction.delete_repo_feed(repo.id)
        return HttpResponseRedirect('/%s/repo/' % request.user.username)
    response_dictionary = {'mainnav': 'repo', 'user_name': user_name, 'repo_name': repo_name, 'error': error}
    return render_to_response('repo/delete.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def get_commits_by_ids(ids):
    return RepoManager.get_commits_by_ids(ids)

def fulfill_gitrepo(repo, remote_git_url):
    gitHandler = GitHandler()
    username = repo.username
    reponame = repo.name
    user_repo_path = '%s/%s' % (REPO_PATH, username)
    if not os.path.exists(user_repo_path):
        os.makedirs(user_repo_path)
        os.chmod(user_repo_path, 0755)
    repo_path = ('%s/%s/%s.git' % (REPO_PATH, username, reponame))
    if not os.path.exists(repo_path):
        if remote_git_url is not None and remote_git_url != '':
            EventManager.send_import_repo_event(username, reponame, remote_git_url)
        else:
            shutil.copytree(GIT_BARE_REPO_PATH, repo_path)
            gitHandler.update_server_info(repo)
    repo = RepoManager.get_repo_by_name(username, reponame)
    RepoManager.check_export_ok_file(repo)

def get_common_repo_dict(request, repo, user_name, repo_name, refs):
    gitHandler = GitHandler()
    refs_meta = gitHandler.repo_ls_refs(repo, repo.get_abs_repopath())
    is_watched_repo = RepoManager.is_watched_repo(request.user.id, repo.id)
    is_star_repo = RepoManager.is_star_repo(request.user.id, repo.id)
    is_repo_member = RepoManager.is_repo_member(repo, request.user)
    is_owner = (repo.user_id == request.user.id)
    is_branch = (refs in refs_meta['branches'])
    has_fork_right = (repo.auth_type == 0 or is_repo_member)
    has_pull_right = is_owner
    if not is_owner:
        child_repo = RepoManager.get_repo_by_forkrepo(request.user.username, repo)
        if child_repo is not None:
            has_pull_right = True
    repo_pull_new_count = RepoManager.count_pullRequest_by_descRepoId(repo.id, PULL_STATUS.NEW)
    return { 'repo': repo, 'user_name': user_name, 'repo_name': repo_name, 'refs': refs, 'is_watched_repo': is_watched_repo, 'is_star_repo': is_star_repo, 'is_repo_member': is_repo_member, 'is_owner': is_owner, 'is_branch': is_branch, 'has_fork_right': has_fork_right, 'has_pull_right': has_pull_right, 'repo_pull_new_count': repo_pull_new_count, 'refs_meta': refs_meta}

@login_required
def list_github_repos(request):
    thirdpartyUser = GsuserManager.get_thirdpartyUser_by_id(request.user.id)
    if thirdpartyUser is None:
        return json_httpResponse({'result': 'failed', 'cdoe': 404, 'message': 'GitHub account not found', 'repos': []})
    access_token = thirdpartyUser.access_token
    repos_json_str = github_list_repo(access_token)
    return HttpResponse(repos_json_str, mimetype='application/json')

def _list_pull_repo(request, repo):
    pull_repo_list = RepoManager.list_parent_repo(repo, 10)
    child_repo = RepoManager.get_childrepo_by_user_forkrepo(request.user, repo)
    if child_repo is not None:
        pull_repo_list = [child_repo] + pull_repo_list
    return pull_repo_list

def _has_pull_right(request, source_pull_repo, desc_pull_repo):
    if source_pull_repo is None or desc_pull_repo is None:
        return False
    if source_pull_repo.auth_type != 0 and not RepoManager.is_repo_member(source_pull_repo, request.user):
        return False
    if desc_pull_repo.auth_type != 0 and not RepoManager.is_repo_member(desc_pull_repo, request.user):
        return False
    return True

def _conver_repos(raw_repos, map_users):
    repos_vo = []
    for raw_repo in raw_repos:
        repo_dict = model_to_dict(raw_repo, fields=[field.name for field in Repo._meta.fields])
        repo_dict['id'] = raw_repo.id
        repo_dict['create_time'] = time.mktime(raw_repo.create_time.timetuple())
        repo_dict['modify_time'] = time.mktime(raw_repo.modify_time.timetuple())
        if raw_repo.user_id in map_users:
            repo_dict['username'] = map_users[raw_repo.user_id]['username']
            repo_dict['imgurl'] = map_users[raw_repo.user_id]['imgurl']
        repos_vo.append(repo_dict) 
    return repos_vo

def json_ok():
    return json_httpResponse({'result': 'ok'})

def json_failed():
    return json_httpResponse({'result': 'failed'})

