from django.db import models
import os

class Userprofile(models.Model):
    create_time = models.DateTimeField(auto_now=False, auto_now_add=True, null=False)
    modify_time = models.DateTimeField(auto_now=True, auto_now_add=True, null=False)
    visibly = models.SmallIntegerField(default=0, null=False)

    tweet = models.CharField(max_length=128)
    nickname = models.CharField(max_length=30)
    company = models.CharField(max_length=64)
    location = models.CharField(max_length=64)
    resume = models.CharField(max_length=2048)
