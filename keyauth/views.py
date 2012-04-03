# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect, Http404

def fingerprint(request, pfingerprint):
    return HttpResponse("auth and distributed", content_type="text/plain")
