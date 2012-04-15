from django.db import models

class Repos(models.Model):
    create_time = models.DateTimeField(auto_now=False, auto_now_add=True, null=False)
    modify_time = models.DateTimeField(auto_now=True, auto_now_add=True, null=False)
    visibly = models.SmallIntegerField(default=0, null=False)

    user_id = models.IntegerField()
    name = models.CharField(max_length=64)
    desc = models.CharField(max_length=512, null=True)
    lang = models.CharField(max_length=16)
    auth_type = models.SmallIntegerField(default=0, null=False)
    quote = models.BigIntegerField(default=0, null=False)
