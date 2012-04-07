# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response

def default(request):
    response_dictionary = {'hello_world': 'hello world'}
    return render_to_response('help/default.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def quickstart(request):
    response_dictionary = {'hello_world': 'hello world'}
    return render_to_response('help/default.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
