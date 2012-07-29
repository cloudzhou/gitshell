# -*- coding: utf-8 -*-  
import json, time
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

def stats(request):
    stats_dict = {}
    if request.user.is_authenticated():
        stats_dict = get_stats_dict(request)
    repo_ids = get_hot_repo_ids()
    repos = RepoManager.list_repo_by_ids(repo_ids)
    user_ids = [x.user_id for x in repos]
    users_dict = GsuserManager.map_users(user_ids)
    response_dictionary = {}
    response_dictionary.update(stats_dict)
    print users_dict
    username_dict = dict([(users_dict[x]['id'], users_dict[x]['username']) for x in users_dict])
    userimgurl_dict = dict([(users_dict[x]['id'], users_dict[x]['imgurl']) for x in users_dict])
    response_dictionary.update({'repos': repos, 'users_dict': users_dict, 'username_dict': username_dict, 'userimgurl_dict': userimgurl_dict})
    return render_to_response('stats/stats.html',
                          response_dictionary,
                          context_instance=RequestContext(request))

def get_stats_dict(request):
    now = datetime.now()
    last12hours = timeutils.getlast12hours(now)
    last7days = timeutils.getlast7days(now)
    last30days = timeutils.getlast30days(now)
    last12months = timeutils.getlast12months(now)
    user = request.user
    raw_last12hours_commit = StatsManager.list_user_stats(user.id, 'hour', datetime.fromtimestamp(last12hours[-1]), datetime.fromtimestamp(last12hours[0]))
    last12hours_commit = dict([(time.mktime(x.date.timetuple()), int(x.count)) for x in raw_last12hours_commit])
    raw_last30days_commit = StatsManager.list_user_stats(user.id, 'day', datetime.fromtimestamp(last30days[-1]), datetime.fromtimestamp(last30days[0]))
    last30days_commit = dict([(time.mktime(x.date.timetuple()), int(x.count)) for x in raw_last30days_commit])
    last7days_commit = {}
    for x in last7days:
        if x in raw_last30days_commit:
            last7days_commit[x] = raw_last30days_commit[x].count
    raw_last12months_commit = StatsManager.list_user_stats(user.id, 'month', datetime.fromtimestamp(last12months[-1]), datetime.fromtimestamp(last12months[0]))
    last12months_commit = dict([(time.mktime(x.date.timetuple()), int(x.count)) for x in raw_last12months_commit])

    round_week = timeutils.get_round_week(now)
    round_month = timeutils.get_round_month(now)
    round_year = timeutils.get_round_year(now)
    raw_per_last_week_commit = StatsManager.list_user_repo_stats(user.id, 'week', round_week)
    raw_per_last_month_commit = StatsManager.list_user_repo_stats(user.id, 'month', round_month)
    raw_per_last_year_commit = StatsManager.list_user_repo_stats(user.id, 'year', round_year)
    per_last_week_commit = [int(x.count) for x in raw_per_last_week_commit]
    per_last_month_commit = [int(x.count) for x in raw_per_last_month_commit]
    per_last_year_commit = [int(x.count) for x in raw_per_last_year_commit]
    raw_per_user_week_commit = [x.user_id for x in raw_per_last_week_commit]
    raw_per_user_month_commit = [x.user_id for x in raw_per_last_month_commit]
    raw_per_user_year_commit = [x.user_id for x in raw_per_last_year_commit]
    mergedlist = list(set(raw_per_user_week_commit + raw_per_user_month_commit + raw_per_user_year_commit))
    user_dict = GsuserManager.map_users(mergedlist)
    per_user_week_commit = [str(user_dict[x]['username']) if x in user_dict else 'unknow' for x in raw_per_user_week_commit]
    per_user_month_commit = [str(user_dict[x]['username']) if x in user_dict else 'unknow' for x in raw_per_user_month_commit]
    per_user_year_commit = [str(user_dict[x]['username']) if x in user_dict else 'unknow' for x in raw_per_user_year_commit]

    userprofile = GsuserManager.get_userprofile_by_id(user.id)
    quotes = {'used_quote': int(userprofile.used_quote), 'total_quote': int(userprofile.quote)}

    stats_dict = {'last12hours': last12hours, 'last7days': last7days, 'last30days': last30days, 'last12months': last12months, 'last12hours_commit': last12hours_commit, 'last7days_commit': last7days_commit, 'last30days_commit': last30days_commit, 'last12months_commit': last12months_commit, 'quotes': quotes, 'round_week': round_week, 'round_month': round_month, 'round_year': round_year, 'per_last_week_commit': per_last_week_commit, 'per_last_month_commit': per_last_month_commit, 'per_last_year_commit': per_last_year_commit, 'per_user_week_commit': per_user_week_commit, 'per_user_month_commit': per_user_month_commit, 'per_user_year_commit': per_user_year_commit}
    return stats_dict

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

