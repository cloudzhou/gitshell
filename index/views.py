from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response
from gitshell.repo.models import RepoManager
from gitshell.gsuser.models import GsuserManager
from gitshell.explore.views import get_hot_repo_ids

def index(request):
    repo_ids = get_hot_repo_ids()
    raw_repos = RepoManager.list_repo_by_ids(repo_ids)
    repos = [x for x in raw_repos if x.auth_type != 2]
    user_ids = [x.user_id for x in repos]
    users_dict = GsuserManager.map_users(user_ids)
    username_dict = dict([(users_dict[x]['id'], users_dict[x]['username']) for x in users_dict])
    userimgurl_dict = dict([(users_dict[x]['id'], users_dict[x]['imgurl']) for x in users_dict])
    response_dictionary = {'repos': repos, 'users_dict': users_dict, 'username_dict': username_dict, 'userimgurl_dict': userimgurl_dict}
    #print repos, users_dict, username_dict
    return render_to_response('index.html',
                          response_dictionary,
                          context_instance=RequestContext(request))
def home(request):
    response_dictionary = {'hello_world': 'hello world'}
    return render_to_response('user/home.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

