import json
import functools
from django.utils.html import escape
from django.http import HttpResponse, HttpResponseRedirect, Http404

def json_httpResponse(o):
    return HttpResponse(json_escape_dumps(o), mimetype='application/json')

def json_escape_dumps(o):
    json.encoder.encode_basestring = encoder
    #json.encoder.encode_basestring_ascii = functools.partial(encoder, _encoder=json.encoder.encode_basestring_ascii)
    return json.dumps(o)

def encoder(o, _encoder=json.encoder.encode_basestring):
    if isinstance(o, basestring):
        o = escape(o)
    return _encoder(o)


