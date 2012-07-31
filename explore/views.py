# -*- coding: utf-8 -*-  
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from gitshell.repo.models import RepoManager
from gitshell.stats import timeutils
from gitshell.stats.models import StatsManager
from gitshell.gsuser.models import GsuserManager


def explore(request):
    response_dictionary = {}
    return render_to_response('explore/explore.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
