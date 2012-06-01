#!/user/bin/python
# -*- coding: utf-8 -*-  
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from gitshell.feed.feed import FeedAction

@login_required
def home(request):
    goto = 'feed'
    return HttpResponseRedirect('/home/%s/' % goto)

@login_required
def feed(request):
    current = 'feed'
    response_dictionary = {'current': current}
    return render_to_response('user/home.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
@login_required
def git(request):
    current = 'git'
    feedAction = FeedAction()
    pri_user_feeds = feedAction.get_pri_user_feeds(request.user.id, 0, 100)
    pub_user_feeds = feedAction.get_pub_user_feeds(request.user.id, 0, 100)
    feeds_as_json = git_feeds_as_json(request, pri_user_feeds, pub_user_feeds)
    response_dictionary = {'current': current, 'feeds_as_json': feeds_as_json}
    return render_to_response('user/home.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def git_feeds_as_json(request, pri_user_feeds, pub_user_feeds):
    feeds_json_val = {}
    feeds_json_val['pri_user_feeds_%s' % request.user.id] = feeds_as_json(pri_user_feeds)
    feeds_json_val['pub_user_feeds_%s' % request.user.id] = feeds_as_json(pub_user_feeds)
    return str(feeds_json_val)

def feeds_as_json(feeds):
    json_arr = []
    for feed in feeds:
        json_arr.append(list(feed))
    return json_arr
    
@login_required
def issues(request):
    current = 'issues'
    response_dictionary = {'current': current}
    return render_to_response('user/home.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
@login_required
def explore(request):
    current = 'explore'
    response_dictionary = {'current': current}
    return render_to_response('user/home.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
@login_required
def notif(request):
    current = 'notif'
    response_dictionary = {'current': current}
    return render_to_response('user/home.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
