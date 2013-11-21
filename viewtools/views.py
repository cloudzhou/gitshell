import time, json, functools
from sets import Set
from datetime import datetime
from django.utils.html import escape
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth.models import User, UserManager, check_password
from gitshell.repo.models import Repo

reserve_field = {
    type(Repo()): ['deploy_url', 'dropbox_url'],
    type(User()): ['password'],
}
def json_httpResponse(o):
    return json_httpResponse_obj2dict(o, True, True)

def json_success(message):
    return json_httpResponse({'code': 200, 'result': 'success', 'message': message})

def json_failed(code, message):
    return json_httpResponse({'code': code, 'result': 'failed', 'message': message})

def json_httpResponse_obj2dict(o, is_obj2dict, is_safe):
    if is_obj2dict:
        o = obj2dict(o, is_safe)
    return HttpResponse(json_escape_dumps(o), mimetype='application/json')

def json_escape_dumps(o):
    #json.encoder.encode_basestring = encoder
    ##json.encoder.encode_basestring_ascii = functools.partial(encoder, _encoder=json.encoder.encode_basestring_ascii)
    #json.encoder.encode_basestring_ascii = encoder
    return json.dumps(o)

def encoder(o, _encoder=json.encoder.encode_basestring):
    if isinstance(o, basestring):
        o = escape(o)
    return _encoder(o)

def obj2dict(obj, is_safe):
    id_dict = {}
    return _recursion_obj2dict(id_dict, obj, True)

def _recursion_obj2dict(id_dict, obj, is_safe):
    if obj is None:
        return None
    if isinstance(obj, basestring):
        return escape(obj)
    if isinstance(obj, (int, long, float, complex)):
        return obj
    if isinstance(obj, datetime):
        return time.mktime(obj.timetuple())
    if isinstance(obj, list):
        lobj = []
        for x in list(obj):
            lobj.append(_recursion_obj2dict(id_dict, x, is_safe))
        return lobj
    if isinstance(obj, dict):
        dobj = {}
        for key, value in dict(obj).items():
            dobj[_recursion_obj2dict(id_dict, key, is_safe)] = _recursion_obj2dict(id_dict, value, is_safe)
        return dobj
    if isinstance(obj, object):
        uuid = id(obj)
        if uuid in id_dict:
            return id_dict[uuid]
        obj_type = type(obj)
        _dict = {}
        for key, value in obj.__dict__.iteritems():
            if is_safe and obj_type in reserve_field:
                if key in reserve_field[obj_type]:
                    continue
            if not key.startswith('_') and not callable(value):
                _dict[_recursion_obj2dict(id_dict, key, is_safe)] = _recursion_obj2dict(id_dict, value, is_safe)
        id_dict[uuid] = _dict
        return _dict
    return obj


