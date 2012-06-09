from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response

def index(request):
    response_dictionary = {'hello_world': 'hello world', 'ii': range(0, 3)}
    return render_to_response('index.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
def home(request):
    response_dictionary = {'hello_world': 'hello world'}
    return render_to_response('user/home.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

