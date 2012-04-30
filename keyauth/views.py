# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect, Http404

def pubkey(request, fingerprint):
    return HttpResponse("auth and distributed", content_type="text/plain")

def keyauth(request, fingerprint, username, reposname):
    return HttpResponse("auth and distributed", content_type="text/plain")
