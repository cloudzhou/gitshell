from django.db import models
from gitshell.objectscache.models import BaseModel
from gitshell.objectscache.da import query, queryraw, execute, count, countraw

class Userprofile(BaseModel):
    tweet = models.CharField(max_length=128, null=True)
    nickname = models.CharField(max_length=30, null=True)
    website = models.CharField(max_length=64, null=True) 
    company = models.CharField(max_length=64, null=True)
    location = models.CharField(max_length=64, null=True)
    resume = models.CharField(max_length=2048, null=True)
    imgurl = models.CharField(max_length=32, null=True)

    pubrepos = models.IntegerField(null=False, default=0) 
    prirepos = models.IntegerField(null=False, default=0)
    watch = models.IntegerField(null=False, default=0)
    be_watched = models.IntegerField(null=False, default=0)
    quote = models.BigIntegerField(null=False, default=67108864)
    used_quote = models.BigIntegerField(null=False, default=0)

class UserprofileManager():

    @classmethod
    def get_userprofile_by_id(self, user_id):
        userprofiles = query(Userprofile, 'gsuser_userprofile', user_id, 'userprofile_s_id', [user_id])
        if len(list(userprofiles)) > 0:
            return userprofiles[0]
        return None

