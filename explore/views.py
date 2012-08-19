# -*- coding: utf-8 -*-  
from datetime import datetime
from datetime import timedelta
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from gitshell.repo.models import RepoManager
from gitshell.stats import timeutils
from gitshell.stats.models import StatsManager
from gitshell.gsuser.models import GsuserManager
from gitshell.feed.feed import FeedAction
from gitshell.feed.views import latest_feeds_as_json


def explore(request):
    repo_ids = get_hot_repo_ids()
    repos = RepoManager.list_repo_by_ids(repo_ids)
    user_ids = [x.user_id for x in repos]
    users_dict = GsuserManager.map_users(user_ids)
    username_dict = dict([(users_dict[x]['id'], users_dict[x]['username']) for x in users_dict])
    userimgurl_dict = dict([(users_dict[x]['id'], users_dict[x]['imgurl']) for x in users_dict])

    feedAction = FeedAction()
    latest_feeds = feedAction.get_latest_feeds(0, 100)
    feeds_as_json = latest_feeds_as_json(request, latest_feeds)

    response_dictionary = {'repos': repos, 'users_dict': users_dict, 'username_dict': username_dict, 'userimgurl_dict': userimgurl_dict, 'feeds_as_json': feeds_as_json}
    return render_to_response('explore/explore.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

random_page = 0
max_page = 1
def get_hot_repo_ids():
    global random_page
    random_page = random_page + 1
    day_page = random_page % max_page
    week_page = (day_page + 1) % max_page
    month_page = (week_page + 1) % max_page
    now = datetime.now()
    round_day = timeutils.get_round_day(now)
    round_week = timeutils.get_round_week(now)
    round_month = timeutils.get_round_month(now)
    day_stats_repo = StatsManager.list_allrepo_stats('day', round_day, 20*day_page, 20*(day_page+1))
    week_stats_repo = StatsManager.list_allrepo_stats('week', round_week, 20*week_page, 20*(week_page+1))
    month_stats_repo = StatsManager.list_allrepo_stats('month', round_month, 20*month_page, 20*(month_page+1))
    uniq_repo_dict = {}
    uniq_repo_ids = []
    for statsrepo in (day_stats_repo + week_stats_repo + month_stats_repo):
        if statsrepo.repo_id not in uniq_repo_dict:
            uniq_repo_dict[statsrepo.repo_id] = 1
            uniq_repo_ids.append(statsrepo.repo_id)
    return uniq_repo_ids

