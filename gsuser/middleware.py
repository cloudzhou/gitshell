from django.contrib import auth
from django.utils.functional import lazy
from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import SimpleLazyObject
from gitshell.gsuser.models import Userprofile

def get_userprofile(request):
    if not hasattr(request, '_cached_userprofile'):
        if request.user.is_authenticated():
            request._cached_userprofile = Userprofile.objects.get(id = request.user.id)
    return request._cached_userprofile


class UserprofileMiddleware(object):
    def process_request(self, request):
        request.userprofile = SimpleLazyObject(lambda: get_userprofile(request))

def userprofile(request):
    if hasattr(request, 'userprofile'):
        userprofile = request.userprofile
    else:
        userprofile = Userprofile()

    return {'userprofile': userprofile }

