from django.db import models
from gitshell.objectscache.models import BaseModel

class Stats(BaseModel):
    stype = models.IntegerField(default=0)
    sid = models.IntegerField(default=0)
    stime = models.DateTimeField(null=False)
    count = models.IntegerField(default=0)
