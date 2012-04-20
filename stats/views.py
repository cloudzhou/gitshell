# -*- coding: utf-8 -*-  
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

def stats(request):
    response_dictionary = {'ii': range(0, 5), 'jj': range(0, 3), 'kk': range(0, 10)}
    return render_to_response('stats/stats.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
