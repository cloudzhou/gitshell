# -*- coding: utf-8 -*-  
import os, re
import shutil, copy
import json, time
from datetime import datetime
from datetime import timedelta
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.shortcuts import render_to_response
from django.utils.html import escape
from gitshell.feed.feed import FeedAction
from gitshell.feed.models import FeedManager
from gitshell.repo.Forms import RepoForm, RepoIssuesForm, IssuesComment, RepoIssuesCommentForm, RepoMemberForm
from gitshell.repo.githandler import GitHandler
from gitshell.repo.models import Repo, RepoManager, Issues
from gitshell.repo.cons import TRACKERS, STATUSES, PRIORITIES, TRACKERS_VAL, STATUSES_VAL, PRIORITIES_VAL, ISSUES_ATTRS, conver_issues, conver_issue_comments, conver_repos
from gitshell.gsuser.models import GsuserManager
from gitshell.gsuser.decorators import repo_permission_check, repo_source_permission_check
from gitshell.stats import timeutils
from gitshell.stats.models import StatsManager
from gitshell.settings import REPO_PATH, GIT_BARE_REPO_PATH, DELETE_REPO_PATH
from gitshell.daemon.models import EventManager
from gitshell.viewtools.views import json_httpResponse
from gitshell.gsuser.middleware import KEEP_REPO_NAME

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
    return repo_ls_tree(request, user_name, repo_name, refs, path, current)

@repo_permission_check
def repo_default_tree(request, user_name, repo_name):
    refs = 'master'; path = '.'; current = 'tree'
    return repo_ls_tree(request, user_name, repo_name, refs, path, current)
    
@repo_permission_check
def repo_tree(request, user_name, repo_name, refs, path):
    current = 'tree'
    return repo_ls_tree(request, user_name, repo_name, refs, path, current)

@repo_permission_check
def repo_raw_tree(request, user_name, repo_name, refs, path):
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None or path.endswith('/'):
        raise Http404
    gitHandler = GitHandler()
    abs_repopath = repo.get_abs_repopath(user_name)
    commit_hash = gitHandler.get_commit_hash(repo, abs_repopath, refs)
    blob = gitHandler.repo_cat_file(abs_repopath, commit_hash, path)
    return HttpResponse(blob, content_type="text/plain")

lang_suffix = {'applescript': 'AppleScript', 'as3': 'AS3', 'bash': 'Bash', 'sh': 'Bash', 'cfm': 'ColdFusion', 'cfc': 'ColdFusion', 'cpp': 'Cpp', 'cxx': 'Cpp', 'c': 'Cpp', 'h': 'Cpp', 'cs': 'CSharp', 'css': 'Css', 'dpr': 'Delphi', 'dfm': 'Delphi', 'pas': 'Delphi', 'diff': 'Diff', 'patch': 'Diff', 'erl': 'Erlang', 'groovy': 'Groovy', 'fx': 'JavaFX', 'jfx': 'JavaFX', 'java': 'Java', 'js': 'JScript', 'pl': 'Perl', 'py': 'Python', 'php': 'Php', 'psl': 'PowerShell', 'rb': 'Ruby', 'sass': 'Sass', 'scala': 'Scala', 'sql': 'Sql', 'vb': 'Vb', 'xml': 'Xml', 'xhtml': 'Xml', 'html': 'Xml', 'htm': 'Xml'}
brush_aliases = {'AppleScript': 'applescript', 'AS3': 'actionscript3', 'Bash': 'shell', 'ColdFusion': 'coldfusion', 'Cpp': 'cpp', 'CSharp': 'csharp', 'Css': 'css', 'Delphi': 'delphi', 'Diff': 'diff', 'Erlang': 'erlang', 'Groovy': 'groovy', 'JavaFX': 'javafx', 'Java': 'java', 'JScript': 'javascript', 'Perl': 'perl', 'Php': 'php', 'Plain': 'plain', 'PowerShell': 'powershell', 'Python': 'python', 'Ruby': 'ruby', 'Sass': 'sass', 'Scala': 'scala', 'Sql': 'sql', 'Vb': 'vb', 'Xml': 'xml'}
@repo_permission_check
def repo_ls_tree(request, user_name, repo_name, refs, path, current):
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    if path is None or path == '':
        path = '.'
    gitHandler = GitHandler()
    abs_repopath = repo.get_abs_repopath(user_name)
    commit_hash = gitHandler.get_commit_hash(repo, abs_repopath, refs)
    is_tree = True ; tree = {} ; blob = u''; lang = 'Plain'; brush = 'plain'
    if repo.auth_type == 0 or RepoManager.is_repo_member(repo, request.user):
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
    is_markdown = path.endswith('.markdown') or path.endswith('.md') or path.endswith('.mkd')
    response_dictionary = {'mainnav': 'repo', 'current': current, 'path': path, 'tree': tree, 'blob': blob, 'is_tree': is_tree, 'lang': lang, 'brush': brush, 'is_markdown': is_markdown}
    response_dictionary.update(get_common_repo_dict(request, repo, user_name, repo_name, refs))
    return render_to_response('repo/tree.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@repo_permission_check
def repo_default_commits(request, user_name, repo_name):
    refs = 'master'; path = '.'
    return repo_commits(request, user_name, repo_name, refs, path)
    
@repo_permission_check
def repo_commits(request, user_name, repo_name, refs, path):
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    if path is None or path == '':
        path = '.'
    gitHandler = GitHandler()
    abs_repopath = repo.get_abs_repopath(user_name)
    commit_hash = gitHandler.get_commit_hash(repo, abs_repopath, refs)
    commits = gitHandler.repo_log_file(abs_repopath, commit_hash, path)
    response_dictionary = {'mainnav': 'repo', 'current': 'commits', 'path': path, 'commits': commits}
    response_dictionary.update(get_common_repo_dict(request, repo, user_name, repo_name, refs))
    return render_to_response('repo/commits.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@repo_permission_check
@require_http_methods(["POST"])
def repo_diff(request, user_name, repo_name, pre_commit_hash, commit_hash, path):
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    if path is None or path == '':
        path = '.'
    gitHandler = GitHandler()
    abs_repopath = repo.get_abs_repopath(user_name)
    diff = u'+++没有源代码、二进制文件，或者没有查看源代码权限，半公开和私有项目需要申请成为成员才能查看源代码'
    if repo.auth_type == 0 or RepoManager.is_repo_member(repo, request.user):
        diff = gitHandler.repo_diff(abs_repopath, pre_commit_hash, commit_hash, path)
    return json_httpResponse({'diff': diff})

@repo_permission_check
def issues(request, user_name, repo_name):
    return issues_list(request, user_name, repo_name, '0', '0', '0', '0', 'modify_time', 0)
 
@repo_permission_check
def issues_list(request, user_name, repo_name, assigned, tracker, status, priority, orderby, page):
    refs = 'master'; path = '.'; current = 'issues'
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    user_id = request.user.id
    member_ids = [o.user_id for o in RepoManager.list_repomember(repo.id)]
    member_ids.insert(0, repo.user_id)
    if user_id != repo.user_id and user_id in member_ids:
        member_ids.remove(user_id)
        member_ids.insert(0, user_id)
    members = GsuserManager.list_user_by_ids(member_ids)
    assigneds = [o.username for o in members]
    assigneds.insert(0, '0')
    if assigned is None:
        assigned = assigneds[0]
    assigned_id = 0
    assigned_user = GsuserManager.get_user_by_name(assigned)
    if assigned_user is not None and assigned in assigneds:
        assigned_id = assigned_user.id
    tracker = int(tracker); status = int(status); priority = int(priority); page = int(page)
    current_attrs = { 'assigned': str(assigned), 'tracker': tracker, 'status': status, 'priority': priority, 'orderby': str(orderby), 'page': page }
    raw_issues = []
    page_size = 50
    offset = page*page_size
    row_count = page_size + 1
    if assigned_id == 0 and tracker == 0 and status == 0 and priority == 0:
        raw_issues = RepoManager.list_issues(repo.id, orderby, offset, row_count)
    else:
        assigned_ids = member_ids if assigned_id == 0 else [assigned_id]
        trackeres = TRACKERS_VAL if tracker == 0 else [tracker]
        statuses = STATUSES_VAL if status == 0 else [status]
        priorities = PRIORITIES_VAL if priority == 0 else [priority] 
        raw_issues = RepoManager.list_issues_cons(repo.id, assigned_ids, trackeres, statuses, priorities, orderby, offset, row_count)
    reporter_ids = [o.user_id for o in raw_issues]
    reporters = GsuserManager.list_user_by_ids(list(set(reporter_ids)-set(member_ids)))
    username_map = {}
    for member in members:
        username_map[member.id] = member.username
    for reporter in reporters:
        username_map[reporter.id] = reporter.username
    issues = conver_issues(raw_issues, username_map, {repo.id: repo.name})

    hasPre = False ; hasNext = False
    if page > 0:
        hasPre = True 
    if len(issues) > page_size:
        hasNext = True
        issues.pop()
    
    response_dictionary = {'mainnav': 'repo', 'current': current, 'path': path, 'assigneds': assigneds, 'assigned': assigned, 'tracker': tracker, 'status': status, 'priority': priority, 'orderby': orderby, 'page': page, 'current_attrs': current_attrs, 'issues': issues, 'hasPre': hasPre, 'hasNext': hasNext}
    response_dictionary.update(ISSUES_ATTRS)
    response_dictionary.update(get_common_repo_dict(request, repo, user_name, repo_name, refs))
    return render_to_response('repo/issues.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@repo_permission_check
def issues_default_show(request, user_name, repo_name, issues_id):
    return issues_show(request, user_name, repo_name, issues_id, None)

@repo_permission_check
def issues_show(request, user_name, repo_name, issues_id, page):
    refs = 'master'; path = '.'; current = 'issues'
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    raw_issue = RepoManager.get_issues(repo.id, issues_id)
    if raw_issue is None:
        raise Http404
    repoIssuesCommentForm = RepoIssuesCommentForm()
    if request.method == 'POST' and request.user.is_authenticated():
        issuesComment = IssuesComment() 
        issuesComment.issues_id = issues_id
        issuesComment.user_id = request.user.id
        repoIssuesCommentForm = RepoIssuesCommentForm(request.POST, instance = issuesComment)
        if repoIssuesCommentForm.is_valid():
            cid = repoIssuesCommentForm.save().id
            FeedManager.notif_issue_comment_at(request.user.id, cid, repoIssuesCommentForm.cleaned_data['content'])
            raw_issue.comment_count = raw_issue.comment_count + 1
            raw_issue.save()
            return HttpResponseRedirect('/%s/%s/issues/%s/' % (user_name, repo_name, issues_id))
    issues_id = int(issues_id)
    username_map = {}
    users = GsuserManager.list_user_by_ids([raw_issue.user_id, raw_issue.assigned])
    for user in users:
        username_map[user.id] = user.username
    issue = conver_issues([raw_issue], username_map, {repo.id: repo.name})[0]
    
    page_size = 50
    total_count = issue['comment_count']
    total_page = issue['comment_count'] / page_size
    if issue['comment_count'] != 0 and issue['comment_count'] % page_size == 0:
        total_page = total_page - 1
    if page is None or int(page) > total_page:
        page = total_page
    else:
        page = int(page)
    user_img_map = {}
    issue_comments = []
    if total_count > 0:
        offset = page*page_size
        row_count = page_size
        raw_issue_comments = RepoManager.list_issues_comment(issues_id, offset, row_count)
        user_ids = [o.user_id for o in raw_issue_comments]
        users = GsuserManager.list_user_by_ids(user_ids)
        userprofiles = GsuserManager.list_userprofile_by_ids(user_ids)
        for user in users:
            username_map[user.id] = user.username
        for userprofile in userprofiles:
            user_img_map[userprofile.id] = userprofile.imgurl 
        issue_comments = conver_issue_comments(raw_issue_comments, username_map, user_img_map)

    member_ids = [o.user_id for o in RepoManager.list_repomember(repo.id)]
    member_ids.insert(0, repo.user_id)
    if raw_issue.user_id != repo.user_id and request.user.id in member_ids:
        member_ids.remove(request.user.id)
        member_ids.insert(0, request.user.id)
    members = GsuserManager.list_user_by_ids(member_ids)
    assigneds = [o.username for o in members]

    has_issues_modify_right = __has_issues_modify_right(request, raw_issue, repo)
    response_dictionary = {'mainnav': 'repo', 'current': current, 'path': path, 'issue': issue, 'issue_comments': issue_comments, 'repoIssuesCommentForm': repoIssuesCommentForm, 'page': page, 'total_page': range(0, total_page+1), 'assigneds': assigneds, 'assigned': issue['assigned'], 'tracker': raw_issue.tracker, 'status': raw_issue.status, 'priority': raw_issue.priority, 'has_issues_modify_right': has_issues_modify_right}
    response_dictionary.update(ISSUES_ATTRS)
    response_dictionary.update(get_common_repo_dict(request, repo, user_name, repo_name, refs))
    return render_to_response('repo/issues_show.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
@repo_permission_check
def issues_create(request, user_name, repo_name, issues_id):
    refs = 'master'; path = '.'; current = 'issues'
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    has_issues_modify = False
    repoIssuesForm = RepoIssuesForm()
    issues = Issues()
    orgi_issue = None
    if issues_id != 0:
        issues = RepoManager.get_issues(repo.id, issues_id)
        orgi_issue = copy.copy(issues)
        has_issues_modify = __has_issues_modify_right(request, issues, repo)
        if not has_issues_modify: 
            issues = Issues()
            orgi_issue = None
        repoIssuesForm = RepoIssuesForm(instance = issues)
    repoIssuesForm.fill_assigned(repo)
    error = ''
    if request.method == 'POST':
        issues.user_id = request.user.id
        issues.repo_id = repo.id
        repoIssuesForm = RepoIssuesForm(request.POST, instance = issues)
        repoIssuesForm.fill_assigned(repo)
        if repoIssuesForm.is_valid():
            nid = repoIssuesForm.save().id
            FeedManager.notif_issue_at(request.user.id, nid, repoIssuesForm.cleaned_data['subject'] + ' ' + repoIssuesForm.cleaned_data['content'])
            FeedManager.feed_issue_change(request.user, repo, orgi_issue, nid)
            return HttpResponseRedirect('/%s/%s/issues/%s/' % (user_name, repo_name, nid))
        else:
            error = u'issues 内容不能为空'
    response_dictionary = {'mainnav': 'repo', 'current': current, 'path': path, 'repoIssuesForm': repoIssuesForm, 'error': error, 'issues_id': issues_id, 'has_issues_modify': has_issues_modify}
    response_dictionary.update(ISSUES_ATTRS)
    response_dictionary.update(get_common_repo_dict(request, repo, user_name, repo_name, refs))
    return render_to_response('repo/issues_create.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
@repo_permission_check
@require_http_methods(["POST"])
def issues_delete(request, user_name, repo_name, issue_id):
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    issues = RepoManager.get_issues(repo.id, issue_id)
    if issues is not None:
        if __has_issues_modify_right(request, issues, repo):
            issues.visibly = 1
            issues.save()
    return json_httpResponse({'result': 'ok'})

@login_required
@repo_permission_check
@require_http_methods(["POST"])
def issues_update(request, user_name, repo_name, issue_id, attr):
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    issues = RepoManager.get_issues(repo.id, issue_id)
    if issues is None:
        raise Http404
    has_issues_modify = __has_issues_modify_right(request, issues, repo)
    if not has_issues_modify:
        return json_failed()
    orgi_issue = copy.copy(issues)
    (key, value) = attr.split('___', 1)
    if key == 'assigned':
        user = GsuserManager.get_user_by_name(value)
        if user is not None:
            repoMember = RepoManager.get_repo_member(repo.id, user.id)
            if repoMember is not None:
                issues.assigned = repoMember.user_id
                issues.save()
                FeedManager.feed_issue_change(request.user, repo, orgi_issue, issues.id)
        return json_ok()
    value = int(value)
    if key == 'tracker':
        issues.tracker = value
    elif key == 'status':
        issues.status = value
    elif key == 'priority':
        issues.priority = value
    issues.save()
    FeedManager.feed_issue_change(request.user, repo, orgi_issue, issues.id)
    return json_ok()

@login_required
@repo_permission_check
@require_http_methods(["POST"])
def issues_comment_delete(request, user_name, repo_name, comment_id):
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        raise Http404
    issues_comment = RepoManager.get_issues_comment(comment_id)
    if issues_comment is not None:
        issues = RepoManager.get_issues(repo.id, issues_comment.issues_id)
        if issues is not None and __has_issues_comments_modify_right(request, issues_comment, repo):
            issues_comment.visibly = 1
            issues_comment.save()
            issues.comment_count = issues.comment_count - 1
            issues.save()
    return json_ok()

@repo_permission_check
def repo_network(request, user_name, repo_name):
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
def repo_clone_watch(request, user_name, repo_name):
    refs = 'master'; path = '.'; current = 'branches'
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
    watch_users = RepoManager.list_watch_user(repo.id)
    response_dictionary = {'mainnav': 'repo', 'current': current, 'path': path, 'fork_repos_tree': fork_repos_tree, 'watch_users': watch_users, 'test': {1, 1}}
    response_dictionary.update(get_common_repo_dict(request, repo, user_name, repo_name, refs))
    return render_to_response('repo/clone_watch.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@repo_permission_check
def repo_stats(request, user_name, repo_name):
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

def change_to_vo(raw_fork_repos_tree):
    user_ids = []
    for raw_fork_repos in raw_fork_repos_tree:
        for raw_fork_repo in raw_fork_repos:
            user_ids.append(raw_fork_repo.user_id)
    fork_repos_tree = []
    user_map = GsuserManager.map_users(user_ids)
    for raw_fork_repos in raw_fork_repos_tree:
        fork_repos_tree.append(conver_repos(raw_fork_repos, user_map))
    return fork_repos_tree

@repo_permission_check
@require_http_methods(["POST"])
def repo_refs(request, user_name, repo_name):
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        return json_httpResponse({'user_name': user_name, 'repo_name': repo_name, 'branches': [], 'tags': []})
    repopath = repo.get_abs_repopath(user_name)

    gitHandler = GitHandler()
    branches_refs = gitHandler.repo_ls_branches(repo, repopath)
    tags_refs = gitHandler.repo_ls_tags(repo, repopath)
    response_dictionary = {'mainnav': 'repo', 'user_name': user_name, 'repo_name': repo_name, 'branches': branches_refs, 'tags': tags_refs}
    return json_httpResponse(response_dictionary)

@repo_permission_check
@login_required
@require_http_methods(["POST"])
def repo_fork(request, user_name, repo_name):
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
    fork_repo = Repo.create(request.user.id, repo.id, repo.name, repo.desc, repo.lang, repo.auth_type, repo.used_quote)
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
def repo_watch(request, user_name, repo_name):
    response_dictionary = {'result': 'success'}
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        message = u'仓库不存在'
        return json_httpResponse({'result': 'failed', 'message': message})
    if not RepoManager.watch_repo(request.userprofile, repo):
        message = u'关注失败，关注数量超过限制或者仓库不允许关注'
        return json_httpResponse({'result': 'failed', 'message': message})
    return json_httpResponse(response_dictionary)

@login_required
@require_http_methods(["POST"])
def repo_unwatch_by_id(request, repo_id):
    response_dictionary = {'result': 'success'}
    repo = RepoManager.get_rawrepo_by_id(repo_id)
    if repo is None:
        message = u'仓库不存在'
        return json_httpResponse({'result': 'failed', 'message': message})
    if not RepoManager.unwatch_repo(request.userprofile, repo):
        message = u'取消关注失败，可能仓库未被关注'
        return json_httpResponse({'result': 'failed', 'message': message})
    return json_httpResponse(response_dictionary)

@login_required
@require_http_methods(["POST"])
def repo_unwatch(request, user_name, repo_name):
    response_dictionary = {'result': 'success'}
    repo = RepoManager.get_repo_by_name(user_name, repo_name)
    if repo is None:
        message = u'仓库不存在'
        return json_httpResponse({'result': 'failed', 'message': message})
    if not RepoManager.unwatch_repo(request.userprofile, repo):
        message = u'取消关注失败，可能仓库未被关注'
        return json_httpResponse({'result': 'failed', 'message': message})
    return json_httpResponse(response_dictionary)

@login_required
def edit(request, user_name, rid):
    error = u''
    if user_name != request.user.username:
        raise Http404
    repo = RepoManager.get_repo_by_id(int(rid))
    if repo is None:
        repo = Repo()
    elif repo.user_id != request.user.id:
        raise Http404
    repo.user_id = request.user.id
    repoForm = RepoForm(instance = repo)
    if request.method == 'POST':
        repoForm = RepoForm(request.POST, instance = repo)
        if repoForm.is_valid():
            name = repoForm.cleaned_data['name']
            if re.match("^\w+$", name) and name not in KEEP_REPO_NAME:
                dest_repo = RepoManager.get_repo_by_userId_name(request.user.id, name)
                if dest_repo is None or (repo.id is not None and dest_repo.id == repo.id):
                    fulfill_gitrepo(request.user.username, name, repoForm.cleaned_data['auth_type'])
                    repoForm.save()
                    return HttpResponseRedirect('/' + request.user.username + '/repo/')
        error = u'输入正确的仓库名称[A-Za-z0-9_]，选择好语言和可见度，仓库名字不能重复，active、watch、recommend、repo是保留的名称。'
    response_dictionary = {'mainnav': 'repo', 'repoForm': repoForm, 'rid': rid, 'error': error}
    return render_to_response('repo/edit.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

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
        gsuser.used_quote = gsuser.used_quote - repo.used_quote
        if gsuser.used_quote < 0:
            gsuser.used_quote = 0
        gsuser.save()
        repo.save()
        delete_path = '%s/%s' % (DELETE_REPO_PATH, repo.id)
        abs_repopath = repo.get_abs_repopath(request.user.username)
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

def fulfill_gitrepo(username, reponame, auth_type):
    user_repo_path = '%s/%s' % (REPO_PATH, username)
    if not os.path.exists(user_repo_path):
        os.makedirs(user_repo_path)
        os.chmod(user_repo_path, 0755)
    repo_path = ('%s/%s/%s.git' % (REPO_PATH, username, reponame))
    if not os.path.exists(repo_path):
        shutil.copytree(GIT_BARE_REPO_PATH, repo_path)
    git_daemon_export_ok_file_path = '%s/%s' % (repo_path, 'git-daemon-export-ok')
    if auth_type == 0:
        if not os.path.exists(git_daemon_export_ok_file_path):
            with open(git_daemon_export_ok_file_path, 'w') as _file:
                _file.close()
    else:
        if os.path.exists(git_daemon_export_ok_file_path):
            os.remove(git_daemon_export_ok_file_path)

def get_common_repo_dict(request, repo, user_name, repo_name, refs):
    is_watched_repo = RepoManager.is_watched_repo(request.user.id, repo.id)
    is_repo_member = RepoManager.is_repo_member(repo, request.user)
    is_owner = (repo.user_id == request.user.id)
    has_fork_right = (repo.auth_type == 0 or is_repo_member)
    return { 'repo': repo, 'user_name': user_name, 'repo_name': repo_name, 'refs': refs, 'is_watched_repo': is_watched_repo, 'is_repo_member': is_repo_member, 'is_owner': is_owner, 'has_fork_right': has_fork_right}

def __has_issues_modify_right(request, issues, repo):
    return issues is not None and (request.user.id == issues.user_id or request.user.id == repo.user_id)

def __has_issues_comments_modify_right(request, issues_comment, repo):
    return issues is not None and (request.user.id == issues_comment.user_id or request.user.id == repo.user_id)

def json_ok():
    return json_httpResponse({'result': 'ok'})

def json_failed():
    return json_httpResponse({'result': 'failed'})

