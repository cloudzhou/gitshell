#!/user/bin/python
# -*- coding: utf-8 -*-  
import re, json, time
from sets import Set
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, HttpResponseRedirect, Http404
from gitshell.feed.feed import FeedAction, PositionKey
from gitshell.repo.models import RepoManager, IssuesComment
from gitshell.repo.cons import conver_issues
from gitshell.gsuser.models import GsuserManager
from gitshell.todolist.models import Scene, ToDoList, ToDoListManager
from gitshell.viewtools.views import json_httpResponse

@login_required
def home(request):
    feedAction = FeedAction()
    goto = feedAction.get_user_position(request.user.id)
    if goto == None:
        goto = PositionKey.FEED
    if goto == PositionKey.FEED:
        return feed(request)
    elif goto == PositionKey.GIT:
        return git(request)
    elif goto == PositionKey.TODO:
        return todo(request)
    elif goto == PositionKey.ISSUES:
        return issues(request, 0)
    elif goto == PositionKey.EXPLORE:
        return explore(request)

@login_required
def feed(request):
    current = 'feed'
    feedAction = FeedAction()
    feedAction.set_user_position(request.user.id, PositionKey.FEED)
    raw_watch_users = feedAction.get_watch_users(request.user.id, 0, 100)
    watch_user_ids = [int(x[0]) for x in raw_watch_users]
    raw_watch_repos = feedAction.get_watch_repos(request.user.id, 0, 100)
    watch_repo_ids = [int(x[0]) for x in raw_watch_repos]

    feeds_as_json = multi_git_feeds_as_json(request, feedAction, watch_user_ids, watch_repo_ids)
    response_dictionary = {'current': current, 'feeds_as_json' : feeds_as_json}
    return render_to_response('user/feed.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
@login_required
def git(request):
    current = 'git'
    feedAction = FeedAction()
    feedAction.set_user_position(request.user.id, PositionKey.GIT)
    pri_user_feeds = feedAction.get_pri_user_feeds(request.user.id, 0, 100)
    pub_user_feeds = feedAction.get_pub_user_feeds(request.user.id, 0, 100)
    feeds_as_json = git_feeds_as_json(request, pri_user_feeds, pub_user_feeds)
    response_dictionary = {'current': current, 'feeds_as_json': feeds_as_json}
    return render_to_response('user/git.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
@login_required
def todo(request):
    current = 'todo'
    feedAction = FeedAction()
    feedAction.set_user_position(request.user.id, PositionKey.TODO)
    scene = Scene.create(request.user.id, 0, 'default')
    return todo_scene(request, scene.id)

@login_required
def todo_scene(request, env_scene_id):
    current = 'todo'
    feedAction = FeedAction()
    feedAction.set_user_position(request.user.id, PositionKey.TODO)
    scene = get_scene(request.user.id, env_scene_id)
    scene_list = ToDoListManager.list_scene_by_userId(request.user.id, 0, 100)
    todoing_list = ToDoListManager.list_doing_todo_by_userId_sceneId(request.user.id, scene.id, 0, 100)
    todone_list = ToDoListManager.list_done_todo_by_userId_sceneId(request.user.id, scene.id, 0, 100)
    response_dictionary = {'current': current, 'scene_list': scene_list, 'scene': scene, 'todoing_list': todoing_list, 'todone_list': todone_list}
    return render_to_response('user/todo.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
@require_http_methods(["POST"])
def add_scene(request, env_scene_id):
    scene_id = 0
    name = request.POST.get('name', '').strip()
    if name != '':
        scene_id = ToDoListManager.add_scene(request.user.id, name)
    response_dictionary = {'scene_id': scene_id, 'name': name}
    return json_httpResponse(response_dictionary)
    # FIXME unicode

@login_required
@require_http_methods(["POST"])
def remove_scene(request, env_scene_id):
    scene_id = ToDoListManager.remove_scene(request.user.id, env_scene_id)
    response_dictionary = {'scene_id': scene_id}
    return json_httpResponse(response_dictionary)

@login_required
@require_http_methods(["POST"])
def add_todo(request, env_scene_id):
    scene = get_scene(request.user.id, env_scene_id)
    todo_text = request.POST.get('todo_text', '').strip()
    todo_id = 0
    if todo_text != '':
        todo_id = ToDoListManager.add_todo(request.user.id, scene.id, todo_text)
    response_dictionary = {'todo_id': todo_id}
    return json_httpResponse(response_dictionary)

@login_required
@require_http_methods(["POST"])
def remove_todo(request, env_scene_id):
    todo_id = int(request.POST.get('todo_id', ''))
    result_todo_id = ToDoListManager.remove_todo(request.user.id, todo_id)
    response_dictionary = {'todo_id': result_todo_id}
    return json_httpResponse(response_dictionary)

@login_required
@require_http_methods(["POST"])
def doing_todo(request, env_scene_id):
    todo_id = int(request.POST.get('todo_id', ''))
    result_todo_id = ToDoListManager.doing_todo(request.user.id, todo_id)
    response_dictionary = {'todo_id': result_todo_id}
    return json_httpResponse(response_dictionary)

@login_required
@require_http_methods(["POST"])
def done_todo(request, env_scene_id):
    todo_id = int(request.POST.get('todo_id', ''))
    result_todo_id = ToDoListManager.done_todo(request.user.id, todo_id)
    response_dictionary = {'todo_id': result_todo_id}
    return json_httpResponse(response_dictionary)

@login_required
@require_http_methods(["POST"])
def update_scene_meta(request, env_scene_id):
    scene = get_scene(request.user.id, env_scene_id)
    todo_str_ids = request.POST.get('todo_ids', '')
    todo_ids = [int(x) for x in todo_str_ids.split(',')]
    result = ToDoListManager.update_scene_meta(request.user.id, scene.id, todo_ids)
    response_dictionary = {'result': result}
    return json_httpResponse(response_dictionary)

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
    issues = RepoManager.get_issues(int(repo_id), int(issues_id))
    if issues is None or issues.user_id != request.user.id:
        response_dictionary = {'result': 'failed'}
        return json_httpResponse(response_dictionary)
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
    response_dictionary = {'current': current}
    return render_to_response('user/home.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
def feedbyids(request):
    ids_str = request.POST.get('ids_str', '')
    feeds = []
    if re.match('^\w+$', ids_str):
        feeds = get_feeds(request, ids_str)
    gravatarmap = get_gravatarmap(feeds)
    response_dictionary = {'feeds': feeds, 'gravatarmap': gravatarmap}
    return json_httpResponse(response_dictionary)

def get_gravatarmap(feeds):
    gravatarmap = {}
    for feed in feeds:
        username = feed['author']
        if username not in gravatarmap:
            userprofile = GsuserManager.get_userprofile_by_name(username)
            if userprofile is not None:
                gravatarmap[username] = userprofile.imgurl
                gravatarmap[username+'_tweet'] = userprofile.tweet
                continue
            gravatarmap[username] = '0'
            gravatarmap[username+'_tweet'] = ''
    return gravatarmap
    

def get_feeds(request, ids_str):
    feeds = []
    ids = []
    max_count = 0
    for idstr in ids_str.split('_'):
        if re.match('^\d+$', idstr):
            ids.append(int(idstr))
        max_count = max_count + 1
        if max_count >= 99:
            break
    commits = RepoManager.get_commits_by_ids(ids)
    repo_ids = [x.repo_id for x in commits]
    repos = RepoManager.list_repo_by_ids(repo_ids)
    repos_dict = dict([(x.id, x) for x in repos])
    user_ids = [x.user_id for x in repos]
    users = GsuserManager.list_user_by_ids(user_ids)
    users_dict = dict([(x.id, x) for x in users])
    
    for commit in commits:
        repo_id = commit.repo_id
        if repo_id not in repos_dict:
            continue
        repo = repos_dict[repo_id]
        if repo.auth_type == 2:
            if not request.user.is_authenticated() or repo.user_id != request.user.id and not RepoManager.is_repo_member(repo, request.user):
                continue
        feed = {}
        feed['id'] = commit.id
        if repo.user_id in users_dict:
            feed['user_name'] = users_dict[repo.user_id].username
        else:
            feed['user_name'] = ''
        feed['repo_name'] = commit.repo_name
        feed['commit_hash'] = commit.commit_hash
        feed['author'] = commit.author
        feed['committer_date'] = time.mktime(commit.committer_date.timetuple())
        feed['subject'] = commit.subject
        feeds.append(feed)
    return feeds

def multi_git_feeds_as_json(request, feedAction, watch_user_ids, watch_repo_ids):
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

def git_feeds_as_json(request, pri_user_feeds, pub_user_feeds):
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
    
def get_scene(user_id, env_scene_id):
    scene = None
    if env_scene_id != 0:
        scene = ToDoListManager.get_scene_by_id(user_id, env_scene_id)
    if scene == None:
        scene = Scene.create(user_id, 0, 'default')
    return scene

