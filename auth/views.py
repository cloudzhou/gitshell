# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect, Http404

def home(request):
    return HttpResponse("auth and distributed", content_type="text/plain")

def fingerprint(request, pfingerprint):
    return HttpResponse("auth and distributed", content_type="text/plain")
