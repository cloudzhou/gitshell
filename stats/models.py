from django.db import models

class Stats(models.Model):
    create_time = models.DateTimeField(auto_now=False, auto_now_add=True, null=False)
    modify_time = models.DateTimeField(auto_now=True, auto_now_add=True, null=False)
    visibly = models.SmallIntegerField(default=0, null=False)

    stype = models.IntegerField(default=0)
    sid = models.IntegerField(default=0)
    stime = models.DateTimeField(null=False)
    count = models.IntegerField(default=0)
