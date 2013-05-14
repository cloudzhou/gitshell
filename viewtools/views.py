import time, json, functools
from sets import Set
from datetime import datetime
from django.utils.html import escape
from django.http import HttpResponse, HttpResponseRedirect, Http404

def json_httpResponse(o):
    return json_httpResponse_obj2dict(o, False)

def json_httpResponse_obj2dict(o, is_obj2dict):
    if is_obj2dict:
        o = obj2dict(o)
    return HttpResponse(json_escape_dumps(o), mimetype='application/json')

def json_escape_dumps(o):
    json.encoder.encode_basestring = encoder
    #json.encoder.encode_basestring_ascii = functools.partial(encoder, _encoder=json.encoder.encode_basestring_ascii)
    json.encoder.encode_basestring_ascii = encoder
    return json.dumps(o)

def encoder(o, _encoder=json.encoder.encode_basestring):
    if isinstance(o, basestring):
        o = escape(o)
    return _encoder(o)

def obj2dict(obj):
    id_set = Set()
    return _recursion_obj2dict(id_set, obj)

def _recursion_obj2dict(id_set, obj):
    if obj is None:
        return None
    if isinstance(obj, (basestring, int, long, float, complex)):
        return obj
    if isinstance(obj, datetime):
        return time.mktime(obj.timetuple())
    if isinstance(obj, list):
        lobj = []
        for x in list(obj):
            lobj.append(_recursion_obj2dict(id_set, x))
        return lobj
    if isinstance(obj, dict):
        dobj = {}
        for key, value in dict(obj).items():
            dobj[_recursion_obj2dict(id_set, key)] = _recursion_obj2dict(id_set, value)
        return dobj
    if isinstance(obj, object):
        uuid = id(obj)
        if uuid in id_set:
            return None
        id_set.add(uuid)
        _dict = {}
        for key, value in obj.__dict__.iteritems():
            if not key.startswith('_') and not callable(value):
                _dict[_recursion_obj2dict(id_set, key)] = _recursion_obj2dict(id_set, value)
        return _dict


