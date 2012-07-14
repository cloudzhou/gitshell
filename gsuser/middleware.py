from django.contrib import auth
from django.utils.functional import lazy
from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import SimpleLazyObject
from gitshell.gsuser.models import UserprofileManager

def get_userprofile(request):
    if not hasattr(request, '_cached_userprofile'):
        if request.user.is_authenticated():
            request._cached_userprofile = UserprofileManager.get_userprofile_by_id(request.user.id)
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

mainnavs = ['index', 'stats', 'skills', 'home', 'login', 'logout', 'join', 'resetpassword', 'help', 'settings', 'private', 'captcha', 'ajax']
def mainnav(request):
    path = request.path
    if path == '' or path == '/':
        return {'mainnav': 'home' }
    second_slash_index = path.find('/', 1)
    if second_slash_index == -1:
        mainnav = path[1:]
    else:
        mainnav = path[1:second_slash_index]
    return {'mainnav': mainnav }
