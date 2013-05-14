#!/user/bin/python
# -*- coding: utf-8 -*-  
import re, json, time, copy
from sets import Set
from django.template import RequestContext
from django.forms.models import model_to_dict
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, HttpResponseRedirect, Http404
from gitshell.feed.feed import FeedAction, PositionKey, AttrKey
from gitshell.feed.models import Feed, FeedManager
from gitshell.repo.models import RepoManager, IssuesComment
from gitshell.repo.cons import conver_issues
from gitshell.gsuser.models import GsuserManager
from gitshell.todolist.views import todo
from gitshell.viewtools.views import json_httpResponse, obj2dict

@login_required
def home(request):
    feedAction = FeedAction()
    goto = feedAction.get_user_position(request.user.id)
    if goto == None:
        goto = PositionKey.FEED
    if goto == PositionKey.FEED:
        return feed(request)
    elif goto == PositionKey.TIMELINE:
        return timeline(request)
    elif goto == PositionKey.TODO:
        return todo(request)
    elif goto == PositionKey.PULL:
        return pull_merge(request)
    elif goto == PositionKey.ISSUES:
        return issues(request, 0)
    elif goto == PositionKey.EXPLORE:
        return explore(request)
    elif goto == PositionKey.NOTIF:
        return notif(request)
    return feed(request)

@login_required
def feed(request):
    current = 'feed'
    feedAction = FeedAction()
    feedAction.set_user_position(request.user.id, PositionKey.FEED)
    raw_watch_users = feedAction.get_watch_users(request.user.id, 0, 100)
    watch_user_ids = [int(x[0]) for x in raw_watch_users]
    raw_watch_repos = feedAction.get_watch_repos(request.user.id, 0, 100)
    watch_repo_ids = [int(x[0]) for x in raw_watch_repos]

    feeds_as_json = multi_feeds_as_json(request, feedAction, watch_user_ids, watch_repo_ids)
    response_dictionary = {'current': current, 'feeds_as_json' : feeds_as_json}
    return render_to_response('user/feed.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
@login_required
def timeline(request):
    current = 'timeline'
    feedAction = FeedAction()
    feedAction.set_user_position(request.user.id, PositionKey.TIMELINE)
    pri_user_feeds = feedAction.get_pri_user_feeds(request.user.id, 0, 100)
    pub_user_feeds = feedAction.get_pub_user_feeds(request.user.id, 0, 100)
    feeds_as_json = get_feeds_as_json(request, pri_user_feeds, pub_user_feeds)
    response_dictionary = {'current': current, 'feeds_as_json': feeds_as_json}
    return render_to_response('user/timeline.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def pull_merge(request):
    current = 'pull'
    feedAction = FeedAction()
    feedAction.set_user_position(request.user.id, PositionKey.PULL)
    pullRequests = RepoManager.list_pullRequest_by_mergeUserId(request.user.id)
    response_dictionary = {'current': current, 'pullRequests': pullRequests}
    return render_to_response('user/pull_merge.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
@login_required
def pull_request(request):
    current = 'pull'
    feedAction = FeedAction()
    feedAction.set_user_position(request.user.id, PositionKey.PULL)
    pullRequests = RepoManager.list_pullRequest_by_pullUserId(request.user.id)
    response_dictionary = {'current': current, 'pullRequests': pullRequests}
    return render_to_response('user/pull_request.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def issues_default(request):
    return issues(request, 0)

@login_required
def issues(request, page):
    current = 'issues'
    feedAction = FeedAction()
    feedAction.set_user_position(request.user.id, PositionKey.ISSUES)
    page = int(page)
    page_size = 50
    offset = page*page_size
    row_count = page_size + 1
    raw_issues = RepoManager.list_assigned_issues(request.user.id, 'modify_time', offset, row_count)
    username_map = {}
    reponame_map = {}
    for raw_issue in raw_issues:
        if raw_issue.user_id not in username_map:
            username_map[raw_issue.user_id] = ''
        if raw_issue.assigned not in username_map:
            username_map[raw_issue.assigned] = ''
        if raw_issue.repo_id not in reponame_map:
            reponame_map[raw_issue.repo_id] = ''
    repos = RepoManager.list_repo_by_ids(reponame_map.keys())
    users = GsuserManager.list_user_by_ids(username_map.keys())
    reponame_map = dict([(x.id, x.name) for x in repos])
    username_map = dict([(x.id, x.username) for x in users])
    issues = conver_issues(raw_issues, username_map, reponame_map)

    hasPre = False ; hasNext = False
    if page > 0:
        hasPre = True 
    if len(issues) > page_size:
        hasNext = True
        issues.pop()
    response_dictionary = {'current': current, 'issues': issues, 'page': page, 'hasPre': hasPre, 'hasNext': hasNext}
    return render_to_response('user/issues.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
@login_required
def doissues(request):
    action = request.POST.get('action', '')
    comment = request.POST.get('comment', '')
    repo_id = request.POST.get('repo_id', '')
    issues_id = request.POST.get('issues_id', '')
    if action == '' or repo_id == '' or issues_id == '':
        response_dictionary = {'result': 'failed'}
        return json_httpResponse(response_dictionary)
    repo = RepoManager.get_repo_by_id(int(repo_id))
    issues = RepoManager.get_issues(int(repo_id), int(issues_id))
    if issues is None or issues.user_id != request.user.id:
        response_dictionary = {'result': 'failed'}
        return json_httpResponse(response_dictionary)
    orgi_issue = copy.copy(issues)
    if action == 'fixed':
        issues.status = 4
    elif action == 'close':
        issues.status = 5
    elif action == 'reject':
        issues.status = 6
    if comment != '':
        issuesComment = IssuesComment() 
        issuesComment.issues_id = issues.id
        issuesComment.user_id = request.user.id
        issuesComment.content = comment
        issuesComment.save()
        issues.comment_count = issues.comment_count + 1
    issues.save()
    FeedManager.feed_issue_change(request.user, repo, orgi_issue, issues.id)
    response_dictionary = {'result': 'sucess'}
    return json_httpResponse(response_dictionary)
        
@login_required
def explore(request):
    current = 'explore'
    feedAction = FeedAction()
    feedAction.set_user_position(request.user.id, PositionKey.EXPLORE)
    latest_feeds = feedAction.get_latest_feeds(0, 100)
    feeds_as_json = latest_feeds_as_json(request, latest_feeds)
    response_dictionary = {'current': current, 'feeds_as_json': feeds_as_json}
    return render_to_response('user/explore.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
@login_required
def notif(request):
    current = 'notif'
    feedAction = FeedAction()
    feedAction.set_user_position(request.user.id, PositionKey.NOTIF)
    notifMessages = FeedManager.list_notifmessage_by_userId(request.user.id, 0, 100)
    for notifMessage in notifMessages:
        relative_user = GsuserManager.get_user_by_id(notifMessage.from_user_id)
        if relative_user is not None:
            notifMessage.relative_name = relative_user.username
        if notifMessage.is_at_commit():
            commitHistory = RepoManager.get_commit_by_id(notifMessage.relative_id)
            notifMessage.relative_obj = commitHistory
        elif notifMessage.is_at_issue():
            issues = RepoManager.get_issues_by_id(notifMessage.relative_id)
            if issues is not None:
                repo = RepoManager.get_repo_by_id(issues.repo_id)
                if repo is not None:
                    issues.username = repo.get_repo_username()
                    issues.reponame = repo.name
            notifMessage.relative_obj = issues
        elif notifMessage.is_at_issue_comment():
            issues_comment = RepoManager.get_issues_comment(notifMessage.relative_id)
            issues = RepoManager.get_issues_by_id(issues_comment.issues_id)
            if issues is not None:
                repo = RepoManager.get_repo_by_id(issues.repo_id)
                if repo is not None:
                    issues_comment.username = repo.get_repo_username()
                    issues_comment.reponame = repo.name
            notifMessage.relative_obj = issues_comment
    if request.userprofile.unread_message != 0:
        request.userprofile.unread_message = 0
        request.userprofile.save()
    response_dictionary = {'current': current, 'notifMessages': notifMessages}
    return render_to_response('user/notif.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
def feed_by_ids(request):
    ids_str = request.POST.get('ids_str', '')
    feeds = []
    if re.match('^\w+$', ids_str):
        feeds = _list_feeds(request, ids_str)
    usernames = []
    userIds = [x.user_id for x in feeds]
    _fillwith_commit_message(request, feeds, usernames, userIds)
    _fillwith_issue_event(feeds, usernames, userIds)
    (gravatar_dict, gravatar_userId_dict) = _get_gravatar_dict(usernames, userIds)
    response_dictionary = {'feeds': obj2dict(feeds), 'gravatar_dict': gravatar_dict, 'gravatar_userId_dict': gravatar_userId_dict}
    return json_httpResponse(response_dictionary)

def _get_gravatar_dict(username_list, userIds):
    gravatar_dict = {}
    for username in username_list:
        if username not in gravatar_dict:
            userprofile = GsuserManager.get_userprofile_by_name(username)
            if userprofile is not None:
                gravatar_dict[username] = userprofile.imgurl
                gravatar_dict[username+'_tweet'] = userprofile.tweet
                continue
            gravatar_dict[username] = '0'
            gravatar_dict[username+'_tweet'] = ''
    gravatar_userId_dict = {}
    for userId in userIds:
        if userId not in gravatar_userId_dict:
            user = GsuserManager.get_user_by_id(userId)
            userprofile = GsuserManager.get_userprofile_by_id(userId)
            if user is not None and userprofile is not None:
                gravatar_userId_dict[userId] = userprofile.imgurl
                gravatar_userId_dict[str(userId)+'_username'] = user.username
                gravatar_userId_dict[str(userId)+'_tweet'] = userprofile.tweet
                continue
            gravatar_userId_dict[userId] = '0'
            gravatar_userId_dict[str(userId)+'_username'] = ''
            gravatar_userId_dict[str(userId)+'_tweet'] = ''
    return (gravatar_dict, gravatar_userId_dict)
    

def _list_feeds(request, ids_str):
    ids = _get_feed_ids(ids_str)
    feeds = FeedManager.list_feed_by_ids(ids)
    return feeds

def _fillwith_commit_message(request, feeds, usernames, userIds):
    commit_ids = []
    for feed in feeds:
        if feed.is_commit_message():
            commit_ids.append(feed.relative_id)
    if len(commit_ids) == 0:
        return
    commits = RepoManager.get_commits_by_ids(commit_ids)
    repo_ids = [x.repo_id for x in commits]
    repos = RepoManager.list_repo_by_ids(repo_ids)
    repos_dict = dict([(x.id, x) for x in repos])
    user_ids = [x.user_id for x in repos]
    users = GsuserManager.list_user_by_ids(user_ids)
    users_dict = dict([(x.id, x) for x in users])
    
    commit_view_dict = {}
    for commit in commits:
        repo_id = commit.repo_id
        if repo_id not in repos_dict:
            continue
        repo = repos_dict[repo_id]
        if repo.auth_type == 2:
            if not request.user.is_authenticated() or repo.user_id != request.user.id and not RepoManager.is_repo_member(repo, request.user):
                continue
        commit_view = {}
        commit_view['id'] = commit.id
        if repo.user_id in users_dict:
            commit_view['user_name'] = users_dict[repo.user_id].username
        else:
            commit_view['user_name'] = ''
        commit_view['repo_name'] = commit.repo_name
        commit_view['commit_hash'] = commit.commit_hash
        commit_view['author'] = commit.author
        if commit.author not in usernames:
            usernames.append(commit.author)
        commit_view['committer_date'] = time.mktime(commit.committer_date.timetuple())
        commit_view['subject'] = commit.subject
        commit_view_dict[commit.id] = commit_view
    # fillwith feed
    for feed in feeds:
        if feed.is_commit_message() and feed.relative_id in commit_view_dict:
            feed.relative_obj = commit_view_dict[feed.relative_id]

def _fillwith_issue_event(feeds, usernames, userIds):
    issues = []
    for feed in feeds:
        if feed.is_issue_event():
            issue = RepoManager.get_issues_by_id(feed.relative_id)
            if issue is not None:
                repo = RepoManager.get_repo_by_id(issue.repo_id)
                issue.username = repo.get_repo_username()
                issue.reponame = repo.name
                feed.relative_obj = issue
                issues.append(issue)

def _get_feed_ids(ids_str):
    ids = []
    max_count = 0
    for idstr in ids_str.split('_'):
        if re.match('^\d+$', idstr):
            ids.append(int(idstr))
        max_count = max_count + 1
        if max_count >= 99:
            break
    return ids

def multi_feeds_as_json(request, feedAction, watch_user_ids, watch_repo_ids):
    feeds_json_val = {}
    for user_id in watch_user_ids:
        pub_user_feeds = feedAction.get_pub_user_feeds(user_id, 0, 50)
        if pub_user_feeds is not None and len(pub_user_feeds) > 0:
            feeds_json_val['uf_%s' % user_id] = feeds_as_json(pub_user_feeds)
    for repo_id in watch_repo_ids:
        repo_feeds = feedAction.get_repo_feeds(repo_id, 0, 50)
        if repo_feeds is not None and len(repo_feeds) > 0:
            feeds_json_val['rf_%s' % repo_id] = feeds_as_json(repo_feeds)
    return str(feeds_json_val)

def get_feeds_as_json(request, pri_user_feeds, pub_user_feeds):
    feeds_json_val = {}
    feeds_json_val['pri_user_feeds_%s' % request.user.id] = feeds_as_json(pri_user_feeds)
    feeds_json_val['pub_user_feeds_%s' % request.user.id] = feeds_as_json(pub_user_feeds)
    return str(feeds_json_val)

def latest_feeds_as_json(request, latest_feeds):
    feeds_json_val = {}
    feeds_json_val['latest_feeds'] = feeds_as_json(latest_feeds)
    return str(feeds_json_val)
    
def feeds_as_json(feeds):
    json_arr = []
    for feed in feeds:
        json_arr.append(list(feed))
    return json_arr
    
