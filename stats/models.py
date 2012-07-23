from django.db import models
from gitshell.objectscache.models import BaseModel

# limit sql update count !
# statstype {0: sum, 1: per}
# datetype  {0: hour, 1: day, 2: week, 3: month, 4: year}

# user:
# id user_id repo_id commit_count
# repo:
# id repo_id user_id commit_count

class user(models.Model):
    statstype = models.SmallIntegerField(default=0)
    datetype = models.SmallIntegerField(default=0)
    date = models.DateTimeField()
    user_id = models.IntegerField()
    repo_id = models.IntegerField()
    count = models.IntegerField(default=0)

    @classmethod
    def create_stats_user(self, statstype, datetype, date, user_id, repo_id, count):
        return user(statstype=statstype, datetype=datetype, date=date, user_id=user_id, repo_id=repo_id, count=count)

class repo(models.Model):
    statstype = models.SmallIntegerField(default=0)
    datetype = models.SmallIntegerField(default=0)
    date = models.DateTimeField()
    repo_id = models.IntegerField()
    user_id = models.IntegerField()
    count = models.IntegerField(default=0)

    @classmethod
    def create_stats_repo(self, statstype, datetype, date, repo_id, user_id, count):
        return repo(statstype=statstype, datetype=datetype, date=date, repo_id=repo_id, user_id=user_id, count=count)


class StatsManager():

    @classmethod
    def list_user_stats(stats_type, datetype):
        pass

    @classmethod
    def list_user_repo_stats(stats_type, datetype):
        pass

    @classmethod
    def list_repo_stats(stats_type, datetype):
        pass

    @classmethod
    def list_repo_user_stats(stats_type, datetype):
        pass

