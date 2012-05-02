from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth.models import User
from gitshell.repos.models import ReposManager
from gitshell.keyauth.models import UserPubkey, KeyauthManager
from gitshell.dist.views import repos as dist_repos

def pubkey(request, fingerprint):
    userPubkey = KeyauthManager.get_userpubkey_by_fingerprint(fingerprint)
    if userPubkey is not None:
        return HttpResponse(userPubkey.key, content_type="text/plain")
    return HttpResponse("", content_type="text/plain")

# TODO repos member support
def keyauth(request, fingerprint, username, reposname):
    try:
        user = User.objects.get(username = username)
    except User.DoesNotExist:
        return HttpResponse("None", content_type="text/plain")
    repos = ReposManager.get_repos_by_userId_name(user.id, reposname)
    if repos is not None:
        return dist_repos(request, username, reposname)
    return HttpResponse("None", content_type="text/plain")
