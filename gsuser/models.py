from django.db import models
from django.contrib.auth.models import User, UserManager
from gitshell.objectscache.models import BaseModel
from gitshell.objectscache.da import query, get, get_many, execute, count, countraw

class Userprofile(BaseModel):
    tweet = models.CharField(max_length=128, null=True)
    nickname = models.CharField(max_length=30, null=True)
    website = models.CharField(max_length=64, null=True) 
    company = models.CharField(max_length=64, null=True)
    location = models.CharField(max_length=64, null=True)
    resume = models.CharField(max_length=2048, null=True)
    imgurl = models.CharField(max_length=32, null=True)

    pubrepo = models.IntegerField(null=False, default=0) 
    prirepo = models.IntegerField(null=False, default=0)
    watch = models.IntegerField(null=False, default=0)
    be_watched = models.IntegerField(null=False, default=0)
    quote = models.BigIntegerField(null=False, default=67108864)
    used_quote = models.BigIntegerField(null=False, default=0)

class UserprofileManager():

    @classmethod
    def get_user_by_id(self, user_id):
        return get(User, 'auth_user', user_id)

    @classmethod
    def get_user_by_name(self, username):
        try:
            user = User.objects.get(username=username)
            return user
        except User.DoesNotExist:
            return None 

    @classmethod
    def list_user_by_ids(self, user_ids):
        return get_many(User, 'auth_user', user_ids)

    @classmethod
    def get_userprofile_by_id(self, user_id):
        return get(Userprofile, 'gsuser_userprofile', user_id)
    
    @classmethod
    def get_userprofile_by_name(self, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None 
        return self.get_userprofile_by_id(user.id)
