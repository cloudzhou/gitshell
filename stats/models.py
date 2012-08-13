import time
from datetime import datetime, timedelta
from django.db import models
from gitshell.objectscache.models import BaseModel
from gitshell.objectscache.da import query, queryraw, execute, count, get, get_many

# limit sql update count !
# statstype {0: sum, 1: per}
# datetype  {0: hour, 1: day, 2: week, 3: month, 4: year}

# user:
# id user_id repo_id commit_count
# repo:
# id repo_id user_id commit_count

class StatsUser(models.Model):
    statstype = models.SmallIntegerField(default=0)
    datetype = models.SmallIntegerField(default=0)
    date = models.DateTimeField()
    user_id = models.IntegerField()
    repo_id = models.IntegerField()
    count = models.IntegerField(default=0)

    @classmethod
    def create_stats_user(self, statstype, datetype, date, user_id, repo_id, count):
        return StatsUser(statstype=statstype, datetype=datetype, date=date, user_id=user_id, repo_id=repo_id, count=count)

class StatsRepo(models.Model):
    statstype = models.SmallIntegerField(default=0)
    datetype = models.SmallIntegerField(default=0)
    date = models.DateTimeField()
    repo_id = models.IntegerField()
    user_id = models.IntegerField()
    count = models.IntegerField(default=0)

    @classmethod
    def create_stats_repo(self, statstype, datetype, date, repo_id, user_id, count):
        return StatsRepo(statstype=statstype, datetype=datetype, date=date, repo_id=repo_id, user_id=user_id, count=count)


class StatsManager():

    datetypeDict = {
        'hour': 0,
        'day': 1,
        'week': 2,
        'month': 3,
        'year': 4,
    }
    @classmethod
    def list_user_stats(self, user_id, datetypeStr, fromDateTime, toDateTime):
        if datetypeStr not in self.datetypeDict:
            return []
        datetype = self.datetypeDict[datetypeStr]
        user_stats = query(StatsUser, user_id, 'statsuser_l_cons', [0, datetype, fromDateTime, toDateTime, user_id])
        return user_stats

    @classmethod
    def list_user_repo_stats(self, user_id, datetypeStr, fromDateTime):
        if datetypeStr not in self.datetypeDict:
            return []
        datetype = self.datetypeDict[datetypeStr]
        user_stats = query(StatsUser, user_id, 'per_statsuser_l_cons', [1, datetype, fromDateTime, user_id])
        return user_stats

    @classmethod
    def list_repo_stats(self, repo_id, datetypeStr, fromDateTime, toDateTime):
        if datetypeStr not in self.datetypeDict:
            return []
        datetype = self.datetypeDict[datetypeStr]
        repo_stats = query(StatsRepo, repo_id, 'statsrepo_l_cons', [0, datetype, fromDateTime, toDateTime, repo_id])
        return repo_stats

    @classmethod
    def list_repo_user_stats(self, repo_id, datetypeStr, fromDateTime):
        if datetypeStr not in self.datetypeDict:
            return []
        datetype = self.datetypeDict[datetypeStr]
        repo_stats = query(StatsRepo, repo_id, 'per_statsrepo_l_cons', [1, datetype, fromDateTime, repo_id])
        return repo_stats

    @classmethod
    def list_allrepo_stats(self, datetypeStr, fromDateTime, offset, row_count):
        if datetypeStr not in self.datetypeDict:
            return []
        datetype = self.datetypeDict[datetypeStr]
        repo_stats = query(StatsRepo, None, 'allstatsrepo_l_cons', [1, datetype, fromDateTime, offset, row_count])
        return repo_stats

    @classmethod
    def stats(self, commits):
        stats_map = {}
        per_stats_map = {}
        now = int(time.time())
        for commit in commits:
            (repo, commitor, author, timestamp) = (commit[0], commit[1], commit[2], commit[3])
            (round_hour, round_day, round_week, round_month, round_year) = self.__get_round_time_list(timestamp)
            for (round_type, round_time) in [('hour', round_hour), ('day', round_day), ('week', round_week), ('month', round_month), ('year', round_year)]:
                timestamp = round_time
                # TODO
                #if now - int(timestamp) > yearinseconds:
                #    continue
                #if round_type == 'hour' and now - int(timestamp) > 60*60*24:
                #    continue
                usertimekey = 'user_%s_%s_%s' % (round_type, commitor, timestamp)
                repotimekey = 'repo_%s_%s_%s' % (round_type, repo, timestamp)
                if usertimekey not in stats_map:
                    stats_map[usertimekey] = 0
                if repotimekey not in stats_map:
                    stats_map[repotimekey] = 0
                stats_map[usertimekey] = stats_map[usertimekey] + 1
                stats_map[repotimekey] = stats_map[repotimekey] + 1
        
                #if round_type == 'hour':
                #    continue
                per_usertimekey = 'userrepo_%s_%s_%s_%s' % (round_type, author, repo, timestamp)
                per_repotimekey = 'repouser_%s_%s_%s_%s' % (round_type, repo, author, timestamp)
                if per_usertimekey not in per_stats_map:
                    per_stats_map[per_usertimekey] = 0
                if per_repotimekey not in per_stats_map:
                    per_stats_map[per_repotimekey] = 0
                per_stats_map[per_usertimekey] = per_stats_map[per_usertimekey] + 1
                per_stats_map[per_repotimekey] = per_stats_map[per_repotimekey] + 1

    round_time_list_cache = {}
    @classmethod
    def __get_round_time_list(self, timestamp):
        dt = datetime.fromtimestamp(timestamp)
        round_hour = datetime(dt.year, dt.month, dt.day, dt.hour)
        if round_hour in round_time_list_cache:
            return round_time_list_cache[round_hour]
        round_day = datetime(dt.year, dt.month, dt.day)
        round_week = round_day + timedelta(days=-dt.weekday())
        round_month = datetime(dt.year, dt.month, 1)
        round_year = datetime(dt.year, 1, 1)
        round_time_list = tuple(x.strftime('%s') for x in [round_hour, round_day, round_week, round_month, round_year])
        if len(round_time_list_cache) > 1000:
            round_time_list_cache = {}
        round_time_list_cache[round_hour.strftime('%s')] = round_time_list
        return round_time_list

