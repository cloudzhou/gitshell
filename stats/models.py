from django.db import models
from gitshell.objectscache.models import BaseModel

# limit sql update times !
# stats_type{0: hour, 1: day, 2: week, 3: month, 4: year}
# user:
# id stats_type stats_date user_id commit_count
# id stats_type stats_date user_id repo_id commit_count

# repo:
# id stats_type stats_date repo_id commit_count
# id stats_type stats_date repo_id user_id commit_count

class user(Models.Model):
    stats_type = models.SmallIntegerField(default=0)
    stats_date = models.DateTimeField()
    user_id = models.IntegerField()
    commit_count = models.IntegerField(default=0)

class user_per_repo(Models.Model):
    stats_type = models.SmallIntegerField(default=0)
    stats_date = models.DateTimeField()
    user_id = models.IntegerField()
    repo_id = models.IntegerField()
    commit_count = models.IntegerField(default=0)

class repo(Models.Model):
    stats_type = models.SmallIntegerField(default=0)
    stats_date = models.DateTimeField()
    repo_id = models.IntegerField()
    commit_count = models.IntegerField(default=0)

class repo_per_user(Models.Model):
    stats_type = models.SmallIntegerField(default=0)
    stats_date = models.DateTimeField()
    repo_id = models.IntegerField()
    user_id = models.IntegerField()
    commit_count = models.IntegerField(default=0)

