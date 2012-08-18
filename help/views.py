from django.core.cache import cache
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.views.decorators.http import require_http_methods
from gitshell.help.Forms import ResetAccessLimitForm
from gitshell.gsuser.middleware import ACL_KEY, ACCESS_WITH_IN_TIME

def default(request):
    response_dictionary = {}
    return render_to_response('help/default.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def quickstart(request):
    response_dictionary = {}
    return render_to_response('help/default.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def error(request):
    response_dictionary = {}
    return render_to_response('help/error.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def access_out_of_limit(request):
    resetAccessLimitForm = ResetAccessLimitForm()
    response_dictionary = {'resetAccessLimitForm': resetAccessLimitForm}
    return render_to_response('help/access_out_of_limit.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

@require_http_methods(["POST"])
def reset_access_limit(request):
    resetAccessLimitForm = ResetAccessLimitForm(request.POST)
    if resetAccessLimitForm.is_valid() and request.user.is_authenticated():
        user_id = request.user.id
        key = '%s:%s' % (ACL_KEY, user_id)
        cache.set(key, 1, ACCESS_WITH_IN_TIME)
    return HttpResponseRedirect('/home/')

