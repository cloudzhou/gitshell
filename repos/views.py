# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from gitshell.repos.Forms import EditForm

def repos(request, repos_name):
    response_dictionary = {'hello_world': 'hello world1'}
    return render_to_response('home.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@login_required
def edit(request, username, rid):
    editForm = EditForm()
    response_dictionary = {'editForm': editForm}
    return render_to_response('repos/edit.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
