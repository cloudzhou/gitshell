import logging, traceback
from django.contrib import auth
from django.core.cache import cache
from django.utils.functional import lazy
from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import SimpleLazyObject
from django.http import HttpResponse, HttpResponseRedirect, Http404
from gitshell.gsuser.models import GsuserManager
from django.dispatch import receiver
from django.db.models.signals import post_save
from gitshell.objectscache.da import da_post_save

MAIN_NAVS = ['index', 'stats', 'skills', 'home', 'login', 'logout', 'join', 'resetpassword', 'help', 'settings', 'private', 'captcha', 'ajax', 'explore', 'error']

def get_userprofile(request):
    if not hasattr(request, '_cached_userprofile'):
        if request.user.is_authenticated():
            request._cached_userprofile = GsuserManager.get_userprofile_by_id(request.user.id)
    return request._cached_userprofile


class UserprofileMiddleware(object):
   def process_request(self, request):
        request.userprofile = SimpleLazyObject(lambda: get_userprofile(request))

ACL_KEY = 'ACL'
ACCESS_WITH_IN_TIME = 30*60
MAX_ACCESS_TIME = 500
OUT_OF_AccessLimit_URL = '/help/access_out_of_limit/'
class UserAccessLimitMiddleware(object):
    def process_request(self, request):
        path = request.path
        if path.startswith('/help/') or path.startswith('/captcha/'):
            return
        if request.user.is_authenticated():
            user_id = request.user.id
            key = '%s:%s' % (ACL_KEY, user_id)
            value = cache.get(key)
            if value is None:
                cache.add(key, 1, ACCESS_WITH_IN_TIME)
                return
            if value > MAX_ACCESS_TIME:
                return HttpResponseRedirect(OUT_OF_AccessLimit_URL)
            cache.incr(key)

class ExceptionLoggingMiddleware(object):
    def process_exception(self, request, exception):
        logger = logging.getLogger('gitshell')
        logger.error(traceback.format_exc())
        return None

def userprofile(request):
    if hasattr(request, 'userprofile'):
        userprofile = request.userprofile
    else:
        userprofile = Userprofile()
    return {'userprofile': userprofile }

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

def __cache_version_update(sender, **kwargs):
    da_post_save(kwargs['instance'])

post_save.connect(__cache_version_update)

