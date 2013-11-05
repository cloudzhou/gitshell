#!/user/bin/python
# -*- coding: utf-8 -*-  
import re, json, time
from sets import Set
from django.template import RequestContext
from django.forms.models import model_to_dict
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, HttpResponseRedirect, Http404
from gitshell.feed.feed import FeedAction, PositionKey, AttrKey
from gitshell.feed.models import Feed, FeedManager
from gitshell.repo.models import RepoManager
from gitshell.gsuser.models import GsuserManager
from gitshell.todolist.models import Scene, ToDoList, ToDoListManager
from gitshell.viewtools.views import json_httpResponse, json_success, json_failed, obj2dict

@login_required
def todo(request):
    current = 'todo'
    feedAction = FeedAction()
    feedAction.set_user_position(request.user.id, PositionKey.TODO)
    scene_id = feedAction.get_user_attr(request.user.id, AttrKey.SCENE_ID)
    if scene_id is None:
        scene_id = 0
    return todo_scene(request, scene_id)

@login_required
def todo_scene(request, env_scene_id):
    current = 'todo'
    feedAction = FeedAction()
    feedAction.set_user_position(request.user.id, PositionKey.TODO)
    feedAction.set_user_attr(request.user.id, AttrKey.SCENE_ID, env_scene_id)
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
    todo_id = int(request.POST.get('todo_id', '0'))
    result_todo_id = ToDoListManager.remove_todo(request.user.id, todo_id)
    response_dictionary = {'todo_id': result_todo_id}
    return json_httpResponse(response_dictionary)

@login_required
@require_http_methods(["POST"])
def doing_todo(request, env_scene_id):
    todo_id = int(request.POST.get('todo_id', '0'))
    result_todo_id = ToDoListManager.doing_todo(request.user.id, todo_id)
    response_dictionary = {'todo_id': result_todo_id}
    return json_httpResponse(response_dictionary)

@login_required
@require_http_methods(["POST"])
def done_todo(request, env_scene_id):
    todo_id = int(request.POST.get('todo_id', '0'))
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

def get_scene(user_id, env_scene_id):
    env_scene_id = int(env_scene_id)
    scene = ToDoListManager.get_scene_by_id(user_id, env_scene_id)
    if scene is None:
        scene = ToDoListManager.get_scene_by_id(user_id, 0)
    return scene

