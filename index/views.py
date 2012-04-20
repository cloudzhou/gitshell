from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response

def index(request):
    response_dictionary = {'hello_world': 'hello world'}
    return render_to_response('index.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
def home(request):
    response_dictionary = {'hello_world': 'hello world'}
    return render_to_response('user/home.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
def warehouse(request):
    response_dictionary = {'hello_world': 'hello world'}
    return render_to_response('warehouse/list.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def folder(request):
    response_dictionary = {'hello_world': 'hello world'}
    return render_to_response('warehouse/folder.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def file(request):
    response_dictionary = {'hello_world': 'hello world'}
    return render_to_response('warehouse/file.html',
                          response_dictionary,
                          context_instance=RequestContext(request))						  

