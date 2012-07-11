from django.db import models
from gitshell.objectscache.models import BaseModel

# limit sql update times !
# user:
# id stats_type stats_date user_id commit_count
# id stats_type stats_date user_id repo_id commit_count

# repo:
# id stats_type stats_date repo_id commit_count
# id stats_type stats_date repo_id user_id commit_count

class Stats(BaseModel):
    stype = models.IntegerField(default=0)
    sid = models.IntegerField(default=0)
    stime = models.DateTimeField(null=False)
    count = models.IntegerField(default=0)

