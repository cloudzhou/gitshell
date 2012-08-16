import time, hashlib
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

round_time_list_cache = {}
round_type_map = {'hour': 0, 'day': 1, 'week': 2, 'month': 3, 'year':4}

class StatsUser(models.Model):
    statstype = models.SmallIntegerField(default=0)
    datetype = models.SmallIntegerField(default=0)
    date = models.DateTimeField()
    user_id = models.IntegerField()
    repo_id = models.IntegerField()
    count = models.IntegerField(default=0)
    hash_id = models.IntegerField()

    @classmethod
    def create_stats_user(self, statstype, datetype, date, user_id, repo_id, count, hash_id):
        return StatsUser(statstype=statstype, datetype=datetype, date=date, user_id=user_id, repo_id=repo_id, count=count, hash_id=hash_id)

class StatsRepo(models.Model):
    statstype = models.SmallIntegerField(default=0)
    datetype = models.SmallIntegerField(default=0)
    date = models.DateTimeField()
    repo_id = models.IntegerField()
    user_id = models.IntegerField()
    count = models.IntegerField(default=0)
    hash_id = models.IntegerField()

    @classmethod
    def create_stats_repo(self, statstype, datetype, date, repo_id, user_id, count, hash_id):
        return StatsRepo(statstype=statstype, datetype=datetype, date=date, repo_id=repo_id, user_id=user_id, count=count, hash_id=hash_id)


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
        user_stats = query(StatsUser, user_id, 'statsuser_l_cons', [user_id, 0, datetype, fromDateTime, toDateTime])
        return user_stats

    @classmethod
    def list_user_repo_stats(self, user_id, datetypeStr, fromDateTime):
        if datetypeStr not in self.datetypeDict:
            return []
        datetype = self.datetypeDict[datetypeStr]
        user_stats = query(StatsUser, user_id, 'per_statsuser_l_cons', [user_id, 1, datetype, fromDateTime])
        return user_stats

    @classmethod
    def list_repo_stats(self, repo_id, datetypeStr, fromDateTime, toDateTime):
        if datetypeStr not in self.datetypeDict:
            return []
        datetype = self.datetypeDict[datetypeStr]
        repo_stats = query(StatsRepo, repo_id, 'statsrepo_l_cons', [repo_id, 0, datetype, fromDateTime, toDateTime])
        return repo_stats

    @classmethod
    def list_repo_user_stats(self, repo_id, datetypeStr, fromDateTime):
        if datetypeStr not in self.datetypeDict:
            return []
        datetype = self.datetypeDict[datetypeStr]
        repo_stats = query(StatsRepo, repo_id, 'per_statsrepo_l_cons', [repo_id, 1, datetype, fromDateTime])
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
            if repo is None or (commitor is None and author is None):
                continue
            (round_hour, round_day, round_week, round_month, round_year) = self.__get_round_time_list(timestamp)
            for (round_type, round_time) in [('hour', round_hour), ('day', round_day), ('week', round_week), ('month', round_month), ('year', round_year)]:
                timestamp = round_time
                if round_type == 'hour' and now - int(timestamp) > 60*60*24:
                    continue
                if round_type == 'day' and now - int(timestamp) > 31*60*60*24:
                    continue
                if commitor is not None:
                    usertimekey = 'user_%s_%s_%s' % (round_type, commitor, timestamp)
                    if usertimekey not in stats_map:
                        stats_map[usertimekey] = 0
                    stats_map[usertimekey] = stats_map[usertimekey] + 1
                repotimekey = 'repo_%s_%s_%s' % (round_type, repo, timestamp)
                if repotimekey not in stats_map:
                    stats_map[repotimekey] = 0
                stats_map[repotimekey] = stats_map[repotimekey] + 1
        
                if round_type == 'hour' or round_type == 'day':
                    continue
                if author is not None:
                    per_usertimekey = 'userrepo_%s_%s_%s_%s' % (round_type, author, repo, timestamp)
                    if per_usertimekey not in per_stats_map:
                        per_stats_map[per_usertimekey] = 0
                    per_stats_map[per_usertimekey] = per_stats_map[per_usertimekey] + 1
                    per_repotimekey = 'repouser_%s_%s_%s_%s' % (round_type, repo, author, timestamp)
                    if per_repotimekey not in per_stats_map:
                        per_stats_map[per_repotimekey] = 0
                    per_stats_map[per_repotimekey] = per_stats_map[per_repotimekey] + 1

        for k, v in stats_map.items():
            (stats_type, raw_round_type, stats_id, round_time) = k.split('_')
            stats_count = v
            round_type = round_type_map[raw_round_type]
            stats_date = datetime.fromtimestamp(int(round_time))
            if stats_type == 'user':
                user_id = int(stats_id)
                hash_id = self.generate_stats_hash_id(0, round_type, stats_date, user_id, 0)
                statsuser = StatsUser.create_stats_user(0, round_type, stats_date, user_id, 0, stats_count, hash_id)
                exists_statsuser = self.__get_stats_user(user_id, hash_id)
                if exists_statsuser is not None:
                    exists_statsuser.count = exists_statsuser.count + stats_count
                    exists_statsuser.save()
                else:
                    statsuser.save()
            elif stats_type == 'repo':
                repo_id = int(stats_id)
                hash_id = self.generate_stats_hash_id(0, round_type, stats_date, repo_id, 0)
                statsrepo = StatsRepo.create_stats_repo(0, round_type, stats_date, repo_id, 0, stats_count, hash_id)
                exists_statsrepo = self.__get_stats_repo(repo_id, hash_id)
                if exists_statsrepo is not None:
                    exists_statsrepo.count = exists_statsrepo.count + stats_count
                    exists_statsrepo.save()
                else:
                    statsrepo.save()

        for k, v in per_stats_map.items():
            (stats_type, raw_round_type, id1, id2, round_time) = k.split('_')
            stats_count = v
            round_type = round_type_map[raw_round_type]
            stats_date = datetime.fromtimestamp(int(round_time))
            if stats_type == 'userrepo':
                user_id = int(id1)
                repo_id = int(id2)
                hash_id = self.generate_stats_hash_id(0, round_type, stats_date, user_id, repo_id)
                statsuser = StatsUser.create_stats_user(1, round_type, stats_date, user_id, repo_id, stats_count, hash_id)
                exists_statsuser = self.__get_stats_user(user_id, hash_id)
                if exists_statsuser is not None:
                    exists_statsuser.count = exists_statsuser.count + stats_count
                    exists_statsuser.save()
                else:
                    statsuser.save()
            elif stats_type == 'repouser':
                repo_id = int(id1)
                user_id = int(id2)
                hash_id = self.generate_stats_hash_id(0, round_type, stats_date, user_id, repo_id)
                statsrepo = StatsRepo.create_stats_repo(1, round_type, stats_date, repo_id, user_id, stats_count, hash_id)
                exists_statsrepo = self.__get_stats_repo(repo_id, hash_id)
                if exists_statsrepo is not None:
                    exists_statsrepo.count = exists_statsrepo.count + stats_count
                    exists_statsrepo.save()
                else:
                    statsrepo.save()

    # eval hash id
    @classmethod
    def generate_stats_hash_id(self, statstype, datetype, date, user_id, repo_id):
        hash_id = int(hashlib.md5('%s|%s|%s|%s|%s' % (statstype, datetype, date, user_id, repo_id)).hexdigest()[0:6], 16)
        return hash_id

    @classmethod
    def __get_stats_user(self, user_id, hash_id):
        user_stats = query(StatsUser, user_id, 'statsuser_s_hash_id', [user_id, hash_id])
        if len(user_stats) > 0:
            return user_stats[0]
        return None

    @classmethod
    def __get_stats_repo(self, repo_id, hash_id):
        repo_stats = query(StatsRepo, repo_id, 'statsrepo_s_hash_id', [repo_id, hash_id])
        if len(repo_stats) > 0:
            return repo_stats[0]
        return None

    @classmethod
    def __get_round_time_list(self, timestamp):
        global round_time_list_cache
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

