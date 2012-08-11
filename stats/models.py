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


